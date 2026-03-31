from __future__ import annotations

import logging
import uuid

from flask import current_app

from app.core.exceptions import AppError
from app.db.connection import get_db
from app.repositories import audit_repository, nota_repository, sequence_repository
from app.utils.fiscal import current_time_hm, generate_access_key, now_iso, round2, today_iso
from app.validators.nota_validator import validate_cancel_payload, validate_emit_payload

log = logging.getLogger(__name__)


def _emitente_defaults() -> dict:
    return dict(current_app.config["EMITENTE"])


def get_next_number_preview(serie: str) -> dict:
    conn = get_db()
    proximo = sequence_repository.get_next_preview(conn, serie)
    return {"serie": serie, "proximo": proximo}


def list_notes(*, q: str = "", status: str = "", limit: int = 50, offset: int = 0) -> dict:
    conn = get_db()
    notes, total = nota_repository.list_notes(conn, q=q, status=status, limit=limit, offset=offset)
    return {"notas": notes, "total": total, "limit": limit, "offset": offset}


def get_note(note_id: str) -> dict:
    conn = get_db()
    note = nota_repository.get_note(conn, note_id)
    if note is None:
        raise AppError("Nota não encontrada", 404)
    return note


def emit_note(payload: dict) -> dict:
    data = validate_emit_payload(payload)
    conn = get_db()
    config = current_app.config
    emitente = _emitente_defaults()
    serie = data["serie"]

    conn.execute("BEGIN IMMEDIATE")
    try:
        numero = sequence_repository.reserve_next_number(
            conn,
            serie,
            config["NF_NUMERO_INICIAL"],
        )

        note_id = str(uuid.uuid4())
        data_emissao = str(data.get("data_emissao") or today_iso())
        hora_emissao = str(data.get("hora_emissao") or current_time_hm())

        access_key = generate_access_key(
            cnpj=data.get("emit_cnpj") or emitente["cnpj"],
            uf_code=emitente["uf_codigo"],
            serie=serie,
            numero=numero,
            data_emissao=data_emissao,
        )

        items = []
        total_produtos = 0.0
        total_icms = 0.0
        total_ipi = 0.0

        for seq, item in enumerate(data["itens"], start=1):
            quantidade = float(item.get("quantidade") or 0)
            valor_unitario = float(item.get("valor_unitario") or 0)
            valor_total = round2(quantidade * valor_unitario)
            aliquota_icms = float(item.get("aliquota_icms") or 0)
            aliquota_ipi = float(item.get("aliquota_ipi") or 0)
            bc_icms = valor_total
            valor_icms = round2(bc_icms * aliquota_icms)
            valor_ipi = round2(valor_total * aliquota_ipi)

            total_produtos += valor_total
            total_icms += valor_icms
            total_ipi += valor_ipi

            items.append(
                {
                    "id": str(uuid.uuid4()),
                    "nota_id": note_id,
                    "seq": seq,
                    "codigo_produto": str(item.get("codigo_produto")).strip(),
                    "descricao": str(item.get("descricao")).strip(),
                    "ncm": str(item.get("ncm") or "").strip(),
                    "cst": str(item.get("cst") or "000").strip(),
                    "cfop": str(item.get("cfop") or "5102").replace(".", "").strip(),
                    "unidade": str(item.get("unidade") or "UN").strip(),
                    "quantidade": quantidade,
                    "valor_unitario": valor_unitario,
                    "valor_total": valor_total,
                    "bc_icms": bc_icms,
                    "aliquota_icms": aliquota_icms,
                    "valor_icms": valor_icms,
                    "aliquota_ipi": aliquota_ipi,
                    "valor_ipi": valor_ipi,
                }
            )

        total_frete = float(data.get("total_frete") or 0)
        total_seguro = float(data.get("total_seguro") or 0)
        total_desconto = float(data.get("total_desconto") or 0)
        total_nota = round2(total_produtos + total_ipi + total_frete + total_seguro - total_desconto)

        timestamp = now_iso()
        note = {
            "id": note_id,
            "numero": numero,
            "serie": serie,
            "chave_acesso": access_key,
            "status": "emitida",
            "data_emissao": data_emissao,
            "hora_emissao": hora_emissao,
            "natureza_op": str(data.get("natureza_op") or "VENDA DE MERCADORIA").strip(),
            "emit_razao": str(data.get("emit_razao") or emitente["razao"]).strip(),
            "emit_cnpj": str(data.get("emit_cnpj") or emitente["cnpj"]).strip(),
            "emit_ie": str(data.get("emit_ie") or emitente["ie"]).strip(),
            "emit_im": str(data.get("emit_im") or emitente["im"]).strip(),
            "emit_endereco": str(data.get("emit_endereco") or emitente["endereco"]).strip(),
            "emit_bairro": str(data.get("emit_bairro") or emitente["bairro"]).strip(),
            "emit_municipio": str(data.get("emit_municipio") or emitente["municipio"]).strip(),
            "emit_uf": str(data.get("emit_uf") or emitente["uf"]).strip(),
            "emit_cep": str(data.get("emit_cep") or emitente["cep"]).strip(),
            "emit_fone": str(data.get("emit_fone") or emitente["fone"]).strip(),
            "dest_nome": data["dest_nome"],
            "dest_cpf_cnpj": str(data.get("dest_cpf_cnpj") or "").strip(),
            "dest_ie": str(data.get("dest_ie") or "ISENTO").strip(),
            "dest_endereco": str(data.get("dest_endereco") or "").strip(),
            "dest_bairro": str(data.get("dest_bairro") or "").strip(),
            "dest_municipio": str(data.get("dest_municipio") or "").strip(),
            "dest_uf": str(data.get("dest_uf") or "SP").strip(),
            "dest_cep": str(data.get("dest_cep") or "").strip(),
            "dest_fone": str(data.get("dest_fone") or "").strip(),
            "total_produtos": round2(total_produtos),
            "total_icms": round2(total_icms),
            "total_ipi": round2(total_ipi),
            "total_frete": round2(total_frete),
            "total_seguro": round2(total_seguro),
            "total_desconto": round2(total_desconto),
            "total_nota": total_nota,
            "transp_frete_conta": str(data.get("transp_frete_conta") or "0").strip(),
            "info_complementar": str(
                data.get("info_complementar") or "-MERCADORIA DESTINADA A USUARIO FINAL"
            ).strip(),
            "motivo_cancelamento": None,
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        nota_repository.insert_note(conn, note, items)
        audit_repository.insert_audit(
            conn,
            tabela="notas_fiscais",
            operacao="INSERT",
            ref_id=note_id,
            dados={"numero": numero, "serie": serie, "dest_nome": data["dest_nome"]},
        )
        conn.commit()

        emitted = nota_repository.get_note(conn, note_id)
        if emitted is None:
            raise AppError("Não foi possível recuperar a nota emitida", 500)
        return emitted

    except AppError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        log.exception("Erro ao emitir NF")
        raise AppError(f"Erro interno ao emitir nota: {exc}", 500) from exc


def cancel_note(note_id: str, payload: dict | None) -> dict:
    conn = get_db()
    note = nota_repository.get_note(conn, note_id)
    if note is None:
        raise AppError("Nota não encontrada", 404)
    if note["status"] == "cancelada":
        raise AppError("Nota já cancelada", 400)

    motivo = validate_cancel_payload(payload)
    info = f"CANCELADA — {motivo}"

    nota_repository.cancel_note(conn, note_id, motivo, info)
    audit_repository.insert_audit(
        conn,
        tabela="notas_fiscais",
        operacao="CANCEL",
        ref_id=note_id,
        dados={"motivo": motivo},
    )
    conn.commit()
    return {"mensagem": "Nota cancelada com sucesso", "id": note_id, "motivo": motivo}
