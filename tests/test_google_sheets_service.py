import unittest
from unittest.mock import Mock, patch

from gspread.exceptions import WorksheetNotFound

from services.google_sheets_service import (SHEET_HEADERS, append_record, ensure_schema, find_record, json_text,
                                            parse_json, spreadsheet, worksheet as get_worksheet)


class GoogleSheetsServiceTest(unittest.TestCase):
    def test_schema_has_three_data_sheets(self):
        self.assertEqual(set(SHEET_HEADERS), {"settings", "analysis_results", "audit_logs"})
        self.assertIn("value_json", SHEET_HEADERS["settings"])

    @patch("services.google_sheets_service.worksheet")
    def test_ensure_schema_initializes_every_sheet_without_deleting_data(self, worksheet):
        worksheet.return_value.row_count = 1000
        result = ensure_schema()
        self.assertEqual(list(result), ["settings", "analysis_results", "audit_logs"])
        self.assertEqual([call.args[0] for call in worksheet.call_args_list],
                         ["settings", "analysis_results", "audit_logs"])

    @patch("services.google_sheets_service.spreadsheet")
    def test_existing_sheet_with_expected_header_is_preserved(self, spreadsheet):
        sheet = Mock()
        sheet.row_values.return_value = SHEET_HEADERS["settings"]
        spreadsheet.return_value.worksheet.return_value = sheet
        self.assertIs(get_worksheet("settings"), sheet)
        spreadsheet.return_value.add_worksheet.assert_not_called()
        sheet.append_row.assert_not_called()

    @patch("services.google_sheets_service.spreadsheet")
    def test_missing_sheet_is_created_with_header(self, spreadsheet):
        sheet = Mock()
        sheet.row_values.return_value = []
        book = spreadsheet.return_value
        book.worksheet.side_effect = WorksheetNotFound("settings")
        book.add_worksheet.return_value = sheet
        self.assertIs(get_worksheet("settings"), sheet)
        book.add_worksheet.assert_called_once()
        sheet.append_row.assert_called_once_with(SHEET_HEADERS["settings"], value_input_option="RAW")

    def test_json_round_trip(self):
        value = {"한글": True, "count": 3}
        self.assertEqual(parse_json(json_text(value), {}), value)
        self.assertEqual(parse_json("broken", {"safe": True}), {"safe": True})

    @patch("services.google_sheets_service.worksheet")
    def test_append_record_uses_declared_column_order(self, worksheet):
        sheet = Mock()
        worksheet.return_value = sheet
        append_record("settings", {"key": "dashboard", "value_json": "{}", "description": "설정"})
        row = sheet.append_row.call_args.args[0]
        self.assertEqual(row[:3], ["dashboard", "{}", "설정"])

    @patch("services.google_sheets_service.records")
    def test_find_record_is_case_insensitive(self, records):
        records.return_value = [{"key": "Dashboard", "value_json": "{}"}]
        found = find_record("settings", "key", "dashboard")
        self.assertEqual(found[0], 2)
        self.assertEqual(found[1]["value_json"], "{}")

    @patch("services.google_sheets_service.google_sheet_id", return_value="sheet-id")
    @patch("services.google_sheets_service.google_service_account", return_value={"type": "service_account"})
    @patch("services.google_sheets_service.gspread.service_account_from_dict")
    def test_connection_uses_sheet_id_and_minimal_scope(self, authorize, _credentials, _sheet_id):
        client = Mock()
        authorize.return_value = client
        spreadsheet.cache_clear()
        spreadsheet()
        client.open_by_key.assert_called_once_with("sheet-id")
        self.assertEqual(authorize.call_args.kwargs["scopes"], ["https://www.googleapis.com/auth/spreadsheets"])
        spreadsheet.cache_clear()


if __name__ == "__main__":
    unittest.main()
