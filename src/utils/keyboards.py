from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from config import (
    CATEGORIES,
    HISTORY_WINDOWS,
    STATS_WINDOWS,
    MAIN_MENU,
    SETTINGS_OPTIONS,
)


def build_menu(buttons, n_cols=2):
    return InlineKeyboardMarkup([buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)])


def get_help_keyboard():
    buttons = [InlineKeyboardButton("⭐ Premium", callback_data="help_premium")]
    return build_menu(buttons, n_cols=1)


def get_subscription_keyboard():
    buttons = [
        InlineKeyboardButton("1 month - $3.99", callback_data="premium:select_plan:1m"),
        InlineKeyboardButton("3 months - $9.99", callback_data="premium:select_plan:3m"),
        InlineKeyboardButton("6 months - $19.99", callback_data="premium:select_plan:6m"),
        InlineKeyboardButton("1 year - $29.99", callback_data="premium:select_plan:12m"),
        InlineKeyboardButton("Cancel", callback_data="premium:cancel"),
    ]
    return build_menu(buttons, n_cols=1)


def get_delete_keyboard(items, keys):
    mapping = zip(items, keys)
    buttons = [InlineKeyboardButton(i, callback_data=f"expenses:delete:id:{k}") for i, k in mapping]
    buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="expenses:delete:cancel"))
    return build_menu(buttons, n_cols=1)


def get_category_keyboard():
    buttons = [
        InlineKeyboardButton(cat, callback_data=f"expenses:category:{cat.split()[-1]}")
        for cat in CATEGORIES
        if "Income" not in cat
    ]
    buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="expenses:cancel"))
    return build_menu(buttons, n_cols=3)


def get_stats_keyboard(is_back_button=False):
    if not is_back_button:
        buttons = [
            InlineKeyboardButton(p, callback_data=f"stats:window:{p}") for p in STATS_WINDOWS
        ]
        buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="stats:cancel"))
        return build_menu(buttons, n_cols=1)
    else:
        buttons = [InlineKeyboardButton("⬅️ Stats Menu", callback_data="stats:back_to_menu")]
        return build_menu(buttons, n_cols=1)


def get_history_keyboard(is_back_button=False):
    if not is_back_button:
        buttons = [
            InlineKeyboardButton(p, callback_data=f"history:window:{p}") for p in HISTORY_WINDOWS
        ]
        buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="history:cancel"))
        return build_menu(buttons, n_cols=1)
    else:
        buttons = [InlineKeyboardButton("⬅️ History Menu", callback_data="history:back_to_menu")]
        return build_menu(buttons, n_cols=1)


def get_settings_keyboard():
    buttons = [
        InlineKeyboardButton(opt, callback_data=f"settings:{opt.split()[-1]}")
        for opt in SETTINGS_OPTIONS
    ]
    buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="settings:cancel"))
    return build_menu(buttons, n_cols=2)


def get_start_keyboard():
    return ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)


def get_category_mgmt_menu(with_add=True, with_delete=True):
    keyboard = []
    if with_add:
        keyboard.append([InlineKeyboardButton("➕ Add Category", callback_data="cust_cat:add")])
    if with_delete:
        keyboard.append(
            [InlineKeyboardButton("🗑️ Delete Category", callback_data="cust_cat:delete")]
        )
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cust_cat:cancel")])
    return build_menu(keyboard, n_cols=1)
