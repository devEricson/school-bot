# School attendance bot

A Russian-language Telegram bot for class registration, attendance, admin menus,
and morning reminders. This is a Python script, not a compiled application.

## Prerequisites

The commands below use a POSIX shell (Linux or macOS), Git, and **Python 3.12**
with `pip` and `venv`. Python 3.12 is the verified version; other versions have
not been tested. Check `git --version` and `python3.12 --version` first.
On Ubuntu 24.04, install the prerequisites with:

```sh
sudo apt-get update
sudo apt-get install -y git python3.12 python3.12-venv
```

On other systems, install Git and Python 3.12 using your OS package manager or
python.org. Installing dependencies requires internet access. Running the bot
also requires a new Telegram bot token from **@BotFather** and access to Telegram.
Offline tests do not require a real token, Telegram access, or class data.

## Clone, install, and test

```sh
git clone https://github.com/devEricson/school-bot.git
cd school-bot
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -m unittest discover -s tests -v
python -m py_compile bot.py
```

Expect five passing tests, `No broken requirements found`, and no compilation
errors. The tests use a fake token and a temporary database; they do not start
polling or send messages. These commands are the build/test verification path.
Reactivate `.venv` in each new shell. Do not install the unrelated `telebot`
package: the `telebot` import is supplied by **pyTelegramBotAPI**.

## Configure and run a new bot

Run all commands from the repository root. Do not use the historical
`class_db.json` for a new deployment: it contains existing class data. Start
with the synthetic example instead:

```sh
cp class_db.example.json class_db.local.json
```

Edit `class_db.local.json`: replace `your_telegram_username` with your own
Telegram username, lowercase and without `@`, and set your display name. Add
other students to `allowed_users` in the same format. Keep `users`, `user_map`,
and `attendance` empty for a new class. Users need a Telegram username and must
be in `allowed_users` before `/start` can register them.

Set the following in your shell (replace each placeholder):

```sh
export TELEGRAM_BOT_TOKEN='REPLACE_WITH_YOUR_NEW_BOTFATHER_TOKEN'
export ADMIN_USERNAMES='your_telegram_username'
export ADMIN_IDS='123456789'
export DATA_FILE='class_db.local.json'
python bot.py
```

- `TELEGRAM_BOT_TOKEN` is required. Keep it secret; do not paste it into commits,
  logs, or bug reports. A `.env` file is **not** loaded automatically.
- `ADMIN_USERNAMES` is a comma-separated list granting the admin menu to
  registered users. Names are normalized to lowercase, with optional `@`.
  These users must also be in `allowed_users` and send `/start`.
- `ADMIN_IDS` is an optional comma-separated list of numeric Telegram user IDs
  receiving suggestions. It does **not** grant admin permissions. Use IDs of
  intended recipients who have already started the bot; omit it if unused.
- `DATA_FILE` defaults to `class_db.local.json`, relative to the current working
  directory. Its parent directory must exist and be writable. A missing file
  starts with an empty roster, so copy and edit the example before first use.
- Both admin lists default to empty; no historical admin is automatically trusted.

The bot prints `Бот запущен!` and remains running. Open your new bot in Telegram
and send `/start`: an allowed user should receive a greeting and menu; a configured
admin should also see the admin panel. Stop with Ctrl+C. Run only one process per
bot token and database. Back up your local JSON database and edit it only while
the bot is stopped. The local database, `.env`, virtual environment, and new
Python bytecode are ignored by Git.

**Credential warning:** a token was previously committed to this repository.
Its owner must revoke it through BotFather and issue a replacement; removing it
from source does not revoke it or remove it from Git history. Never reuse it.

## Timing and limitations

Attendance checks use `Asia/Almaty` time and allow self-marking from 08:00 up to
09:00, excluding weekends and Kazakhstan holidays. The reminder scheduler uses
**the host's local timezone** at 08:00; configure the host to `Asia/Almaty` if
reminders should match attendance hours. On Linux/macOS you can launch with
`TZ=Asia/Almaty python bot.py` instead. The bot must remain running for reminders.
Attendance is currently keyed by weekday, not date: it is not a long-term daily
attendance archive. JSON storage is not designed for multiple bot processes.

## Troubleshooting

- `No module named telebot` (or another dependency): activate `.venv`, then run
  `python -m pip install -r requirements.txt` with the same interpreter.
- `ensurepip is not available` when creating the environment: install the
  Python 3.12 `venv` package for your OS, then recreate `.venv`.
- `Set TELEGRAM_BOT_TOKEN ...`: export the token in the shell running the bot.
- Invalid token / Telegram 401: replace the placeholder with a fresh BotFather
  token. The offline tests do not validate real credentials.
- Telegram polling conflict: stop other processes using the same token; use a
  dedicated new bot for testing, not the existing class bot.
- Rejected by `/start`: check your Telegram username against `allowed_users`.
- JSON decode error: stop the bot and repair the local JSON syntax or restore a
  backup. Do not overwrite an existing attendance database with the example.

See [the setup audit](docs/setup-audit.md) for observed failures, fixes, and
verification boundaries.
