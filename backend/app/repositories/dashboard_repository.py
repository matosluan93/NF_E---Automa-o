from __future__ import annotations

import sqlite3


def get_summary(conn: sqlite3.Connection) -> dict:
    total_emitidas = conn.execute(
        "SELECT COUNT(*) FROM notas_fiscais WHERE status = 'emitida'"
    ).fetchone()[0]
    total_canceladas = conn.execute(
        "SELECT COUNT(*) FROM notas_fiscais WHERE status = 'cancelada'"
    ).fetchone()[0]
    faturamento_total = conn.execute(
        "SELECT COALESCE(SUM(total_nota), 0) FROM notas_fiscais WHERE status = 'emitida'"
    ).fetchone()[0]
    ultima_nota = conn.execute(
        "SELECT numero, serie, dest_nome, total_nota, total_icms, data_emissao, status FROM notas_fiscais ORDER BY numero DESC LIMIT 1"
    ).fetchone()
    ultimas_notas = conn.execute(
        "SELECT numero, serie, dest_nome, total_nota, total_icms, data_emissao, status FROM notas_fiscais ORDER BY numero DESC LIMIT 10"
    ).fetchall()

    return {
        "total_emitidas": int(total_emitidas),
        "total_canceladas": int(total_canceladas),
        "faturamento_total": round(float(faturamento_total or 0), 2),
        "ultima_nota": dict(ultima_nota) if ultima_nota else None,
        "ultimas_notas": [dict(row) for row in ultimas_notas],
    }
