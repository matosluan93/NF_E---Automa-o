from __future__ import annotations

from flask import jsonify


def ok(payload, status_code: int = 200):
    return jsonify(payload), status_code


def error(message: str, status_code: int = 400, **extra):
    payload = {"erro": message}
    payload.update(extra)
    return jsonify(payload), status_code
