from __future__ import annotations

import sqlite3


def list_notes(
    conn: sqlite3.Connection,
    *,
    q: str = "",
    status: str = "",
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    sql = """
        SELECT n.*,
               (SELECT COUNT(*) FROM nf_itens i WHERE i.nota_id = n.id) AS qtd_itens
        FROM notas_fiscais n
        WHERE 1 = 1
    """
    params: list[object] = []

    if q:
        like = f"%{q}%"
        sql += " AND (n.dest_nome LIKE ? OR n.dest_cpf_cnpj LIKE ? OR CAST(n.numero AS TEXT) LIKE ?)"
        params.extend([like, like, like])

    if status:
        sql += " AND n.status = ?"
        params.append(status)

    total = conn.execute(f"SELECT COUNT(*) FROM ({sql})", params).fetchone()[0]
    sql += " ORDER BY n.numero DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows], int(total)


def get_note(conn: sqlite3.Connection, note_id: str) -> dict | None:
    note_row = conn.execute(
        "SELECT * FROM notas_fiscais WHERE id = ?",
        (note_id,),
    ).fetchone()
    if note_row is None:
        return None

    note = dict(note_row)
    item_rows = conn.execute(
        "SELECT * FROM nf_itens WHERE nota_id = ? ORDER BY seq",
        (note_id,),
    ).fetchall()
    note["itens"] = [dict(row) for row in item_rows]
    return note


def insert_note(conn: sqlite3.Connection, note: dict, items: list[dict]) -> None:
    conn.execute(
        """
        INSERT INTO notas_fiscais(
            id, numero, serie, chave_acesso, status,
            data_emissao, hora_emissao, natureza_op,
            emit_razao, emit_cnpj, emit_ie, emit_im,
            emit_endereco, emit_bairro, emit_municipio, emit_uf, emit_cep, emit_fone,
            dest_nome, dest_cpf_cnpj, dest_ie,
            dest_endereco, dest_bairro, dest_municipio, dest_uf, dest_cep, dest_fone,
            total_produtos, total_icms, total_ipi,
            total_frete, total_seguro, total_desconto, total_nota,
            transp_frete_conta, info_complementar, motivo_cancelamento,
            created_at, updated_at
        ) VALUES (
            :id, :numero, :serie, :chave_acesso, :status,
            :data_emissao, :hora_emissao, :natureza_op,
            :emit_razao, :emit_cnpj, :emit_ie, :emit_im,
            :emit_endereco, :emit_bairro, :emit_municipio, :emit_uf, :emit_cep, :emit_fone,
            :dest_nome, :dest_cpf_cnpj, :dest_ie,
            :dest_endereco, :dest_bairro, :dest_municipio, :dest_uf, :dest_cep, :dest_fone,
            :total_produtos, :total_icms, :total_ipi,
            :total_frete, :total_seguro, :total_desconto, :total_nota,
            :transp_frete_conta, :info_complementar, :motivo_cancelamento,
            :created_at, :updated_at
        )
        """,
        note,
    )

    for item in items:
        conn.execute(
            """
            INSERT INTO nf_itens(
                id, nota_id, seq, codigo_produto, descricao, ncm, cst, cfop,
                unidade, quantidade, valor_unitario, valor_total,
                bc_icms, aliquota_icms, valor_icms, aliquota_ipi, valor_ipi
            ) VALUES (
                :id, :nota_id, :seq, :codigo_produto, :descricao, :ncm, :cst, :cfop,
                :unidade, :quantidade, :valor_unitario, :valor_total,
                :bc_icms, :aliquota_icms, :valor_icms, :aliquota_ipi, :valor_ipi
            )
            """,
            item,
        )


def cancel_note(conn: sqlite3.Connection, note_id: str, motivo: str, info_complementar: str) -> None:
    conn.execute(
        """
        UPDATE notas_fiscais
           SET status = 'cancelada',
               motivo_cancelamento = ?,
               info_complementar = ?,
               updated_at = CURRENT_TIMESTAMP
         WHERE id = ?
        """,
        (motivo, info_complementar, note_id),
    )
