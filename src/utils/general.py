from datetime import timezone, timedelta, datetime
import requests


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


def single_msg(msg, token, chat_id):
    return requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": int(chat_id), "text": msg},
    )


def send_typing_action_raw(token: str, chat_id: int):
    url = f"https://api.telegram.org/bot{token}/sendChatAction"
    payload = {"chat_id": chat_id, "action": "typing"}
    response = requests.post(url, data=payload)
    return response.json()


def truncate(text, max_len=15):
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


if __name__ == "__main__":
    print(get_date_with_tz(fmt="%Y-%m-%d %H:%M"))
