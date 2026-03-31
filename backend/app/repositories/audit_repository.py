from __future__ import annotations

import json
import sqlite3
import uuid

from app.utils.fiscal import now_iso


def insert_audit(
    conn: sqlite3.Connection,
    *,
    tabela: str,
    operacao: str,
    ref_id: str | None = None,
    dados: dict | None = None,
) -> None:
    conn.execute(
        "INSERT INTO audit_log(id, tabela, operacao, ref_id, dados, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (
            str(uuid.uuid4()),
            tabela,
            operacao,
            ref_id,
            json.dumps(dados, ensure_ascii=False) if dados else None,
            now_iso(),
        ),
    )


def list_audit(conn: sqlite3.Connection, limit: int = 100) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]
