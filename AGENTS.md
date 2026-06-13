# AGENTS.md

## Cursor Cloud specific instructions

This repo is a single-process **Telegram bot** ("eSIM Support Bot", Python 3). There is no web server, no build step, and (currently) no committed automated tests or linter config. See `README.md` for the feature overview and standard run steps.

### Services
- **`python bot.py`** — the only service. It runs via Telegram long-polling (`run_polling`); it does not open a local port. Stop with Ctrl+C.

### Required setup (handled by the update script)
- System libraries `libzbar0`, `libgl1`, `libglib2.0-0` are required by `pyzbar`/`opencv-python`. `pyzbar` is optional at runtime (code falls back to OpenCV's `QRCodeDetector`), but installing `libzbar0` enables the faster/preferred path.
- Python deps: `pip install -r requirements.txt`.
- `config.py` must exist (it is gitignored). Create it once with `cp config.example.py config.py`. `config.py` is imported at module load by `bot.py` and `simplifytrip_api.py`, so missing it breaks all imports.

### Compile checks & unit tests
- `python3`/`pip3` are available system-wide (no install needed). Deps come from `requirements.txt` (installed by the update script).
- Compile check: `python3 -m py_compile bot.py esim_tools.py esim_storage.py simplifytrip_api.py config.example.py`.
- Unit tests: `python3 -m unittest discover -v`. There are currently no committed tests, so this reports "NO TESTS RAN" (exit code 5); the only test file `test_tools.py` is gitignored. New `test_*.py` files are auto-discovered once added.

### Running / testing caveats
- The bot refuses to start unless `BOT_TOKEN` is set to a real value (placeholder `YOUR_BOT_TOKEN_HERE` exits immediately). Provide it via the `BOT_TOKEN` env var (preferred) or by editing `config.py`. A real token from @BotFather is required for any actual Telegram end-to-end test.
- The core eSIM features in `esim_tools.py` (LPA parsing, install-link + QR generation, QR decoding) and the SQLite warehouse in `esim_storage.py` are fully local and can be exercised/tested offline without any token or network — import the module and call its methods directly. This is the best smoke test in a credential-less environment.
- The "Check ICCID" feature (`simplifytrip_api.py`) calls the external SimplifyTrip API and needs `SIMPLIFYTRIP_EMAIL` / `SIMPLIFYTRIP_PASSWORD` (optionally `SIMPLIFYTRIP_PROXY`). Optional; not needed for link/QR/warehouse features.
- Runtime files `esim_storage.db` and `simplifytrip_cookies.json` are created automatically and are gitignored.
