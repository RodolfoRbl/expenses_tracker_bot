import os
from utils.general import single_msg


ENVIRONMENT = os.getenv("MY_ENVIRONMENT")

if ENVIRONMENT == "local":
    from dotenv import load_dotenv

    load_dotenv(override=True)

single_msg("Starting...", os.getenv("BOT_TOKEN"), os.getenv("MY_CHAT_ID"))

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
from handlers.user_handlers import (
    start_handler,
    callback_handler,
    msg_handler_by_conv_status,
    stats_handler,
    history_handler,
    last_n_handler,
    settings_handler,
    subscription_handler,
    help_handler,
    categories_handler,
    export_handler,
    budget_handler,
    unknown_command_handler,
    delete_handler,
)
from handlers.admin_handlers import empty_user_data, usage, broadcast, admin_help
from utils.db import ExpenseDB  # noqa


BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"))
REQUESTS_PER_DAY = 100

app = ApplicationBuilder().token(BOT_TOKEN).build()
db = ExpenseDB(region_name="eu-central-1")
app.bot_data.update(
    {
        "db": db,
        "admins": {int(i) for i in os.getenv("ADMINS", "").split(",") if i.isdigit()},
        "owner": MY_CHAT_ID,
        "requests_per_day": REQUESTS_PER_DAY,
    }
)

# Menu Messages
for pattern, handler in [
    ("^❓ Help$", help_handler),
    ("^⚙️ Settings$", settings_handler),
    ("^⭐ Subscription$", subscription_handler),
    ("^💹 Stats$", stats_handler),
    ("^📆 History$", history_handler),
]:
    app.add_handler(MessageHandler(filters.Regex(pattern), handler))

# General message for expenses
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler_by_conv_status))

# Commands
for cmd, handler in [
    ("start", start_handler),
    ("help", help_handler),
    ("settings", settings_handler),
    ("subscription", subscription_handler),
    ("stats", stats_handler),
    ("history", history_handler),
    ("last", last_n_handler),
    # Premium
    ("categories", categories_handler),
    ("budget", budget_handler),
    ("export", export_handler),
    ("delete", delete_handler),
    # Admin
    ("empty_user_data", empty_user_data),
    ("usage", usage),
    ("broadcast", broadcast),
    ("admin", admin_help),
]:
    app.add_handler(CommandHandler(cmd, handler))


# Callback queries
app.add_handler(CallbackQueryHandler(callback_handler))


# Unknown commands
app.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))

is_initialized = None


async def main(event):
    global is_initialized
    try:
        if not is_initialized:
            await app.initialize()
            is_initialized = True
        update = Update.de_json(json.loads(event["body"]), app.bot)
        await app.process_update(update)
    except Exception as e:
        single_msg(f"ERROR in main: {str(e)}", BOT_TOKEN, MY_CHAT_ID)
    return {"statusCode": 200, "body": "Success"}


def lambda_handler(event, context):
    try:
        asyncio.get_event_loop().run_until_complete(main(event))
        return {"statusCode": 200, "body": "Success"}
    except Exception as e:
        single_msg(str(e))


if ENVIRONMENT == "local":
    print("Running...")
    app.run_polling()
