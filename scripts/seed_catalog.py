from __future__ import annotations

from app import create_app
from app.db.seed import seed_products_if_needed


def main():
    app = create_app()
    with app.app_context():
        seed_products_if_needed()
        print("Seed executado com sucesso.")


if __name__ == "__main__":
    main()
