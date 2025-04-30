# Default categories
DEFAULT_CATEGORIES = {
    "0": {"name": "🍔 Food", "active": 1},
    "1": {"name": "🚗 Transport & Cars", "active": 1},
    "2": {"name": "🏠 Rent", "active": 1},
    "3": {"name": "💡 Utilities", "active": 1},
    "4": {"name": "🎮 Entertainment", "active": 1},
    "5": {"name": "🛒 Groceries", "active": 1},
    "6": {"name": "💊 Health", "active": 1},
    "7": {"name": "💼 Business", "active": 1},
    "8": {"name": "🎁 Gifts", "active": 1},
    "9": {"name": "✈️ Travel", "active": 1},
    "10": {"name": "📚 Education & Learning", "active": 1},
    "11": {"name": "🔧 Home Maintenance", "active": 1},
    "12": {"name": "❓ Other", "active": 1},
    "99": {"name": "💰 Income", "active": 1},
}


HISTORY_WINDOWS = ["Today", "This Week", "This Month", "Previous Month"]

STATS_WINDOWS = ["Today", "This Week", "This Month", "This Year", "All Time"]

MAIN_MENU = [
    ["💹 Stats", "📆 History"],
    ["⚙️ Settings", "⭐ Premium"],
    ["🧠 Artificial Intelligence", "❓ Help"],
]

SETTINGS_OPTIONS = [
    "💵 Currency",
    "🌐 Language",
    "⏰ Timezone",
    "📂 Categories",
    "🔔 Notifications",
    "🧠 Artificial Intelligence",
]


MAX_CATEGORIES = 15
MAX_CAT_LENGTH = 30

# Conversation status
ST_REGULAR = 0
ST_WAIT_CATEGORY = 1


PREMIUM_PRICES = {
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


TZ_BY_OFFSET = {
    "UTC-8": "LA/Vancouver/Tijuana",
    "UTC-7": "Denver/Calgary",
    "UTC-6": "Chicago/Mexico City",
    "UTC-5": "New York/Toronto/Lima",
    "UTC-4": "Santiago/Caracas",
    "UTC-3": "São Paulo/Buenos Aires/Montevideo",
    "UTC-2": "South Georgia",
    "UTC-1": "Azores/Cape Verde",
    "UTC+0": "London/Lisbon/Dakar",
    "UTC+1": "Berlin/Madrid/Paris",
    "UTC+2": "Athens/Johannesburg/Cairo",
    "UTC+3": "Moscow/Istanbul/Nairobi",
    "UTC+4": "Dubai/Baku/Yerevan",
    "UTC+5": "Karachi/Tashkent/Yekaterinburg",
    "UTC+6": "Dhaka/Almaty/Bishkek",
    "UTC+7": "Bangkok/Jakarta/Ho Chi Minh City",
    "UTC+8": "Beijing/Singapore/Shanghai",
    "UTC+9": "Tokyo/Seoul/Pyongyang",
    "UTC+10": "Sydney/Brisbane",
}


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

<b>/help</b> 🆘 – Show this help message

<b>/artificial_intelligence</b> 🧠 – Change AI status

<b>/premium</b> 💎 – View premium benefits

<b>/settings</b> ⚙️ – Update your profile<b>/settings</b> ⭐️

<b>/categories</b> 🗂 – Manage and add your own categories ⭐️

<b>/export</b> 📁 – Download your history (CSV) ⭐️

<b>/budget</b> 🎯 – Set a monthly budget ⭐️


⭐️ = <i>Premium features (available with a subscription)</i>
"""


PREMIUM_TEXT = """
⚪️ <b>Premium plan is inactive</b>

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

CMD_FOR_PREMIUM_TEXT = "<i>⚠️ Command available only for ⭐️<b>PREMIUM</b>⭐️ users</i> ⚠️\nSend /premium to get Fundu Premium"
CMD_PREMIUM_WELCOME_TEXT = "<b>Welcome!</b> You can now use all <i>⭐️<b>PREMIUM</b>⭐️</i> features.\nSend /help to see what you can do."


LLM_TEMPLATE = """
You are an assistant that categorizes expenses.

Given a description of an expense, you must select the most fitting category from the following list:

{{categories}}

Rules:
- You must only answer with the name of one category from the list.
- No extra text, no explanations, no new categories.
- The category must include its emoji as shown.
- Categories are limited to 20 characters maximum, including the emoji.
- If no description is provided, respond with the "other" category.

Example:

Description: "Lunch with friends at a restaurant"
Answer: "🍔 Food"

Description: "Bought medicine for a headache"
Answer: "💊 Health"

Description: ""
Answer: "❓ Other"

Now categorize this:

Description: "{{description}}"
Answer:
"""
