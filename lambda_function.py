import json
import threading

from base.update import Update
from base.bot import Bot
from base.google_spreadsheets import Spreadsheet

from config import TOKEN_BOT, HTML, MY_CHAT_ID, TOKEN_GOOGLE
import handlers as h


bot = Bot(TOKEN_BOT)
sh: Spreadsheet = None


def conectar():
    global sh
    sh = Spreadsheet("Rodolfo Robles", "GASTOS", TOKEN_GOOGLE)


t_conectar = threading.Thread(target=conectar)
t_conectar.start()


def lambda_handler(event, context):
    global sh
    update = Update(json.loads(event["body"]), TOKEN_BOT)

    try:
        if update.user_id == MY_CHAT_ID:
            t_inicio = threading.Thread(
                target=update.sendMessage, args=("Iniciando...",)
            )
            t_inicio.start()

            t_conectar.join()

            if update.text and not update.command:
                update.messageHandler("default", h.cmd_text_general, sh=sh)

            elif update.command:
                handlers = {
                    "last_records": h.cmd_last_records,
                    "delete_last_record": h.cmd_delete_last_record,
                    "update_json": h.cmd_update_json,
                    "get_debt": h.cmd_get_debt,
                    "debt": h.cmd_add_debt_record,
                    "find": h.cmd_find_pattern,
                    'delete_debt': h.cmd_delete_debt_record
                }

                for k, v in handlers.items():
                    if update.commandHandler(k, v, sh=sh):
                        break

            # Formatos no soportados
            else:
                texto = f"<strong>Actividad extraña:</strong> \n\n {json.dumps(event,indent=4)}"
                update.sendMessage(texto, parse_mode=HTML)

        # Usuarios diferentes
        else:
            unknown_user = f"<strong>Usuario desconocido:</strong> \n\n {json.dumps(event,indent=4)}"
            bot.post(
                "sendMessage",
                params={
                    "chat_id": MY_CHAT_ID,
                    "text": unknown_user,
                    "parse_mode": HTML,
                },
            )

    # Errores de código
    except Exception as e:
        event_string = json.dumps(event, indent=4)
        bot.sendMessage(
            update,
            f"<strong>ERROR:</strong> \n\n{e}",
            parse_mode=HTML,
        )

    return {"statusCode": 200, "body": "Success"}
