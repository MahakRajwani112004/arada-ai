"""Cron expression parser and validator.

Supports standard 5-field cron expressions:
    minute hour day month day_of_week

Examples:
    - "0 9 * * 1-5"     -> 9 AM on weekdays
    - "*/15 * * * *"    -> Every 15 minutes
    - "0 0 1 * *"       -> First day of every month at midnight
    - "0 12 * * 0"      -> Noon on Sundays
    - "30 8 1,15 * *"   -> 8:30 AM on the 1st and 15th of each month
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Set, Tuple
from zoneinfo import ZoneInfo

# Field ranges
FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day": (1, 31),
    "month": (1, 12),
    "day_of_week": (0, 6),  # 0 = Sunday
}

# Month name mappings
MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Day of week name mappings
DOW_NAMES = {
    "sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6,
}


class CronParseError(ValueError):
    """Error parsing cron expression."""
    pass


@dataclass
class CronExpression:
    """Parsed cron expression."""
    minute: Set[int]
    hour: Set[int]
    day: Set[int]
    month: Set[int]
    day_of_week: Set[int]
    original: str

    def matches(self, dt: datetime) -> bool:
        """Check if datetime matches this cron expression."""
        return (
            dt.minute in self.minute
            and dt.hour in self.hour
            and dt.day in self.day
            and dt.month in self.month
            and dt.weekday() in {(d + 6) % 7 for d in self.day_of_week}  # Convert from cron dow to Python dow
        )


def _parse_field(field: str, field_name: str) -> Set[int]:
    """Parse a single cron field into a set of values."""
    min_val, max_val = FIELD_RANGES[field_name]
    result: Set[int] = set()

    # Handle names (for month and day_of_week)
    field_lower = field.lower()
    if field_name == "month":
        for name, num in MONTH_NAMES.items():
            field_lower = field_lower.replace(name, str(num))
    elif field_name == "day_of_week":
        for name, num in DOW_NAMES.items():
            field_lower = field_lower.replace(name, str(num))
    field = field_lower

    # Split by comma
    for part in field.split(","):
        part = part.strip()

        # Handle step values (*/n or range/n)
        step = 1
        if "/" in part:
            part, step_str = part.split("/", 1)
            try:
                step = int(step_str)
                if step < 1:
                    raise CronParseError(f"Invalid step value: {step_str}")
            except ValueError:
                raise CronParseError(f"Invalid step value: {step_str}")

        # Handle wildcard
        if part == "*":
            result.update(range(min_val, max_val + 1, step))
            continue

        # Handle range (n-m)
        if "-" in part:
            try:
                start_str, end_str = part.split("-", 1)
                start = int(start_str)
                end = int(end_str)
                if start < min_val or end > max_val or start > end:
                    raise CronParseError(
                        f"Invalid range {part} for {field_name} (must be {min_val}-{max_val})"
                    )
                result.update(range(start, end + 1, step))
            except ValueError:
                raise CronParseError(f"Invalid range: {part}")
            continue

        # Handle single value
        try:
            value = int(part)
            if value < min_val or value > max_val:
                raise CronParseError(
                    f"Value {value} out of range for {field_name} ({min_val}-{max_val})"
                )
            result.add(value)
        except ValueError:
            raise CronParseError(f"Invalid value: {part}")

    if not result:
        raise CronParseError(f"Empty field: {field_name}")

    return result


def parse_cron(expression: str) -> CronExpression:
    """Parse a cron expression into a CronExpression object.

    Args:
        expression: Standard 5-field cron expression

    Returns:
        CronExpression object

    Raises:
        CronParseError: If the expression is invalid
    """
    parts = expression.strip().split()
    if len(parts) != 5:
        raise CronParseError(
            f"Invalid cron expression: expected 5 fields, got {len(parts)}"
        )

    try:
        return CronExpression(
            minute=_parse_field(parts[0], "minute"),
            hour=_parse_field(parts[1], "hour"),
            day=_parse_field(parts[2], "day"),
            month=_parse_field(parts[3], "month"),
            day_of_week=_parse_field(parts[4], "day_of_week"),
            original=expression,
        )
    except CronParseError:
        raise
    except Exception as e:
        raise CronParseError(f"Failed to parse cron expression: {e}")


def validate_cron(expression: str) -> Tuple[bool, Optional[str]]:
    """Validate a cron expression.

    Args:
        expression: Cron expression to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        parse_cron(expression)
        return True, None
    except CronParseError as e:
        return False, str(e)


def get_next_run(
    expression: str,
    after: Optional[datetime] = None,
    timezone: str = "UTC"
) -> datetime:
    """Get the next run time for a cron expression.

    Args:
        expression: Cron expression
        after: Start time (default: now)
        timezone: IANA timezone name

    Returns:
        Next run time (timezone-aware)
    """
    cron = parse_cron(expression)
    tz = ZoneInfo(timezone)

    if after is None:
        after = datetime.now(tz)
    elif after.tzinfo is None:
        after = after.replace(tzinfo=tz)
    else:
        after = after.astimezone(tz)

    # Start from the next minute
    current = after.replace(second=0, microsecond=0) + timedelta(minutes=1)

    # Search up to 4 years ahead (covers all cases including leap years)
    max_iterations = 365 * 4 * 24 * 60  # ~2 million iterations max
    for _ in range(max_iterations):
        if cron.matches(current):
            return current
        current += timedelta(minutes=1)

    raise CronParseError(f"Could not find next run time for: {expression}")


def get_next_runs(
    expression: str,
    count: int = 5,
    after: Optional[datetime] = None,
    timezone: str = "UTC"
) -> List[datetime]:
    """Get the next N run times for a cron expression.

    Args:
        expression: Cron expression
        count: Number of run times to return
        after: Start time (default: now)
        timezone: IANA timezone name

    Returns:
        List of next run times (timezone-aware)
    """
    runs = []
    current = after

    for _ in range(count):
        next_run = get_next_run(expression, after=current, timezone=timezone)
        runs.append(next_run)
        current = next_run

    return runs


def describe_cron(expression: str) -> str:
    """Generate a human-readable description of a cron expression.

    Args:
        expression: Cron expression

    Returns:
        Human-readable description
    """
    try:
        cron = parse_cron(expression)
    except CronParseError:
        return "Invalid cron expression"

    parts = []

    # Minutes
    if cron.minute == set(range(60)):
        parts.append("Every minute")
    elif len(cron.minute) == 1:
        minute = list(cron.minute)[0]
        if minute == 0:
            pass  # Will be described with hour
        else:
            parts.append(f"At minute {minute}")
    else:
        parts.append(f"At minutes {', '.join(str(m) for m in sorted(cron.minute))}")

    # Hours
    if cron.hour == set(range(24)):
        if "Every minute" not in parts[0] if parts else True:
            parts.append("every hour")
    elif len(cron.hour) == 1:
        hour = list(cron.hour)[0]
        am_pm = "AM" if hour < 12 else "PM"
        hour_12 = hour % 12 or 12
        if len(cron.minute) == 1 and list(cron.minute)[0] == 0:
            parts = [f"At {hour_12}:00 {am_pm}"]
        else:
            parts.append(f"at {hour_12} {am_pm}")
    else:
        hours_str = ", ".join(str(h) for h in sorted(cron.hour))
        parts.append(f"at hours {hours_str}")

    # Days
    if cron.day != set(range(1, 32)):
        if len(cron.day) == 1:
            parts.append(f"on day {list(cron.day)[0]}")
        else:
            parts.append(f"on days {', '.join(str(d) for d in sorted(cron.day))}")

    # Months
    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if cron.month != set(range(1, 13)):
        if len(cron.month) == 1:
            parts.append(f"in {month_names[list(cron.month)[0]]}")
        else:
            months = ", ".join(month_names[m] for m in sorted(cron.month))
            parts.append(f"in {months}")

    # Day of week
    dow_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    if cron.day_of_week != set(range(7)):
        if cron.day_of_week == {1, 2, 3, 4, 5}:
            parts.append("on weekdays")
        elif cron.day_of_week == {0, 6}:
            parts.append("on weekends")
        elif len(cron.day_of_week) == 1:
            parts.append(f"on {dow_names[list(cron.day_of_week)[0]]}s")
        else:
            days = ", ".join(dow_names[d] for d in sorted(cron.day_of_week))
            parts.append(f"on {days}")

    return " ".join(parts) if parts else "At specified times"
