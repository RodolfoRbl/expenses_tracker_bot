from telegram import Update
from telegram.ext import ContextTypes
from utils.keyboards import (
    get_start_keyboard,
    get_stats_keyboard,
    get_history_keyboard,
    get_settings_keyboard,
    get_delete_keyboard,
    get_help_keyboard,
    get_premium_keyboard,
)
from utils.general import truncate, get_db
from handlers.callbacks import _show_categories_to_manage
from utils.dates import parse_timezone, get_str_timestamp

from handlers._decorators import rate_counter
from handlers.callbacks import _ai_handler
from datetime import datetime
import csv
import io

from config import (
    START_TEXT,
    HELP_TEXT,
    PREMIUM_TEXT,
    CMD_FOR_PREMIUM_TEXT,
    CMD_PREMIUM_WELCOME_TEXT,
    DEFAULT_CATEGORIES,
    ST_REGULAR,
)


@rate_counter
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    await update.message.reply_text(
        START_TEXT,
        parse_mode="HTML",
        reply_markup=get_start_keyboard(),
    )

    user_id = str(update.effective_user.id)
    bot_id = str(context.bot.id)

    # Check if the user and bot already exist in the table
    existing_user = db.users_table.get_item(Key={"user_id": user_id, "bot_id": bot_id}).get("Item")

    if not existing_user:
        curr_time = get_str_timestamp()
        db.users_table.put_item(
            Item={
                "user_id": user_id,
                "bot_id": bot_id,
                "username": update.effective_user.username or "",
                "first_name": update.effective_user.first_name or "",
                "language_code": update.effective_user.language_code or "",
                "is_premium": False,
                "end_premium": "",
                "joined_at": curr_time,
                "last_active": curr_time,
                "daily_requests": 0,
                "total_requests": 0,  # It is handled after all handlers
                "user_timezone": "UTC-6",
                "categories": DEFAULT_CATEGORIES,
                "lang": "EN",
                "budget": 0,
                "currency": "USD",
                "temp_data": {},
                "conversation_status": ST_REGULAR,
                "artificial_intelligence": False,
            }
        )


@rate_counter
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HELP_TEXT,
        reply_markup=get_help_keyboard(),
        parse_mode="HTML",
    )


@rate_counter
async def premium_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        PREMIUM_TEXT,
        reply_markup=get_premium_keyboard(),
        parse_mode="HTML",
    )


@rate_counter
async def delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    user_id = str(update.effective_user.id)

    try:
        n = 10
        records = db.fetch_latest_expenses(user_id, n)
        if not records:
            await update.message.reply_text("No records found to delete.")
            return
        # Build message body
        cats = db.get_fields(user_id, context.bot.id, "categories")
        history = [
            f"{item['date']} - ${item['amount']:,.2f} - {cats[item['category']]['name']}"
            + (f" ({truncate(item['description'])})" if item.get("description") else "")
            for item in records
        ]
        keys = [i["timestamp"] for i in records]
        await update.message.reply_text(
            "Select a record to <b>delete</b>:",
            parse_mode="HTML",
            reply_markup=get_delete_keyboard(history, keys),
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


@rate_counter
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Select time period:", reply_markup=get_stats_keyboard())


@rate_counter
async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Select time window for history:", reply_markup=get_history_keyboard()
    )


@rate_counter
async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_admin = user_id in context.bot_data.get("admins", [])
    if is_admin:
        await update.message.reply_text(
            CMD_PREMIUM_WELCOME_TEXT, parse_mode="HTML", reply_markup=get_settings_keyboard()
        )
        return
    else:
        is_premium = get_db(context).get_fields(user_id, context.bot.id, "is_premium")
        if is_premium:
            await update.message.reply_text(
                CMD_PREMIUM_WELCOME_TEXT, parse_mode="HTML", reply_markup=get_settings_keyboard()
            )
        else:
            await update.message.reply_text(CMD_FOR_PREMIUM_TEXT, parse_mode="HTML")


@rate_counter
async def categories_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _show_categories_to_manage(update, context)


@rate_counter
async def export_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    user_id = str(update.effective_user.id)
    try:
        # Fetch all records for the user
        records = db.fetch_expenses_by_user_and_date(user_id, "1950-01-01", "2100-12-31")
        await update.message.reply_text("🟡 Exporting your data...")
        if not records:
            await update.message.reply_text("⚠️ No records found to export.")
            return

        # Create in memory CSV
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Date", "Amount", "Category", "Description", "Income"])
        cats = db.get_fields(user_id, context.bot.id, "categories")
        for record in records:
            writer.writerow(
                [
                    record["date"],
                    record["amount"],
                    cats[record["category"]]["name"],
                    record.get("description", ""),
                    "Yes" if record["income"] else "No",
                ]
            )
        output.seek(0)
        file_dt = datetime.now(parse_timezone()).strftime("%Y_%m_%d")
        await update.message.reply_document(
            document=io.BytesIO(output.getvalue().encode()),
            filename=f"expenses_{file_dt}.csv",
            caption="✅ Your export is ready!",
        )
    except Exception as e:
        await update.message.reply_text(f"Error exporting data: {str(e)}")


@rate_counter
async def budget_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(CMD_FOR_PREMIUM_TEXT, parse_mode="HTML")


@rate_counter
async def cmd_ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ai_handler(update, context)


@rate_counter
async def last_n_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    user_id = str(update.effective_user.id)
    try:
        if context.args:
            try:
                n = int(context.args[0])
                if n <= 0:
                    raise ValueError
            except ValueError:
                await update.message.reply_text(
                    "Please provide a valid positive number. Example: /last 5"
                )
                return
        else:
            n = 5

        # Fetch the last N records
        records = db.fetch_latest_expenses(user_id, n)
        if not records:
            await update.message.reply_text("No records found.")
            return
        cats = db.get_fields(user_id, context.bot.id, "categories")
        history = "\n".join(
            f"{item['date']}: <code>${item['amount']:,.2f}</code> - {cats[item['category']]['name']}"
            + (f" ({item['description']})" if item["description"] else "")
            for item in records
        )

        await update.message.reply_text(
            f"📋 <b>Last {n} Records:</b>\n\n{history}",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"Error fetching records: {str(e)}")


@rate_counter
async def unknown_command_handler(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Sorry, I didn't understand that command.\nTry /help for a list of commands."
    )
