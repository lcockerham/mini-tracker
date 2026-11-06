# mini-tracker project notes

## Security: read first (added 2026-11-03)

- **No version pins or lockfile.** Add a lock or constraints file before relying on this further. The `.venv` was hand-patched on 2026-11-03 for certifi and Pillow CVEs (certifi 2026.10.23, pillow 13.0.0); a fresh `pip install -r requirements.txt` gives no such guarantee.
- **The FastAPI app has no auth and accepts `.xlsx` uploads** (parsed by openpyxl, which uses Pillow). Never run uvicorn with `--host 0.0.0.0`; keep it on `127.0.0.1`.
- **CI hardening:** all workflows set `permissions: contents: read`, and every action is pinned by commit SHA. Dependabot's `github-actions` config bumps the pins weekly.

## Database backups

Before any significant change to `mini_tracker.db` (bulk imports, schema/migration changes, scripted data cleanup, or anything else that writes to many rows at once), copy it to `backups/mini_tracker.<timestamp>.db` first, e.g.:

```bash
mkdir -p backups
cp mini_tracker.db "backups/mini_tracker.$(date +%Y%m%d%H%M%S).db"
```

Keep at most 3 backups. After creating a new one, delete the oldest until only 3 remain:

```bash
/bin/ls -1t backups/*.db | tail -n +4 | xargs -r rm
```

(Use `/bin/ls`, not the `eza`-aliased `ls` — `ls -1t` isn't valid eza syntax and errors out.)

Routine single-record edits through the app's normal CRUD routes don't need a backup — this is for anything that could clobber or corrupt a meaningful chunk of the collection in one shot.

## Security review before PRs

Run `/security-review` on the branch before opening any PR, and fix (or explain in the PR description) anything it reports. Mention in the PR's test plan that it ran and what it found. This app pulls in text and URLs from outside sites (Minis Gallery, Dwarven Forge) and renders them, which is where past issues came from (e.g. `javascript:` links in `source_url` fields).
