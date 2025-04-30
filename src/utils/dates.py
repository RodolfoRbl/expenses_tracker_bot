from datetime import datetime, timedelta, timezone
from config import TZ_BY_OFFSET


def parse_timezone(timezone_str: str = "UTC-6") -> timezone:
    """
    Parse a timezone string (e.g., 'UTC-6' or 'UTC+3') into a timezone object.
    """
    if timezone_str.startswith("UTC") and len(timezone_str) == 5:
        sign = timezone_str[3]
        offset_hours = int(timezone_str[4:])
        if sign == "-":
            offset = timedelta(hours=-offset_hours)
        elif sign == "+":
            offset = timedelta(hours=offset_hours)
        else:
            raise ValueError("Invalid timezone format. Use 'UTC±X'.")
        return timezone(offset)
    else:
        return timezone(timedelta(hours=0))


def get_str_timestamp():
    return str(int(datetime.now().timestamp()))


def get_date_with_tz(timezone: str = "UTC", fmt="%Y-%m-%d", timestamp: int = None):
    tz = parse_timezone(timezone)
    if timestamp:
        current_time = datetime.fromtimestamp(timestamp, tz)
    else:
        current_time = datetime.now(tz)
    return current_time.strftime(fmt)


def parse_city_timezone(offset_str: str) -> str:
    """
    Returns a string of cities and current time for a given UTC offset string (e.g. 'UTC+5')
    """
    # Parse the UTC offset
    offset_hours = float(offset_str.replace("UTC", ""))
    offset = timedelta(hours=offset_hours)
    now = datetime.now(timezone(offset))
    time_str = now.strftime("%Y-%m-%d %H:%M")

    # Get cities for the offset
    cities = TZ_BY_OFFSET.get(offset_str)
    if not cities:
        return f"{offset_str}: No known cities."
    return f"{cities} ⌛️ {time_str}"


def get_time_all_zones():
    """
    Returns a string of cities and current time for all known timezones.
    """
    return {tz_i: parse_city_timezone(tz_i) for tz_i in TZ_BY_OFFSET.keys()}
