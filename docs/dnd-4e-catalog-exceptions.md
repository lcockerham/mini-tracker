# D&D 4e catalog enrichment exceptions

Started: 2026-09-04

Baseline inventory: 127 D&D 4e records. No records contained a product URL or
were marked as digitally owned when this pass began.

Completed: 2026-09-04

Result: 114 records enriched with a verified DMsGuild product URL and cover;
none displayed the signed-in `You own this title` banner. For adventures
published only as part of a Dungeon issue, rulebook, or boxed kit, the
official containing product and its cover were used. Thirteen records remained
unresolved.

**2026-09-14 update:** Two of the thirteen were resolved with links the user
supplied; the other eleven had no path to resolution and were removed from the
catalog outright (not just this tracker) rather than left open indefinitely.

## Open (0)

None.

## Resolved (2)

| Book ID | Title | Category | Evidence | Required next action | Status |
| ---: | --- | --- | --- | --- | --- |
| 753 | Dungeons & Dragons Fantasy Roleplaying Game Starter Set (Red box cover) | Listing unavailable | User-supplied DriveThruRPG product 157081, "Dungeons & Dragons Starter Set (4e)". | None — enriched with the cited DriveThruRPG product. | Resolved — enriched in mini_tracker.db 2026-09-14 |
| 921 | The Grand History of the Realms | Metadata conflict | User-supplied DMsGuild product 51644, "Grand History of the Realms (3.5)". | None — moved to D&D 3e (game_system_id 10) and enriched with the cited DMsGuild product. | Resolved — moved and enriched in mini_tracker.db 2026-09-14 |

## Removed from catalog (2026-09-14)

The following eleven records had no identifiable official product after
repeated searches and no further path to resolution, so they were deleted
from `mini_tracker.db` rather than kept open: 696 (Beneath the Dust), 710
(Hidden Destinies), 732 (Shards of Selune), 739 (The Lost Mines of Karak), 754
(Dungeons & Dragons Roleplaying Game Starter Set, Blue box cover), 767
(Devilspawn), 768 (Map Pack), 769 (The Kroten Adventures), 770 (The Kroten
Campaign Companion), 771 (The Kroten Campaign Guide), 772 (The Lendore Isle
Companion).

Only unresolved or materially noteworthy exceptions belong in this table.
