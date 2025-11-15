import os
import json
import re
from datetime import datetime
from base.update import Update
from base.utils import get_mx_time
from base.google_spreadsheets import Spreadsheet
from config import HTML

# ###########################################################################################
# ################################# C O M A N D S ############################################
# ############################################################################################


def cmd_update_json(update: Update, sh: Spreadsheet):
    update.sendMessage(update.full_string)
    return 1


def cmd_last_records(update: Update, sh: Spreadsheet, offset=5):
    try:
        update.sendMessage(sh.get_last_records(offset))
    except Exception as e:
        update.sendMessage(str(e))


def cmd_get_debt(update: Update, sh: Spreadsheet):
    try:
        final_string = ""
        for record in sh.wks.get("A3:C11"):
            if len(record):
                final_string += str(record) + "\n" + "-" * 60 + "\n"
        mensaje = sh.clean_record_output(final_string)
        if mensaje != "":
            update.sendMessage(mensaje)
        else:
            update.sendMessage("No debt records found")
    except Exception as e:
        update.sendMessage(str(e))


def cmd_delete_debt_record(update: Update, sh: Spreadsheet):
    try:
        last_data = sh.get_next_empty_row(start_row=2, max_row=14) - 1
        range_str = f"A{last_data}:C{last_data}"
        datos = sh.wks.get(range_str)
        msg = f"The row {last_data} has been cleared"
        mensaje = f"{msg}\n{'-'*len(msg)}\n{sh.clean_record_output(datos)}"
        update.sendMessage(mensaje)
        sh.clear_range(range_str)
    except Exception as e:
        update.sendMessage(str(e))


def cmd_add_debt_record(update: Update, sh: Spreadsheet):
    try:
        info_split = update.text.split()
        if len(info_split) < 3:
            update.sendMessage("Se requiere descripción y monto")

        elif re.findall("^-?\d+(\.\d+)?$", info_split[-1]):
            nar = sh.get_next_empty_row(3, 11)
            if nar <= 11:
                description = " ".join(info_split[1:-1])
                cost = info_split[-1]
                date = get_mx_time("%d/%m/%Y")

                cell_list = sh.wks.range(f"A{nar}:C{nar}")
                cell_values = [description, cost, date]
                for i, val in enumerate(cell_values):
                    cell_list[i].value = val
                msg = f"""A{nar} | B{nar} | C{nar}\n{description} | {cost} | {date}"""
                update.sendMessage(msg)
                sh.wks.update_cells(cell_list, value_input_option="USER_ENTERED")
            else:
                update.sendMessage("No hay espacio para agregar la deuda")
        else:
            update.sendMessage("Unrecognized pattern")
    except Exception as e:
        Update.sendMessage(str(e))


def cmd_find_pattern(update: Update, sh: Spreadsheet):
    try:
        pattern = update.text.split(maxsplit=1)[1] if len(update.text.split()) > 1 else None

        if not pattern:
            update.sendMessage("Missing search pattern")
            return

        # Get all records in the spreadsheet
        records = sh.get_all_values()

        # Search for the pattern in the records
        matched_records = []
        for row in records:
            for cell in row:
                if re.search(pattern, cell, re.IGNORECASE):
                    matched_records.append(row)
                    break

        # Format and send the matched records
        if matched_records:
            msg = ""
            # Max. telegram characters are 4096
            for record in matched_records[-50:]:
                msg += str(record) + "\n"
            msg = sh.clean_record_output(msg)
            update.sendMessage(msg)
        else:
            update.sendMessage("No results found")
    except Exception as e:
        update.sendMessage(str(e))


def cmd_delete_last_record(update: Update, sh: Spreadsheet) -> str:
    last_data = sh.get_next_available_row() - 1
    datos = sh.wks.get(f"A{last_data}:C{last_data}")
    msg = f"The row {last_data} has been cleared"
    mensaje = f"{msg}\n{'-'*len(msg)}\n{sh.clean_record_output(datos)}"
    update.sendMessage(mensaje)
    sh.wks.delete_rows(last_data)


def cmd_show_menu(update: Update, sh: Spreadsheet):
    """Show the main menu with expense tracking options"""

    buttons = [
        [
            {"text": "📊 Month Total", "callback_data": "month_total"},
        ],
        [
            {"text": "💰 Last 5", "callback_data": "last_records"},
            {"text": "🔍 Search", "callback_data": "search"},
        ],
        [
            {"text": "💳 Debt", "callback_data": "debt_summary"},
            {"text": "❌ Delete", "callback_data": "delete_last"},
        ],
    ]

    markup = json.dumps({"inline_keyboard": buttons})
    update.sendMessage("Choose an option:", reply_markup=markup)


def handle_callback_query(update: Update, sh: Spreadsheet):
    """Handle callback queries from inline keyboard buttons"""
    query_data = update.callback_data
    update.answerCallbackQuery()

    if query_data == "month_total":
        total = sh.get_month_total()
        current_month = datetime.now().strftime("%B %Y")
        update.sendMessage(f"Total expenses for {current_month}: ${total:,.2f}")

    elif query_data == "last_records":
        cmd_last_records(update, sh)

    elif query_data == "search":
        update.sendMessage("Send /find followed by the text you want to search")

    elif query_data == "debt_summary":
        cmd_get_debt(update, sh)

    elif query_data == "delete_last":
        cmd_delete_last_record(update, sh)


# ############################################################################################
# ################################# M E S S A G E S ##########################################
# ############################################################################################


def repeat_record(update: Update, sh: Spreadsheet) -> str:
    nar = sh.get_next_available_row()
    data = list(sh.wks.get(f"A{nar-1}:B{nar-1}"))
    cost = data[0][1]
    description = data[0][0]
    date = get_mx_time("%d/%m/%Y")
    mensaje = f"""A{nar} | B{nar} | C{nar}\n{description} | {cost} | {date}"""
    update.sendMessage(mensaje)
    cell_list = sh.wks.range(f"A{nar}:C{nar}")
    cell_values = [description, cost, date]
    for i, val in enumerate(cell_values):
        cell_list[i].value = val
    sh.wks.update_cells(cell_list, value_input_option="USER_ENTERED")


def update_row(row: str, desc: str, cost: str, date: str, sh: Spreadsheet):
    cell_list = sh.wks.range(f"A{row}:C{row}")
    for i, val in enumerate([desc, cost, date]):
        cell_list[i].value = val
    sh.wks.update_cells(cell_list, value_input_option="USER_ENTERED")


def cmd_text_general(update: Update, sh: Spreadsheet) -> str:
    info_split = update.text.split()
    date = get_mx_time("%d/%m/%Y")
    numero_primero = re.findall("^\d+(\.\d+)?$", info_split[0])
    numero_final = re.findall("^\d+(\.\d+)?$", info_split[-1])
    lwr_txt = update.text.lower()
    all_shortcuts = json.loads(os.getenv("EXPENSES_SHORTCUTS", "{}"))
    short_desc = {k: v for k, v in all_shortcuts.items() if isinstance(v, str)}
    shortcuts = {k: v for k, v in all_shortcuts.items() if isinstance(v, int)}
    nar = sh.get_next_available_row()
    formatted_msg = lambda desc, cost: (
        f"<b>Desc:</b> {desc}\n"
        f"<b>Amt:</b> ${cost}.00\n"
        f"<b>Date:</b> {date}\n"
        f"<b>Row:</b> {nar}"
    )

    if info_split[0] == ".":
        desc, cost, _ = sh.wks.get(f"A{nar-1}:C{nar-1}")[0]
        cost = cost.replace("$", "")
        update.sendMessage(formatted_msg(desc, cost), parse_mode=HTML)
        update_row(nar, desc, cost, date, sh)

    elif lwr_txt in shortcuts:
        cost = shortcuts[lwr_txt]
        # See if the text also matches a description shortcut (not just an amount)
        description = short_desc.get(lwr_txt, lwr_txt)
        update.sendMessage(formatted_msg(description, cost), parse_mode=HTML)
        update_row(nar, description, f"{cost}", date, sh)

    elif len(info_split) < 2:
        update.sendMessage("Sintaxis incorrecta", parse_mode=HTML)

    elif numero_primero or numero_final:
        cost = info_split[0] if numero_primero else info_split[-1]
        description = " ".join(info_split[1:]) if numero_primero else " ".join(info_split[0:-1])
        if len(info_split) == 2 and description.lower() in short_desc:
            description = short_desc[description.lower()]
        update.sendMessage(formatted_msg(description, cost), parse_mode=HTML)
        update_row(nar, description, cost, date, sh)
    else:
        update.sendMessage("Se necesita un valor numerico", parse_mode=HTML)
