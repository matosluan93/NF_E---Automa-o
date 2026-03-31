from __future__ import annotations

from flask import Blueprint

from app.core.responses import ok
from app.services.dashboard_service import get_dashboard

bp = Blueprint("dashboard", __name__, url_prefix="/api")


@bp.get("/dashboard")
def dashboard():
    return ok(get_dashboard())
