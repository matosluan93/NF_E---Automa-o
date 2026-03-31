from __future__ import annotations

from app.core.exceptions import AppError


def validate_emit_payload(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        raise AppError("Payload inválido", 400)

    serie = str(payload.get("serie") or "1").strip()
    dest_nome = str(payload.get("dest_nome") or "").strip()
    itens = payload.get("itens") or []

    if not dest_nome:
        raise AppError("Nome do destinatário obrigatório", 400)
    if not isinstance(itens, list) or not itens:
        raise AppError("A nota deve ter ao menos 1 item", 400)

    for index, item in enumerate(itens, start=1):
        if not isinstance(item, dict):
            raise AppError(f"Item {index} inválido", 400)

        descricao = str(item.get("descricao") or "").strip()
        codigo = str(item.get("codigo_produto") or "").strip()
        quantidade = float(item.get("quantidade") or 0)
        valor_unitario = float(item.get("valor_unitario") or 0)

        if not codigo:
            raise AppError(f"Item {index}: código do produto obrigatório", 400)
        if not descricao:
            raise AppError(f"Item {index}: descrição obrigatória", 400)
        if quantidade <= 0:
            raise AppError(f"Item {index}: quantidade deve ser maior que zero", 400)
        if valor_unitario < 0:
            raise AppError(f"Item {index}: valor unitário inválido", 400)

    cleaned = dict(payload)
    cleaned["serie"] = serie
    cleaned["dest_nome"] = dest_nome
    cleaned["itens"] = itens
    return cleaned


def validate_cancel_payload(payload: dict | None) -> str:
    if not payload:
        return "Cancelamento solicitado"
    motivo = str(payload.get("motivo") or "Cancelamento solicitado").strip()
    return motivo or "Cancelamento solicitado"
