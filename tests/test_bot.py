import copy
import importlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


# Keep the real decorators and keyboard types, but never construct a live client.
client = Mock()
client.message_handler.side_effect = lambda **kwargs: lambda handler: handler
client.callback_query_handler.side_effect = lambda **kwargs: lambda handler: handler
with patch("telebot.TeleBot", return_value=client):
    bot = importlib.import_module("bot")


def message(uid=2, username="student_one", text="✅ Я на уроке"):
    return SimpleNamespace(
        from_user=SimpleNamespace(id=uid, username=username),
        chat=SimpleNamespace(id=uid), text=text, message_id=10,
    )


def callback(data, uid=1):
    return SimpleNamespace(
        from_user=SimpleNamespace(id=uid), data=data, id="callback",
        message=message(uid),
    )


class BotTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "class_db.json"
        data_file = patch.object(bot, "DATA_FILE", str(self.path))
        data_file.start()
        self.addCleanup(data_file.stop)
        telegram = patch.object(bot, "bot", Mock())
        self.client = telegram.start()
        self.addCleanup(telegram.stop)
        self.db = {
            "allowed_users": {"damikiri": "Admin", "student_one": "Ученик", "other": "Other"},
            "users": {"1": "Admin", "2": "Ученик", "3": "Other", "4": "Ученик"},
            "user_map": {"1": "damikiri", "2": "student_one", "3": "other", "4": "student_one"},
            "attendance": {
                "Понедельник": {"2": {"status": "late", "reason": "Bus"}, "3": "present"},
                "Вторник": {"4": "absent", "3": {"status": "present"}},
            },
        }
        bot.save_db(self.db)

    def assert_unchanged(self, before):
        self.assertEqual(self.path.read_bytes(), before)

    def test_database_round_trip_preserves_unicode_and_both_attendance_formats(self):
        self.assertEqual(bot.load_db(), self.db)
        self.assertIn("Ученик", self.path.read_text(encoding="utf-8"))

    def test_legacy_database_gains_missing_collections_without_losing_data(self):
        self.path.write_text(json.dumps({"users": {"2": "Student"}, "extra": 42}))
        self.assertEqual(bot.load_db(), {
            "users": {"2": "Student"}, "extra": 42,
            "allowed_users": {}, "user_map": {}, "attendance": {},
        })

    def test_corrupt_database_raises_without_overwriting_file(self):
        self.path.write_text("{broken")
        before = self.path.read_bytes()
        with self.assertRaises(json.JSONDecodeError):
            bot.load_db()
        self.assert_unchanged(before)

    def test_admin_lookup_requires_a_known_privileged_mapping(self):
        for uid, expected in [(1, True), ("1", True), (2, False), (999, False)]:
            with self.subTest(uid=uid):
                self.assertIs(bot.is_admin(uid), expected)

    def test_start_rejects_missing_or_unlisted_username_without_writes(self):
        before = self.path.read_bytes()
        for username in [None, "", "outsider"]:
            with self.subTest(username=username):
                self.client.reset_mock()
                bot.cmd_start(message(uid=99, username=username))
                self.assert_unchanged(before)
                self.client.reply_to.assert_called_once()
                self.client.send_message.assert_not_called()

    def test_start_normalizes_username_and_persists_only_registered_identity(self):
        bot.cmd_start(message(uid=99, username="StUdEnT_OnE"))
        expected = copy.deepcopy(self.db)
        expected["users"]["99"] = "Ученик"
        expected["user_map"]["99"] = "student_one"
        self.assertEqual(bot.load_db(), expected)
        self.client.send_message.assert_called_once()

    def test_non_admin_cannot_delete_or_manually_mark_students(self):
        before = self.path.read_bytes()
        for uid in [2, 999]:
            for handler, data in [
                (bot.delete_student, "delete_confirm_student_one"),
                (bot.confirm_delete_student, "delete_un_student_one"),
                (bot.set_status, "set_3_absent"),
            ]:
                with self.subTest(uid=uid, handler=handler.__name__):
                    self.client.reset_mock()
                    handler(callback(data, uid))
                    self.assert_unchanged(before)
                    self.assertEqual(self.client.mock_calls, [])

    def test_delete_removes_all_linked_ids_and_records_but_preserves_other_students(self):
        bot.delete_student(callback("delete_confirm_student_one"))
        expected = copy.deepcopy(self.db)
        del expected["allowed_users"]["student_one"]
        for uid in ["2", "4"]:
            del expected["users"][uid]
            del expected["user_map"][uid]
            for records in expected["attendance"].values():
                records.pop(uid, None)
        self.assertEqual(bot.load_db(), expected)
        self.client.answer_callback_query.assert_called_once()

    def test_username_edit_updates_all_mappings_without_losing_attendance(self):
        with patch.object(bot, "admin_panel"):
            bot.process_edit_username(message(uid=1, text=" @NEW_Name "), "student_one")
        expected = copy.deepcopy(self.db)
        expected["allowed_users"]["new_name"] = expected["allowed_users"].pop("student_one")
        expected["user_map"].update({"2": "new_name", "4": "new_name"})
        self.assertEqual(bot.load_db(), expected)
        self.client.get_chat.assert_called_once_with("@new_name")

    def test_username_edit_rejects_empty_duplicate_and_unresolvable_input(self):
        before = self.path.read_bytes()
        for text, lookup_error in [(" @ ", False), ("@other", False), ("@missing", True)]:
            with self.subTest(text=text):
                self.client.reset_mock()
                self.client.get_chat.side_effect = RuntimeError("Not found") if lookup_error else None
                bot.process_edit_username(message(uid=1, text=text), "student_one")
                self.assert_unchanged(before)
                self.client.send_message.assert_called_once()
                if not lookup_error:
                    self.client.get_chat.assert_not_called()

    def test_attendance_window_includes_eight_but_excludes_nine(self):
        for hour, accepted in [(7, False), (8, True), (9, False)]:
            with self.subTest(hour=hour):
                bot.save_db(self.db)
                before = self.path.read_bytes()
                with patch.object(bot, "get_today", return_value="Среда"), patch.object(
                    bot, "is_weekend_or_holiday", return_value=(False, "")
                ), patch.object(bot, "datetime") as clock:
                    clock.now.return_value.hour = hour
                    bot.set_student_status(message())
                if accepted:
                    expected = copy.deepcopy(self.db)
                    expected["attendance"]["Среда"] = {"2": {"status": "present"}}
                    self.assertEqual(bot.load_db(), expected)
                else:
                    self.assert_unchanged(before)

    def test_duplicate_attendance_cannot_replace_status_or_reason(self):
        before = self.path.read_bytes()
        with patch.object(bot, "get_today", return_value="Понедельник"), patch.object(
            bot, "is_weekend_or_holiday", return_value=(False, "")
        ), patch.object(bot, "datetime") as clock:
            clock.now.return_value.hour = 8
            bot.set_student_status(message())
        self.assert_unchanged(before)
        self.client.register_next_step_handler.assert_not_called()

    def test_holiday_blocks_student_and_admin_attendance_writes(self):
        before = self.path.read_bytes()
        with patch.object(bot, "is_weekend_or_holiday", return_value=(True, "holiday")):
            bot.set_student_status(message())
            bot.set_status(callback("set_3_absent"))
        self.assert_unchanged(before)
        self.client.answer_callback_query.assert_called_once()
        self.assertTrue(self.client.answer_callback_query.call_args.kwargs["show_alert"])


if __name__ == "__main__":
    unittest.main()
