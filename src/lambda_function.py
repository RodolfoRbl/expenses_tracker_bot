import os
import asyncio
import json
from dotenv import load_dotenv

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
    message_handler,
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
from utils.general import single_msg

if os.getenv("MY_ENVIRONMENT"):
    load_dotenv(override=True)


BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"))
ENVIRONMENT = os.getenv("ENVIRONMENT")
REQUESTS_PER_DAY = 100

single_msg("Starting...", BOT_TOKEN, MY_CHAT_ID)

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


# Menu Messages
for pattern, handler in [
    ("^❓ Help$", help_handler),
    ("^⚙️ Settings$", settings_handler),
    ("^⭐ Subscription$", subscription_handler),
    ("^💹 Stats$", stats_handler),
    ("^📆 History$", history_handler),
]:
    app.add_handler(MessageHandler(filters.Regex(pattern), handler))

# Callback queries
app.add_handler(CallbackQueryHandler(callback_handler))
app.add_handler(CallbackQueryHandler(subscription_handler))  # To avoid duplicate rate count

# General message for expenses
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

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
