"""Parse CV date fields for chronological sorting."""

from __future__ import annotations

import re
from typing import Any

_MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


def _raw_from_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        for key in ("en", "cz"):
            if value.get(key):
                return str(value[key])
        for item in value.values():
            if item:
                return str(item)
        return ""
    return str(value)


def parse_from_date(value: Any) -> tuple[int, int]:
    """Return (year, month) for sorting. Uses only the 'from' field."""
    text = _raw_from_value(value).strip().lower()
    if not text:
        return (0, 0)

    if re.fullmatch(r"\d{4}", text):
        return (int(text), 0)

    match = re.match(r"([a-z]+)\s+(\d{4})", text)
    if match:
        month_name, year = match.groups()
        return (int(year), _MONTHS.get(month_name, 0))

    year_match = re.search(r"(\d{4})", text)
    if year_match:
        return (int(year_match.group(1)), 0)

    return (0, 0)


def sort_by_from_desc(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort entries by 'from' date, most recent first."""
    return sorted(items, key=lambda item: parse_from_date(item.get("from")), reverse=True)
