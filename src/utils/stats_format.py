from collections import defaultdict
from datetime import datetime


def group_and_sum_by_key(data: list):
    """
    Groups a list of dictionaries by a specified key and sums the 'amount' property.
    """
    grouped = defaultdict(float)
    for item in data:
        grouped[item["date"]] += float(item.get("amount", 0))
    return dict(grouped)


def graph_weekly_expenses(expenses_list, window="daily", max_bars=10):
    """
    Graphs expenses as a horsizontal bar chart using characters.
    """
    if window not in {"daily", "weekly", "monthly"}:
        raise ValueError("Invalid window value. Choose from 'daily', 'weekly', or 'monthly'.")

    expenses_by_date = group_and_sum_by_key(expenses_list)

    parsed_data = {
        datetime.strptime(date_str, "%Y-%m-%d"): float(amount)
        for date_str, amount in expenses_by_date.items()
    }
    grouped = defaultdict(float)
    if window == "daily":
        # Just return sorted by date
        grouped = {
            date.strftime("%Y-%m-%d"): amount for date, amount in sorted(parsed_data.items())
        }

    elif window == "weekly":
        for date, amount in parsed_data.items():
            year_month = date.strftime("%Y-%b").upper()
            week_number = (date.day - 1) // 7 + 1  # 1-7 = week 1, 8-14 = week 2, etc.
            key = f"{year_month}-W{week_number}"
            grouped[key] += amount

    elif window == "monthly":
        for date, amount in parsed_data.items():
            key = date.strftime("%Y-%b").upper()
            grouped[key] += amount

    else:
        raise ValueError("Invalid window value. Choose from 'week', 'month', or 'year'.")

    grouped_expenses = dict(grouped)
    max_amount = max(grouped_expenses.values())
    scale_factor = max_bars / max_amount
    msg = ""
    for period, amount in grouped_expenses.items():
        bar_length = max(int(amount * scale_factor), 1)  # At least 1 character
        bar = "■" * bar_length
        msg += f"{period:10} {bar} ${amount:,.2f}\n"
    return msg
