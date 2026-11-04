# mini-tracker

A personal tracker for an RPG miniatures collection, built with FastAPI, SQLAlchemy (SQLite) and Jinja2 templates. It tracks minis (painted, unpainted, pre-painted), paints and which minis they were used on, photos, a wishlist, Dwarven Forge terrain, RPG books and maps, with a dashboard of charts. Collections can be imported from an `.xlsx` spreadsheet.

> **No authentication or CSRF protection — run on 127.0.0.1 only; don't expose it to a network.**

## Running locally

Requires Python 3.12 (the version CI uses).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload    # binds to 127.0.0.1:8000 by default
```

Open http://127.0.0.1:8000. The SQLite database (`mini_tracker.db`) is created in the working directory on first run and is gitignored.

Lint and test with `make lint` and `make test`.

## Catalog sync

`make sync-minis` (or monthly via launchd, `make install-sync-schedule`) crawls the public Icons of the Realms / Onslaught catalog pages on minisgallery.com and queues WizKids minis that aren't in the collection yet for review at `/minis/review`. Nothing is added until approved. The crawler is polite: it sends an identifying User-Agent (`mini-tracker/1.0 (personal collection sync)`) and waits about a second between requests.

## License

MIT — see [LICENSE](LICENSE).
