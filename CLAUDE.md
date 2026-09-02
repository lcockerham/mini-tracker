# mini-tracker project notes

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

## Media backups

Book images live in the gitignored `media/` directory. Database backups preserve
image metadata and associations, but they do not preserve the image files. Back up
`mini_tracker.db` and the entire `media/` directory together to a private location,
and label both with the same timestamp. Restore both parts of the same snapshot so
database paths and content-addressed files stay in sync.

Do not commit media backups. Treat them as private collection data and keep them out
of CI artifacts, releases, screenshots, and documentation.
