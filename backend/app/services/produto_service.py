from __future__ import annotations

from app.core.exceptions import AppError
from app.db.connection import get_db
from app.repositories import audit_repository, produto_repository
from app.validators.produto_validator import validate_product_payload


def list_products(q: str = "", limit: int = 100) -> list[dict]:
    conn = get_db()
    return produto_repository.list_active(conn, q=q, limit=limit)


def create_product(payload: dict) -> dict:
    conn = get_db()
    cleaned = validate_product_payload(payload)
    product = produto_repository.upsert(conn, cleaned)
    audit_repository.insert_audit(
        conn,
        tabela="produtos",
        operacao="UPSERT",
        ref_id=cleaned["codigo"],
        dados={"codigo": cleaned["codigo"], "nome": cleaned["nome"]},
    )
    conn.commit()
    return product


def update_product(code: str, payload: dict) -> dict:
    conn = get_db()
    if produto_repository.get_by_code(conn, code) is None:
        raise AppError("Produto não encontrado", 404)

    cleaned = validate_product_payload(payload, code_from_url=code)
    product = produto_repository.upsert(conn, cleaned)
    audit_repository.insert_audit(
        conn,
        tabela="produtos",
        operacao="UPDATE",
        ref_id=code,
        dados={"codigo": cleaned["codigo"], "nome": cleaned["nome"]},
    )
    conn.commit()
    return product


def deactivate_product(code: str) -> None:
    conn = get_db()
    if produto_repository.get_by_code(conn, code) is None:
        raise AppError("Produto não encontrado", 404)

    produto_repository.deactivate(conn, code)
    audit_repository.insert_audit(
        conn,
        tabela="produtos",
        operacao="DEACTIVATE",
        ref_id=code,
    )
    conn.commit()
