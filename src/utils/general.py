import requests
from telegram import Update
from telegram.ext import ContextTypes
from utils.db import ExpenseDB
from utils.llm import AIClient
from utils.dates import get_date_with_tz


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


def get_db(context: ContextTypes.DEFAULT_TYPE) -> ExpenseDB:
    return context.bot_data.get("db")


def get_ai_client(context: ContextTypes.DEFAULT_TYPE) -> AIClient:
    return context.bot_data.get("llm")


def get_active_categories(db: ExpenseDB, user_id: str, bot_id: str) -> dict:
    return {
        k: v for k, v in db.get_fields(user_id, bot_id, "categories").items() if v["active"] == 1
    }


def format_agg_cats(data_dict: dict) -> str:
    total = sum(data_dict.values())
    sorted_data = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
    formatted = [
        f"<code>${amount:,.2f} ({int(amount / total * 100) if total != 0 else 0}%)</code> - {category}"
        for category, amount in sorted_data
    ]
    return "\n".join(formatted)


async def parse_msg_to_elements(update: Update, text: str) -> tuple:
    # Split the text into words
    words = text.split()
    is_last_digit = words[-1].lstrip("+-").replace(".", "", 1).isdigit()
    is_first_digit = words[0].lstrip("+-").replace(".", "", 1).isdigit()
    if len(words) == 1 and is_first_digit:
        amount = float(words[0])
        description = ""
        is_income = "+" in words[0]
    elif len(words) < 2:
        await update.message.reply_text("Please use the format: amount description")
        return [None] * 3
    elif is_last_digit and is_first_digit:
        await update.message.reply_text(
            "Invalid format. Digits should be at the start or end, not both."
        )
        return [None] * 3
    # Check if the first or last word is a valid amount
    elif is_first_digit:
        is_income = "+" in words[0]
        amount = float(words[0])
        description = " ".join(words[1:])
    elif is_last_digit:
        is_income = "+" in words[-1]
        amount = float(words[-1])
        description = " ".join(words[:-1])
    else:
        await update.message.reply_text("Please use the format: amount description")
        return [None] * 3
    return amount, description, is_income


def replace_all(text: str, replacements: dict) -> str:
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


if __name__ == "__main__":
    print(get_date_with_tz(fmt="%Y-%m-%d %H:%M"))
