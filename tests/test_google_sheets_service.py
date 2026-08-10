import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from services.google_sheets_service import (GoogleSheetsAPIError, SHEET_HEADERS, append_record, ensure_schema,
                                            find_record, json_text, parse_json, records)

WEB_APP_URL = "https://script.google.com/macros/s/test-deployment/exec"


class GoogleSheetsServiceTest(unittest.TestCase):
    def test_apps_script_manifest_uses_only_required_sheets_scope(self):
        project_root = Path(__file__).resolve().parents[1]
        manifest = json.loads((project_root / "google_apps_script" / "appsscript.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["oauthScopes"], ["https://www.googleapis.com/auth/spreadsheets"])

    def test_apps_script_does_not_use_unneeded_google_services(self):
        project_root = Path(__file__).resolve().parents[1]
        source = (project_root / "google_apps_script" / "Code.gs").read_text(encoding="utf-8")
        for service in ("DriveApp", "GmailApp", "UrlFetchApp", "DocumentApp", "FormApp", "SlidesApp"):
            self.assertNotIn(service, source)

    def test_schema_has_three_data_sheets(self):
        self.assertEqual(set(SHEET_HEADERS), {"settings", "analysis_results", "audit_logs"})
        self.assertIn("value_json", SHEET_HEADERS["settings"])

    def test_json_round_trip(self):
        value = {"한글": True, "count": 3}
        self.assertEqual(parse_json(json_text(value), {}), value)
        self.assertEqual(parse_json("broken", {"safe": True}), {"safe": True})

    @patch("services.google_sheets_service.google_apps_script_url", return_value=WEB_APP_URL)
    @patch("services.google_sheets_service.httpx.post")
    def test_ensure_schema_calls_web_app_and_follows_redirects(self, post, _url):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"ok": True, "data": {"settings": 1, "analysis_results": 2, "audit_logs": 3}}
        post.return_value = response
        self.assertEqual(ensure_schema()["analysis_results"], 2)
        self.assertEqual(post.call_args.args[0], WEB_APP_URL)
        self.assertEqual(post.call_args.kwargs["json"], {"action": "ensure_schema"})
        self.assertTrue(post.call_args.kwargs["follow_redirects"])

    @patch("services.google_sheets_service.google_apps_script_url", return_value=WEB_APP_URL)
    @patch("services.google_sheets_service.httpx.post")
    def test_records_and_append_contract(self, post, _url):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.side_effect = [
            {"ok": True, "data": [{"key": "dashboard", "value_json": "{}"}]},
            {"ok": True, "data": {"saved": True}},
        ]
        post.return_value = response
        self.assertEqual(records("settings")[0]["key"], "dashboard")
        append_record("settings", {"key": "retention", "value_json": "{}"})
        self.assertEqual(post.call_args.kwargs["json"], {
            "action": "append_record", "sheet": "settings",
            "data": {"key": "retention", "value_json": "{}"},
        })

    @patch("services.google_sheets_service.records")
    def test_find_record_is_case_insensitive(self, records_mock):
        records_mock.return_value = [{"key": "Dashboard", "value_json": "{}"}]
        found = find_record("settings", "key", "dashboard")
        self.assertEqual(found[0], 2)
        self.assertEqual(found[1]["value_json"], "{}")

    @patch("services.google_sheets_service.google_apps_script_url", return_value="http://example.com/not-exec")
    def test_rejects_non_web_app_url(self, _url):
        with self.assertRaises(RuntimeError):
            ensure_schema()

    @patch("services.google_sheets_service.google_apps_script_url", return_value=WEB_APP_URL)
    @patch("services.google_sheets_service.httpx.post")
    def test_surfaces_apps_script_error(self, post, _url):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"ok": False, "error": "header mismatch"}
        post.return_value = response
        with self.assertRaisesRegex(GoogleSheetsAPIError, "header mismatch"):
            ensure_schema()


if __name__ == "__main__":
    unittest.main()
