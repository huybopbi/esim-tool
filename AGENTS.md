# AGENTS.md

## Cursor Cloud specific instructions

This repo is a single-process **Telegram bot** ("eSIM Support Bot", Python 3). There is no web server and no build step. See `README.md` for the feature overview, deploy steps, and current user-facing behavior.

### Working rules for future agents
- Read `README.md` and this `AGENTS.md` before changing code.
- Work directly on `master` unless the user explicitly asks for a separate branch or PR.
- After code changes, run the unit tests and compile check listed below.
- If verification passes, commit with a clear message and push directly to `origin/master`.
- Do not create pull requests unless the user explicitly asks.
- Do not create new `.md` files unless the user explicitly asks. Editing existing Markdown files is OK when requested or needed to keep docs accurate.
- SimplifyTrip / Check ICCID has been removed from the bot; do not reintroduce it unless the user explicitly requests a replacement integration.

### Services
- **`python bot.py`** — the only service. It runs via Telegram long-polling (`run_polling`); it does not open a local port. Stop with Ctrl+C.

### Required setup (handled by the update script)
- System libraries `libzbar0`, `libgl1`, `libglib2.0-0` are required by `pyzbar`/`opencv-python`. `pyzbar` is optional at runtime (code falls back to OpenCV's `QRCodeDetector`), but installing `libzbar0` enables the faster/preferred path.
- Python deps: `pip install -r requirements.txt`.
- `config.py` must exist (it is gitignored). Create it once with `cp config.example.py config.py`. `config.py` is imported at module load by `bot.py`, so missing it breaks imports.

### Compile checks & unit tests
- `python3`/`pip3` are available system-wide (no install needed). Deps come from `requirements.txt` (installed by the update script).
- Compile check: `python3 -m py_compile bot.py bot_constants.py bot_handlers.py bot_keyboards.py bot_user_info.py esim_tools.py esim_storage.py config.example.py`.
- Unit tests: `python3 -m unittest discover -s tests -v`.

### Running / testing caveats
- The bot refuses to start unless `BOT_TOKEN` is set to a real value (placeholder `YOUR_BOT_TOKEN_HERE` exits immediately). Provide it via the `BOT_TOKEN` env var (preferred) or by editing `config.py`. A real token from @BotFather is required for any actual Telegram end-to-end test.
- The core eSIM features in `esim_tools.py` (LPA parsing, install-link + QR generation, QR decoding) and the SQLite warehouse in `esim_storage.py` are fully local and can be exercised/tested offline without any token or network — import the module and call its methods directly. This is the best smoke test in a credential-less environment.
- Runtime file `esim_storage.db` is created automatically and is gitignored.
