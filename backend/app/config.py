from __future__ import annotations

import os
from pathlib import Path


class Config:
    APP_NAME = os.getenv("APP_NAME", "Sistema NF-e Stefanini")
    DEBUG = os.getenv("DEBUG", "0").lower() in {"1", "true", "yes", "on"}
    HOST = os.getenv("HOST", "127.0.0.1")
    NFE_ACCESS_PASSWORD = os.getenv("NFE_ACCESS_PASSWORD", "")
    NFE_PUBLIC_ORIGIN = os.getenv("NFE_PUBLIC_ORIGIN", "").rstrip("/")
    PORT = int(os.getenv("PORT", "5000"))

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    DB_PATH = os.getenv("DB_PATH", str(PROJECT_ROOT / "db" / "nfe.db"))
    FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", str(PROJECT_ROOT / "frontend")))
    CATALOG_PATH = Path(os.getenv("CATALOG_PATH", str(PROJECT_ROOT / "data" / "catalogo.json")))

    DEFAULT_SERIE = os.getenv("DEFAULT_SERIE", "1")
    NF_NUMERO_INICIAL = int(os.getenv("NF_NUMERO_INICIAL", "26078"))

    EMITENTE = {
        "razao": os.getenv("EMIT_RAZAO", "STEFANINI COM. PRODS DE INFORMATICA E ELETROELETRONICOS LTDA"),
        "cnpj": os.getenv("EMIT_CNPJ", "17.805.881/0001-10"),
        "ie": os.getenv("EMIT_IE", "127975217112"),
        "im": os.getenv("EMIT_IM", "617475"),
        "endereco": os.getenv("EMIT_ENDERECO", "RUA JAMIL JOAO ZARIF, 684 - GALPAO06 ANEXO II"),
        "bairro": os.getenv("EMIT_BAIRRO", "JARDIM SANTA VICENCIA"),
        "municipio": os.getenv("EMIT_MUNICIPIO", "Guarulhos"),
        "uf": os.getenv("EMIT_UF", "SP"),
        "cep": os.getenv("EMIT_CEP", "07143-000"),
        "fone": os.getenv("EMIT_FONE", "(11)3094-6000"),
        "uf_codigo": os.getenv("EMIT_UF_CODIGO", "35"),
    }

    JSON_AS_ASCII = False
    SORT_JSON_KEYS = False
