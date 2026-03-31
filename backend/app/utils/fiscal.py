from __future__ import annotations

import datetime as dt
import re
import uuid


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def today_iso() -> str:
    return dt.date.today().isoformat()


def current_time_hm() -> str:
    return dt.datetime.now().strftime("%H:%M")


def round2(value) -> float:
    return round(float(value or 0), 2)


def digits_only(value: str) -> str:
    return re.sub(r"\D", "", str(value or ""))


def generate_access_key(*, cnpj: str, uf_code: str, serie: str, numero: int, data_emissao: str) -> str:
    cnpj_digits = digits_only(cnpj).zfill(14)
    clean_date = str(data_emissao).replace("-", "")
    aamm = clean_date[2:6] if len(clean_date) >= 6 else dt.date.today().strftime("%y%m")
    modelo = "55"
    serie_pad = str(serie).zfill(3)
    numero_pad = str(numero).zfill(9)
    tp_emis = "1"
    c_nf = str(uuid.uuid4().int)[:8].zfill(8)
    raw = f"{str(uf_code).zfill(2)}{aamm}{cnpj_digits}{modelo}{serie_pad}{numero_pad}{tp_emis}{c_nf}"

    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = 0
    peso_idx = 0
    for i in range(len(raw) - 1, -1, -1):
        soma += int(raw[i]) * pesos[peso_idx]
        peso_idx = (peso_idx + 1) % len(pesos)

    resto = soma % 11
    dv = 0 if resto < 2 else 11 - resto
    chave = f"{raw}{dv}"
    return " ".join(chave[i:i + 4] for i in range(0, len(chave), 4))
