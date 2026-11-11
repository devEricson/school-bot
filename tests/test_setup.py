import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


class SetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.env = patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "123456:offline-test-not-a-real-token",
            "DATA_FILE": str(Path(cls.temp.name) / "class_db.json"),
            "ADMIN_USERNAMES": "@Example_Admin, other_admin",
            "ADMIN_IDS": "123456, 789012",
        })
        cls.env.start()
        with patch("socket.socket", side_effect=AssertionError("Tests must stay offline")):
            cls.bot = importlib.import_module("bot")

    @classmethod
    def tearDownClass(cls):
        cls.env.stop()
        cls.temp.cleanup()

    def test_database_round_trip_and_admin(self):
        db = self.bot.load_db()
        self.assertEqual(db, {"users": {}, "user_map": {}, "attendance": {}, "allowed_users": {}})
        db["user_map"]["123456"] = "example_admin"
        self.bot.save_db(db)
        self.assertEqual(self.bot.load_db(), db)
        self.assertTrue(self.bot.is_admin(123456))
        self.assertFalse(self.bot.is_admin(999999))
        self.assertEqual(self.bot.ADMIN_IDS, [123456, 789012])

    def test_example_database(self):
        example = Path(__file__).resolve().parents[1] / "class_db.example.json"
        self.assertEqual(set(json.loads(example.read_text())), {"users", "user_map", "attendance", "allowed_users"})

    def test_handlers_and_calendar(self):
        self.assertTrue(self.bot.bot.message_handlers)
        self.assertTrue(self.bot.bot.callback_query_handlers)
        self.assertIsInstance(self.bot.is_weekend_or_holiday()[0], bool)
        self.assertIsNotNone(self.bot.get_student_menu())
        self.assertIsNotNone(self.bot.get_admin_menu())

    def test_missing_token_has_actionable_error(self):
        env = dict(os.environ)
        env.pop("TELEGRAM_BOT_TOKEN", None)
        result = subprocess.run([sys.executable, "bot.py"], env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Set TELEGRAM_BOT_TOKEN", result.stderr)

    def test_invalid_admin_ids_have_actionable_error(self):
        result = subprocess.run([sys.executable, "bot.py"], env={**os.environ, "ADMIN_IDS": "not-an-id"}, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ADMIN_IDS must be", result.stderr)


if __name__ == "__main__":
    unittest.main()
