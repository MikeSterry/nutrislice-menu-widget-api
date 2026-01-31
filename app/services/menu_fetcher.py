from __future__ import annotations

from datetime import date
from typing import Dict, Any, Optional
import time
import re
import requests

from ..utils import week_start


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

    Features:
    - Always calls Nutrislice using the Monday of the requested week (week_start)
    - Caches parsed week results (TTL)
    - Parses feeds where section headers ("Breakfast", "Grab & Go", etc.) appear as food items
    - Produces buckets: Breakfast, Lunch, Grab & Go, Deli Entree
    - Conjunction cleanup pipeline via conjunction_junction()
    - "No school" detection when explicitly labeled
    """

    _ORDER = ("Breakfast", "Lunch", "Grab & Go", "Deli Entree")

    def __init__(self, nutrislice_root_url: str, cache_ttl_seconds: int = 1800):
        self.root_url = nutrislice_root_url.rstrip("/") + "/"
        self.cache = SimpleTTLCache(cache_ttl_seconds)

        # Conjunction words we expect in the token stream
        self.conjunctions = {"with", "and", "or"}

        # Headers often appear as food items
        self.header_map = {
            "breakfast": "Breakfast",
            "lunch": "Lunch",
            "grab & go": "Grab & Go",
            "grab and go": "Grab & Go",
            "deli entree": "Deli Entree",
            "deli entrée": "Deli Entree",
        }

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def get_week(self, any_day: date) -> Dict[str, Dict[str, str]]:
        """
        Fetch and parse the full week that contains any_day.

        NOTE: Nutrislice returns the entire week's content when you call
        the endpoint using that week's Monday date.
        """
        monday = week_start(any_day)
        cache_key = f"week:{monday.isoformat()}"

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        url = self._build_url(monday)
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()

        parsed = self._parse_week(resp.json())
        self.cache.set(cache_key, parsed)
        return parsed

    # ------------------------------------------------------------------ #
    # Request + parse helpers
    # ------------------------------------------------------------------ #

    def _build_url(self, d: date) -> str:
        # Nutrislice expects /year/month/day/
        return f"{self.root_url}{d.year}/{d.month}/{d.day}/"

    def _parse_week(self, data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        out: Dict[str, Dict[str, str]] = {}

        for day in data.get("days", []) or []:
            date_key = day.get("date")
            if not date_key:
                continue

            items = day.get("menu_items", []) or []

            explicit_no_school = self._explicit_no_school(items)
            if explicit_no_school:
                out[date_key] = {"No school": explicit_no_school}
                continue

            meals = self._parse_meals(items)
            if meals:
                meals = self._maybe_convert_to_no_school(meals)
                out[date_key] = self._order_day_menu(meals)
            else:
                out[date_key] = {"No data": "Menu not available"}

        return out

    # ------------------------------------------------------------------ #
    # Parsing: state machine on section headers
    # ------------------------------------------------------------------ #

    def _parse_meals(self, items: list[Dict[str, Any]]) -> Dict[str, str]:
        """
        Many Nutrislice feeds emit a token stream like:

          Breakfast
          item
          item
          Lunch
          item
          Grab & Go
          item
          Deli Entree
          item

        The words "Breakfast", "Lunch", etc. can appear as FOOD NAMES
        rather than reliable menu_type metadata. We treat them as section headers.
        """
        buckets: Dict[str, list[str]] = {}
        current_bucket: Optional[str] = None

        for mi in items:
            name = self._food_name(mi)
            if not name:
                continue

            k = name.strip().lower()

            # Header switch
            if k in self.header_map:
                current_bucket = self.header_map[k]
                buckets.setdefault(current_bucket, [])
                continue

            # If we never saw a header, pick a reasonable default
            if not current_bucket:
                current_bucket = "Breakfast" if "breakfast" in k else "Lunch"
                buckets.setdefault(current_bucket, [])

            # Append conjunction or normal token
            if k in self.conjunctions:
                buckets[current_bucket].append(k)
            else:
                buckets[current_bucket].append(name)

        # Join + clean up punctuation/conjunction formatting
        result: Dict[str, str] = {}
        for bucket, tokens in buckets.items():
            if not tokens:
                continue
            joined = ", ".join(tokens)
            result[bucket] = self.conjunction_junction(joined)

        return result

    # ------------------------------------------------------------------ #
    # Conjunction cleanup pipeline
    # ------------------------------------------------------------------ #

    def conjunction_junction(self, s: str) -> str:
        """
        Runs all conjunction cleanup steps in a consistent order.
        """
        s = self._ensure_space_after_w_slash(s)
        s = self._replace_w_slash_with_with(s)
        s = self._remove_commas_around_conjunctions(s)
        return self._normalize_whitespace(s)

    def _ensure_space_after_w_slash(self, s: str) -> str:
        """
        Turns 'w/Variety' into 'w/ Variety'
        """
        return re.sub(r"(?i)\bw/(\S)", r"w/ \1", s)

    def _replace_w_slash_with_with(self, s: str) -> str:
        """
        Turns 'w/' into 'with'
        """
        # Replace common w/ forms (case-insensitive)
        s = re.sub(r"(?i)\bw/\b", "with", s)
        s = re.sub(r"(?i)\bw/\s+", "with ", s)
        s = re.sub(r"(?i)\bw/", "with ", s)
        return s

    def _remove_commas_around_conjunctions(self, s: str) -> str:
        """
        Turns 'Chicken, with, Rice' into 'Chicken with Rice'
        and 'A, and, B' into 'A and B'
        """
        conj_pattern = "|".join(re.escape(c) for c in sorted(self.conjunctions))

        # Replace ", with," (and variants) with " with "
        s = re.sub(rf"\s*,\s*({conj_pattern})\s*,\s*", r" \1 ", s, flags=re.IGNORECASE)

        # Handle "with," or ",with" edge cases
        s = re.sub(rf"\s*({conj_pattern})\s*,\s*", r"\1 ", s, flags=re.IGNORECASE)
        s = re.sub(rf"\s*,\s*({conj_pattern})\s*", r" \1", s, flags=re.IGNORECASE)

        return s

    def _normalize_whitespace(self, s: str) -> str:
        """
        Collapses repeated whitespace and trims.
        """
        return re.sub(r"\s{2,}", " ", s).strip()

    # ------------------------------------------------------------------ #
    # Ordering
    # ------------------------------------------------------------------ #

    def _order_day_menu(self, day_menu: Dict[str, str]) -> Dict[str, str]:
        """
        Ensure consistent ordering of keys:
          Breakfast, Lunch, Grab & Go, Deli Entree
        Any unknown keys are appended afterward (e.g., No school, No data).
        """
        ordered: Dict[str, str] = {}

        for k in self._ORDER:
            if k in day_menu:
                ordered[k] = day_menu[k]

        for k, v in day_menu.items():
            if k not in ordered:
                ordered[k] = v

        return ordered

    # ------------------------------------------------------------------ #
    # "No school" detection + food name extraction
    # ------------------------------------------------------------------ #

    def _explicit_no_school(self, items: Any) -> Optional[str]:
        """
        Only treat as "No school" when explicitly labeled in the feed.
        """
        for mi in items or []:
            if not isinstance(mi, dict):
                continue
            name = self._food_name(mi)
            if name and name.lower().startswith("no school"):
                return name
        return None

    def _food_name(self, mi: Dict[str, Any]) -> str:
        """
        Attempts to extract the menu item name across common Nutrislice shapes.
        """
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

    def _maybe_convert_to_no_school(self, meals: Dict[str, str]) -> Dict[str, str]:
        """
        Nutrislice sometimes returns no-school reasons under a normal bucket
        (often Lunch) rather than explicitly labeling "No school".

        If a day has no real meal content and has a single reason-like string,
        normalize it to {"No school": "<reason>"}.
        """
        if not meals:
            return meals

        # Already normalized
        if "No school" in meals:
            return meals

        breakfast = (meals.get("Breakfast") or "").strip()
        lunch = (meals.get("Lunch") or "").strip()
        grab = (meals.get("Grab & Go") or "").strip()
        deli = (meals.get("Deli Entree") or "").strip()

        # If only Lunch has content and everything else is empty -> likely no school
        only_lunch_has_text = bool(lunch) and not breakfast and not grab and not deli
        if not only_lunch_has_text:
            return meals

        reason = lunch

        # Heuristic keywords that typically indicate closures
        reason_l = reason.lower()
        keywords = (
            "conference",
            "conferences",
            "staff development",
            "inservice",
            "in-service",
            "teacher work day",
            "holiday",
            "no school",
            "school closed",
            "early release",
            "snow day",
        )

        if any(k in reason_l for k in keywords):
            return {"No school": reason}

        # Some feeds put closure text without those keywords; still normalize if it’s short-ish.
        # (Prevents converting a real lunch menu accidentally.)
        if len(reason) <= 80:
            return {"No school": reason}

        return meals