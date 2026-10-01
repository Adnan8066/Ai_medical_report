"""Reference-range evaluation for laboratory results."""

import re
from decimal import Decimal, InvalidOperation

RANGE_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:-|to)\s*(-?\d+(?:\.\d+)?)")


def parse_range(reference_range):
    """Extract (low, high) from a string such as '13.5 - 17.5 g/dL'."""
    if not reference_range:
        return None
    match = RANGE_PATTERN.search(reference_range)
    if not match:
        return None
    try:
        return Decimal(match.group(1)), Decimal(match.group(2))
    except InvalidOperation:
        return None


def evaluate_flag(numeric_value, reference_range):
    """
    Return 'normal' / 'high' / 'low' / 'unknown'.

    This is a pure formatting aid for the UI - it never interprets a result
    clinically and is always shown alongside the laboratory's own reference
    range.
    """
    if numeric_value is None:
        return "unknown"
    bounds = parse_range(reference_range)
    if bounds is None:
        return "unknown"
    low, high = bounds
    value = Decimal(str(numeric_value))
    if value < low:
        return "low"
    if value > high:
        return "high"
    return "normal"
