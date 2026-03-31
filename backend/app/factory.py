from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, Response, jsonify, send_from_directory

from app.api import BLUEPRINTS
from app.config import Config
from app.core.exceptions import AppError
from app.core.logging_config import configure_logging
from app.core.responses import error
from app.db.connection import close_db, init_db
from app.db.seed import seed_products_if_needed

log = logging.getLogger(__name__)


def create_app() -> Flask:
    configure_logging()

    app = Flask(__name__, static_folder=None, instance_relative_config=False)
    app.config.from_object(Config)

    frontend_dir = Path(app.config["FRONTEND_DIR"])
    frontend_dir.mkdir(parents=True, exist_ok=True)

    _register_middlewares(app)
    _register_error_handlers(app)
    _register_blueprints(app)
    _register_frontend_routes(app, frontend_dir)

    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()
        seed_products_if_needed()
        log.info("Aplicação inicializada com DB em %s", app.config["DB_PATH"])

    return app


def _register_middlewares(app: Flask) -> None:
    @app.after_request
    def apply_cors(response: Response) -> Response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    @app.route("/api/<path:_path>", methods=["OPTIONS"])
    def options_handler(_path: str):
        return jsonify({}), 200


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        return error(err.message, err.status_code)

    @app.errorhandler(404)
    def handle_not_found(_err):
        return error("Recurso não encontrado", 404)

    @app.errorhandler(Exception)
    def handle_unexpected_error(err: Exception):
        log.exception("Erro não tratado: %s", err)
        return error("Erro interno do servidor", 500)


def _register_blueprints(app: Flask) -> None:
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)


def _register_frontend_routes(app: Flask, frontend_dir: Path) -> None:
    @app.get("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/<path:filename>")
    def static_files(filename: str):
        path = frontend_dir / filename
        if path.exists() and path.is_file():
            return send_from_directory(frontend_dir, filename)
        return send_from_directory(frontend_dir, "index.html")
