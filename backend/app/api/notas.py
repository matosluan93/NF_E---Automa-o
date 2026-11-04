from __future__ import annotations

from flask import Blueprint, request

from app.core.responses import ok
from app.services.nota_service import cancel_note, emit_note, get_next_number_preview, get_note, list_notes

bp = Blueprint("notas", __name__, url_prefix="/api")


@bp.get("/numeracao/proximo/<serie>")
def next_number(serie: str):
    return ok(get_next_number_preview(serie))


@bp.get("/notas")
def notes_list():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    limit = min(max(request.args.get("limit", 50, type=int), 1), 200)
    offset = max(request.args.get("offset", 0, type=int), 0)
    return ok(list_notes(q=q, status=status, limit=limit, offset=offset))


@bp.get("/notas/<note_id>")
def note_detail(note_id: str):
    return ok(get_note(note_id))


@bp.post("/notas")
def note_emit():
    payload = request.get_json(silent=True) or {}
    return ok(emit_note(payload), 201)


@bp.post("/notas/<note_id>/cancelar")
def note_cancel(note_id: str):
    payload = request.get_json(silent=True) or {}
    return ok(cancel_note(note_id, payload))
