# AD&D 1e catalog enrichment exceptions

Started: 2026-09-04
Completed: 2026-09-04
Reclassified: 2026-09-05

Baseline inventory: 216 AD&D 1e records. No records contained a product URL or
were marked as digitally owned when this pass began.

Result: 113 records were enriched with a verified DMsGuild product URL and
cover; none displayed the signed-in `You own this title` banner. A later system
audit moved 56 Basic/BECMI records to D&D Basic, 24 Expert-set records to D&D
Expert, and four original Monster & Treasure Assortment records to OD&D.
Midnight on Dagger Alley remains under AD&D 1e because it is an AD&D product.
The follow-up DMsGuild pass enriched 80 of the 84 moved records; the four
unresolved records now appear in the D&D Basic exception report.

The split follows the published product lines: Basic and B-series material plus
the wider BECMI line are filed under D&D Basic; Expert rules, X-series, O-series,
and DA-series adventures are filed under D&D Expert.

The remaining 19 records have no confidently identifiable standalone listing.

**2026-09-07 update:** Cross-referenced all 19 records against Shannon Appelcline's
*Designers & Dragons: Origins, Vol. 1*, a publishing history of TSR/D&D. It
independently confirms why 15 of the 19 have no DMsGuild listing — four RPGA
tournament modules were never actually published, five more were only ever
published as Polyhedron newszine articles rather than standalone TSR products,
and six more are confirmed-legitimate official TSR products (with catalog
codes) whose print-only tournament-module runs were apparently never digitized.
Only Quest for the Fazzlewood is not mentioned in the book at all.

**2026-09-07 removal:** Nine of these records were never an actual purchasable
product — four (Air Plane!, Dwarven Quest for the Rod of Seven Parts, Tinker's
Canyon, Yog's Dessert) were planned RPGA modules that TSR never published at
all, and five more (And the Gods Will Have Their Way, Bigby's Tomb, Great
Bugbear Hunt, Incants of Ishcabeble, Riddle of Dolmen Moor) only ever existed
as Polyhedron newszine articles, not standalone TSR releases. Since they don't
represent a book/module the collection can actually own, all nine were deleted
from `mini_tracker.db` after a backup (see `backups/`). The rows below are kept
for the audit trail but the underlying Book records no longer exist.

## Open (3)

| Book ID | Title | Category | Evidence | Required next action | Status |
| ---: | --- | --- | --- | --- | --- |
| 101 | Queen of the Spiders | Confirmed reprint compilation | *Designers & Dragons: Origins, Vol. 1* confirms this is the 1986/1987 supermodule "GDQ1-7: Queen of the Spiders," a reprint of older TSR modules, matching the earlier DMsGuild search finding. | Recheck if an official listing is added, restored, or link to the individual GDQ modules. | Open |
| 102 | Quest for the Fazzlewood | Listing unavailable | Not mentioned in *Designers & Dragons: Origins, Vol. 1*; exact and simplified signed-in DMsGuild searches found no confidently matching standalone product. | Recheck if an official listing is added, restored, or the containing publication is identified. | Open |
| 114 | Scourge of the Slave Lords | Confirmed reprint compilation | *Designers & Dragons: Origins, Vol. 1* confirms this is the 1986 supermodule "A1-4: Scourge of the Slavelords," a reprint of older TSR modules, matching the earlier DMsGuild search finding. | Recheck if an official listing is added, restored, or link to the individual A-series modules. | Open |

## Resolved (16)

| Book ID | Title | Category | Evidence | Required next action | Status |
| ---: | --- | --- | --- | --- | --- |
| 15 | Air Plane! | Never published | *Designers & Dragons: Origins, Vol. 1* confirms "R10: Air Plane!" was one of four planned Mentzer RPGA tournament modules (R7-R10) that "have never been published, and so remain a holy grail for D&D enthusiasts." | None — no product exists to list. | Removed from collection (2026-09-07) |
| 17 | And the Gods Will Have Their Way | Polyhedron serial, not a standalone product | *Designers & Dragons: Origins, Vol. 1* identifies this as "...And the Gods Will Have Their Way" in Polyhedron #19 (1984), part of a four-part RPGA tournament series later collected as C5: The Bane of Llywelyn (1985). | Consider retitling/relinking this record to C5: The Bane of Llywelyn if the collection wants a purchasable product; otherwise leave as a magazine credit with no DMsGuild listing. | Removed from collection (2026-09-07) |
| 21 | Bigby's Tomb | Never published under this title; later ran as a Polyhedron serial | *Designers & Dragons: Origins, Vol. 1* says Mentzer's "Bigby's Tomb" replaced the planned RPGA module "R6," but was itself never published as a module — it later appeared as "384th Incarnation of Bigby's Tomb" in Polyhedron #20 (1984). | None — no standalone product exists to list. | Removed from collection (2026-09-07) |
| 32 | Conan Against Darkness! | Confirmed legitimate product, code CB2 | *Designers & Dragons: Origins, Vol. 1*'s index confirms this is the official 1984 TSR module "CB2: Conan: Against Darkness!" A DMsGuild keyword search on 2026-09-07 confirms no listing exists, consistent with Conan being a licensed Robert E. Howard property, not TSR's own IP. | None expected — the Conan license is probably why no listing exists. | Resolved (no listing found; licensed IP) |
| 33 | Conan Unchained! | Confirmed legitimate product, code CB1 | *Designers & Dragons: Origins, Vol. 1* references "CB1: Conan: Unchained!" (1984) as the official TSR module. A DMsGuild keyword search on 2026-09-07 confirms no listing exists, consistent with Conan being a licensed Robert E. Howard property, not TSR's own IP. | None expected — the Conan license is probably why no listing exists. | Resolved (no listing found; licensed IP) |
| 60 | Dwarven Quest for the Rod of Seven Parts | Never published | *Designers & Dragons: Origins, Vol. 1* confirms "R7: 'Dwarven' Quest for the Rod of Seven Parts" was one of four planned Mentzer RPGA tournament modules (R7-R10) that "have never been published." | None — no product exists to list. | Removed from collection (2026-09-07) |
| 69 | Great Bugbear Hunt | Never published as a standalone module; later ran as a Polyhedron serial | *Designers & Dragons: Origins, Vol. 1* says "R5: The Great Bugbear Hunt" ran as a tournament at Gen Con South V (1982) but was never published as a module — it later appeared as "The Great Bugbear Hunt" in Polyhedron #28 (1985). | None — no standalone product exists to list. | Removed from collection (2026-09-07) |
| 75 | Incants of Ishcabeble | Polyhedron serial, not a standalone product | *Designers & Dragons: Origins, Vol. 1* identifies this as "The Incants of Ishcabeble" in Polyhedron #17 (1984), part of the same four-part series as record 17, later collected as C5: The Bane of Llywelyn (1985). | Consider retitling/relinking to C5: The Bane of Llywelyn if a purchasable product is wanted. | Removed from collection (2026-09-07) |
| 87 | Midnight on Dagger Alley | Confirmed legitimate product, code MV1 | *Designers & Dragons: Origins, Vol. 1*'s index confirms this is the official 1984 TSR module "MV1: Midnight on Dagger Alley." A DMsGuild keyword search on 2026-09-07 confirms no listing exists. | Recheck periodically if an official listing is added or restored. | Resolved (no listing found) |
| 110 | Red Sonja Unconquered | Confirmed legitimate product, code RS1 | *Designers & Dragons: Origins, Vol. 1*'s index confirms this is the official 1986 TSR module "RS1: Red Sonja Unconquered." A DMsGuild keyword search on 2026-09-07 confirms no listing exists, consistent with Red Sonja being a licensed property, not TSR's own IP. | None expected — the Red Sonja license is probably why no listing exists. | Resolved (no listing found; licensed IP) |
| 111 | Riddle of Dolmen Moor | Polyhedron serial, not a standalone product | *Designers & Dragons: Origins, Vol. 1* identifies this as "The Riddle of Dolmen Moor" in Polyhedron #16 (1983), the first installment of the same series as records 17 and 75, later collected as C5: The Bane of Llywelyn (1985). | Consider retitling/relinking to C5: The Bane of Llywelyn if a purchasable product is wanted. | Removed from collection (2026-09-07) |
| 120 | Swords of Deceit | Confirmed legitimate product, code CA2 | *Designers & Dragons: Origins, Vol. 1*'s index confirms this is the official 1986 TSR module "CA2: Swords Of Deceit." A DMsGuild keyword search on 2026-09-07 confirms no listing exists. | Recheck periodically if an official listing is added or restored. | Resolved (no listing found) |
| 123 | Swords of the Undercity | Confirmed legitimate product, code CA1 | *Designers & Dragons: Origins, Vol. 1*'s index confirms this is the official 1985 TSR module "CA1: Swords of the Undercity." A DMsGuild keyword search on 2026-09-07 confirms no listing exists. | Recheck periodically if an official listing is added or restored. | Resolved (no listing found) |
| 181 | Tinker's Canyon | Never published | *Designers & Dragons: Origins, Vol. 1* confirms "R9: Tinker's Canyon" was one of four planned Mentzer RPGA tournament modules (R7-R10) that "have never been published." | None — no product exists to list. | Removed from collection (2026-09-07) |
| 189 | Up the Garden Path | Confirmed legitimate product, code ST1 | *Designers & Dragons: Origins, Vol. 1*'s index confirms this is the official 1986 TSR module "ST1: Up the Garden Path." A DMsGuild keyword search on 2026-09-07 confirms no listing exists. | Recheck periodically if an official listing is added or restored. | Resolved (no listing found) |
| 196 | Yog's Dessert | Never published | *Designers & Dragons: Origins, Vol. 1* confirms "R8: Yog's Dessert" was one of four planned Mentzer RPGA tournament modules (R7-R10) that "have never been published." | None — no product exists to list. | Removed from collection (2026-09-07) |

Only unresolved or materially noteworthy exceptions belong in this table.
