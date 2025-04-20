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
    "💰 Income": 99,
}

HISTORY_WINDOWS = ["Today", "This Week", "This Month", "Previous Month"]
STATS_WINDOWS = ["Today", "This Week", "This Month", "This Year", "All Time"]

MAIN_MENU = [["💹 Stats", "📆 History"], ["⚙️ Settings", "⭐ Subscription"], ["❓ Help"]]


def build_menu(buttons, n_cols=2):
    return InlineKeyboardMarkup([buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)])


def get_remove_keyboard(items):
    buttons = [
        InlineKeyboardButton(f"{i+1}", callback_data=f"remove_{item['timestamp']}")
        for i, item in enumerate(items)
    ]
    buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="remove_cancel"))
    return build_menu(buttons, n_cols=5)


def get_category_keyboard():
    buttons = [
        InlineKeyboardButton(cat, callback_data=f"cat_{cat.split()[-1]}")
        for cat in CATEGORIES
        if "Income" not in cat
    ]
    buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="cat_cancel"))
    return build_menu(buttons, n_cols=3)


def get_stats_keyboard():
    buttons = [InlineKeyboardButton(p, callback_data=f"stats_{p}") for p in STATS_WINDOWS]
    buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="stats_cancel"))
    return build_menu(buttons, n_cols=1)


def get_history_keyboard():
    buttons = [InlineKeyboardButton(p, callback_data=f"hist_{p}") for p in HISTORY_WINDOWS]
    buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="hist_cancel"))
    return build_menu(buttons, n_cols=1)


def get_settings_keyboard():
    options = ["💵 Currency", "🌐 Language", "⏰ Timezone", "📂 Categories"]
    buttons = [InlineKeyboardButton(opt, callback_data=f"settings_{opt}") for opt in options]
    buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="settings_cancel"))
    return build_menu(buttons, n_cols=2)


def get_start_keyboard():
    return ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
