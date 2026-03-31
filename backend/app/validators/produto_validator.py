from __future__ import annotations

from app.core.exceptions import AppError


def validate_product_payload(payload: dict | None, code_from_url: str | None = None) -> dict:
    if not isinstance(payload, dict):
        raise AppError("Payload inválido", 400)

    codigo = code_from_url or str(payload.get("codigo") or "").strip()
    nome = str(payload.get("nome") or "").strip()

    if not codigo:
        raise AppError("Código do produto obrigatório", 400)
    if not nome:
        raise AppError("Nome do produto obrigatório", 400)

    return {
        "codigo": codigo,
        "nome": nome,
        "descricao_danfe": str(payload.get("descricao_danfe") or nome).strip(),
        "ncm": str(payload.get("ncm") or "").strip(),
        "unidade": str(payload.get("unidade") or "UN").strip(),
        "valor_unitario": float(payload.get("valor_unitario") or 0),
        "aliquota_icms": float(payload.get("aliquota_icms") or 0),
        "cfop": str(payload.get("cfop") or "5102").strip(),
    }
