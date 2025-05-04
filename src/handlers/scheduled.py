from utils.db import ExpenseDB
from telegram import Bot
import time
from handlers.callbacks import _get_stats_report
from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key, Attr


async def send_monthly_report(bot: Bot, db: ExpenseDB):
    """
    Sends a monthly report message to all users for the given bot
    """
    users = [i.get("user_id") for i in db.get_fields_by_bot(bot.id)]

    # Last day of the previous month
    now = datetime.now(timezone.utc)
    now = now.replace(day=1).date()
    lday = now - timedelta(days=1)
    lday = datetime.strftime(lday, "%Y-%m-%d")

    for i in range(0, len(users), 20):
        chunk = users[i : i + 20]
        for user_id in chunk:
            try:
                msg = await _get_stats_report(db, "This Month", user_id, bot.id, cutoff_date=lday)
                await bot.send_message(chat_id=user_id, text=msg, parse_mode="HTML")
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
        # Sleep only if there are more chunks to process
        if i + 20 < len(users):
            time.sleep(2)


async def send_daily_reminder(bot: Bot, db: ExpenseDB):
    """
    Sends a daily reminder to record expenses
    """
    response = db.users_table.query(
        IndexName="bot_id-index",
        KeyConditionExpression=Key("bot_id").eq(str(bot.id)),
        ProjectionExpression=", ".join(["user_id", "daily_reminders"]),
        FilterExpression=Attr("daily_reminders").eq(True),
    )
    items = response.get("Items", {})
    users = [item["user_id"] for item in items]
    msg = (
        "📝 Don’t forget to add any pending expenses for today!\n"
        "You can turn off daily reminders in /settings."
    )
    for usr in users:
        await bot.send_message(usr, text=msg, parse_mode="HTML")
        time.sleep(0.05)
