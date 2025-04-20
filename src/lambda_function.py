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

from utils.admin_handlers import empty_user_data, get_users_stats, broadcast

from utils.db import ExpenseDB


db = ExpenseDB(region_name="eu-central-1")

# Load environment variables
load_dotenv(override=True)
BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"))
# Initialize the application
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Commands
app.add_handler(CommandHandler("start", start_handler))
app.add_handler(CommandHandler("help", help_handler))
app.add_handler(CommandHandler("settings", settings_handler))
app.add_handler(CommandHandler("subscription", subscription_handler))
app.add_handler(CommandHandler("stats", stats_handler))
app.add_handler(CommandHandler("history", history_handler))

# Pass the database instance to handlers
msg_hdl = lambda u, c: message_handler(u, c, db)
cbk_hdl = lambda u, c: callback_handler(u, c, db)
rmv_hdl = lambda u, c: delete_handler(u, c, db)
exp_hdl = lambda u, c: export_handler(u, c, db)

admin_empty_hdl = lambda u, c: empty_user_data(u, c, db)
admin_users_stats = lambda u, c: get_users_stats(u, c, db)
admin_broadcast = lambda u, c: broadcast(u, c, db)

# Premium commands
app.add_handler(CommandHandler("categories", categories_handler))
app.add_handler(CommandHandler("export", exp_hdl))
app.add_handler(CommandHandler("budget", budget_handler))
app.add_handler(CommandHandler("delete", rmv_hdl))

# Admin commands
app.add_handler(CommandHandler("empty_user_data", admin_empty_hdl))
app.add_handler(CommandHandler("users_stats", admin_users_stats))
app.add_handler(CommandHandler("broadcast", admin_broadcast))


# Menu options
app.add_handler(MessageHandler(filters.Regex("^❓ Help$"), help_handler))
app.add_handler(MessageHandler(filters.Regex("^⚙️ Settings$"), settings_handler))
app.add_handler(MessageHandler(filters.Regex("^⭐ Subscription$"), subscription_handler))
app.add_handler(MessageHandler(filters.Regex("^💹 Stats$"), stats_handler))
app.add_handler(MessageHandler(filters.Regex("^📆 History$"), history_handler))

# Callback queries
app.add_handler(CallbackQueryHandler(cbk_hdl))

# General message for expenses
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_hdl))


# Unknown commands
app.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))


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
