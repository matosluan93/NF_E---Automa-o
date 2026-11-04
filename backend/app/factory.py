from __future__ import annotations

import logging
import re
from ipaddress import ip_address
from secrets import compare_digest
from pathlib import Path

from flask import Flask, Response, abort, request, send_from_directory
from werkzeug.exceptions import HTTPException

from app.api import BLUEPRINTS
from app.config import Config
from app.core.exceptions import AppError
from app.core.logging_config import configure_logging
from app.core.responses import error
from app.db.connection import close_db, init_db
from app.db.seed import seed_products_if_needed

log = logging.getLogger(__name__)


def create_app(config: dict | None = None) -> Flask:
    configure_logging()

    app = Flask(__name__, static_folder=None, instance_relative_config=False)
    app.config.from_object(Config)
    if config is not None:
        app.config.update(config)
    password = app.config["NFE_ACCESS_PASSWORD"]
    if password and len(password) < 16:
        raise RuntimeError("NFE_ACCESS_PASSWORD deve ter pelo menos 16 caracteres.")

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
    @app.before_request
    def protect_api():
        password = app.config["NFE_ACCESS_PASSWORD"]
        if request.path == "/api/health" or (not password and not request.path.startswith("/api/")):
            return None
        if password:
            credentials = request.authorization
            if (not credentials or credentials.type != "basic" or credentials.username != "nfe"
                    or not compare_digest((credentials.password or "").encode(), password.encode())):
                response, status = error("Autenticação necessária", 401)
                response.headers["WWW-Authenticate"] = 'Basic realm="NF-e", charset="UTF-8"'
                return response, status
        elif (not request.remote_addr or not ip_address(request.remote_addr).is_loopback
              or not re.fullmatch(r"(?:localhost|127[.]0[.]0[.]1|\[::1\])(?::[0-9]{1,5})?", request.host, re.I)):
            return error("Acesso restrito ao computador local", 403)

        origin = request.headers.get("Origin")
        if origin and origin != (app.config["NFE_PUBLIC_ORIGIN"] or request.host_url.rstrip("/")):
            return error("Origem não autorizada", 403)
        return None

    @app.after_request
    def protect_response(response: Response) -> Response:
        if request.path.startswith("/api/") or app.config["NFE_ACCESS_PASSWORD"]:
            response.headers["Cache-Control"] = "no-store"
        return response


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        return error(err.message, err.status_code)

    @app.errorhandler(404)
    def handle_not_found(_err):
        return error("Recurso não encontrado", 404)

    @app.errorhandler(Exception)
    def handle_unexpected_error(err: Exception):
        if isinstance(err, HTTPException):
            return err.get_response()
        log.error("Erro não tratado (%s)", type(err).__name__)
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
        path = (frontend_dir / filename).resolve()
        if not path.is_relative_to(frontend_dir.resolve()) or filename.startswith("api/"):
            abort(404)
        if path.is_file():
            return send_from_directory(frontend_dir, filename)
        return send_from_directory(frontend_dir, "index.html")
