from dataclasses import dataclass
from typing import Optional, Dict

@dataclass(frozen=True)
class DayMenu:
    date: str  # YYYY-MM-DD
    breakfast: Optional[str] = None
    lunch: Optional[str] = None
    grab_and_go: Optional[str] = None
    deli_entree: Optional[str] = None
    no_school: Optional[str] = None

    # New: relative label for styling hooks
    relative: Optional[str] = None  # "yesterday"|"today"|"tomorrow"|None

    @property
    def is_yesterday(self) -> bool:
        return self.relative == "yesterday"

    @property
    def is_today(self) -> bool:
        return self.relative == "today"

    @property
    def is_tomorrow(self) -> bool:
        return self.relative == "tomorrow"

    @staticmethod
    def from_raw(date_str: str, raw: Dict, relative: Optional[str] = None) -> "DayMenu":
        if "No school" in raw:
            return DayMenu(date=date_str, no_school=raw.get("No school"), relative=relative)
        return DayMenu(
            date=date_str,
            breakfast=raw.get("Breakfast"),
            lunch=raw.get("Lunch"),
            grab_and_go=raw.get("Grab & Go"),
            deli_entree=raw.get("Deli Entree"),
            relative=relative,
        )