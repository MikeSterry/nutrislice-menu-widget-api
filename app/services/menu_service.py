from __future__ import annotations

from datetime import date, timedelta, datetime
from typing import Dict, Any, List
from typing import Set

from .menu_fetcher import MenuFetcher
from ..models import DayMenu
from ..utils import (
    week_start,
    week_end,
    daterange,
    iso,
    add_business_days,
)


class MenuService:
    def __init__(self, fetcher: MenuFetcher):
        self.fetcher = fetcher

    # ------------------------------------------------------------------ #
    # Week-based views
    # ------------------------------------------------------------------ #

    def week_menu(self, anchor: date) -> Dict[str, Any]:
        """
        Full Monday–Friday menu for the week containing anchor.
        """
        raw = self.fetcher.get_week(anchor)
        start = week_start(anchor)
        end = week_end(anchor)
        return self._slice(raw, start, end)

    def remainder_of_week(self, anchor: date) -> Dict[str, Any]:
        """
        Menu from anchor through Friday of the same week.
        """
        raw = self.fetcher.get_week(anchor)
        start = anchor
        end = week_end(anchor)
        return self._slice(raw, start, end)

    # ------------------------------------------------------------------ #
    # Day-based views (business-day aware)
    # ------------------------------------------------------------------ #

    def day_at_offset(self, base: date, days_ahead: int) -> Dict[str, Any]:
        """
        Menu for base + N business days (skips weekends).
        """
        target = add_business_days(base, days_ahead)
        raw = self.fetcher.get_week(target)
        return self._day(raw, target)

    def today(self, d: date) -> Dict[str, Any]:
        return self.day_at_offset(d, 0)

    def tomorrow(self, d: date) -> Dict[str, Any]:
        return self.day_at_offset(d, 1)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _day(self, raw: Dict[str, Any], d: date) -> Dict[str, Any]:
        key = iso(d)
        if key not in raw:
            return {key: {"No data": "Menu not available"}}
        return {key: raw[key]}

    def _slice(self, raw: Dict[str, Any], start: date, end: date) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for d in daterange(start, end):
            k = iso(d)
            if k in raw:
                out[k] = raw[k]
        return out

    # ------------------------------------------------------------------ #
    # Model conversion (for widgets)
    # ------------------------------------------------------------------ #

    def to_day_models(self, data: Dict[str, Any], base_today: date) -> List[DayMenu]:
        yesterday = (base_today - timedelta(days=1)).isoformat()
        today = base_today.isoformat()
        tomorrow = (base_today + timedelta(days=1)).isoformat()

        days: List[DayMenu] = []
        for k in sorted(data.keys()):
            relative = None
            if k == yesterday:
                relative = "yesterday"
            elif k == today:
                relative = "today"
            elif k == tomorrow:
                relative = "tomorrow"

            weekday_name = ""
            try:
                weekday_name = datetime.strptime(k, "%Y-%m-%d").strftime("%A")
            except Exception:
                weekday_name = ""

            days.append(DayMenu.from_raw(k, data[k], relative=relative, weekday_name=weekday_name))

        return days

    def window_business_days(self, base: date, count: int) -> Dict[str, Any]:
        """
        Return a dict containing `count` school days starting at `base`,
        skipping weekends. Includes base day as day 1.

        Example: base=Friday, count=3 -> Fri, Mon, Tue
        """
        count = max(1, int(count))

        # Build the list of business dates we want to include
        dates: list[date] = [base]
        while len(dates) < count:
            dates.append(add_business_days(dates[-1], 1))

        # Fetch week data for any weeks we touch (efficient across week boundaries)
        week_mondays: Set[date] = {week_start(d) for d in dates}
        week_data: Dict[str, Any] = {}
        for monday in sorted(week_mondays):
            week_data.update(self.fetcher.get_week(monday))

        # Slice to only the dates we want (preserve order)
        out: Dict[str, Any] = {}
        for d in dates:
            k = iso(d)
            out[k] = week_data.get(k, {"No data": "Menu not available"})
        return out