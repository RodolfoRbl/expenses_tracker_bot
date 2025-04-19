import os
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
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
)

from utils.db import ExpenseDB

# Initialize DB
db = ExpenseDB(region_name="eu-central-1")


def lambda_handler(event, context):
    # Load environment variables
    load_dotenv(override=True)

    # Initialize the application
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    # Commands
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("settings", settings_handler))
    app.add_handler(CommandHandler("subscription", subscription_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("history", history_handler))

    # Premium commands
    app.add_handler(CommandHandler("categories", categories_handler))
    app.add_handler(CommandHandler("export", export_handler))
    app.add_handler(CommandHandler("budget", budget_handler))

    # Menu options
    app.add_handler(MessageHandler(filters.Regex("^❓ Help$"), help_handler))
    app.add_handler(MessageHandler(filters.Regex("^⚙️ Settings$"), settings_handler))
    app.add_handler(MessageHandler(filters.Regex("^⭐ Subscription$"), subscription_handler))
    app.add_handler(MessageHandler(filters.Regex("^💹 Stats$"), stats_handler))
    app.add_handler(MessageHandler(filters.Regex("^📆 History$"), history_handler))

    # Pass the database instance to handlers
    msg_hdl = lambda u, c: message_handler(u, c, db)
    cbk_hdl = lambda u, c: callback_handler(u, c, db)

    # Callback queries
    app.add_handler(CallbackQueryHandler(cbk_hdl))

    # General message for expenses
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_hdl))

    # Start the bot
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    lambda_handler(None, None)
