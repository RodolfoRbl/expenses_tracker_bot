from telegram import Update
from telegram.ext import ContextTypes
from functools import wraps
from utils.rate_limiter import RateLimiter
from datetime import datetime, timezone
from config import CMD_FOR_PREMIUM_TEXT
from utils.general import get_db


def rate_counter(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        _allowed_reqs = context.bot_data["requests_per_day"]
        is_admin = update.effective_user.id in context.bot_data["admins"]
        def_allowed = _allowed_reqs * 20 if is_admin else _allowed_reqs

        rlim = RateLimiter(
            update.effective_user.id,
            context.bot.id,
            context.bot_data["db"],
            max_reqs_allowed=def_allowed,
        )
        rlim.get_current_reqs()
        n_warns = rlim.max_reqs_allowed + 5
        is_max = rlim.is_max_reached()
        if update.callback_query:
            ans_func = update.callback_query.edit_message_text
        else:
            ans_func = update.effective_user.send_message
        if not is_max:
            await func(update, context)
        elif is_max and rlim.daily_requests < n_warns:
            await ans_func(
                f"⚠️ <b>Limit reached!</b> Try again in <b>{rlim.get_time_until_reset()}</b> ⏳",
                parse_mode="HTML",
            )
        else:
            pass
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


def check_premium_or_admin(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.callback_query:
            ans_func = update.callback_query.edit_message_text
        else:
            ans_func = update.message.reply_text

        if update.effective_user.id in context.bot_data.get("admins", []):
            await func(update, context)
        else:
            db = get_db(context)
            fields = db.get_fields(
                update.effective_user.id, context.bot.id, ["is_premium", "end_premium"]
            )
            is_premium = fields.get("is_premium")
            end_premium = fields.get("end_premium")
            current_time = datetime.now(timezone.utc).timestamp()
            if not is_premium:
                await ans_func(CMD_FOR_PREMIUM_TEXT, parse_mode="HTML")
            elif is_premium and end_premium < current_time:
                db.update_multiple_fields(
                    update.effective_user.id,
                    context.bot.id,
                    {
                        "is_premium": False,
                        "end_premium": "",
                        "premium_plan": "",
                    },
                )
            else:
                await func(update, context)

    return wrapper
