from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
from .keyboards import (
    MAIN_MENU,
    get_category_keyboard,
    get_stats_keyboard,
    get_history_keyboard,
    get_settings_keyboard,
)

# State storage
user_pending_expenses = {}


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
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True),
    )


async def help_handler(update: Update, context: CallbackContext):
    help_text = """
⚙️ Commands Overview

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


⭐️ = Premium features (available with a subscription)
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


async def message_handler(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    words = text.split()
    amount = None
    description = None

    # Check if the first word is a number
    if words[0].replace(".", "", 1).isdigit():
        amount = float(words[0])
        description = " ".join(words[1:])
    # Check if the last word is a number
    elif words[-1].replace(".", "", 1).isdigit():
        amount = float(words[-1])
        description = " ".join(words[:-1])

    if amount is not None:
        user_pending_expenses[update.message.from_user.id] = amount
        desc_text = f"\n<b>Description</b>: {description}" if description else ""
        await update.message.reply_text(
            f"<b>Amount:</b> ${amount:,.2f}{desc_text}",
            parse_mode="HTML",
            reply_markup=get_category_keyboard(),
        )
    else:
        await update.message.reply_text("Please include an amount (e.g. 12.50)")


async def callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("cat_"):
        category = query.data[4:]
        user_id = query.from_user.id
        if user_id in user_pending_expenses:
            amount = user_pending_expenses.pop(user_id)
            await query.edit_message_text(f"✅ Logged: ${amount} in {category}")

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
        "⚠️ Settings available only for ⭐️<b>PREMIUM</b>⭐️ users ⚠️:",
        parse_mode="HTML",
        reply_markup=get_settings_keyboard(),
    )
