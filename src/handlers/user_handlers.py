from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes
from utils.keyboards import (
    get_start_keyboard,
    get_category_keyboard,
    get_stats_keyboard,
    get_history_keyboard,
    get_settings_keyboard,
    get_delete_keyboard,
    get_help_keyboard,
    get_subscription_keyboard,
)
from utils.general import (
    truncate,
    get_db,
    format_agg_cats,
    parse_msg_to_elements,
)

from utils.dates import parse_timezone, get_str_timestamp

from handlers.decorators import rate_counter
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict
import csv
import io

from config import (
    START_TEXT,
    HELP_TEXT,
    PREMIUM_TEXT,
    CATEGORIES,
    ST_WAIT_CATEGORY,
    ST_REGULAR,
)


cat_map = {k.split()[-1]: v for k, v in CATEGORIES.items()}
parse_cat_id = lambda id: {v: k for k, v in CATEGORIES.items()}[int(id)]


# ############################################
# ######## COMMANDS
# ############################################


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
                "joined_at": curr_time,
                "last_active": curr_time,
                "daily_requests": 0,
                "total_requests": 0,  # It is handled after all handlers
                "custom_data": {
                    "timezone": "UTC-6",
                    "categories": {},
                    "lang": "EN",
                    "budget": 0,
                    "currency": "USD",
                },
                "temp_data": {},
                "conversation_status": ST_REGULAR,
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
async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        PREMIUM_TEXT,
        reply_markup=get_subscription_keyboard(),
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
        history = [
            f"{item['date']} - ${item['amount']:,.2f} - {parse_cat_id(item['category'])}"
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
    await update.message.reply_text(
        "<i>⚠️ Settings available only for ⭐️<b>PREMIUM</b>⭐️ users</i> ⚠️\nSend /subscription to get Fundu Premium",
        parse_mode="HTML",
        reply_markup=get_settings_keyboard(),
    )


@rate_counter
async def categories_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<i>⚠️ Categories command available only for ⭐️<b>PREMIUM</b>⭐️ users</i> ⚠️\nSend /subscription to get Fundu Premium",
        parse_mode="HTML",
    )


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
        for record in records:
            writer.writerow(
                [
                    record["date"],
                    record["amount"],
                    parse_cat_id(record["category"].split()[-1]),
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
    await update.message.reply_text(
        "<i>⚠️ Budget command available only for ⭐️<b>PREMIUM</b>⭐️ users</i> ⚠️\nSend /subscription to get Fundu Premium",
        parse_mode="HTML",
    )


@rate_counter
async def unknown_command_handler(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Sorry, I didn't understand that command.\nTry /help for a list of commands."
    )


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

        history = "\n".join(
            f"{item['date']}: <code>${item['amount']:,.2f}</code> - {parse_cat_id(item['category'])}"
            + (f" ({item['description']})" if item["description"] else "")
            for item in records
        )

        await update.message.reply_text(
            f"📋 <b>Last {n} Records:</b>\n\n{history}",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"Error fetching records: {str(e)}")


# ############################################
# ######## MESSAGES
# ############################################


async def _msg_regular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    text = update.message.text.strip()
    if len(text) >= 100:
        await update.message.reply_text("Message too long. Please keep it under 100 characters.")
        return
    user_id = str(update.effective_user.id)

    amount, description, is_income = await parse_msg_to_elements(update, text)
    _desc = f"<b>Description</b>: {description}" if description else ""
    if is_income is None:
        pass
    elif is_income:
        try:
            await update.message.reply_text(f"✅ Logged: ${amount:,.2f} in Income")
            db.insert_expense(
                user_id=user_id,
                amount=amount,
                category="99",  # Income category
                currency="USD",
                description=description,
                income=is_income,
            )
        except Exception as e:
            await update.message.reply_text(f"Error inserting income: {str(e)}")
    else:
        try:
            await update.message.reply_text(
                f"<b>Expense</b>: ${amount:,.2f}\n{_desc}\n" "Please select a category:",
                parse_mode="HTML",
                reply_markup=get_category_keyboard(),
            )

            db.users_table.update_item(
                Key={"user_id": user_id, "bot_id": str(context.bot.id)},
                UpdateExpression="SET temp_data = :tmp_data",
                ExpressionAttributeValues={
                    ":tmp_data": {
                        "pend_amt": Decimal(str(amount)),
                        "pend_desc": description,
                        "pend_inc": is_income,
                    }
                },
            )
        except Exception as e:
            await update.message.reply_text(f"Error recording expense: {str(e)}")


async def _msg_custom_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Logic to validate and update categories")
    await update.message.reply_text("Reset conv status")


@rate_counter
async def msg_handler_by_conv_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    status = db.get_fields(update.effective_user.id, context.bot.id, "conversation_status") or 0
    msg_hand_map = {
        ST_REGULAR: _msg_regular,
        ST_WAIT_CATEGORY: _msg_custom_category,
    }
    await msg_hand_map[status](update, context)


# ############################################
# ######## CALLBACKS
# ############################################


async def _category_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    query = update.callback_query
    user_id = str(query.from_user.id)
    cat_name = query.data[4:]
    if cat_name == "cancel":
        await query.edit_message_text("Cancelled new record.")
        return
    try:
        state = db.get_fields(user_id, context.bot.id, "temp_data")  # Get temp data
        if not state:
            await query.edit_message_text("No pending expense or income to log.")
            return
        amount = state.get("pend_amt")
        description = state.get("pend_desc")
        is_income = state.get("pend_inc")
        await query.edit_message_text(f"✅ Logged: ${amount:,.2f} in {cat_name}")
        # Store
        db.insert_expense(
            user_id=user_id,
            amount=amount,
            category=str(cat_map[cat_name]),
            currency="USD",  # Default currency
            description=description,
            income=is_income,
        )
        # Remove temp data
        db.users_table.update_item(
            Key={"user_id": user_id, "bot_id": str(context.bot.id)},
            UpdateExpression="SET temp_data = :tmp_data",
            ExpressionAttributeValues={":tmp_data": {}},
        )
    except Exception as e:
        await query.edit_message_text(f"Error inserting record: {str(e)}")


async def _history_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    query = update.callback_query
    window = query.data[5:]
    if window == "cancel":
        await query.edit_message_text("Cancelled history request.")
        return
    user_id = str(query.from_user.id)
    tz = parse_timezone("UTC-6")
    today_dt = datetime.now(tz)
    try:
        if window == "Today":
            data = db.fetch_expenses_by_user_and_date(user_id, today_dt, today_dt)
        elif window == "This Week":
            start_date = today_dt - timedelta(days=today_dt.weekday())
            data = db.fetch_expenses_by_user_and_date(user_id, start_date, today_dt)
        elif window == "This Month":
            start_date = today_dt.replace(day=1)
            data = db.fetch_expenses_by_user_and_date(user_id, start_date, today_dt)
        elif window == "Previous Month":
            first_of_month = today_dt.replace(day=1)
            start_date = (first_of_month - timedelta(days=1)).replace(day=1)
            last_day_dt = first_of_month - timedelta(days=1)
            data = db.fetch_expenses_by_user_and_date(user_id, start_date, last_day_dt)
        elif window == "back":
            await update.callback_query.edit_message_text(
                "Select time window for history:", reply_markup=get_history_keyboard()
            )
            return
        else:
            await query.edit_message_text(f"Invalid time window: {window}")
            return

        if not data:
            await query.edit_message_text("No records found for the selected time window.")
            return

        entries = [
            f"{item['date']}: <code>${item['amount']:,.2f}</code> - {parse_cat_id(item['category'])}"
            + (f" ({item['description']})" if item["description"] else "")
            for item in data
        ]

        history_lines = []
        total_length = 0
        for entry in entries:
            entry_len = len(entry) + 1
            if total_length + entry_len > 4096 - 3:
                history_lines.insert(0, "...")
                break
            history_lines.insert(0, entry)
            total_length += entry_len

        history = "\n".join(history_lines)

        await query.edit_message_text(
            f"📅 <b>History for {window}</b>:\n\n{history}",
            parse_mode="HTML",
            reply_markup=get_history_keyboard(is_back_button=True),
        )
    except Exception as e:
        await query.edit_message_text(f"Error fetching history: {str(e)}")


async def _stats_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    query = update.callback_query
    stats_window = query.data[6:]
    if stats_window == "cancel":
        await query.edit_message_text("Cancelled stats request.")
        return
    user_id = str(query.from_user.id)
    tz = parse_timezone("UTC-6")
    today_dt = datetime.now(tz)
    try:
        if stats_window == "Today":
            data = db.fetch_expenses_by_user_and_date(user_id, today_dt, today_dt)
        elif stats_window == "This Week":
            start_date = today_dt - timedelta(days=today_dt.weekday())
            data = db.fetch_expenses_by_user_and_date(user_id, start_date, today_dt)
        elif stats_window == "This Month":
            start_date = today_dt.replace(day=1)
            data = db.fetch_expenses_by_user_and_date(user_id, start_date, today_dt)
        elif stats_window == "This Year":
            start_date = today_dt.replace(month=1, day=1)
            data = db.fetch_expenses_by_user_and_date(user_id, start_date, today_dt)
        elif stats_window == "All Time":
            start_date = today_dt.replace(year=1900)
            data = db.fetch_expenses_by_user_and_date(user_id, start_date, today_dt)
        elif stats_window == "back":
            await update.callback_query.edit_message_text(
                "Select time period:", reply_markup=get_stats_keyboard()
            )
            return
        else:
            await query.edit_message_text(f"Invalid time window: {stats_window}")
            return

        if not data:
            await query.edit_message_text("No records found for the selected time window.")
            return

        category_totals = defaultdict(Decimal)
        for item in data:
            cat_name = parse_cat_id(int(item["category"]))
            category_totals[cat_name] += Decimal(item["amount"])

        n_spend = sum([1 for i in data if int(i["category"]) != 99])
        n_inc = len(data) - n_spend

        # Format the grouped data
        spe_dict = {
            category: total
            for category, total in category_totals.items()
            if "Income" not in category
        }
        inc_dict = {i: category_totals.get(i, 0) for i in ["💰 Income"]}
        spending_total = sum(category_totals.values())
        income_total = inc_dict.get("💰 Income", 0)
        net = income_total - spending_total
        sign = "- " if net < 0 else ""
        await query.edit_message_text(
            (
                f"📊 <b>Stats for {stats_window}</b>:\n\n"
                f"<b>➖ Expenses</b>\n\n{format_agg_cats(spe_dict)}\n\n"
                f"<b>➕ Income\n\n{format_agg_cats(inc_dict)}</b>\n\n"
                f"<b>Total Expenses: <code>${spending_total:,.2f}</code></b> ({n_spend})\n"
                f"<b>Total Income: <code>${income_total:,.2f}</code></b>  ({n_inc})\n\n"
                f"<b>Total Net:  <code>{sign}${abs(net):,.2f}</code></b>"
            ),
            parse_mode="HTML",
            reply_markup=get_stats_keyboard(is_back_button=True),
        )

    except Exception as e:
        await query.edit_message_text(f"Error fetching history: {str(e)}")


async def _delete_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    query = update.callback_query
    user_id = str(query.from_user.id)
    if query.data == "delete_cancel":
        await query.edit_message_text("Cancelled record removal.")
        return
    try:
        item = db.table.get_item(Key={"user_id": str(user_id), "timestamp": query.data[7:]}).get(
            "Item"
        )

        txt = (
            f"{item['date']}: <code>${item['amount']:,.2f}</code> - {parse_cat_id(item['category'])}"
            + (f" ({item['description']})" if item["description"] else "")
        )

        await query.edit_message_text(f"🗑 <b>Deleted</b>:\n {txt}", parse_mode="HTML")
        db.remove_expense(user_id, query.data[7:])
    except Exception as e:
        await query.edit_message_text(f"Error removing record: {str(e)}")


async def _settings_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "settings_cancel":
        await query.edit_message_text("Cancelled settings operation.")
    else:
        period = query.data.split("_")[-1]
        await query.edit_message_text(f"Pending logic for handling {period} settings.")


async def _help_premium_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(
        PREMIUM_TEXT, reply_markup=get_subscription_keyboard(), parse_mode="HTML"
    )


async def _subs_plan_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    SUBSCRIPTION_PRICES = {
        "1m": 200,
        "3m": 500,
        "6m": 1000,
        "12m": 1500,
    }

    STARS_TO_USD = {
        200: 3.99,
        500: 9.99,
        1000: 19.99,
        1500: 29.99,
    }

    query = update.callback_query
    plan = query.data.split("_")[-1]

    if plan in SUBSCRIPTION_PRICES:
        await query.edit_message_text(PREMIUM_TEXT, parse_mode="HTML")
        price = SUBSCRIPTION_PRICES[plan]
        _months = int(plan.split("m")[0])
        _plural = "s" if _months > 1 else ""
        price_list = [LabeledPrice(f"{plan.capitalize()} Subscription", price)]

        await query.message.reply_invoice(
            title=f"Fundu Premium - {_months} month{_plural} plan",
            description=f"\n${STARS_TO_USD[price]} USD - Subscription for {_months} month{_plural} access to Fundu Premium\n",
            payload=f"invoice_subs_{plan}",
            currency="XTR",
            provider_token="",
            prices=price_list,
            is_flexible=False,
            photo_url="https://github.com/RodolfoRbl/expenses_tracker_bot/blob/2d748bdf7eb5ac7b8967b4abdc0b3f5875a3a3c6/images/premium.jpg?raw=true",
            photo_width=400,
            photo_height=250,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(f"Pay XTR {price}", pay=True)]]
            ),
        )
    elif plan == "cancel":
        await query.edit_message_text("Cancelled subscription request.")


@rate_counter
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prefs_map = {
        "cat_": _category_callback_handler,
        "stats_": _stats_callback_handler,
        "hist_": _history_callback_handler,
        "delete_": _delete_callback_handler,
        "settings_": _settings_callback_handler,
        "help_premium": _help_premium_handler,
        "subs_plan_": _subs_plan_callback_handler,
    }
    for prefix, handler in prefs_map.items():
        if update.callback_query.data.startswith(prefix):
            await handler(update, context)
            break
