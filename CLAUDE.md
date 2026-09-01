# mini-tracker project notes

## Database backups

Before any significant change to `mini_tracker.db` (bulk imports, schema/migration changes, scripted data cleanup, or anything else that writes to many rows at once), copy it to `backups/mini_tracker.<timestamp>.db` first, e.g.:

```bash
mkdir -p backups
cp mini_tracker.db "backups/mini_tracker.$(date +%Y%m%d%H%M%S).db"
```

Keep at most 3 backups. After creating a new one, delete the oldest until only 3 remain:

```bash
ls -1t backups/*.db | tail -n +4 | xargs -r rm
```

Routine single-record edits through the app's normal CRUD routes don't need a backup — this is for anything that could clobber or corrupt a meaningful chunk of the collection in one shot.
