from __future__ import annotations

from datetime import datetime, timezone as utc_timezone

from flask import Blueprint, Response, abort
from requests import RequestException

from ..models import DayMenu
from ..services.menu_service import MenuService
from ..utils import parse_date, week_start

MEAL_FEEDS = {
    "breakfast": ("Breakfast", "breakfast"),
    "lunch": ("Lunch", "lunch"),
    "grab-and-go": ("Grab & Go", "grab_and_go"),
    "deli-entree": ("Deli Entree", "deli_entree"),
}


def escape_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def fold_line(line: str) -> str:
    """Fold at 75 UTF-8 octets, including the continuation space."""
    parts = []
    start = size = 0
    for index, character in enumerate(line):
        width = len(character.encode("utf-8"))
        if size + width > 75:
            parts.append(line[start:index])
            start = index
            size = 1
        size += width
    parts.append(line[start:])
    return "\r\n ".join(parts)


def render_calendar(days: list[DayMenu], feed: str) -> str:
    meals = MEAL_FEEDS if feed == "all" else {feed: MEAL_FEEDS[feed]}
    calendar_name = "Echo Park Elementary Menu"
    if feed != "all":
        calendar_name += f" - {MEAL_FEEDS[feed][0]}"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Echo Park Elementary Menu API//School Menu//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{escape_text(calendar_name)}",
    ]
    stamp = datetime.now(utc_timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for day in days:
        events = [
            (slug, label, getattr(day, field))
            for slug, (label, field) in meals.items()
        ]
        if feed == "all" and day.no_school:
            events.append(("no-school", "No school", day.no_school))

        for slug, label, menu in events:
            if not menu or not menu.strip():
                continue
            menu = menu.strip()
            summary = label if menu.casefold() == label.casefold() else f"{label}: {menu}"
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:echo-park-menu-{day.date}-{slug}@nutrislice-menu-widget-api",
                f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{day.date.replace('-', '')}",
                f"SUMMARY:{escape_text(summary)}",
                f"DESCRIPTION:{escape_text(menu)}",
                "TRANSP:TRANSPARENT",
                "END:VEVENT",
            ])
    lines.append("END:VCALENDAR")
    return "\r\n".join(map(fold_line, lines)) + "\r\n"


def create_calendar_blueprint(menu_service: MenuService, timezone: str) -> Blueprint:
    bp = Blueprint("calendar", __name__)

    @bp.get("/calendar/<feed>.ics")
    def calendar(feed: str):
        if feed != "all" and feed not in MEAL_FEEDS:
            abort(404)

        today = parse_date(None, timezone)
        try:
            data = menu_service.window_business_days(week_start(today), count=20)
        except RequestException:
            abort(502, description="The school menu is temporarily unavailable.")

        days = menu_service.to_day_models(data, today)
        return Response(render_calendar(days, feed), mimetype="text/calendar")

    return bp
