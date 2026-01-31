from __future__ import annotations

from datetime import datetime
from flask import Flask

from .controllers.api_controller import create_api_blueprint
from .controllers.widget_controller import create_widget_blueprint
from .controllers.health_controller import create_health_blueprint
from .services.menu_fetcher import MenuFetcher
from .services.menu_service import MenuService


# ------------------------------------------------------------------ #
# Template helpers
# ------------------------------------------------------------------ #

def register_template_helpers(app: Flask) -> None:
    @app.template_filter("todow")
    def todow(date_str: str) -> str:
        """
        Convert YYYY-MM-DD -> Monday, Tuesday, etc.
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
        except Exception:
            return ""

    @app.context_processor
    def inject_include():
        """
        Allows: {{ include('icons/breakfast.svg') }}
        Loads files from app/templates/<path>
        """
        def include(path: str) -> str:
            with app.open_resource(f"templates/{path}") as f:
                return f.read().decode("utf-8")
        return {"include": include}


# ------------------------------------------------------------------ #
# App factory
# ------------------------------------------------------------------ #

def create_app() -> Flask:
    app = Flask(__name__)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    app.config.setdefault("TIMEZONE", "America/Chicago")
    app.config.setdefault(
        "NUTRISLICE_ROOT_URL",
        "https://district196.api.nutrislice.com/menu/api/weeks/school/echo-park/menu-type/breakfast-lunch/",
    )

    # ------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------
    fetcher = MenuFetcher(
        nutrislice_root_url=app.config["NUTRISLICE_ROOT_URL"]
    )
    menu_service = MenuService(fetcher)

    # ------------------------------------------------------------------
    # Blueprints
    # ------------------------------------------------------------------
    app.register_blueprint(
        create_api_blueprint(menu_service, app.config["TIMEZONE"])
    )
    app.register_blueprint(
        create_widget_blueprint(menu_service, app.config["TIMEZONE"])
    )
    app.register_blueprint(create_health_blueprint())

    # ------------------------------------------------------------------
    # Template helpers
    # ------------------------------------------------------------------
    register_template_helpers(app)

    return app


# ------------------------------------------------------------------ #
# WSGI entrypoint
# ------------------------------------------------------------------ #

app = create_app()