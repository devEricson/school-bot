# Tests

This repository had no test suite or configured framework. These tests use
Python's standard-library `unittest` and the bot's runtime dependencies:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install pyTelegramBotAPI pytz schedule holidays
.venv/bin/python -m unittest discover -s tests -v
```

Telegram construction and calls are mocked; polling and scheduling do not start.
Every test uses a temporary JSON database with synthetic students, never the
checked-in class database. No Telegram credentials or network access are needed
to run the tests after dependencies are installed.

Coverage focuses on registration and admin authorization, JSON preservation,
deletion across linked records, username validation/migration, and attendance
time, holiday and duplicate-entry guards. This is not a full security audit.
