from __future__ import annotations
from flask import Blueprint, request, render_template
from ..utils import parse_date, normalize_view, normalize_theme
from ..services.menu_service import MenuService

def create_widget_blueprint(menu_service: MenuService, timezone: str) -> Blueprint:
    bp = Blueprint("widget", __name__)

    @bp.get("/widget")
    def widget():
        view = normalize_view(request.args.get("view"))
        theme = normalize_theme(request.args.get("theme"))
        base = parse_date(request.args.get("date"), timezone)

        # New param: business-day offset into the future
        days_ahead_raw = request.args.get("days_ahead")

        # If days_ahead not provided, infer from view
        if days_ahead_raw is None or days_ahead_raw == "":
            if view == "tomorrow":
                days_ahead = 1
            elif view == "today":
                days_ahead = 0
            else:
                days_ahead = 0
        else:
            try:
                days_ahead = max(0, int(days_ahead_raw))
            except ValueError:
                days_ahead = 0

        if view == "week":
            # highlight moves with days_ahead (skips weekends)
            target_day_payload = menu_service.day_at_offset(base, days_ahead)
            target_date = next(iter(target_day_payload.keys()))

            data = menu_service.week_menu(base)  # show the week that contains "base"
            title = "This Week"
            highlight = target_date
            days = menu_service.to_day_models(data, base_today=base)

        else:
            # Single-day widget based on days_ahead
            data = menu_service.day_at_offset(base, days_ahead)
            target_date = next(iter(data.keys()))
            highlight = target_date

            if days_ahead == 0:
                title = "Today's Menu"
            elif days_ahead == 1:
                title = "Tomorrow's Menu"
            else:
                title = f"Menu in {days_ahead} school days"

            days = menu_service.to_day_models(data, base_today=base)

        return render_template(
            "widget.html",
            title=title,
            theme=theme,
            view=view,
            anchor_date=base.isoformat(),
            highlight_date=highlight,
            days=days,
        )

    return bp