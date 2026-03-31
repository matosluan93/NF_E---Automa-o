from __future__ import annotations

from flask import Blueprint, current_app

bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    return {
        "status": "ok",
        "app": current_app.config["APP_NAME"],
    }
