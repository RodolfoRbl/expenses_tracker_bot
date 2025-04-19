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
)


def lambda_handler(event, context):
    # Load environment variables
    load_dotenv(override=True)

    # Initialize the application
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("history", history_handler))
    app.add_handler(CommandHandler("settings", settings_handler))
    app.add_handler(CommandHandler("subscription", subscription_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Menu option handlers
    app.add_handler(MessageHandler(filters.Regex("^❓ Help$"), help_handler))
    app.add_handler(MessageHandler(filters.Regex("^💹 Stats$"), stats_handler))
    app.add_handler(MessageHandler(filters.Regex("^📆 History$"), history_handler))
    app.add_handler(MessageHandler(filters.Regex("^⚙️ Settings$"), settings_handler))
    app.add_handler(MessageHandler(filters.Regex("^⭐ Subscription$"), subscription_handler))

    # General message handler for expenses
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Start the bot
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    lambda_handler(None, None)
