from telegram import Update
from telegram.ext import CallbackContext
from .keyboards import (
    get_start_keyboard,
    get_category_keyboard,
    get_stats_keyboard,
    get_history_keyboard,
    get_settings_keyboard,
    get_remove_keyboard,
    get_help_keyboard,
    get_subscription_keyboard,
    CATEGORIES,
)
from .db import ExpenseDB
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict

cat_map = {k.split()[-1]: v for k, v in CATEGORIES.items()}
parse_cat_id = lambda id: {v: k for k, v in CATEGORIES.items()}[int(id)]

# ############################################
# ######## AUXILIARY
# ############################################


def _format_agg_cats(data_dict: dict) -> str:
    total = sum(data_dict.values())
    sorted_data = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
    formatted = [
        f"<code>${amount:,.2f} ({int(amount / total * 100) if total != 0 else 0}%)</code> - {category}"
        for category, amount in sorted_data
    ]
    return "\n".join(formatted)


async def _parse_msg_to_elements(update: Update, text: str) -> tuple:
    # Split the text into words
    words = text.split()
    is_last_digit = words[-1].lstrip("+-").replace(".", "", 1).isdigit()
    is_first_digit = words[0].lstrip("+-").replace(".", "", 1).isdigit()
    if len(words) == 1 and is_first_digit:
        amount = float(words[0])
        description = ""
        is_income = "+" in words[0]
    elif len(words) < 2:
        await update.message.reply_text("Please use the format: amount description")
        return [None] * 3
    elif is_last_digit and is_first_digit:
        await update.message.reply_text(
            "Invalid format. Digits should be at the start or end, not both."
        )
        return [None] * 3
    # Check if the first or last word is a valid amount
    elif is_first_digit:
        is_income = "+" in words[0]
        amount = float(words[0])
        description = " ".join(words[1:])
    elif is_last_digit:
        is_income = "+" in words[-1]
        amount = float(words[-1])
        description = " ".join(words[:-1])
    else:
        await update.message.reply_text("Please use the format: amount description")
        return [None] * 3
    return amount, description, is_income


# ############################################
# ######## COMMANDS
# ############################################


async def start_handler(update: Update, context: CallbackContext):
    await update.message.reply_text(
        """
Hey, I'm <b>Fundu</b>! 👋🏼

I'm here to help you track your expenses 💸

Send me your expenses like this:
👉🏼 2500 groceries
👉🏼 food 50

To record income, use a <b>+</b> sign:
💰 +1000 bonus

Here's what I can do for you:

/summary 📊   View your spending stats
/history 📋   See your full expense history
/delete ❌   Remove your last record
/help 🆘   Full list of available commands

Let’s get your finances under control 🚀
""",
        parse_mode="HTML",
        reply_markup=get_start_keyboard(),
    )


async def help_handler(update: Update, context: CallbackContext):
    help_text = """
⚙️ <b>Bot Commands</b>

<b>/summary</b> 📊 – Show spending statistics

<b>/delete</b> ❌ – Remove your last record

<b>/history</b> 📋 – Show all records

<b>/cancel</b> 🚫 – Cancel the current action

<b>/subscription</b> 💎 – View premium benefits

<b>/help</b> 🆘 – Show this help message

<b>/settings</b> ⚙️ – Update your profile<b>/settings</b> ⭐️

<b>/categories</b> 🗂 – Manage and add your own categories ⭐️

<b>/export</b> 📁 – Download your history (CSV) ⭐️

<b>/budget</b> 🎯 – Set a monthly budget ⭐️


⭐️ = <i>Premium features (available with a subscription)</i>
"""
    await update.message.reply_text(
        help_text,
        reply_markup=get_help_keyboard(),
        parse_mode="HTML",
    )


async def subscription_handler(update: Update, context: CallbackContext):
    premium_text = """
⚪️ <b>Subscription is inactive</b>

<b>What's included in Premium?</b>

👛 <b>Monthly Budget</b>
Set a budget limit and track how much remains.

💶 <b>Multi-currency Support</b>
Add any currency to a record. Example: <code>500 JPY beer</code>

📅 <b>Custom Dates</b>
Backdate expenses. Example: <code>50 groceries yesterday</code> or <code>50 groceries 2024-01-28</code>

✏️ <b>Record Editing</b>
Edit or delete <b><i>any</i></b> entry — not just the last one.

📅 <b>Custom History</b>
Specify a date range for your history. Example: <code>2024-01-15 2024-03-25</code>

🧾 <b>Export</b>
Download your data to <b>Excel/CSV</b> for backups or analysis.
"""
    if update.callback_query:
        await update.callback_query.answer()
        func = update.callback_query.edit_message_text
    else:
        func = update.message.reply_text

    await func(
        premium_text,
        reply_markup=get_subscription_keyboard(),
        parse_mode="HTML",
    )


async def remove_handler(update: Update, context: CallbackContext, db: ExpenseDB):
    user_id = str(update.effective_user.id)
    try:
        # Fetch the last n records from the database
        n = 5  # Number of records to fetch
        records = db.fetch_latest_expenses(
            user_id,
            10,
        )
        if not records:
            await update.message.reply_text("No records found to remove.")
            return

        history = "\n".join(
            f"<b>{i + 1}</b>. {item['date']}: <code>${item['amount']:,.2f}</code> - {parse_cat_id(item['category'])}"
            + (f" ({item['description']})" if item["description"] else "")
            for i, item in enumerate(records)
        )

        await update.message.reply_text(
            f"📋 <b>Last {n} Records:</b>\n\n{history}\n\nSelect a record to remove:",
            parse_mode="HTML",
            reply_markup=get_remove_keyboard(records),
        )
    except Exception as e:
        await update.message.reply_text(f"Error fetching records: {str(e)}")


async def stats_handler(update: Update, context: CallbackContext):
    await update.message.reply_text("Select time period:", reply_markup=get_stats_keyboard())


async def history_handler(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Select time window for history:", reply_markup=get_history_keyboard()
    )


async def settings_handler(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "⚠️ <i>Settings available only for ⭐️<b>PREMIUM</b>⭐️ users</i> ⚠️",
        parse_mode="HTML",
        reply_markup=get_settings_keyboard(),
    )


async def categories_handler(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "⚠️ Categories command available only for ⭐️<b>PREMIUM</b>⭐️ users</i> ⚠️", parse_mode="HTML"
    )


async def export_handler(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "⚠️ Export command available only for ⭐️<b>PREMIUM</b>⭐️ users</i> ⚠️", parse_mode="HTML"
    )


async def budget_handler(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "⚠️ Budget command available only for ⭐️<b>PREMIUM</b>⭐️ users</i> ⚠️", parse_mode="HTML"
    )


async def unknown_command_handler(update, context):
    await update.message.reply_text(
        "Sorry, I didn't understand that command.\nTry /help for a list of commands."
    )


# ############################################
# ######## MESSAGES
# ############################################


async def message_handler(update: Update, context: CallbackContext, db: ExpenseDB):
    text = update.message.text.strip()
    if len(text) >= 100:
        await update.message.reply_text("Message too long. Please keep it under 100 characters.")
        return
    user_id = str(update.effective_user.id)

    amount, description, is_income = await _parse_msg_to_elements(update, text)
    _desc = f"<b>Description</b>: {description}" if description else ""
    if is_income is None:
        return
    elif is_income:
        try:
            db.insert_expense(
                user_id=user_id,
                amount=amount,
                category="99",  # Income category
                currency="USD",
                description=description,
                income=is_income,
            )
            await update.message.reply_text(f"✅ Logged: ${amount:,.2f} in Income")
        except Exception as e:
            await update.message.reply_text(f"Error inserting income: {str(e)}")
            return
    else:
        try:
            await update.message.reply_text(
                f"<b>Expense</b>: ${amount:,.2f}\n{_desc}\n" "Please select a category:",
                parse_mode="HTML",
                reply_markup=get_category_keyboard(),
            )

            db.state_table.put_item(
                Item={
                    "user_id": user_id,
                    "pend_amt": Decimal(str(amount)),
                    "pend_desc": description,
                    "pend_inc": is_income,
                }
            )
        except Exception as e:
            await update.message.reply_text(f"Error recording expense: {str(e)}")


# ############################################
# ######## CALLBACKS
# ############################################


async def category_callback_handler(update: Update, context: CallbackContext, db: ExpenseDB):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    cat_name = query.data[4:]
    if cat_name == "cancel":
        await query.edit_message_text("Cancelled new record.")
        return
    try:
        # Get the pending state from the database
        state = db.get_state(user_id)
        if not state:
            await query.edit_message_text("No pending expense or income to log.")
            return
        amount = state.get("pend_amt")
        description = state.get("pend_desc")
        is_income = state.get("pend_inc")
    except Exception as e:
        await query.edit_message_text(f"Error fetching state: {str(e)}")
        return
    try:
        # Log the expense or income
        db.insert_expense(
            user_id=user_id,
            amount=amount,
            category=str(cat_map[cat_name]),
            currency="USD",  # Default currency
            description=description,
            income=is_income,
        )
    except Exception as e:
        await query.edit_message_text(f"Error inserting expense: {str(e)}")
        return
    await query.edit_message_text(f"✅ Logged: ${amount:,.2f} in {cat_name}")
    try:
        # Remove the pending entry from the state table
        db.state_table.delete_item(Key={"user_id": user_id})
    except Exception as e:
        await query.edit_message_text(f"Error deleting pending state: {str(e)}")
        return


async def history_callback_handler(update: Update, window: str, db: ExpenseDB):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    window = query.data[5:]
    tz = db._parse_timezone("UTC-6")
    today_dt = datetime.now(tz)
    if window == "cancel":
        await query.edit_message_text("Cancelled history request.")
        return
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
        else:
            await query.edit_message_text(f"Invalid time window: {window}")
            return

        if not data:
            await query.edit_message_text("No records found for the selected time window.")
            return

        history = "\n".join(
            f"{item['date']}: <code>${item['amount']:,.2f}</code> - {parse_cat_id(item['category'])}"
            + (f" ({item['description']})" if item["description"] else "")
            for item in data
        )
        await query.edit_message_text(
            f"📅 <b>History for {window}</b>:\n\n{history}",
            parse_mode="HTML",
        )
    except Exception as e:
        await query.edit_message_text(f"Error fetching history: {str(e)}")


async def stats_callback_handler(update: Update, window: str, db: ExpenseDB):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    stats_window = query.data[6:]
    tz = db._parse_timezone("UTC-6")
    today_dt = datetime.now(tz)
    if stats_window == "cancel":
        await query.edit_message_text("Cancelled stats request.")
        return
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
        else:
            await query.edit_message_text(f"Invalid time window: {window}")
            return

        if not data:
            await query.edit_message_text("No records found for the selected time window.")
            return

        category_totals = defaultdict(Decimal)
        for item in data:
            cat_name = parse_cat_id(int(item["category"]))
            category_totals[cat_name] += Decimal(item["amount"])

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
                f"<b>➖ Expenses</b>\n\n{_format_agg_cats(spe_dict)}\n\n"
                f"<b>➕ Income\n\n{_format_agg_cats(inc_dict)}</b>\n\n"
                f"<b>Total Expenses: <code>${spending_total:,.2f}</code></b>\n"
                f"<b>Total Income: <code>${income_total:,.2f}</code></b>\n\n"
                f"<b>Total Net:  <code>{sign}${abs(net):,.2f}</code></b>"
            ),
            parse_mode="HTML",
        )

    except Exception as e:
        await query.edit_message_text(f"Error fetching history: {str(e)}")


async def remove_callback_handler(update: Update, context: CallbackContext, db: ExpenseDB):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    if query.data == "remove_cancel":
        await query.edit_message_text("Cancelled record removal.")
        return
    try:
        db.remove_expense(user_id, query.data[7:])
        await query.edit_message_text("✅ Record removed successfully.")
    except Exception as e:
        await query.edit_message_text(f"Error removing record: {str(e)}")


async def subscription_callback_handler(update: Update, context: CallbackContext, db: ExpenseDB):
    query = update.callback_query
    await query.answer()
    if query.data == "subscribe_cancel":
        await query.edit_message_text("Cancelled subscription request.")
    else:
        period = query.data.split("_")[-1]
        await query.edit_message_text(f"Pending logic for handling {period} subscription actions.")


async def help_callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("PRUEBA")


async def callback_handler(update: Update, context: CallbackContext, db: ExpenseDB):
    query = update.callback_query
    if query.data.startswith("cat_"):
        await category_callback_handler(update, context, db)

    elif query.data.startswith("stats_"):
        period = query.data[6:]
        await stats_callback_handler(update, period, db)

    elif query.data.startswith("hist_"):
        await history_callback_handler(update, context, db)

    elif query.data.startswith("remove_"):
        await remove_callback_handler(update, context, db)

    elif query.data.startswith("help_premium"):
        await subscription_handler(update, context)

    elif query.data.startswith("subscribe_"):
        await subscription_callback_handler(update, context, db)
