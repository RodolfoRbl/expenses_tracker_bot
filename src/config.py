# Default categories
CATEGORIES = {
    "🍔 Food": 0,
    "🚌 Transport": 1,
    "🏠 Rent": 2,
    "💡 Utilities": 3,
    "🎮 Entertainment": 4,
    "🛒 Groceries": 5,
    "💊 Health": 6,
    "💼 Business": 7,
    "🎁 Gifts": 8,
    "✈️ Travel": 9,
    "📚 Education": 10,
    "❓ Other": 11,
    "💰 Income": 99,
}

HISTORY_WINDOWS = ["Today", "This Week", "This Month", "Previous Month"]

STATS_WINDOWS = ["Today", "This Week", "This Month", "This Year", "All Time"]

MAIN_MENU = [["💹 Stats", "📆 History"], ["⚙️ Settings", "⭐ Subscription"], ["❓ Help"]]

SETTINGS_OPTIONS = ["💵 Currency", "🌐 Language", "⏰ Timezone", "📂 Categories"]


CUSTOM_CATS_LIM = 15

# Conversation status
ST_REGULAR = 0
ST_WAIT_CATEGORY = 1


HELP_TEXT = """

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


PREMIUM_TEXT = """
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

START_TEXT = """
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
"""
