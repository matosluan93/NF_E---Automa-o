from __future__ import annotations

from app.db.connection import get_db
from app.repositories import dashboard_repository, sequence_repository


def get_dashboard() -> dict:
    conn = get_db()
    summary = dashboard_repository.get_summary(conn)
    sequencias = sequence_repository.list_sequences(conn)
    summary["sequencias"] = sequencias
    summary["sequencia"] = sequencias[0] if sequencias else None
    return summary
