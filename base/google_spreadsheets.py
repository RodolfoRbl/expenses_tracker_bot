from gspread import service_account_from_dict


class Spreadsheet:
    def __init__(self, file, sheet, creds_dict) -> None:

        self.file = file
        self.sheet = sheet

        sa = service_account_from_dict(creds_dict)
        sh = sa.open(self.file)
        self.wks = sh.worksheet(self.sheet)

    def get_next_available_row(self):
        return len(self.wks.col_values(1)) + 1

    def get_next_empty_row(self, start_row, max_row):
        for i in range(start_row, max_row + 1):
            if not self.wks.cell(i, 1).value:
                return i
        return max_row + 1

    def get_all_values(self, start_row=13, end_row=None) -> list[list[str]]:
        array = []
        last = end_row or self.get_next_available_row()
        for record in self.wks.get(f"A{start_row}:C{last}"):
            array.append(record)
        return array

    def get_last_records(self, offset=5) -> list:
        final_string = ""
        nar = self.get_next_available_row()
        for record in self.wks.get(f"A{nar-offset}:C{nar-1}"):
            final_string += str(record) + "\n" + "-" * 60 + "\n"
        return self.clean_record_output(final_string)

    def clean_record_output(self, value) -> str:
        string_value = str(value)
        characters = {"[": "", "]": "", "'": ""}
        for key, value in characters.items():
            string_value = string_value.replace(key, value)
        return string_value

    def clear_range(self, range_string: str):
        """
        Clears the values in the specified range of cells in the spreadsheet.

        Args:
            sh (Spreadsheet): The Spreadsheet object.
            range_string (str): The range of cells to clear (e.g., "A1:B2").
        """
        try:
            # Get the range of cells
            cell_list = self.wks.range(range_string)
            # Set each cell's value to empty
            for cell in cell_list:
                cell.value = ""
            # Update the cells in the worksheet
            self.wks.update_cells(cell_list, value_input_option="USER_ENTERED")
        except Exception as e:
            print(f"An error occurred: {e}")
