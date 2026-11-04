from __future__ import annotations

import tempfile

import pytest

from app import create_app


@pytest.fixture()
def app():
    with tempfile.TemporaryDirectory() as tmp:
        yield create_app({"TESTING": True, "DB_PATH": f"{tmp}/test.db", "NFE_ACCESS_PASSWORD": ""})


@pytest.fixture()
def client(app):
    return app.test_client()
