from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes

from utils.keyboards import get_category_keyboard
from utils.general import get_db, parse_msg_to_elements
from handlers._decorators import rate_counter
from config import ST_WAIT_CATEGORY, ST_REGULAR


async def _msg_regular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    text = update.message.text.strip()
    if len(text) >= 100:
        await update.message.reply_text("Message too long. Please keep it under 100 characters.")
        return
    user_id = str(update.effective_user.id)

    amount, description, is_income = await parse_msg_to_elements(update, text)
    _desc = f"<b>Description</b>: {description}" if description else ""
    if is_income is None:
        pass
    elif is_income:
        try:
            await update.message.reply_text(f"✅ Logged: ${amount:,.2f} in Income")
            db.insert_expense(
                user_id=user_id,
                amount=amount,
                category="99",  # Income category
                currency="USD",
                description=description,
                income=is_income,
            )
        except Exception as e:
            await update.message.reply_text(f"Error inserting income: {str(e)}")
    else:
        try:
            await update.message.reply_text(
                f"<b>Expense</b>: ${amount:,.2f}\n{_desc}\n" "Please select a category:",
                parse_mode="HTML",
                reply_markup=get_category_keyboard(),
            )

            db.users_table.update_item(
                Key={"user_id": user_id, "bot_id": str(context.bot.id)},
                UpdateExpression="SET temp_data = :tmp_data",
                ExpressionAttributeValues={
                    ":tmp_data": {
                        "pend_amt": Decimal(str(amount)),
                        "pend_desc": description,
                        "pend_inc": is_income,
                    }
                },
            )
        except Exception as e:
            await update.message.reply_text(f"Error recording expense: {str(e)}")


async def _msg_custom_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Logic to validate and update categories")
    await update.message.reply_text("Reset conv status")


@rate_counter
async def text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    status = db.get_fields(update.effective_user.id, context.bot.id, "conversation_status") or 0
    msg_hand_map = {
        ST_REGULAR: _msg_regular,
        ST_WAIT_CATEGORY: _msg_custom_category,
    }
    await msg_hand_map[status](update, context)
