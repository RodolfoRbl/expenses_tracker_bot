import asyncio
import os
from telegram import BotCommand
from telegram.ext import Application
from dotenv import load_dotenv

load_dotenv(override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def set_bot_commands():
    app = Application.builder().token(BOT_TOKEN).build()

    commands = [
        BotCommand("start", "▶️ Start the bot"),
        BotCommand("help", "🆘 Bot instructions"),
        BotCommand("last", "⌛️ Show last records"),
        BotCommand("stats", "📊 Statistics"),
        BotCommand("subscription", "💎 View premium benefits"),
        BotCommand("history", "📋 Show all records"),
        BotCommand("delete", "❌ Delete a recent record"),
        BotCommand("settings", "⚙️ Custom settings ⭐️"),
        BotCommand("categories", "🗂 Manage your categories ⭐️"),
        BotCommand("export", "📁 Download history for Excel ⭐️"),
        BotCommand("budget", "🎯 Set a monthly budget ⭐️"),
    ]

    await app.bot.set_my_commands(commands)
    print("✅ Commands set successfully.")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(set_bot_commands())
