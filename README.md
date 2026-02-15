# This Day (Family Birthday Edition)

A small Flask app that shows a mini calendar (birthdays highlighted) and generates a “This Day” fun-facts page on demand.

## Quick start (local)

```bash
python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows (powershell)
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt

# required for Basic Auth
set APP_USER=you
set APP_PASS=secret
# mac/linux: export APP_USER=you; export APP_PASS=secret

python -m this_day.cli --serve --port 5000
# open http://127.0.0.1:5000
```

## Deploy (Render)

- Web Service
- Build: `pip install -r requirements.txt`
- Start: `gunicorn this_day.app:app`
- Env vars: `APP_USER`, `APP_PASS`
- Optional env vars:
  - `BIRTHDAYS_FILE` (default `birthdays.json` in repo root)
  - `CACHE_DIR` (default `.cache_this_day`)
  - `PAGE_TITLE`, `PAGE_SUBTITLE`
  - `SPORTS_KEYWORDS`, `ROCK_KEYWORDS`

## Static export

```bash
python -m this_day.cli --date 12-18 --out this_day.html --show
```

(Without `--show`, export keeps “facts” hidden behind the Generate button.)
