import os
import unittest
from unittest.mock import patch

from bot.config import Settings


class SettingsTestCase(unittest.TestCase):
    def test_settings_accepts_telegram_bot_token_alias(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test-token-1234567890"}, clear=True):
            settings = Settings()
            self.assertEqual(settings.bot_token.get_secret_value(), "test-token-1234567890")


if __name__ == "__main__":
    unittest.main()
