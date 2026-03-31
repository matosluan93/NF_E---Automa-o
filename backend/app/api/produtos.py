from __future__ import annotations

from flask import Blueprint, request

from app.core.responses import ok
from app.services.produto_service import create_product, deactivate_product, list_products, update_product

bp = Blueprint("produtos", __name__, url_prefix="/api")


@bp.get("/produtos")
def products_list():
    q = request.args.get("q", "").strip()
    return ok(list_products(q=q))


@bp.post("/produtos")
def products_create():
    payload = request.get_json(silent=True) or {}
    return ok(create_product(payload), 201)


@bp.put("/produtos/<code>")
def products_update(code: str):
    payload = request.get_json(silent=True) or {}
    return ok(update_product(code, payload))


@bp.delete("/produtos/<code>")
def products_delete(code: str):
    deactivate_product(code)
    return ok({"ok": True})
