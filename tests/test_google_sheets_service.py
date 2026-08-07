import unittest
from unittest.mock import Mock, patch

from services.google_sheets_service import SHEET_HEADERS, append_record, find_record, json_text, parse_json, spreadsheet


class GoogleSheetsServiceTest(unittest.TestCase):
    def test_schema_has_four_human_readable_sheets(self):
        self.assertEqual(set(SHEET_HEADERS), {"users", "settings", "analysis_results", "audit_logs"})
        self.assertEqual(SHEET_HEADERS["users"][1:5], ["email", "name", "status", "role"])

    def test_json_round_trip(self):
        value = {"한글": True, "count": 3}
        self.assertEqual(parse_json(json_text(value), {}), value)
        self.assertEqual(parse_json("broken", {"safe": True}), {"safe": True})

    @patch("services.google_sheets_service.worksheet")
    def test_append_record_uses_declared_column_order(self, worksheet):
        sheet = Mock()
        worksheet.return_value = sheet
        append_record("users", {"email": "user@example.com", "name": "사용자", "status": "pending", "role": "operator"})
        row = sheet.append_row.call_args.args[0]
        self.assertEqual(row[1:5], ["user@example.com", "사용자", "pending", "operator"])

    @patch("services.google_sheets_service.records")
    def test_find_record_is_case_insensitive(self, records):
        records.return_value = [{"email": "User@Example.com", "status": "approved"}]
        found = find_record("users", "email", "user@example.com")
        self.assertEqual(found[0], 2)
        self.assertEqual(found[1]["status"], "approved")

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
