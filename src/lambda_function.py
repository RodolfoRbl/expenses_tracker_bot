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
app.add_handler(CommandHandler("start", with_db(start_handler)))
app.add_handler(CommandHandler("help", help_handler))
app.add_handler(CommandHandler("settings", settings_handler))
app.add_handler(CommandHandler("subscription", subscription_handler))
app.add_handler(CommandHandler("stats", stats_handler))
app.add_handler(CommandHandler("history", history_handler))

# Premium commands
app.add_handler(CommandHandler("categories", categories_handler))
app.add_handler(CommandHandler("budget", budget_handler))
app.add_handler(CommandHandler("export", with_db(export_handler)))
app.add_handler(CommandHandler("delete", with_db(delete_handler)))

# Admin commands
app.add_handler(CommandHandler("empty_user_data", with_db(admn.empty_user_data)))
app.add_handler(CommandHandler("users_stats", with_db(admn.get_users_stats)))
app.add_handler(CommandHandler("broadcast", admn.broadcast))
app.add_handler(CommandHandler("admin", admn.admin_help))

# Menu options
app.add_handler(MessageHandler(filters.Regex("^❓ Help$"), help_handler))
app.add_handler(MessageHandler(filters.Regex("^⚙️ Settings$"), settings_handler))
app.add_handler(MessageHandler(filters.Regex("^⭐ Subscription$"), subscription_handler))
app.add_handler(MessageHandler(filters.Regex("^💹 Stats$"), stats_handler))
app.add_handler(MessageHandler(filters.Regex("^📆 History$"), history_handler))

# Callback queries
app.add_handler(CallbackQueryHandler(with_db(callback_handler)))

# General message for expenses
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, with_db(message_handler)))

# Unknown commands
app.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))

# Always executed
app.add_handler(
    MessageHandler(
        filters.ALL, lambda u, c: db.add_activity(str(u.effective_user.id), str(c.bot.id))
    )
)


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
