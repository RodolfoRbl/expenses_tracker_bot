from telegram import Update
from telegram.ext import CallbackContext
from .keyboards import (
    get_start_keyboard,
    get_category_keyboard,
    get_stats_keyboard,
    get_history_keyboard,
    get_settings_keyboard,
)
from .db import ExpenseDB
from decimal import Decimal


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

/stats 📊   View your spending stats
/list 📋   See your full expense history
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

<b>/stats</b> 📊 – Show spending statistics

<b>/delete</b> ❌ – Remove your last record

<b>/list</b> 📋 – Show all records

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

🫂 <b>Shared Recording</b>
Record expenses or income for your partner using <code>@username</code>

🧾 <b>Export</b>
Download your data to <b>Excel/CSV</b> for backups or analysis.
"""
    await update.message.reply_text(premium_text, parse_mode="HTML")


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


async def message_handler(update: Update, context: CallbackContext, db: ExpenseDB):
    text = update.message.text.strip()
    if len(text) >= 100:
        await update.message.reply_text("Message too long. Please keep it under 100 characters.")
        return
    user_id = str(update.effective_user.id)

    amount, description, is_income = await _parse_msg_to_elements(update, text)

    if is_income is None:
        return
    try:
        _desc = f"<b>Description</b>: {description}" if description else ""
        await update.message.reply_text(
            f"<b>{'Income' if is_income else 'Expense'}</b>: ${amount:,.2f}\n{_desc}\n"
            "Please select a category:",
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


async def callback_handler(update: Update, context: CallbackContext, db: ExpenseDB):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("cat_"):
        category = query.data[4:]
        user_id = str(query.from_user.id)
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
                category=category,
                currency="USD",  # Default currency
                description=description,
                income=is_income,
            )
        except Exception as e:
            await query.edit_message_text(f"Error inserting expense: {str(e)}")
            return
        await query.edit_message_text(f"✅ Logged: ${amount:,.2f} in {category}")
        try:
            # Remove the pending entry from the state table
            db.state_table.delete_item(Key={"user_id": user_id})
        except Exception as e:
            await query.edit_message_text(f"Error deleting pending state: {str(e)}")
            return

    elif query.data.startswith("stats_"):
        period = query.data[6:]
        await query.edit_message_text(f"Stats for {period} (coming soon)")


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
