import unittest
from unittest.mock import Mock, patch

import pandas as pd

from services.export_service import dataframe_to_xlsx
from services.teams_service import build_alert_payload, send_teams_alert


class TeamsAndExportTest(unittest.TestCase):
    def test_adaptive_card_contains_metrics(self):
        payload = build_alert_payload({"keywords": 2, "surges": 1, "matched": 1, "total_today": 1234})
        self.assertEqual(payload["type"], "message")
        card = payload["attachments"][0]["content"]
        self.assertEqual(card["type"], "AdaptiveCard")
        self.assertEqual(card["body"][1]["facts"][3]["value"], "1,234")

    @patch("services.teams_service.httpx.post")
    def test_send_teams_alert(self, post):
        response = Mock()
        response.raise_for_status.return_value = None
        post.return_value = response
        send_teams_alert({"keywords": 1}, webhook_url="https://example.invalid/webhook")
        self.assertEqual(post.call_args.args[0], "https://example.invalid/webhook")
        self.assertNotIn("https://example.invalid/webhook", str(post.call_args.kwargs["json"]))

    def test_rejects_insecure_webhook(self):
        with self.assertRaises(ValueError):
            send_teams_alert({}, webhook_url="http://example.invalid/webhook")

    def test_xlsx_export(self):
        content = dataframe_to_xlsx(pd.DataFrame([{"keyword": "세럼", "today": 10}]))
        self.assertTrue(content.startswith(b"PK"))


if __name__ == "__main__":
    unittest.main()
