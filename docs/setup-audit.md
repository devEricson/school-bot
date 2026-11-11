# Clean setup audit — 2026-11-11

Baseline: commit `0939465`, on Linux with Python 3.12.3 and Git already installed.
No project setup command was configured or run by the workspace. A fresh
virtual environment was used to avoid relying on globally installed packages.
This was not a newly provisioned OS; OS package installation was not rehearsed.

There was no README or setup documentation to follow. The tracked repository
contained `bot.py`, `class_db.json`, and a CPython 3.14 bytecode file only.
The following records the attempted path and the missing steps rather than
claiming an existing documented sequence succeeded.

| Step / inspection | Observation | Resolution |
| --- | --- | --- |
| Find README/setup instructions | No instructions, prerequisite versions, or launch command existed. | Added root README with clone, prerequisites, environment, install, test, and launch steps. |
| Create a fresh Python 3.12 virtual environment | Succeeded. | Documented isolated environment creation and activation. |
| Run `python bot.py` in that environment | Failed immediately: `ModuleNotFoundError: No module named 'telebot'`. No dependency manifest existed. | Added pinned direct dependencies for all four third-party imports; documented the distribution/import name difference. |
| Inspect startup configuration | Token embedded in source; no safe newcomer credential setup. | Read `TELEGRAM_BOT_TOKEN` from the environment and fail with an actionable message when absent. Documented mandatory rotation of the historical token. |
| Inspect class/admin bootstrap | Existing class data and fallback roster, hard-coded administrators and suggestion recipients; no new-class instructions. | Added synthetic database example, ignored local database, empty fallback, configurable admin names and IDs, and registration instructions. Existing `class_db.json` is left unchanged. |
| Find build/test procedure | No tests or test command; tracked bytecode depended on another Python version. | Added five offline smoke tests and compile check instructions; removed tracked bytecode and ignored generated files. |
| Inspect reminder scheduling | Attendance uses Almaty time but scheduler uses host local time. | Documented host timezone requirement and a `TZ=Asia/Almaty` launch command. |
| Inspect persistence expectations | Attendance uses weekday keys rather than dates. | Documented this limitation without expanding the task into a storage redesign. |

## Verification

- Baseline `python -m py_compile bot.py` passed; no baseline syntax failure was
  observed.
- Dependency installation, `pip check`, all five offline tests, and compilation
  passed on Python 3.12.3. The final README sequence was repeated in a separate
  clean directory with a newly created virtual environment.
- Tests cover handler import/registration, calendar dependencies, menu creation,
  isolated JSON persistence, admin configuration, missing-token errors, invalid
  admin-ID errors, and the example database shape.
- Pip emitted a sandbox-specific cache-permission warning and disabled its cache;
  installation still succeeded without elevated permissions.
- Live Telegram polling, message delivery, and timed reminders were **not** run:
  they require a newly issued credential and explicit test accounts. No existing
  credential was used and no real student was contacted.
- Git and Python were preinstalled; macOS and OS package-manager instructions
  were not executed. Dependency installation needs internet; tests run offline
  after installation. Direct dependencies are pinned, not the full transitive
  dependency tree.

## Owner follow-up

Revoke the historical bot token via BotFather. Source removal cannot invalidate
it. Existing student data and historical revisions remain in the repository;
review repository access and data-retention requirements before sharing it.
For an intentional existing deployment, set `DATA_FILE` to its existing database
and explicitly configure its admins; the new defaults isolate fresh setups.
