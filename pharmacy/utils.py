"""Shared validation, date, formatting, and export utilities."""

from __future__ import annotations

import csv
import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Sequence

from pharmacy.config import CURRENCY_SYMBOL, DEFAULT_EXPIRY_WARNING_DAYS


class ValidationError(ValueError):
    """Raised when user input fails field or format validation."""


class BusinessRuleError(RuntimeError):
    """Raised when an operation violates pharmacy domain rules."""


DATE_FORMAT = "%Y-%m-%d"
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def today_date() -> date:
    """Return today's local calendar date."""
    return date.today()


def today_iso() -> str:
    """Return today's date as an ISO-8601 YYYY-MM-DD string."""
    return today_date().strftime(DATE_FORMAT)


def now_timestamp() -> str:
    """Return current local timestamp as YYYY-MM-DD HH:MM:SS."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_iso_date(value: str, field_name: str = "Date") -> date:
    """Parse a strict YYYY-MM-DD string into a date object."""
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValidationError(f"{field_name} is required (YYYY-MM-DD).")
    try:
        return datetime.strptime(cleaned, DATE_FORMAT).date()
    except ValueError as exc:
        raise ValidationError(
            f"{field_name} must be a valid date in YYYY-MM-DD format."
        ) from exc


def validate_non_empty(value: str, field_name: str) -> str:
    """Ensure a string field is present and non-whitespace."""
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValidationError(f"{field_name} cannot be empty.")
    return cleaned


def validate_optional_email(value: str) -> str:
    """Validate optional email address."""
    cleaned = (value or "").strip()
    if cleaned and not EMAIL_REGEX.match(cleaned):
        raise ValidationError("Email address format is invalid.")
    return cleaned


def parse_non_negative_int(value: object, field_name: str) -> int:
    """Parse an integer >= 0."""
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a whole number.") from exc
    if parsed < 0:
        raise ValidationError(f"{field_name} cannot be negative.")
    return parsed


def parse_positive_int(value: object, field_name: str) -> int:
    """Parse an integer > 0."""
    parsed = parse_non_negative_int(value, field_name)
    if parsed <= 0:
        raise ValidationError(f"{field_name} must be greater than zero.")
    return parsed


def parse_non_negative_float(value: object, field_name: str) -> float:
    """Parse a decimal number >= 0, rounded to 2 decimal places."""
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid number.") from exc
    if parsed < 0:
        raise ValidationError(f"{field_name} cannot be negative.")
    return round(parsed, 2)


def parse_positive_float(value: object, field_name: str) -> float:
    """Parse a decimal number > 0, rounded to 2 decimal places."""
    parsed = parse_non_negative_float(value, field_name)
    if parsed <= 0:
        raise ValidationError(f"{field_name} must be greater than zero.")
    return parsed


def format_currency(amount: float) -> str:
    """Format a monetary amount with configured currency symbol."""
    return f"{CURRENCY_SYMBOL}{amount:,.2f}"


def is_expired(expiry_iso: str, reference_date: date | None = None) -> bool:
    """Return True if the batch expiry date is on or before reference_date.

    Strict pharmacy policy: medicines expiring today or earlier cannot be sold.
    """
    ref = reference_date or today_date()
    exp = parse_iso_date(expiry_iso, "Expiry date")
    return exp <= ref


def days_until_expiry(expiry_iso: str, reference_date: date | None = None) -> int:
    """Return signed day count from reference_date to expiry date."""
    ref = reference_date or today_date()
    exp = parse_iso_date(expiry_iso, "Expiry date")
    return (exp - ref).days


def expiry_status_label(
    expiry_iso: str,
    warning_days: int = DEFAULT_EXPIRY_WARNING_DAYS,
    reference_date: date | None = None,
) -> str:
    """Classify medicine expiry status: 'Expired', 'Expiring Soon', or 'Valid'."""
    remaining = days_until_expiry(expiry_iso, reference_date)
    if remaining <= 0:
        return "Expired"
    if remaining <= warning_days:
        return "Expiring Soon"
    return "Valid"


def export_rows_to_csv(
    file_path: str | Path,
    headers: Sequence[str],
    rows: Iterable[Sequence[object]],
) -> int:
    """Write tabular rows to a UTF-8 CSV file and return exported row count."""
    target = Path(file_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
            count += 1
    return count
