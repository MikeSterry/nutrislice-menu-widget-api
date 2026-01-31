from __future__ import annotations

from flask import Blueprint, request, render_template

from ..services.menu_service import MenuService
from ..utils import parse_date, normalize_view, normalize_theme, parse_bool


def create_widget_blueprint(menu_service: MenuService, timezone: str) -> Blueprint:
    bp = Blueprint("widget", __name__)

    @bp.get("/widget")
    def widget():
        show_header = parse_bool(request.args.get("show_header"), default=True)
        show_footer = parse_bool(request.args.get("show_footer"), default=True)
        raw_view = request.args.get("view")
        view = normalize_view(raw_view)

        theme = normalize_theme(request.args.get("theme"))
        base_date = parse_date(request.args.get("date"), timezone)

        # Parse days_ahead (int >= 0). If missing, keep None so we can branch.
        days_ahead_raw = request.args.get("days_ahead")
        days_ahead = None
        if days_ahead_raw is not None and days_ahead_raw != "":
            try:
                days_ahead = max(0, int(days_ahead_raw))
            except ValueError:
                days_ahead = 0

        # ------------------------------------------------------------
        # NEW: If view is NOT explicitly provided, but days_ahead is,
        # interpret days_ahead as "number of school days to show"
        # starting at base_date (skips weekends).
        #
        # Example (Friday + days_ahead=3): Fri, Mon, Tue
        # ------------------------------------------------------------
        if raw_view is None and days_ahead is not None and days_ahead > 0:
            data = menu_service.window_business_days(base_date, days_ahead)
            highlight_date = base_date.isoformat()
            title = f"Next {days_ahead} School Days"
            days = menu_service.to_day_models(data, base_today=base_date)

            return render_template(
                "widget.html",
                title=title,
                theme=theme,
                view="window",
                anchor_date=base_date.isoformat(),
                highlight_date=highlight_date,
                days=days,
                show_header=show_header,
                show_footer=show_footer,
            )

        # ------------------------------------------------------------
        # Existing semantics:
        # - view=week shows whole week; days_ahead controls highlight
        # - view=today/tomorrow show a single day; days_ahead offsets
        #   (skips weekends)
        # ------------------------------------------------------------

        # If days_ahead isn't provided, infer for tomorrow; else default 0.
        if days_ahead is None:
            if view == "tomorrow":
                days_ahead = 1
            else:
                days_ahead = 0

        if view == "week":
            # Highlight moves with business-day offset
            target_payload = menu_service.day_at_offset(base_date, days_ahead)
            highlight_date = next(iter(target_payload.keys()))

            data = menu_service.week_menu(base_date)
            title = "This Week"
            days = menu_service.to_day_models(data, base_today=base_date)

        else:
            # Single-day widget based on business-day offset
            data = menu_service.day_at_offset(base_date, days_ahead)
            highlight_date = next(iter(data.keys()))

            if days_ahead == 0:
                title = "Today's Menu"
            elif days_ahead == 1:
                title = "Tomorrow's Menu"
            else:
                title = f"Menu in {days_ahead} School Days"

            days = menu_service.to_day_models(data, base_today=base_date)

        return render_template(
            "widget.html",
            title=title,
            theme=theme,
            view=view,
            anchor_date=base_date.isoformat(),
            highlight_date=highlight_date,
            days=days,
        )

    return bp