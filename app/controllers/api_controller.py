from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services.menu_service import MenuService
from ..utils import parse_date, normalize_view


def create_api_blueprint(menu_service: MenuService, timezone: str) -> Blueprint:
    bp = Blueprint("api", __name__)

    @bp.get("/api")
    def api():
        view = normalize_view(request.args.get("view"))
        anchor = parse_date(request.args.get("date"), timezone)

        if view == "week":
            payload = menu_service.week_menu(anchor)
        elif view == "remainder":
            payload = menu_service.remainder_of_week(anchor)
        elif view == "today":
            payload = menu_service.today(anchor)
        elif view == "tomorrow":
            payload = menu_service.tomorrow(anchor)
        else:
            payload = menu_service.week_menu(anchor)

        return jsonify({
            "view": view,
            "anchor_date": anchor.isoformat(),
            "data": payload,
        })

    return bp