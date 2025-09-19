"""Normalization helpers used before comparison."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional


def normalize_date(value: str) -> Optional[str]:
    """Normalize date strings into ISO format (YYYY-MM-DD).

    Supports common separators (., /, -) and returns ``None`` when parsing fails.
    """

    if value is None:
        return None

    value = value.strip()
    if not value:
        return None

    # try multiple formats
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.date().isoformat()
        except ValueError:
            continue

    # handle formats like YYYY年MM月DD日
    try:
        clean = value.replace("年", "-").replace("月", "-").replace("日", "")
        parsed = datetime.strptime(clean, "%Y-%m-%d")
        return parsed.date().isoformat()
    except ValueError:
        return None


def normalize_numeric(value: str) -> Optional[str]:
    """Normalize numeric strings by removing separators and standardizing decimals."""

    if value is None:
        return None

    value = value.strip().replace(",", "")
    if not value:
        return None

    try:
        number = Decimal(value)
        return format(number.normalize(), "f")
    except (InvalidOperation, ValueError):
        return None
