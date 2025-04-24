from telegram import Update
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
    CATEGORIES,
)
from utils.general import parse_timezone, get_str_timestamp
from handlers.decorators import rate_counter
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict
import csv
import io

cat_map = {k.split()[-1]: v for k, v in CATEGORIES.items()}
parse_cat_id = lambda id: {v: k for k, v in CATEGORIES.items()}[int(id)]

# ############################################
# ######## AUXILIARY
# ############################################


def get_db(context: ContextTypes.DEFAULT_TYPE):
    return context.bot_data.get("db")


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


@rate_counter
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
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

/stats 📊   View your spending stats
/history 📋   See your full expense history
/delete ❌   Delete a recent record
/help 🆘   Full list of available commands

Let’s get your finances under control 🚀
""",
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
                "temp": {},
            }
        )


@rate_counter
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """

Send me your expenses like this:
👉🏼 2500 groceries
👉🏼 food 50

To record income, use a + sign:
👉🏼 +1000 bonus

⚙️ <b>Bot Commands</b>

<b>/stats</b> 📊 – Show spending statistics

<b>/delete</b> ❌ – Delete a recent record

<b>/history</b> 📋 – Show all records

<b>/last</b> ⌛️ – Show last records
<i>(Example. /last 8, /last 15, /last)</i>

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


@rate_counter
async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        premium_text,
        reply_markup=get_subscription_keyboard(),
        parse_mode="HTML",
    )


@rate_counter
async def delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    user_id = str(update.effective_user.id)
    try:
        # Fetch last n
        n = 10
        records = db.fetch_latest_expenses(user_id, n)
        if not records:
            await update.message.reply_text("No records found to delete.")
            return

        emoji_map = {
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣",
            10: "🔟",
        }

        history = "\n".join(
            f"<b>{emoji_map[i + 1]}</b>. {item['date']}: <code>${item['amount']:,.2f}</code> - {parse_cat_id(item['category'])}"
            + (f" ({item['description']})" if item["description"] else "")
            for i, item in enumerate(records)
        )

        await update.message.reply_text(
            f"📋 <b>Last {n} Records:</b>\n\n{history}\n\nSelect a record to delete:",
            parse_mode="HTML",
            reply_markup=get_delete_keyboard(records),
        )
    except Exception as e:
        await update.message.reply_text(f"Error fetching records: {str(e)}")


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


@rate_counter
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    text = update.message.text.strip()
    if len(text) >= 100:
        await update.message.reply_text("Message too long. Please keep it under 100 characters.")
        return
    user_id = str(update.effective_user.id)

    amount, description, is_income = await _parse_msg_to_elements(update, text)
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


async def _category_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    query = update.callback_query
    user_id = str(query.from_user.id)
    cat_name = query.data[4:]
    if cat_name == "cancel":
        await query.edit_message_text("Cancelled new record.")
        return
    try:
        # Get temp data
        state = db.get_state(user_id)
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
        db.state_table.delete_item(Key={"user_id": user_id})
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
                f"<b>➖ Expenses</b>\n\n{_format_agg_cats(spe_dict)}\n\n"
                f"<b>➕ Income\n\n{_format_agg_cats(inc_dict)}</b>\n\n"
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
        await query.edit_message_text("✅ Record deleted successfully.")
        db.remove_expense(user_id, query.data[7:])
    except Exception as e:
        await query.edit_message_text(f"Error removing record: {str(e)}")


async def _subscription_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "subscribe_cancel":
        await query.edit_message_text("Cancelled subscription request.")
    else:
        period = query.data.split("_")[-1]
        await query.edit_message_text(f"Pending logic for handling {period} subscription actions.")


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
        premium_text, reply_markup=get_subscription_keyboard(), parse_mode="HTML"
    )


@rate_counter
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prefs_map = {
        "cat_": _category_callback_handler,
        "stats_": _stats_callback_handler,
        "hist_": _history_callback_handler,
        "delete_": _delete_callback_handler,
        "subscribe_": _subscription_callback_handler,
        "settings_": _settings_callback_handler,
        "help_premium": _help_premium_handler,
    }
    for prefix, handler in prefs_map.items():
        if update.callback_query.data.startswith(prefix):
            await handler(update, context)
            break
