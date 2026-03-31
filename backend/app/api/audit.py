from __future__ import annotations

from flask import Blueprint, request

from app.core.responses import ok
from app.services.audit_service import get_latest_audit

bp = Blueprint("audit", __name__, url_prefix="/api")


@bp.get("/audit")
def audit():
    limit = min(int(request.args.get("limit", 100)), 200)
    return ok(get_latest_audit(limit=limit))
