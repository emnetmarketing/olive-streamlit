import os
import time
import unittest
from unittest.mock import patch

from components.auth import authenticate
from components.config import secret_bool
from components.session import _decode, _encode
from services.settings_service import _validate


class SettingsAndAuthTest(unittest.TestCase):
    def test_dashboard_thresholds_are_bounded(self):
        settings = _validate("dashboard", {"surge_threshold": 0, "match_threshold": 200,
                                            "yesterday_max": -1, "schedule_times": []})
        self.assertEqual(settings["surge_threshold"], 1)
        self.assertEqual(settings["match_threshold"], 100)
        self.assertEqual(settings["yesterday_max"], 0)
        self.assertEqual(settings["schedule_times"], ["09:00"])

    def test_environment_boolean(self):
        os.environ["TEST_COOKIE_FLAG"] = "false"
        self.assertFalse(secret_bool("TEST_COOKIE_FLAG", True))
        os.environ.pop("TEST_COOKIE_FLAG", None)

    @patch("components.session.secret", return_value="strong-shared-password")
    def test_session_token_is_signed_expires_and_hides_password(self, _secret):
        token = _encode({"exp": int(time.time()) + 60})
        self.assertNotIn("strong-shared-password", token)
        self.assertIsNotNone(_decode(token))
        self.assertIsNone(_decode(token + "tampered"))
        self.assertIsNone(_decode(_encode({"exp": 1}), now=2))

    @patch("components.auth.save_session")
    @patch("components.auth.secret", return_value="strong-shared-password")
    def test_password_comparison(self, _secret, save_session):
        self.assertFalse(authenticate("wrong-password"))
        save_session.assert_not_called()
        self.assertTrue(authenticate("strong-shared-password"))
        save_session.assert_called_once()


if __name__ == "__main__":
    unittest.main()
