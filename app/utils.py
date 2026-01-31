from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable
from dateutil import tz


# ------------------------------------------------------------------ #
# Date parsing / normalization
# ------------------------------------------------------------------ #

def parse_date(date_str: str | None, timezone: str) -> date:
    """
    Parse YYYY-MM-DD into a date.
    If not provided, return 'today' in the configured timezone.
    """
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    now = datetime.now(tz.gettz(timezone))
    return now.date()


def iso(d: date) -> str:
    """Return YYYY-MM-DD"""
    return d.isoformat()


# ------------------------------------------------------------------ #
# Week helpers
# ------------------------------------------------------------------ #

def week_start(d: date) -> date:
    """Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


def week_end(d: date) -> date:
    """Friday of the week containing d."""
    return week_start(d) + timedelta(days=4)


def daterange(start: date, end: date) -> Iterable[date]:
    """Inclusive date range."""
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


# ------------------------------------------------------------------ #
# Business-day math
# ------------------------------------------------------------------ #

def add_business_days(start: date, days_ahead: int) -> date:
    """
    Move forward by N business days (Mon–Fri).
    Skips weekends automatically.
    """
    if days_ahead <= 0:
        return start

    d = start
    added = 0

    while added < days_ahead:
        d += timedelta(days=1)
        if d.weekday() < 5:  # 0=Mon .. 4=Fri
            added += 1

    return d


# ------------------------------------------------------------------ #
# Query param normalization
# ------------------------------------------------------------------ #

def normalize_view(view: str | None) -> str:
    v = (view or "week").strip().lower()
    if v not in {"week", "remainder", "today", "tomorrow"}:
        return "week"
    return v


def normalize_theme(theme: str | None) -> str:
    t = (theme or "dark").strip().lower()
    if t not in {"dark", "light", "transparent"}:
        return "dark"
    return t

# ------------------------------------------------------------------ #
# Parsing / normalization
# ------------------------------------------------------------------ #

def parse_bool(val: str | None, default: bool = True) -> bool:
    if val is None:
        return default
    return val.strip().lower() not in {
        "0", "false", "no", "off", "disable", "disabled"
    }