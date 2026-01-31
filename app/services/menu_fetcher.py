from __future__ import annotations
from ..utils import week_start
from datetime import date
from typing import Dict, Any, Optional
import time
import requests


class SimpleTTLCache:
    def __init__(self, ttl_seconds: int):
        self.ttl = ttl_seconds
        self._store: Dict[str, tuple[float, Any]] = {}

    def get(self, key: str):
        item = self._store.get(key)
        if not item:
            return None
        ts, val = item
        if time.time() - ts > self.ttl:
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: str, val: Any):
        self._store[key] = (time.time(), val)


class MenuFetcher:
    """
    Robust Nutrislice menu parser.

    Handles:
    - Section headers emitted as food items ("Breakfast", "Grab & Go", etc.)
    - Districts that do NOT reliably set menu_type
    - Explicit and implicit "No school" days
    """

    def __init__(self, nutrislice_root_url: str, cache_ttl_seconds: int = 1800):
        self.root_url = nutrislice_root_url.rstrip("/") + "/"
        self.cache = SimpleTTLCache(cache_ttl_seconds)
        self.conjunctions = {"with", "and", "or"}

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def get_week(self, any_day: date) -> Dict[str, Dict[str, str]]:
        monday = week_start(any_day)
        cache_key = f"week:{monday.isoformat()}"

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Nutrislice expects the Monday date to return the full week
        url = self._build_url(monday)

        resp = requests.get(url, timeout=20)
        resp.raise_for_status()

        parsed = self._parse_week(resp.json())
        self.cache.set(cache_key, parsed)
        return parsed

    # ------------------------------------------------------------------ #
    # Parsing
    # ------------------------------------------------------------------ #

    def _parse_week(self, data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        out: Dict[str, Dict[str, str]] = {}

        for day in data.get("days", []) or []:
            date_key = day.get("date")
            if not date_key:
                continue

            items = day.get("menu_items", []) or []

            # Explicit No School
            explicit = self._explicit_no_school(items)
            if explicit:
                out[date_key] = {"No school": explicit}
                continue

            meals = self._parse_meals(items)
            if meals:
                out[date_key] = meals
            else:
                out[date_key] = {"No data": "Menu not available"}

        return out

    # ------------------------------------------------------------------ #
    # Meal parsing (state machine)
    # ------------------------------------------------------------------ #

    def _parse_meals(self, items: list[Dict[str, Any]]) -> Dict[str, str]:
        """
        Nutrislice often emits this sequence:

        Breakfast
          food
          food
        Lunch
          food
        Grab & Go
          food
        Deli Entree
          food

        We treat the header items as bucket switches.
        """

        header_map = {
            "breakfast": "Breakfast",
            "lunch": "Lunch",
            "grab & go": "Grab & Go",
            "grab and go": "Grab & Go",
            "deli entree": "Deli Entree",
            "deli entrée": "Deli Entree",
        }

        buckets: Dict[str, list[str]] = {}
        current_bucket: Optional[str] = None

        for mi in items:
            name = self._food_name(mi)
            if not name:
                continue

            key = name.lower().strip()

            # Header switch
            if key in header_map:
                current_bucket = header_map[key]
                buckets.setdefault(current_bucket, [])
                continue

            # If we never saw a header, default intelligently
            if not current_bucket:
                current_bucket = "Breakfast" if "breakfast" in key else "Lunch"
                buckets.setdefault(current_bucket, [])

            if key in self.conjunctions:
                buckets[current_bucket].append(key)
            else:
                buckets[current_bucket].append(name)

        return {
            bucket: ", ".join(items)
            for bucket, items in buckets.items()
            if items
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _explicit_no_school(self, items: Any) -> Optional[str]:
        for mi in items or []:
            name = self._food_name(mi)
            if name and name.lower().startswith("no school"):
                return name
        return None

    def _food_name(self, mi: Dict[str, Any]) -> str:
        food = mi.get("food")
        if isinstance(food, dict):
            name = food.get("name")
            if isinstance(name, str):
                return name.strip()

        for key in ("name", "text"):
            val = mi.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()

        nested = mi.get("menu_item")
        if isinstance(nested, dict):
            food2 = nested.get("food")
            if isinstance(food2, dict):
                name2 = food2.get("name")
                if isinstance(name2, str):
                    return name2.strip()

        return ""