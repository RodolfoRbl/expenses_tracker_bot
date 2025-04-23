from datetime import timezone, timedelta, datetime
import requests


def parse_timezone(timezone_str: str = "UTC-6") -> timezone:
    """
    Parse a timezone string (e.g., 'UTC-6' or 'UTC+3') into a timezone object.
    """
    if timezone_str.startswith("UTC"):
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
        raise ValueError("Invalid timezone format. Use 'UTC±X'.")


def get_str_timestamp():
    return str(int(datetime.now().timestamp()))


def single_msg(msg, token, chat_id):
    return requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": int(chat_id), "text": msg},
    )
