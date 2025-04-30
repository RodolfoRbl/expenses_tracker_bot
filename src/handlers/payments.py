from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils.general import get_db
import datetime as dt


# Do not count towards the limit
async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


# Do not count towards the limit
async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    payment = update.message.successful_payment
    plan = payment.invoice_payload
    plan_months = {"plan_1m": 1, "plan_3m": 3, "plan_6m": 6, "plan_12m": 12}

    now = datetime.now(dt.timezone.utc)
    end_date = now + relativedelta(months=plan_months.get(plan))
    new_premium = {
        "is_premium": True,
        "end_premium": end_date.timestamp(),
        "premium_plan": plan,
    }
    db.update_multiple_fields(update.effective_user.id, context.bot.id, updates=new_premium)
    end_date_fmt = f"{end_date.strftime('%Y-%m-%d %H:%M')} UTC"
    await update.message.reply_text(
        f"✅ Payment successful! Premium activated until {end_date_fmt}"
    )
