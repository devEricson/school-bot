import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch


# Import real handlers without constructing a Telegram client or starting polling.
client = MagicMock()
client.message_handler.side_effect = lambda **kwargs: lambda handler: handler
spec = importlib.util.spec_from_file_location(
    "attendance_bot", Path(__file__).resolve().parents[1] / "bot.py"
)
attendance_bot = importlib.util.module_from_spec(spec)
with patch("telebot.TeleBot", return_value=client):
    spec.loader.exec_module(attendance_bot)


class StudentStatusTests(unittest.TestCase):
    statuses = {
        "✅ Я на уроке": "present",
        "❌ Не смогу прийти": "absent",
        "⏰ Я опоздаю": "late",
    }

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database = Path(directory.name) / "class_db.json"
        for patcher in (
            patch.object(attendance_bot, "DATA_FILE", str(self.database)),
            patch.object(attendance_bot, "is_weekend_or_holiday",
                         return_value=(False, "")),
            patch.object(attendance_bot, "datetime"),
        ):
            mocked = patcher.start()
            self.addCleanup(patcher.stop)
            if patcher.attribute == "datetime":
                mocked.now.return_value = SimpleNamespace(hour=8, weekday=lambda: 0)
        client.reset_mock()

    def write_database(self, users):
        database = {
            "users": users, "user_map": {}, "allowed_users": {},
            "attendance": {},
        }
        self.database.write_text(json.dumps(database), encoding="utf-8")
        return database

    def submit(self, text):
        attendance_bot.set_student_status(SimpleNamespace(
            from_user=SimpleNamespace(id=123),
            chat=SimpleNamespace(id=123),
            text=text,
        ))

    def test_unregistered_user_cannot_submit_any_status_directly(self):
        for text in self.statuses:
            with self.subTest(text=text):
                original = self.write_database({})
                client.reset_mock()
                self.submit(text)
                self.assertEqual(attendance_bot.load_db(), original)
                client.register_next_step_handler.assert_not_called()

    def test_registered_user_can_submit_each_status(self):
        for text, status in self.statuses.items():
            with self.subTest(text=text):
                self.write_database({"123": "Test Student"})
                client.reset_mock()
                self.submit(text)
                self.assertEqual(
                    attendance_bot.load_db()["attendance"],
                    {"Понедельник": {"123": {"status": status}}},
                )
                self.assertEqual(
                    client.register_next_step_handler.call_count,
                    int(status in {"absent", "late"}),
                )

    def test_registered_user_cannot_replace_existing_attendance(self):
        self.write_database({"123": "Test Student"})
        self.submit("✅ Я на уроке")
        original = attendance_bot.load_db()
        self.submit("❌ Не смогу прийти")
        self.assertEqual(attendance_bot.load_db(), original)
        client.register_next_step_handler.assert_not_called()


if __name__ == "__main__":
    unittest.main()
