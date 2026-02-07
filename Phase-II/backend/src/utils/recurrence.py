"""
Recurrence Pattern Parser for Phase V Recurring Tasks.

Supported Patterns:
- daily: Recurs every day
- weekly: Recurs every week on the same day
- weekly:<days>: Recurs on specific days (e.g., "weekly:monday,friday")
- monthly: Recurs every month on the same date
- monthly:<dates>: Recurs on specific dates (e.g., "monthly:1,15" for 1st and 15th)
- yearly: Recurs every year on the same date

Constitutional Compliance:
- Simple, human-readable patterns
- No complex cron expressions
- Clear validation errors
"""

import re
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Valid day names (case-insensitive)
WEEKDAY_NAMES = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


class RecurrencePattern:
    """
    Parsed recurrence pattern with metadata.

    Attributes:
        pattern_type: Type of recurrence (daily, weekly, monthly, yearly)
        interval: Interval value (default 1)
        days: List of weekday numbers (0=Monday, 6=Sunday) for weekly patterns
        dates: List of day-of-month numbers for monthly patterns
        raw_pattern: Original pattern string
    """

    def __init__(
        self,
        pattern_type: str,
        interval: int = 1,
        days: Optional[List[int]] = None,
        dates: Optional[List[int]] = None,
        raw_pattern: str = "",
    ):
        self.pattern_type = pattern_type
        self.interval = interval
        self.days = days or []
        self.dates = dates or []
        self.raw_pattern = raw_pattern

    def __repr__(self) -> str:
        return f"<RecurrencePattern type={self.pattern_type} interval={self.interval}>"


def validate_pattern(pattern: str) -> Tuple[bool, str]:
    """
    Validate recurrence pattern format.

    Args:
        pattern: Recurrence pattern string

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
            - (True, "") if pattern is valid
            - (False, error_message) if pattern is invalid

    Examples:
        >>> validate_pattern("daily")
        (True, "")
        >>> validate_pattern("weekly:monday,friday")
        (True, "")
        >>> validate_pattern("monthly:1,15,30")
        (True, "")
        >>> validate_pattern("invalid")
        (False, "Invalid pattern type 'invalid'")
    """
    if not pattern or not isinstance(pattern, str):
        return False, "Pattern must be a non-empty string"

    pattern = pattern.strip().lower()

    # Split pattern into type and parameters
    parts = pattern.split(":", 1)
    pattern_type = parts[0].strip()

    # Validate pattern type
    valid_types = ["daily", "weekly", "monthly", "yearly"]
    if pattern_type not in valid_types:
        return False, f"Invalid pattern type '{pattern_type}'. Must be one of: {', '.join(valid_types)}"

    # Validate pattern-specific parameters
    if len(parts) == 2:
        params = parts[1].strip()

        if pattern_type == "daily":
            return False, "Daily pattern does not accept parameters"

        elif pattern_type == "weekly":
            # Validate weekday names
            day_names = [d.strip() for d in params.split(",")]
            for day_name in day_names:
                if day_name not in WEEKDAY_NAMES:
                    return False, f"Invalid weekday '{day_name}'. Valid days: {', '.join(set(WEEKDAY_NAMES.keys()))}"

        elif pattern_type == "monthly":
            # Validate day-of-month numbers
            try:
                dates = [int(d.strip()) for d in params.split(",")]
                for day_num in dates:
                    if day_num < 1 or day_num > 31:
                        return False, f"Invalid day-of-month '{day_num}'. Must be between 1 and 31"
            except ValueError:
                return False, "Monthly pattern parameters must be comma-separated numbers (e.g., '1,15,30')"

        elif pattern_type == "yearly":
            return False, "Yearly pattern does not accept parameters"

    return True, ""


def parse_recurrence_pattern(pattern: str) -> RecurrencePattern:
    """
    Parse recurrence pattern string into structured format.

    Args:
        pattern: Recurrence pattern string (e.g., "daily", "weekly:monday,friday")

    Returns:
        RecurrencePattern: Parsed pattern object

    Raises:
        ValueError: If pattern is invalid

    Examples:
        >>> parse_recurrence_pattern("daily")
        <RecurrencePattern type=daily interval=1>
        >>> parse_recurrence_pattern("weekly:monday,friday")
        <RecurrencePattern type=weekly interval=1>
        >>> parse_recurrence_pattern("monthly:1,15")
        <RecurrencePattern type=monthly interval=1>
    """
    # Validate pattern first
    is_valid, error_msg = validate_pattern(pattern)
    if not is_valid:
        raise ValueError(f"Invalid recurrence pattern: {error_msg}")

    pattern = pattern.strip().lower()
    parts = pattern.split(":", 1)
    pattern_type = parts[0].strip()

    # Initialize pattern object
    recurrence = RecurrencePattern(
        pattern_type=pattern_type,
        interval=1,
        raw_pattern=pattern
    )

    # Parse pattern-specific parameters
    if len(parts) == 2:
        params = parts[1].strip()

        if pattern_type == "weekly":
            # Parse weekday names
            day_names = [d.strip() for d in params.split(",")]
            recurrence.days = [WEEKDAY_NAMES[day_name] for day_name in day_names]
            recurrence.days.sort()  # Sort for consistency

        elif pattern_type == "monthly":
            # Parse day-of-month numbers
            recurrence.dates = [int(d.strip()) for d in params.split(",")]
            recurrence.dates.sort()  # Sort for consistency

    logger.debug(f"Parsed recurrence pattern: {pattern} -> {recurrence}")
    return recurrence


def calculate_next_occurrence(
    pattern: RecurrencePattern,
    from_date: datetime,
    end_date: Optional[datetime] = None
) -> Optional[datetime]:
    """
    Calculate the next occurrence date for a recurrence pattern.

    Args:
        pattern: Parsed recurrence pattern
        from_date: Starting date to calculate from
        end_date: Optional end date for recurrence (if None, no limit)

    Returns:
        Optional[datetime]: Next occurrence date, or None if past end_date

    Examples:
        >>> pattern = parse_recurrence_pattern("daily")
        >>> calculate_next_occurrence(pattern, datetime(2025, 1, 1))
        datetime.datetime(2025, 1, 2, 0, 0)
    """
    if pattern.pattern_type == "daily":
        next_date = from_date + timedelta(days=1)

    elif pattern.pattern_type == "weekly":
        if pattern.days:
            # Find next occurrence on specified days
            current_weekday = from_date.weekday()
            days_ahead = None

            # Find the closest day ahead
            for target_day in pattern.days:
                if target_day > current_weekday:
                    days_ahead = target_day - current_weekday
                    break

            # If no day found ahead this week, use first day next week
            if days_ahead is None:
                days_ahead = (7 - current_weekday) + pattern.days[0]

            next_date = from_date + timedelta(days=days_ahead)
        else:
            # Default weekly: same day next week
            next_date = from_date + timedelta(weeks=1)

    elif pattern.pattern_type == "monthly":
        if pattern.dates:
            # Find next occurrence on specified dates
            current_day = from_date.day
            next_month = from_date.month
            next_year = from_date.year

            # Find the closest date ahead this month
            target_day = None
            for day_num in pattern.dates:
                if day_num > current_day:
                    target_day = day_num
                    break

            # If no date found ahead this month, use first date next month
            if target_day is None:
                target_day = pattern.dates[0]
                next_month += 1
                if next_month > 12:
                    next_month = 1
                    next_year += 1

            # Handle month-end edge cases (e.g., February 30 -> February 28/29)
            import calendar
            max_day_in_month = calendar.monthrange(next_year, next_month)[1]
            target_day = min(target_day, max_day_in_month)

            next_date = from_date.replace(
                year=next_year,
                month=next_month,
                day=target_day,
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )
        else:
            # Default monthly: same day next month
            import calendar
            next_month = from_date.month + 1
            next_year = from_date.year
            if next_month > 12:
                next_month = 1
                next_year += 1

            # Handle month-end edge cases
            max_day_in_month = calendar.monthrange(next_year, next_month)[1]
            target_day = min(from_date.day, max_day_in_month)

            next_date = from_date.replace(
                year=next_year,
                month=next_month,
                day=target_day,
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )

    elif pattern.pattern_type == "yearly":
        # Same day next year
        next_date = from_date.replace(year=from_date.year + 1)

    else:
        raise ValueError(f"Unknown pattern type: {pattern.pattern_type}")

    # Check if next occurrence is past end date
    if end_date and next_date > end_date:
        return None

    return next_date


def get_all_occurrences(
    pattern: RecurrencePattern,
    start_date: datetime,
    end_date: Optional[datetime] = None,
    max_occurrences: int = 100
) -> List[datetime]:
    """
    Generate all occurrence dates for a recurrence pattern.

    Args:
        pattern: Parsed recurrence pattern
        start_date: Starting date
        end_date: Optional end date (if None, uses max_occurrences limit)
        max_occurrences: Maximum number of occurrences to generate (default 100)

    Returns:
        List[datetime]: List of occurrence dates

    Examples:
        >>> pattern = parse_recurrence_pattern("daily")
        >>> occurrences = get_all_occurrences(pattern, datetime(2025, 1, 1), max_occurrences=7)
        >>> len(occurrences)
        7
    """
    occurrences = [start_date]
    current_date = start_date

    for _ in range(max_occurrences - 1):
        next_date = calculate_next_occurrence(pattern, current_date, end_date)
        if next_date is None:
            break
        occurrences.append(next_date)
        current_date = next_date

    return occurrences
