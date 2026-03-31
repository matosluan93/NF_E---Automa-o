from __future__ import annotations

import sqlite3

from app.utils.fiscal import now_iso


def get_next_preview(conn: sqlite3.Connection, serie: str) -> int:
    row = conn.execute(
        "SELECT ultimo_numero FROM nf_sequences WHERE serie = ?",
        (serie,),
    ).fetchone()
    return 1 if row is None else int(row["ultimo_numero"]) + 1


def reserve_next_number(conn: sqlite3.Connection, serie: str, initial_number: int) -> int:
    row = conn.execute(
        "SELECT ultimo_numero FROM nf_sequences WHERE serie = ?",
        (serie,),
    ).fetchone()
    if row is None:
        numero = initial_number + 1
        conn.execute(
            "INSERT INTO nf_sequences(serie, ultimo_numero, updated_at) VALUES (?, ?, ?)",
            (serie, numero, now_iso()),
        )
        return numero

    numero = int(row["ultimo_numero"]) + 1
    conn.execute(
        "UPDATE nf_sequences SET ultimo_numero = ?, updated_at = ? WHERE serie = ?",
        (numero, now_iso(), serie),
    )
    return numero


def list_sequences(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT serie, ultimo_numero, updated_at FROM nf_sequences ORDER BY serie"
    ).fetchall()
    return [dict(row) for row in rows]
