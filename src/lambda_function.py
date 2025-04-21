import os
import asyncio
import json

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram import Update
from dotenv import load_dotenv
from utils.handlers import (
    start_handler,
    callback_handler,
    message_handler,
    stats_handler,
    history_handler,
    settings_handler,
    subscription_handler,
    help_handler,
    categories_handler,
    export_handler,
    budget_handler,
    unknown_command_handler,
    delete_handler,
)

from utils import admin_handlers as admn
from utils.db import ExpenseDB

db = ExpenseDB(region_name="eu-central-1")

load_dotenv(override=True)
BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"))

app = ApplicationBuilder().token(BOT_TOKEN).build()


def with_db(handler):
    "Return the function object with the database instance"
    return lambda u, c: handler(u, c, db)


# Commands
for cmd, handler in [
    ("start", start_handler),
    ("help", help_handler),
    ("settings", settings_handler),
    ("subscription", subscription_handler),
    ("stats", stats_handler),
    ("history", history_handler),
    # Premium
    ("categories", categories_handler),
    ("budget", budget_handler),
    ("export", export_handler),
    ("delete", delete_handler),
    # Admin
    ("empty_user_data", admn.empty_user_data),
    ("users_stats", admn.get_users_stats),
    ("broadcast", admn.broadcast),
    ("admin", admn.admin_help),
]:
    app.add_handler(CommandHandler(cmd, with_db(handler)))


# Menu Messages
for pattern, handler in [
    ("^❓ Help$", help_handler),
    ("^⚙️ Settings$", settings_handler),
    ("^⭐ Subscription$", subscription_handler),
    ("^💹 Stats$", stats_handler),
    ("^📆 History$", history_handler),
]:
    app.add_handler(MessageHandler(filters.Regex(pattern), with_db(handler)))

# Callback queries
app.add_handler(CallbackQueryHandler(with_db(callback_handler)))

# General message for expenses
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, with_db(message_handler)))

# Unknown commands
app.add_handler(MessageHandler(filters.COMMAND, with_db(unknown_command_handler)))


def sm(m):
    import requests

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": MY_CHAT_ID, "text": m},
    )


async def main(event, context):
    try:
        async with app:
            await app.process_update(Update.de_json(json.loads(event["body"]), app.bot))
    except Exception as e:
        sm(f"ERROR in main: {str(e)}")
    return {"statusCode": 200, "body": "Success"}


def lambda_handler(event, context):
    try:
        asyncio.get_event_loop().run_until_complete(main(event, context))
        return {"statusCode": 200, "body": "Success"}
    except Exception as e:
        sm(str(e))
