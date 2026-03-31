from __future__ import annotations

import sqlite3

from app.utils.fiscal import now_iso


def list_active(conn: sqlite3.Connection, q: str = "", limit: int = 100) -> list[dict]:
    sql = "SELECT * FROM produtos WHERE ativo = 1"
    params: list[object] = []
    if q:
        like = f"%{q}%"
        sql += " AND (codigo LIKE ? OR nome LIKE ? OR descricao_danfe LIKE ?)"
        params.extend([like, like, like])
    sql += " ORDER BY codigo LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def get_by_code(conn: sqlite3.Connection, code: str) -> dict | None:
    row = conn.execute("SELECT * FROM produtos WHERE codigo = ?", (code,)).fetchone()
    return dict(row) if row else None


def upsert(conn: sqlite3.Connection, payload: dict) -> dict:
    timestamp = now_iso()
    conn.execute(
        """
        INSERT INTO produtos(
            codigo, nome, descricao_danfe, ncm, unidade,
            valor_unitario, aliquota_icms, cfop, ativo, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        ON CONFLICT(codigo) DO UPDATE SET
            nome = excluded.nome,
            descricao_danfe = excluded.descricao_danfe,
            ncm = excluded.ncm,
            unidade = excluded.unidade,
            valor_unitario = excluded.valor_unitario,
            aliquota_icms = excluded.aliquota_icms,
            cfop = excluded.cfop,
            ativo = 1,
            updated_at = excluded.updated_at
        """,
        (
            payload["codigo"],
            payload["nome"],
            payload["descricao_danfe"],
            payload["ncm"],
            payload["unidade"],
            payload["valor_unitario"],
            payload["aliquota_icms"],
            payload["cfop"],
            timestamp,
            timestamp,
        ),
    )
    return get_by_code(conn, payload["codigo"])


def deactivate(conn: sqlite3.Connection, code: str) -> None:
    conn.execute(
        "UPDATE produtos SET ativo = 0, updated_at = ? WHERE codigo = ?",
        (now_iso(), code),
    )
