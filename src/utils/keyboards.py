from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

# Categories mapping for msgs and database
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
}

MAIN_MENU = [["💹 Stats", "📆 History"], ["⚙️ Settings", "⭐ Subscription"], ["❓ Help"]]


def build_menu(buttons, n_cols=2):
    return InlineKeyboardMarkup([buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)])


def get_category_keyboard():
    buttons = [
        InlineKeyboardButton(cat, callback_data=f"cat_{cat.split()[-1]}") for cat in CATEGORIES
    ]
    return build_menu(buttons, n_cols=3)


def get_stats_keyboard():
    periods = [
        "Current Month",
        "Last Month",
        "Last 30 Days",
        "Last 12 Months",
        "All Time",
        "Cancel",
    ]
    buttons = [InlineKeyboardButton(p, callback_data=f"stats_{p}") for p in periods]
    return build_menu(buttons, n_cols=1)


def get_history_keyboard():
    periods = ["Today", "This Week", "This Month", "Last Month", "Custom Range", "Cancel"]
    buttons = [InlineKeyboardButton(p, callback_data=f"history_{p}") for p in periods]
    return build_menu(buttons, n_cols=1)


def get_settings_keyboard():
    options = ["💵 Currency", "🌐 Language", "⏰ Timezone", "📂 Categories"]
    buttons = [InlineKeyboardButton(opt, callback_data=f"settings_{opt}") for opt in options]
    return build_menu(buttons, n_cols=2)


def get_start_keyboard():
    return ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
