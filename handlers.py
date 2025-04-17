import os
import json
import re
from base.update import Update
from base.utils import get_mx_time
from base.google_spreadsheets import Spreadsheet

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
            update.sendMessage("Sin registros de deuda")
    except Exception as e:
        update.sendMessage(str(e))


def cmd_delete_debt_record(update: Update, sh: Spreadsheet):
    try:
        last_data = sh.get_next_empty_row(start_row=2, max_row=14) - 1
        range_str = f"A{last_data}:C{last_data}"
        datos = sh.wks.get(range_str)
        mensaje = f"The row {last_data} has been cleared\n{'-'*60}\n{sh.clean_record_output(datos)}"
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
            update.sendMessage("Patron no reconocido")
    except Exception as e:
        Update.sendMessage(str(e))


def cmd_find_pattern(update: Update, sh: Spreadsheet):
    try:
        pattern = (
            update.text.split(maxsplit=1)[1] if len(update.text.split()) > 1 else None
        )

        if not pattern:
            update.sendMessage("Falta el patrón de búsqueda")
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
            update.sendMessage("Sin resultados")
    except Exception as e:
        update.sendMessage(str(e))


def cmd_delete_last_record(update: Update, sh: Spreadsheet) -> str:
    last_data = sh.get_next_available_row() - 1
    datos = sh.wks.get(f"A{last_data}:C{last_data}")
    mensaje = f"The row {last_data} has been cleared\n{'-'*60}\n{sh.clean_record_output(datos)}"
    update.sendMessage(mensaje)
    sh.wks.delete_rows(last_data)


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
    formatted_msg = (
        lambda desc, cost: f"""A{nar} | B{nar} | C{nar}\n{desc} | ${cost}.00 | {date}"""
    )

    if info_split[0] == ".":
        desc, cost, _ = sh.wks.get(f"A{nar-1}:C{nar-1}")[0]
        cost = cost.replace("$", "")
        update.sendMessage(formatted_msg(desc, cost))
        update_row(nar, desc, cost, date, sh)

    elif lwr_txt in shortcuts:
        update.sendMessage(formatted_msg(lwr_txt, shortcuts[lwr_txt]))
        update_row(nar, lwr_txt, f"{shortcuts[lwr_txt]}", date, sh)

    elif len(info_split) < 2:
        update.sendMessage("Sintaxis incorrecta")

    elif numero_primero or numero_final:
        cost = info_split[0] if numero_primero else info_split[-1]
        description = (
            " ".join(info_split[1:]) if numero_primero else " ".join(info_split[0:-1])
        )
        if len(info_split) == 2 and description.lower() in short_desc:
            description = short_desc[description.lower()]
        update.sendMessage(formatted_msg(description, cost))
        update_row(nar, description, cost, date, sh)
    else:
        update.sendMessage("Se necesita un valor numerico")
