from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, Any, List
from .menu_fetcher import MenuFetcher
from ..models import DayMenu
from ..utils import week_start, week_end, daterange, iso, add_business_days

class MenuService:
    def __init__(self, fetcher: MenuFetcher):
        self.fetcher = fetcher

    def week_menu(self, anchor: date) -> Dict[str, Any]:
        raw = self.fetcher.get_week(anchor)
        start = week_start(anchor)
        end = week_end(anchor)
        return self._slice(raw, start, end)

    def remainder_of_week(self, anchor: date) -> Dict[str, Any]:
        raw = self.fetcher.get_week(anchor)
        start = anchor
        end = week_end(anchor)
        return self._slice(raw, start, end)

    def day_at_offset(self, base: date, days_ahead: int) -> Dict[str, Any]:
        target = add_business_days(base, days_ahead)
        raw = self.fetcher.get_week(target)
        return self._day(raw, target)

    def today(self, d: date) -> Dict[str, Any]:
        return self.day_at_offset(d, 0)

    def tomorrow(self, d: date) -> Dict[str, Any]:
        return self.day_at_offset(d, 1)

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

    def to_day_models(self, data: Dict[str, Any], base_today: date) -> List[DayMenu]:
        # base_today = "real today" (or the date param)
        y = (base_today - timedelta(days=1)).isoformat()
        t = base_today.isoformat()
        tm = (base_today + timedelta(days=1)).isoformat()

        days: List[DayMenu] = []
        for k in sorted(data.keys()):
            rel = None
            if k == y:
                rel = "yesterday"
            elif k == t:
                rel = "today"
            elif k == tm:
                rel = "tomorrow"
            days.append(DayMenu.from_raw(k, data[k], relative=rel))
        return days