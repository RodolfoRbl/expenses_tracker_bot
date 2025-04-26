from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes

from utils.keyboards import get_category_keyboard, get_category_mgmt_menu
from utils.general import get_db, parse_msg_to_elements, get_active_categories
from handlers._decorators import rate_counter
from config import ST_WAIT_CATEGORY, ST_REGULAR
import uuid


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
            act_cats = get_active_categories(db, user_id, context.bot.id)
            await update.message.reply_text(
                f"<b>Expense</b>: ${amount:,.2f}\n{_desc}\n" "Please select a category:",
                parse_mode="HTML",
                reply_markup=get_category_keyboard(act_cats),
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
    db = get_db(context)
    txt = update.message.text.strip()
    is_name_ok = not txt.startswith("/") and len(txt) <= 20
    user_id = str(update.effective_user.id)
    if is_name_ok:
        cats = db.get_fields(user_id, context.bot.id, "categories")
        # Seek if the category already existed
        for cat_id, cat_data in cats.items():
            if cat_data["name"] == txt:
                cats[cat_id]["active"] = 1
                db.update_field(update.effective_user.id, context.bot.id, "categories", cats)
                await update.message.reply_text(f"Category '{txt}' reactivated.")
                db.update_fields(user_id, context.bot.id, "conversation_status", ST_REGULAR)
                return
        # If not, create a new one
        new_cat_id = str(uuid.uuid4()).split("-")[0]
        new_category = {"name": txt, "active": 1}
        cats[new_cat_id] = new_category
        db.update_field(update.effective_user.id, context.bot.id, "categories", cats)
        await update.message.reply_text(f"New category <b>'{txt}'</b> created.", parse_mode="HTML")
    else:
        await update.message.reply_text(
            "⚠️ Invalid category name. Please try again.",
            reply_markup=get_category_mgmt_menu(with_delete=False, with_reset=False),
        )
    db.update_field(user_id, context.bot.id, "conversation_status", ST_REGULAR)


@rate_counter
async def text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    status = db.get_fields(update.effective_user.id, context.bot.id, "conversation_status") or 0
    msg_hand_map = {
        ST_REGULAR: _msg_regular,
        ST_WAIT_CATEGORY: _msg_custom_category,
    }
    await msg_hand_map[status](update, context)
