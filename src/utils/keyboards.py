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
        InlineKeyboardButton("1 month - $3.99", callback_data="subs_plan_1m"),
        InlineKeyboardButton("3 months - $9.99", callback_data="subs_plan_3m"),
        InlineKeyboardButton("6 months - $19.99", callback_data="subs_plan_6m"),
        InlineKeyboardButton("1 year - $29.99", callback_data="subs_plan_12m"),
        InlineKeyboardButton("Cancel", callback_data="subs_plan_cancel"),
    ]
    return build_menu(buttons, n_cols=1)


def get_delete_keyboard(items, keys):
    mapping = zip(items, keys)
    buttons = [InlineKeyboardButton(i, callback_data=f"delete_{k}") for i, k in mapping]
    buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="delete_cancel"))
    return build_menu(buttons, n_cols=1)


def get_category_keyboard():
    buttons = [
        InlineKeyboardButton(cat, callback_data=f"cat_{cat.split()[-1]}")
        for cat in CATEGORIES
        if "Income" not in cat
    ]
    buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="cat_cancel"))
    return build_menu(buttons, n_cols=3)


def get_stats_keyboard(is_back_button=False):
    if not is_back_button:
        buttons = [InlineKeyboardButton(p, callback_data=f"stats_{p}") for p in STATS_WINDOWS]
        buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="stats_cancel"))
        return build_menu(buttons, n_cols=1)
    else:
        buttons = [InlineKeyboardButton("⬅️ Stats Menu", callback_data="stats_back")]
        return build_menu(buttons, n_cols=1)


def get_history_keyboard(is_back_button=False):
    if not is_back_button:
        buttons = [InlineKeyboardButton(p, callback_data=f"hist_{p}") for p in HISTORY_WINDOWS]
        buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="hist_cancel"))
        return build_menu(buttons, n_cols=1)
    else:
        buttons = [InlineKeyboardButton("⬅️ History Menu", callback_data="hist_back")]
        return build_menu(buttons, n_cols=1)


def get_settings_keyboard():
    buttons = [
        InlineKeyboardButton(opt, callback_data=f"settings_{opt.split('_')[-1]}")
        for opt in SETTINGS_OPTIONS
    ]
    buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="settings_cancel"))
    return build_menu(buttons, n_cols=2)


def get_start_keyboard():
    return ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)


def get_category_mgmt_menu():
    keyboard = [
        [InlineKeyboardButton("➕ Add Category", callback_data="cat:add")],
        [InlineKeyboardButton("🗑️ Delete Category", callback_data="cat:delete")],
    ]
    return build_menu(keyboard, n_cols=1)
