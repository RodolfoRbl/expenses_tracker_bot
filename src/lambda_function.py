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
    PreCheckoutQueryHandler,
    filters,
)
from telegram import Update
from handlers import (
    commands as cm_hdl,
    callbacks as cb_hdl,
    admins as ad_hdl,
    messages as msg_hdl,
    payments as pm_hdl,
)
from utils.db import ExpenseDB
from utils.llm import AIClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"))
LLM_API_KEY = os.getenv("LLM_API_KEY")
SPECIAL_PREFIX = os.getenv("SPECIAL_PREFIX")
REQUESTS_PER_DAY = 100

app = ApplicationBuilder().token(BOT_TOKEN).build()
db = ExpenseDB(region_name="eu-central-1")
llm = AIClient(api_key=LLM_API_KEY)

app.bot_data.update(
    {
        "db": db,
        "llm": llm,
        "admins": {int(i) for i in os.getenv("ADMINS", "").split(",") if i.isdigit()},
        "owner": MY_CHAT_ID,
        "requests_per_day": REQUESTS_PER_DAY,
        "special_prefix": SPECIAL_PREFIX,
    }
)

# Menu Messages
for pattern, handler in [
    ("^❓ Help$", cm_hdl.help_handler),
    ("^⚙️ Settings$", cm_hdl.settings_handler),
    ("^⭐ Premium$", cm_hdl.premium_handler),
    ("^💹 Stats$", cm_hdl.stats_handler),
    ("^📆 History$", cm_hdl.history_handler),
    ("^🧠 Artificial Intelligence$", cb_hdl.settings_ai),
]:
    app.add_handler(MessageHandler(filters.Regex(pattern), handler))

# General message for expenses
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_hdl.text_messages))

# Commands
for cmd, handler in [
    ("start", cm_hdl.start_handler),
    ("help", cm_hdl.help_handler),
    ("settings", cm_hdl.settings_handler),
    ("premium", cm_hdl.premium_handler),
    ("stats", cm_hdl.stats_handler),
    ("history", cm_hdl.history_handler),
    ("last", cm_hdl.last_n_handler),
    ("artificial_intelligence", cm_hdl.cmd_ai_handler),
    # Premium
    ("categories", cm_hdl.categories_handler),
    ("budget", cm_hdl.budget_handler),
    ("export", cm_hdl.export_handler),
    ("delete", cm_hdl.delete_handler),
    # Admin
    ("empty_user_data", ad_hdl.empty_user_data),
    ("usage", ad_hdl.usage),
    ("broadcast", ad_hdl.broadcast),
    ("admin", ad_hdl.admin_help),
]:
    app.add_handler(CommandHandler(cmd, handler))


callback_queries = {
    # Help
    "^help_premium$": cb_hdl.help_premium,
    # Settings
    "^settings:Currency$": cb_hdl.settings_currency,
    "^settings:Language$": cb_hdl.settings_language,
    "^settings:Timezone$": cb_hdl.settings_timezone,
    "^settings:Timezone:pt2$": cb_hdl.settings_timezone,
    "^settings:Timezone:reset$": cb_hdl.settings_timezone_reset,
    "^settings:Timezone:id:": cb_hdl.settings_timezone_confirm,
    "^settings:Categories$": cb_hdl.settings_categories,
    "^settings:Notifications$": cb_hdl.settings_notify,
    "^settings:cancel$": cb_hdl.settings_cancel,
    "^settings:Artificial Intelligence$": cb_hdl.settings_ai,
    # AI
    "^settings:ai:": cb_hdl.ai_change_status,
    # History
    "^history:cancel$": cb_hdl.history_cancel,
    "^history:window:": cb_hdl.history_windows,
    "^history:back_to_menu$": cb_hdl.history_back,
    # Stats
    "^stats:cancel$": cb_hdl.stats_cancel,
    "^stats:window:": cb_hdl.stats_windows,
    "^stats:back_to_menu$": cb_hdl.stats_back,
    # Expenses (add, delete)
    "^expenses:cancel$": cb_hdl.cancel_new_expense,
    "^expenses:delete:cancel$": cb_hdl.cancel_expense_deletion,
    "^expenses:category:": cb_hdl.expense_confirm_category,
    "^expenses:delete:id:": cb_hdl.confirm_delete_expense,
    # Categories
    "^categories:menu:cancel$": cb_hdl.cancel_mgmt_categories,
    "^categories:menu:add$": cb_hdl.add_category,
    "^categories:menu:reset$": cb_hdl.reset_categories,
    "^categories:menu:delete$": cb_hdl.delete_category,
    "^categories:delete:back_to_menu$": cb_hdl.categories_back_to_menu,
    "^categories:delete:list:": cb_hdl.confirm_delete_category,
    # Premium
    "^premium:cancel$": cb_hdl.cancel_select_plan,
    "^premium:select_plan:": cb_hdl.confirm_premium_plan,
    # Unknown callback
    "unknown": cb_hdl.unknown_callback,
}

for pattern, handler in callback_queries.items():
    app.add_handler(CallbackQueryHandler(handler, pattern))

# Payments
app.add_handler(PreCheckoutQueryHandler(pm_hdl.pre_checkout_handler))
app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, pm_hdl.successful_payment_handler))

app.add_handler(MessageHandler(filters.COMMAND, cm_hdl.unknown_command_handler))

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
