import json
import threading

from base.update import Update
from base.bot import Bot
from base.google_spreadsheets import Spreadsheet

from config import TOKEN_BOT, HTML, MY_CHAT_ID, TOKEN_GOOGLE, FILE_NAME, SHEET_NAME
import handlers as h


bot = Bot(TOKEN_BOT)
sh: Spreadsheet = None


def conectar():
    global sh
    sh = Spreadsheet(FILE_NAME, SHEET_NAME, TOKEN_GOOGLE)


t_conectar = threading.Thread(target=conectar)
t_conectar.start()


def lambda_handler(event, context):
    global sh
    update = Update(json.loads(event["body"]), TOKEN_BOT)

    try:
        if update.user_id == MY_CHAT_ID:
            t_inicio = threading.Thread(target=update.sendMessage, args=("Starting...",))
            t_inicio.start()

            t_conectar.join()

            if update.callback_query:
                h.handle_callback_query(update, sh)

            elif update.text and not update.command:
                update.messageHandler("default", h.cmd_text_general, sh=sh)

            elif update.command:
                handlers = {
                    "menu": h.cmd_show_menu,
                    "last_records": h.cmd_last_records,
                    "delete_last_record": h.cmd_delete_last_record,
                    "update_json": h.cmd_update_json,
                    "get_debt": h.cmd_get_debt,
                    "debt": h.cmd_add_debt_record,
                    "find": h.cmd_find_pattern,
                    "delete_debt": h.cmd_delete_debt_record,
                }

                for k, v in handlers.items():
                    if update.commandHandler(k, v, sh=sh):
                        break

            # Unsupported formats
            else:
                texto = f"<strong>Strange activity:</strong> \n\n {json.dumps(event,indent=4)}"
                update.sendMessage(texto, parse_mode=HTML)

        # Different users
        else:
            unknown_user = f"<strong>Unknown user:</strong> \n\n {json.dumps(event,indent=4)}"
            bot.post(
                "sendMessage",
                params={
                    "chat_id": MY_CHAT_ID,
                    "text": unknown_user,
                    "parse_mode": HTML,
                },
            )

    # Code errors
    except Exception as e:
        event_string = json.dumps(event, indent=4)
        bot.sendMessage(
            update,
            f"<strong>ERROR:</strong> \n\n{e}\n\n{event_string}",
            parse_mode=HTML,
        )

    return {"statusCode": 200, "body": "Success"}
