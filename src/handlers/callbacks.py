from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes

from utils.general import get_db, format_agg_cats, get_active_categories
from utils.dates import parse_timezone
from utils.keyboards import (
    get_history_keyboard,
    get_premium_keyboard,
    get_stats_keyboard,
    get_category_mgmt_menu,
    get_delete_category_keyboard,
    get_ai_settings_keyboard,
)
from handlers._decorators import rate_counter
import re
from config import (
    DEFAULT_CATEGORIES,
    PREMIUM_TEXT,
    PREMIUM_PRICES,
    STARS_TO_USD,
    MAX_CATEGORIES,
    ST_WAIT_CATEGORY,
)


# ##############################################################
# Shared (don't count for rate limiting)
# ##############################################################


async def _show_categories_to_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    func = (
        update.callback_query.edit_message_text
        if update.callback_query
        else update.message.reply_text
    )
    db = get_db(context)
    try:
        act_cats = {
            k: v
            for k, v in get_active_categories(db, update.effective_user.id, context.bot.id).items()
            if not re.match(r"(?i).*(income|other)$", v["name"])
        }
        can_add = len(act_cats) < MAX_CATEGORIES
        can_delete = len(act_cats) > 0
        default_manageable = {
            k: v
            for k, v in DEFAULT_CATEGORIES.items()
            if not re.match(r"(?i).*(income|other)$", v["name"])
        }
        ix_same_default = act_cats.keys() == default_manageable.keys()
        if not can_delete:
            message = "You have no categories to manage."
        else:
            message = "Here are the categories you can manage:\n\n" + "\n".join(
                cat["name"] for cat in act_cats.values()
            )

        await func(
            message,
            parse_mode="HTML",
            reply_markup=get_category_mgmt_menu(
                with_add=can_add, with_delete=can_delete, with_reset=not ix_same_default
            ),
        )
    except Exception as e:
        await func(f"Error fetching categories: {str(e)}")


async def _ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    func = (
        update.callback_query.edit_message_text
        if update.callback_query
        else update.message.reply_text
    )
    db = get_db(context)
    is_ai = db.get_fields(update.effective_user.id, context.bot.id, "artificial_intelligence")
    if is_ai:
        msg = "🟢 AI is currently enabled for your expenses"
    else:
        msg = "🔴 AI is not enabled"
    await func(msg, reply_markup=get_ai_settings_keyboard(is_ai), parse_mode="HTML")


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
    await _show_categories_to_manage(update, context)


@rate_counter
async def settings_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ai_handler(update, context)


@rate_counter
async def settings_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Pending logic for handling notifications settings.")


@rate_counter
async def settings_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Cancelled settings request.")


# ##############################################################
# AI activate
# ##############################################################


@rate_counter
async def ai_change_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action = query.data.split(":")[-1]
    db = get_db(context)
    new_active = False if action == "disable" else True
    st_txt = "enabled" if new_active else "disabled"
    await query.edit_message_text(
        f"✅ AI has been <b>{st_txt}</b> for your expenses.", parse_mode="HTML"
    )
    db.update_field(update.effective_user.id, context.bot.id, "artificial_intelligence", new_active)


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

        cats = db.get_fields(user_id, context.bot.id, "categories")

        entries = [
            f"{item['date']}: <code>${item['amount']:,.2f}</code> - {cats[item['category']]['name']}"
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
        cats = db.get_fields(user_id, context.bot.id, "categories")

        for item in data:
            cat_name = cats[item["category"]]["name"]
            category_totals[cat_name] += Decimal(item["amount"])

        n_spend = sum([1 for i in data if i["category"] != "99"])
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
async def expense_confirm_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    query = update.callback_query
    user_id = str(query.from_user.id)
    cat_id = query.data.split(":")[-1]
    try:
        _data = db.get_fields(user_id, context.bot.id, ["temp_data", "categories"])  # Get temp data
        state = _data["temp_data"]
        cats = _data["categories"]
        if not state:
            await query.edit_message_text("No pending expense or income to log.")
            return
        amount = state.get("pend_amt")
        description = state.get("pend_desc")
        is_income = state.get("pend_inc")
        cat_text = cats[cat_id]["name"]
        await query.edit_message_text(
            f"✅ Logged: <b>${amount:,.2f}</b> in <b>{cat_text}</b>", parse_mode="HTML"
        )

        # Store
        db.insert_expense(
            user_id=user_id,
            amount=amount,
            category=str(cat_id),
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
        cat_id = item["category"]
        cat_name = db.get_fields(user_id, context.bot.id, "categories")[cat_id]["name"]
        txt = f"{item['date']}: <code>${item['amount']:,.2f}</code> - {cat_name}" + (
            f" ({item['description']})" if item["description"] else ""
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


# ##############################################################
# Categories
# ##############################################################


@rate_counter
async def cancel_mgmt_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("Cancelled categories operation.")


@rate_counter
async def categories_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _show_categories_to_manage(update, context)


@rate_counter
async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = get_db(context)
    await query.edit_message_text(
        "Please send the name of the new category. It should be unique and not exceed 20 characters."
    )
    db.update_field(
        update.effective_user.id, context.bot.id, "conversation_status", ST_WAIT_CATEGORY
    )


@rate_counter
async def reset_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    user_id = str(update.effective_user.id)
    bot_id = str(context.bot.id)
    try:
        categories = db.get_fields(user_id, bot_id, "categories")
        for cat_id, _ in categories.items():
            if cat_id in DEFAULT_CATEGORIES:
                categories[cat_id]["active"] = 1
            else:
                categories[cat_id]["active"] = 0
        await update.callback_query.edit_message_text("Categories have been reset to default.")
        db.update_field(user_id, bot_id, "categories", categories)
    except Exception as e:
        await update.callback_query.edit_message_text(f"Error resetting categories: {str(e)}")


@rate_counter
async def delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = get_db(context)
    try:
        cats = {
            k: v
            for k, v in get_active_categories(db, update.effective_user.id, context.bot.id).items()
            if not re.match(r"(?i).*(income|other)$", v["name"])
        }
        await query.edit_message_text(
            "Select a category to delete:", reply_markup=get_delete_category_keyboard(cats)
        )
    except Exception as e:
        await query.edit_message_text(f"Error fetching categories: {str(e)}")


@rate_counter
async def confirm_delete_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = get_db(context)
    deleted_id = query.data.split(":")[-1]
    cats = db.get_fields(update.effective_user.id, context.bot.id, "categories")
    await query.edit_message_text(f"🗑 Category {cats[deleted_id]['name']} was deleted.")
    cats[deleted_id]["active"] = 0
    db.update_field(update.effective_user.id, context.bot.id, "categories", cats)


@rate_counter
async def unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(f"Unknown callback data received: {query.data}")
