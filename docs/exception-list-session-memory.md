# Exception-list session memory

Updated: 2026-09-10

## Tomorrow's objective

Continue resolving the book catalog exception lists. The working pattern is for
the collection owner to add a URL or correction beside an open row, then:

1. Verify the supplied product is the exact title, edition, publisher, and
   module/product code.
2. Save the canonical DMsGuild URL without search-query parameters.
3. Check the signed-in product page for the exact `You own this title` banner.
4. Save the full-size cover under `app/static/images/books/<book-id>.webp` (or
   another supported image extension).
5. Update or remove the database record as directed.
6. Move the exception row from Open to Resolved and update the section counts
   and report summary.
7. Verify the database, image, and local detail-page rendering. Back up the
   database before multi-record updates.

Do not infer ownership from a listing, cart, or library link; only the explicit
signed-in ownership banner is authoritative. Do not guess when a title,
edition, or product-code match is ambiguous.

## Current exception counts

| Report | Open |
| --- | ---: |
| AD&D 1e | 0 |
| AD&D 2e | 17 |
| D&D 3e/3.5e | 45 |
| D&D 4e | 13 |
| D&D 5e | 25 |
| D&D Basic/Expert | 4 |
| OD&D | 1 |

## AD&D 1e completed this session

All AD&D 1e exceptions are resolved. The report is
`docs/adnd-1e-catalog-exceptions.md` and is included in the handoff commit.

- Book 101, *Queen of the Spiders*: canonical URL saved as
  `https://www.dmsguild.com/en/product/17036/gdq-1-7-queen-of-the-spiders`.
  The full-size 450x568 WebP cover is saved as
  `app/static/images/books/101.webp`. The signed-in page did not show the
  ownership banner, so `owns_digital` remains false.
- Book 114, *Scourge of the Slave Lords*: canonical URL saved as
  `https://www.dmsguild.com/en/product/17362/scourge-of-the-slave-lords`.
  The full-size 569x729 WebP cover is saved as
  `app/static/images/books/114.webp`. The signed-in page did not show the
  ownership banner, so `owns_digital` remains false.
- Book 102, *Quest for the Fazzlewood*, was removed after the owner's review
  identified it as a duplicate/misnamed record for book 147, *The Gem and the
  Staff*. Book 147 remains intact under D&D Expert with code O1 and product
  17085.

The current database has 945 books and 123 AD&D 1e books. `PRAGMA
integrity_check` returned `ok`; all 15 book tests and the books-router lint check
passed. The local detail pages render both new covers.

## AD&D 2e progress this session

Fourteen AD&D 2e exceptions were resolved from owner notes and generalized
catalog rules, reducing the open list from 31 to 17:

- The original-printing Dungeon Master's Guide and Player's Handbook records
  use the owner-approved revised 2e DMsGuild counterparts.
- Moonlight Madness, Slavers, and TSR Jam 1999 use exact stock-code DMsGuild
  matches despite erroneous 1e category badges. None of the five checked
  DMsGuild pages showed the signed-in ownership banner.
- First Quest, Ravenloft: 25th Anniversary, and all seven licensed
  Lankhmar/Nehwon titles are marked physical-only.
- Covers were saved for books 217, 220, 222, 303, 321, 334, and 340. The three
  Lankhmar titles with Wikipedia covers (236, 369, and 387) were saved earlier;
  Wikipedia had no exact cover for the other four.
- DMsGuild 294522 was rejected for book 219 because its description is for
  basic 3rd-edition rules, its category badge says 4e, and it has no matching
  TSR 11450 stock code.

## Backups

- Permanent checkpoint, excluded from rotating cleanup:
  `database-checkpoints/mini_tracker.post-mini-image-enrichment.20260908.db`.
  This predates the three AD&D 1e resolutions above.
- Rotating backup immediately before the AD&D 1e database changes:
  `backups/mini_tracker.20260908221243.db`.
- Rotating backup immediately before the AD&D 2e database changes:
  `backups/mini_tracker.20260909231742.db`.
- The `backups/` directory currently contains four database files because the
  oldest backup was preserved during this session. Its documented target is
  the three newest files. Never apply that cleanup rule to
  `database-checkpoints/`.

## Miniature work completed and merged

PR #13, "Add miniature catalog images and detail navigation," was merged. The
local database contains 6,162 minis and 4,583 photo records. Mini list rows show
small thumbnails; detail pages show a larger image beside the editable data and
have filtered previous/next navigation matching books. Manufacturer-specific
image exceptions are under `docs/*-mini-image-exceptions.md`.

## Git state at handoff

The handoff branch is `fix/adnd-2e-exceptions`, based on `origin/main` at merge
commit `22aaf44`. It contains both updated exception reports and this session
memory. On the Mac mini, fetch the remote and switch to that branch to resume.

The SQLite database, rotating backups, and downloaded book covers are
intentionally ignored by Git and remain only on the source Mac. Copy
`mini_tracker.db` and `app/static/images/books/` separately before continuing
catalog mutations on the Mac mini; the Git branch transfers documentation, not
the updated collection data or cover assets.
