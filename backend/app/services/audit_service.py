from __future__ import annotations

from app.db.connection import get_db
from app.repositories.audit_repository import list_audit


def get_latest_audit(limit: int = 100) -> list[dict]:
    conn = get_db()
    return list_audit(conn, limit=limit)
