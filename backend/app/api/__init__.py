from .audit import bp as audit_bp
from .dashboard import bp as dashboard_bp
from .health import bp as health_bp
from .notas import bp as notas_bp
from .produtos import bp as produtos_bp

BLUEPRINTS = [
    health_bp,
    notas_bp,
    produtos_bp,
    dashboard_bp,
    audit_bp,
]
