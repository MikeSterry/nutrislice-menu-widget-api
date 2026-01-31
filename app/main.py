from __future__ import annotations

from flask import Flask, jsonify
from .config import AppConfig
from .services.menu_fetcher import MenuFetcher
from .services.menu_service import MenuService
from .controllers.api_controller import create_api_blueprint
from .controllers.widget_controller import create_widget_blueprint

def create_app() -> Flask:
    config = AppConfig()

    fetcher = MenuFetcher(
        nutrislice_root_url=config.nutrislice_root_url,
        cache_ttl_seconds=config.cache_ttl_seconds,
    )
    menu_service = MenuService(fetcher)

    app = Flask(__name__, template_folder="templates", static_folder="static")

    from . import register_template_helpers
    register_template_helpers(app)

    app.register_blueprint(create_api_blueprint(menu_service, config.timezone))
    app.register_blueprint(create_widget_blueprint(menu_service, config.timezone))

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app

app = create_app()
