from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes

from utils.general import get_db, format_agg_cats
from utils.dates import parse_timezone
from utils.keyboards import get_history_keyboard, get_premium_keyboard, get_stats_keyboard
from handlers._decorators import rate_counter
from config import CATEGORIES, PREMIUM_TEXT, PREMIUM_PRICES, STARS_TO_USD


cat_map = {k.split()[-1]: v for k, v in CATEGORIES.items()}
parse_cat_id = lambda id: {v: k for k, v in CATEGORIES.items()}[int(id)]


@rate_counter
async def help_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(
        PREMIUM_TEXT, reply_markup=get_premium_keyboard(), parse_mode="HTML"
    )


# ##############################################################
# Settings
# ##############################################################


@rate_counter
async def settings_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Pending logic for handling currency settings.")


@rate_counter
async def settings_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Pending logic for handling language settings.")


@rate_counter
async def settings_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Pending logic for handling timezone settings.")


@rate_counter
async def settings_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Pending logic for handling categories settings.")


@rate_counter
async def settings_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Pending logic for handling notifications settings.")


@rate_counter
async def settings_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Cancelled settings request.")


# ##############################################################
# History
# ##############################################################


@rate_counter
async def history_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Cancelled history request.")


@rate_counter
async def history_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "Select time window for history:", reply_markup=get_history_keyboard()
    )


@rate_counter
async def history_windows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    query = update.callback_query
    window = query.data.split(":")[-1]
    user_id = str(query.from_user.id)
    tz = parse_timezone("UTC-6")
    today_dt = datetime.now(tz)

    start_dt = {
        "Today": today_dt,
        "This Week": today_dt - timedelta(days=today_dt.weekday()),
        "This Month": today_dt.replace(day=1),
        "Previous Month": (today_dt.replace(day=1) - timedelta(days=1)).replace(day=1),
    }
    try:
        if window in ["Today", "This Week", "This Month"]:
            data = db.fetch_expenses_by_user_and_date(user_id, start_dt[window], today_dt)
        elif window == "Previous Month":
            last_day_dt = today_dt.replace(day=1) - timedelta(days=1)
            data = db.fetch_expenses_by_user_and_date(user_id, start_dt[window], last_day_dt)
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


# ##############################################################
# Stats
# ##############################################################


@rate_counter
async def stats_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Cancelled stats request.")


@rate_counter
async def stats_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "Select time period:", reply_markup=get_stats_keyboard()
    )


@rate_counter
async def stats_windows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    query = update.callback_query
    stats_window = query.data.split(":")[-1]
    user_id = str(query.from_user.id)
    tz = parse_timezone("UTC-6")
    today_dt = datetime.now(tz)
    try:
        time_windows = {
            "Today": (today_dt, today_dt),
            "This Week": (today_dt - timedelta(days=today_dt.weekday()), today_dt),
            "This Month": (today_dt.replace(day=1), today_dt),
            "This Year": (today_dt.replace(month=1, day=1), today_dt),
            "All Time": (today_dt.replace(year=1900), today_dt),
        }

        if stats_window in time_windows:
            start_date, end_date = time_windows[stats_window]
            data = db.fetch_expenses_by_user_and_date(user_id, start_date, end_date)
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


# ##############################################################
# Expenses
# ##############################################################


@rate_counter
async def cancel_new_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Cancelled new record.")


@rate_counter
async def expense_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    query = update.callback_query
    user_id = str(query.from_user.id)
    cat_name = query.data.split(":")[-1]
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


@rate_counter
async def cancel_expense_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Cancelled record removal.")


@rate_counter
async def confirm_delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    query = update.callback_query
    user_id = str(query.from_user.id)
    expense_id = query.data.split(":")[-1]
    try:
        item = db.table.get_item(Key={"user_id": str(user_id), "timestamp": expense_id}).get("Item")
        txt = (
            f"{item['date']}: <code>${item['amount']:,.2f}</code> - {parse_cat_id(item['category'])}"
            + (f" ({item['description']})" if item["description"] else "")
        )

        await query.edit_message_text(f"🗑 <b>Deleted</b>:\n {txt}", parse_mode="HTML")
        db.remove_expense(user_id, expense_id)
    except Exception as e:
        await query.edit_message_text(f"Error removing record: {str(e)}")


# ##############################################################
# Premium plans
# ##############################################################


@rate_counter
async def cancel_select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Cancelled premium request.")


@rate_counter
async def confirm_premium_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    plan = query.data.split(":")[-1]

    if plan in PREMIUM_PRICES:
        await query.edit_message_text(PREMIUM_TEXT, parse_mode="HTML")
        price = PREMIUM_PRICES[plan]
        _months = int(plan.split("m")[0])
        _plural = "s" if _months > 1 else ""
        price_list = [LabeledPrice(f"{plan.capitalize()} Premium", price)]

        await query.message.reply_invoice(
            title=f"Fundu Premium - {_months} month{_plural} plan",
            description=f"\n${STARS_TO_USD[price]} USD - Fundu Premium for {_months} month{_plural}\n",
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
    else:
        await query.edit_message_text("Plan not identified.")


@rate_counter
async def unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(f"Unknown callback data received: {query.data}")
