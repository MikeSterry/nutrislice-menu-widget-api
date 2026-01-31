from __future__ import annotations
from datetime import date, timedelta, datetime
from typing import Iterable
from dateutil import tz

def parse_date(date_str: str | None, timezone: str) -> date:
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    # Default "today" in configured timezone
    now = datetime.now(tz.gettz(timezone))
    return now.date()

def week_start(d: date) -> date:
    # Monday = 0
    return d - timedelta(days=d.weekday())

def add_business_days(start: date, days_ahead: int) -> date:
    """
    Move forward by N business days (Mon–Fri), skipping Sat/Sun.
    days_ahead=0 returns start.
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

def week_end(d: date) -> date:
    return week_start(d) + timedelta(days=4)  # Mon..Fri

def daterange(a: date, b: date) -> Iterable[date]:
    cur = a
    while cur <= b:
        yield cur
        cur += timedelta(days=1)

def iso(d: date) -> str:
    return d.isoformat()

def normalize_theme(theme: str | None) -> str:
    t = (theme or "dark").strip().lower()
    if t not in {"dark", "light", "transparent"}:
        return "dark"
    return t

def normalize_view(view: str | None) -> str:
    v = (view or "week").strip().lower()
    if v not in {"week", "remainder", "today", "tomorrow"}:
        return "week"
    return v
