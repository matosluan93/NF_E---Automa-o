from __future__ import annotations

import os
import tempfile

import pytest

from app import create_app


@pytest.fixture()
def app():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        os.environ["DB_PATH"] = db_path
        application = create_app()
        application.config.update(TESTING=True)
        yield application
        os.environ.pop("DB_PATH", None)


@pytest.fixture()
def client(app):
    return app.test_client()
