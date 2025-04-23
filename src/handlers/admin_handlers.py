from telegram import Update
from telegram.ext import ContextTypes
from .decorators import admin_only, rate_counter
from ..utils.db import ExpenseDB


def get_db(context: ContextTypes.DEFAULT_TYPE) -> ExpenseDB:
    return context.bot_data.get("db")


@rate_counter
@admin_only
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help for admins."""
    msg = """
📋 <b>Admin Commands Help</b>:

<b>/empty_user_data</b> - Delete all records for yourself.

<b>/users_stats</b> - Get usage stats for a given user or for all.

<b>/broadcast</b> - Send a message to all bot users.

<b>Note</b>: These commands are restricted to admin users only.
"""
    await update.message.reply_text(msg, parse_mode="HTML")


@rate_counter
@admin_only
async def empty_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete all records for a specific user."""
    db = get_db(context)
    user_id = str(update.effective_user.id)
    try:
        records = db.fetch_expenses_by_user_and_date(user_id, "1900-01-01", "2100-12-31")
        db.remove_batch_records(records)
        await update.message.reply_text(f"✅ Deleted {len(records)} records for user {user_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error deleting user data: {str(e)}")


@rate_counter
@admin_only
async def usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get usage statistics for a specific user or all users."""
    db = get_db(context)
    owner = context.bot_data["owner"]
    args = context.args
    try:
        if args:
            if args[0] != "me":
                user_id = str(args[0])
            else:
                user_id = owner
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


@rate_counter
@admin_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message to all bot users."""
    await update.message.reply_text("📣 Broadcasting logic to be implemented")
