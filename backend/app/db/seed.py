from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import current_app

from app.utils.fiscal import now_iso

log = logging.getLogger(__name__)


def seed_products_if_needed() -> None:
    db_path = Path(current_app.config["DB_PATH"])
    catalog_path = Path(current_app.config["CATALOG_PATH"])

    if not catalog_path.exists():
        log.warning("Catálogo não encontrado em %s. Seed ignorado.", catalog_path)
        return

    with closing(sqlite3.connect(db_path)) as conn, conn:
        current_total = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        if current_total > 0:
            return

        raw_products = json.loads(catalog_path.read_text(encoding="utf-8"))
        deduped = {}
        duplicates = 0
        for product in raw_products:
            code = str(product.get("codigo", "")).strip()
            if not code:
                continue
            if code in deduped:
                duplicates += 1
            deduped[code] = product

        timestamp = now_iso()
        for code, product in deduped.items():
            conn.execute(
                """
                INSERT INTO produtos(
                    codigo, nome, descricao_danfe, ncm, unidade,
                    valor_unitario, aliquota_icms, cfop, ativo, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    code,
                    str(product.get("nome", "")).strip(),
                    str(product.get("descricao_danfe") or product.get("nome") or "").strip(),
                    str(product.get("ncm") or "").strip(),
                    str(product.get("unidade") or "UN").strip(),
                    float(product.get("valor_unitario") or 0),
                    float(product.get("aliquota_icms") or 0),
                    str(product.get("cfop") or "5102").strip(),
                    timestamp,
                    timestamp,
                ),
            )
        conn.commit()

    log.info(
        "Seed de produtos concluído: %s registros importados (%s duplicidades consolidadas).",
        len(deduped),
        duplicates,
    )
