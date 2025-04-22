import os
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from .db import ExpenseDB

ADMINS = {int(x.strip()) for x in os.getenv("ADMINS", "").split(",") if x.strip().isdigit()}
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"))


def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id in ADMINS:
            return await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text("⛔ This command is only for admins.")

    return wrapper


@admin_only
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE, db: ExpenseDB):
    """Help for admins."""
    msg = """
📋 <b>Admin Commands Help</b>:

<b>/empty_user_data</b> - Delete all records for yourself.

<b>/users_stats</b> - Get usage stats for a given user or for all.

<b>/broadcast</b> - Send a message to all bot users.

<b>Note</b>: These commands are restricted to admin users only.
"""
    await update.message.reply_text(msg, parse_mode="HTML")


@admin_only
async def empty_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE, db: ExpenseDB):
    """Delete all records for a specific user."""
    user_id = str(update.effective_user.id)
    try:
        records = db.fetch_expenses_by_user_and_date(user_id, "1900-01-01", "2100-12-31")
        db.remove_batch_records(records)
        await update.message.reply_text(f"✅ Deleted {len(records)} records for user {user_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error deleting user data: {str(e)}")


@admin_only
async def get_users_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, db: ExpenseDB):
    """Get usage statistics for a specific user or all users."""
    args = context.args
    try:
        if args:
            if args[0] != "me":
                user_id = str(args[0])
            else:
                user_id = str(MY_CHAT_ID)
            records = db.fetch_expenses_by_user_and_date(user_id, "1900-01-01", "2100-12-31")
            msg = f"📊 Stats for user {user_id}:\n"
            msg += f"Total records: {len(records)}\n"
            if records:
                first_date = min(r["date"] for r in records)
                last_date = max(r["date"] for r in records)
                msg += f"First record: {first_date}\n"
                msg += f"Last record: {last_date}"
        else:
            # TODO: Implement global stats across all users
            msg = "⚠️ Global stats not implemented yet"

        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ Error getting stats: {str(e)}")


@admin_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, db: ExpenseDB):
    """Send a message to all bot users."""
    await update.message.reply_text("📣 Broadcasting logic to be implemented")
