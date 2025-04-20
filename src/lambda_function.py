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
    remove_handler,
)

from utils.db import ExpenseDB

# Initialize DB
db = ExpenseDB(region_name="eu-central-1")

# Load environment variables
load_dotenv(override=True)

# Initialize the application
app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

# Commands
app.add_handler(CommandHandler("start", start_handler))
app.add_handler(CommandHandler("help", help_handler))
app.add_handler(CommandHandler("settings", settings_handler))
app.add_handler(CommandHandler("subscription", subscription_handler))
app.add_handler(CommandHandler("summary", stats_handler))
app.add_handler(CommandHandler("history", history_handler))

# Menu options
app.add_handler(MessageHandler(filters.Regex("^❓ Help$"), help_handler))
app.add_handler(MessageHandler(filters.Regex("^⚙️ Settings$"), settings_handler))
app.add_handler(MessageHandler(filters.Regex("^⭐ Subscription$"), subscription_handler))
app.add_handler(MessageHandler(filters.Regex("^💹 Summary$"), stats_handler))
app.add_handler(MessageHandler(filters.Regex("^📆 History$"), history_handler))

# Pass the database instance to handlers
msg_hdl = lambda u, c: message_handler(u, c, db)
cbk_hdl = lambda u, c: callback_handler(u, c, db)
rmv_hdl = lambda u, c: remove_handler(u, c, db)

# Callback queries
app.add_handler(CallbackQueryHandler(cbk_hdl))

# General message for expenses
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_hdl))

# Premium commands
app.add_handler(CommandHandler("categories", categories_handler))
app.add_handler(CommandHandler("export", export_handler))
app.add_handler(CommandHandler("budget", budget_handler))
app.add_handler(CommandHandler("remove", rmv_hdl))

# Unknown commands
app.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))


async def main(event, context):
    try:
        await app.initialize()
        await app.process_update(Update.de_json(json.loads(event["body"]), app.bot))
        return {"statusCode": 200, "body": "Success"}
    except Exception as e:
        return {"statusCode": 500, "body": f"Failure {e}"}


def lambda_handler(event, context):
    return asyncio.get_event_loop().run_until_complete(main(event, context))
