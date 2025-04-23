from telegram import Update
from telegram.ext import ContextTypes
from functools import wraps
from utils.rate_limiter import RateLimiter


def rate_counter(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        rlim = RateLimiter(
            update.effective_user.id,
            context.bot.id,
            context.bot_data["db"],
            max_reqs_allowed=context.bot_data["requests_per_day"],
        )
        rlim.get_current_reqs()
        if rlim.is_max_reached():
            if update.callback_query:
                ans_func = update.callback_query.edit_message_text
            else:
                ans_func = update.effective_user.send_message
            await ans_func(
                f"⚠️ <b>Limit reached!</b> Try again in <b>{rlim.get_time_until_reset()}</b> ⏳",
                parse_mode="HTML",
            )
        else:
            await func(update, context)
        rlim.update_db_reqs()

    return wrapper


def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id in context.bot_data["admins"]:
            await func(update, context)
        else:
            await update.message.reply_text("⛔ This command is only for admins.")

    return wrapper
