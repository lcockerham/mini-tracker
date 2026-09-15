# D&D 3e catalog enrichment exceptions

Started: 2026-09-04

Baseline inventory: 125 D&D 3e records. No records contained a product URL or
were marked as digitally owned when this pass began.

Pass result: 55 exact official 3e/3.0 matches were enriched with a DMsGuild URL
and local cover. None displayed the `You own this title` banner. The 70 records
below remain unchanged: 28 have an edition/classification conflict and 42 had no
matching official product in the DMsGuild search results.

**2026-09-07 update:** The D&D 3e/3.5e split was collapsed — WotC's own DMsGuild
storefront doesn't consistently distinguish "3e" from "3.5e" for reprints (many
3.0 books are tagged 3.5 and vice versa), which is exactly what was causing
every "Metadata conflict" row below. Rather than keep chasing that distinction,
the `D&D 3.5e` game system was removed and all 73 records that were filed under
it got moved into `D&D 3e`, merging the two exception reports into this one.
The 28 conflicts that already lived in this report, plus the 9 that came over
from the old `dnd-3-5e-catalog-exceptions.md` (now deleted), are marked
Resolved below — each was enriched with the DMsGuild product ID cited in its
evidence, and its cover was downloaded to `app/static/images/books/`. The three
former 3.5e "Listing unavailable" rows (Dungeons & Dragons Basic Game
2004/2006, Dungeons & Dragons Player's Kit) are appended at the bottom, unchanged
except for now being D&D 3e records.

**2026-09-11 update:** A second search pass (re-checking every remaining
"Listing unavailable" row) found 33 more official DMsGuild matches, confirmed
against each product page individually. All 33 are now enriched with a
DriveThruRPG URL and a downloaded cover in `mini_tracker.db` /
`app/static/images/books/`, moved to Resolved below.

Two of those needed a correction: the URLs added to this doc for **672**
(`.../dungeon-master-s-guide-ii-3-5`, product 25841) and **674**
(`.../monster-manual-iii-3-5`, product 25927) point to the sequel supplements
*Dungeon Master's Guide II* and *Monster Manual III* — different books, not the
"Core Rulebook" this catalog's title refers to. Enriched instead with the
plain 3.5 reprints that actually match: **DMG** (product 149132) and **Monster
Manual** (product 148765).

Also re-verified and found genuinely wrong: **673** (Dungeons & Dragons
Adventure Game, product 284581) is a 2021, 5e-era "D&D Basic" boxed product —
not a match for the 3e-era record. Left in Open below rather than enriched.

## Open (13)

| Book ID | Title | Category | Evidence | Required next action | Status |
| ---: | --- | --- | --- | --- | --- |
| 600 | Fantastic Locations: City of Peril | Listing unavailable | The exact-title DMsGuild search returned no matching product; the only similarly named result was the unrelated City of Stormreach. | Confirm whether an official DMsGuild listing exists or leave the record without a cover and URL. | Open | physical only
| 601 | Fantastic Locations: Dragondown Grotto | Listing unavailable | The exact-title DMsGuild search returned no product result. | Confirm whether an official DMsGuild listing exists or leave the record without a cover and URL. | Open | physical only
| 605 | Fantastic Locations: The Frostfell Rift | Listing unavailable | The exact-title DMsGuild search returned no product result. | Confirm whether an official DMsGuild listing exists or leave the record without a cover and URL. | Open | physical only
| 621 | March of the Sane | Listing unavailable | Re-checked 2026-09-11: still no listing — appears to be a free WotC web adventure never sold on DMsGuild. | User marked "Remove from collection" — awaiting confirmation before deleting the record. | Open | Remove from collection (not yet actioned)
| 624 | Primrose Path | Listing unavailable | Re-checked 2026-09-11: still no listing found. | User marked "Remove from collection" — awaiting confirmation before deleting the record. | Open | Remove from collection (not yet actioned)
| 627 | Return to the Temple of the Frog | Listing unavailable | Re-checked 2026-09-11: still no listing — appears to have been a free WotC download, never re-released for sale. | User marked "Remove from collection" — awaiting confirmation before deleting the record. | Open | Remove from collection (not yet actioned)
| 648 | The Last Breaths of Ashenport | Listing unavailable | Re-checked 2026-09-11: no standalone 3e/3.5e listing found (only bundled in 4e's Dungeon #156). | User marked "Remove" — awaiting confirmation before deleting the record. | Open | Remove (not yet actioned)
| 673 | Dungeons & Dragons Adventure Game | Edition mismatch | The only DMsGuild product with this exact title (284581) is a 2021 5e-era "D&D Basic" boxed set, not the 3e-era record in this catalog. | Confirm whether the 3e original was ever sold on DMsGuild under a different title, or leave without a cover and URL. | Open |
| 935 | Cormyr | Listing unavailable / ambiguous | Only the AD&D 2e "Cormyr" sourcebook (product 16843) carries this exact title; the 3.5-era Forgotten Realms book is a differently-titled adventure, "Cormyr: The Tearing of the Weave" (product 57149) — not the same book. | User asked: is this record supposed to be Cormyr: The Tearing of the Weave, or the 2e Cormyr sourcebook? Still awaiting an answer. | Open | Is this supposed to be Cormyr the Tearing of the Weave? Or the 2e Cormyr sourcebook
| 521 | Dungeons & Dragons Basic Game (2006) | Listing unavailable | No DMsGuild listing found; physical-only boxed game, never digitized. | User marked "duplicate" — awaiting confirmation of which record (520 vs. 521) to keep before deleting. | Open | duplicate (not yet actioned)

Two more rows kept a cover image even though no DMsGuild/DriveThruRPG listing
exists, since the game was never sold digitally:

| Book ID | Title | Category | Evidence | Required next action | Status |
| ---: | --- | --- | --- | --- | --- |
| 520 | Dungeons & Dragons Basic Game (2004) | Listing unavailable | Physical-only boxed game, never digitized. Cover downloaded 2026-09-11 from Wikipedia (`File:DnDStarter2004.jpg`, low-res fair-use box art) since no DMsGuild listing exists. | None — cover enriched; no DriveThruRPG URL applies. | Cover only — enriched in mini_tracker.db 2026-09-11 |
| 522 | Dungeons & Dragons Player's Kit | Listing unavailable | Physical-only boxed set, never digitized. Cover captured 2026-09-11 from the Noble Knight Games listing the user linked (a retailer, not DriveThruRPG). | None — cover enriched; no DriveThruRPG URL applies. | Cover only — enriched in mini_tracker.db 2026-09-11 |

## Resolved (71)

| Book ID | Title | Category | Evidence | Required next action | Status |
| ---: | --- | --- | --- | --- | --- |
| 575 | A Dark and Stormy Knight | Metadata conflict | The exact DMsGuild result is product 169621, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 581 | Bad Light | Metadata conflict | The exact DMsGuild result is product 173435, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 582 | Bad Moon Waning | Metadata conflict | The exact DMsGuild result is product 182423, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 583 | Barrow of the Forgotten King | Metadata conflict | The exact DMsGuild result is product 54287 (DD1), explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 587 | Cave of the Spiders | Metadata conflict | The exact DMsGuild result is product 181421, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 591 | Dry Spell | Metadata conflict | The exact DMsGuild result is product 171885, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 597 | Fait Accompli | Metadata conflict | The exact DMsGuild result is product 185360, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 602 | Fantastic Locations: Fane of the Drow | Metadata conflict | The exact DMsGuild result is product 187858, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 603 | Fantastic Locations: Fields of Ruin | Metadata conflict | The exact DMsGuild result is product 187867, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 604 | Fantastic Locations: Hellspike Prison | Metadata conflict | The exact DMsGuild result is product 187862, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 606 | Force of Nature | Metadata conflict | The exact DMsGuild result is product 189494, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 608 | Frozen Whispers | Metadata conflict | The exact DMsGuild result is product 171886, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 610 | Hasken's Manor | Metadata conflict | The exact DMsGuild result is product 178244, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 617 | Lest Darkness Rise | Metadata conflict | The exact DMsGuild result is product 178604, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 618 | Lochfell's Secret | Metadata conflict | The exact DMsGuild result is product 188405, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 631 | Shadows of the Last War | Metadata conflict | The exact DMsGuild result is product 3739, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 632 | Sheep's Clothing | Metadata conflict | The exact DMsGuild result is product 185359, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 635 | Something's Cooking | Metadata conflict | The exact DMsGuild result is product 170093, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 638 | Tarus's Banquet! | Metadata conflict | The exact DMsGuild result is product 183603, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 644 | The Eye of the Sun | Metadata conflict | The exact DMsGuild result is product 174200, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 652 | The Shattered Gates of Slaughtergarde | Metadata conflict | The exact DMsGuild result is product 54405, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 658 | The Thunder Below | Metadata conflict | The exact DMsGuild result is product 189492, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 665 | Tomb of Horrors | Metadata conflict | The matching revised adventure is DMsGuild product 169623, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 666 | Tower in the Ice | Metadata conflict | The exact DMsGuild result is product 181423, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 667 | Voyage of the Golden Dragon | Metadata conflict | The exact DMsGuild result is product 29618, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 670 | White Plume Mountain | Metadata conflict | The matching revised adventure is DMsGuild product 170094, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 671 | Wreck Ashore | Metadata conflict | The exact DMsGuild result is product 170092, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 934 | City of Splendors: Waterdeep | Metadata conflict | The exact DMsGuild result is product 25995, explicitly labeled 3.5, while this collection record is filed under D&D 3e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 527 | Dungeonscape | Metadata conflict | Merged in from the former D&D 3.5e report. The exact DMsGuild result is product 54309, explicitly labeled 3e, while this collection record was filed under D&D 3.5e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 529 | Ghostwalk | Metadata conflict | Merged in from the former D&D 3.5e report. The exact DMsGuild result is product 169140, explicitly labeled 3e, while this collection record was filed under D&D 3.5e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 530 | Sandstorm | Metadata conflict | Merged in from the former D&D 3.5e report. The exact DMsGuild result is product 28493, explicitly labeled 3e, while this collection record was filed under D&D 3.5e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 531 | Stormwrack | Metadata conflict | Merged in from the former D&D 3.5e report. The exact DMsGuild result is product 28313, explicitly labeled 3e, while this collection record was filed under D&D 3.5e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 532 | Arms and Equipment Guide | Metadata conflict | Merged in from the former D&D 3.5e report. The exact DMsGuild result is product 3726, explicitly labeled 3e, while this collection record was filed under D&D 3.5e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 549 | Fiend Folio | Metadata conflict | Merged in from the former D&D 3.5e report. The exact DMsGuild result is product 1751, explicitly labeled 3e, while this collection record was filed under D&D 3.5e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 552 | Heroes of Battle | Metadata conflict | Merged in from the former D&D 3.5e report. The exact DMsGuild result is product 3732, explicitly labeled 3e, while this collection record was filed under D&D 3.5e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 569 | Savage Species | Metadata conflict | Merged in from the former D&D 3.5e report. The exact DMsGuild result is product 25108, explicitly labeled 3e, while this collection record was filed under D&D 3.5e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 936 | Faiths and Pantheons | Metadata conflict | Merged in from the former D&D 3.5e report. The exact DMsGuild result is product 28544, explicitly labeled 3e, while this collection record was filed under D&D 3.5e. | None — enriched with the cited DMsGuild product now that 3e/3.5e are one category. | Resolved — enriched in mini_tracker.db 2026-09-07 |
| 594 | Expedition to the Demonweb Pits | Listing unavailable | Confirmed DMsGuild product 54341, "Expedition to the Demonweb Pits (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 595 | Expedition to the Ruins of Greyhawk | Listing unavailable | Confirmed DMsGuild product 54342, "Expedition to the Ruins of Castle Greyhawk (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 596 | Eyes of the Lich Queen | Listing unavailable | Confirmed DMsGuild product 54343, "EBERRON: Eyes of the Lich Queen (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 607 | Fortress of the Yuan-Ti | Listing unavailable | Confirmed DMsGuild product 54388, "DD3 Fortress of the Yuan-Ti (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 609 | Grasp of the Emerald Claw | Listing unavailable | Confirmed DMsGuild product 28587, "EBERRON: Grasp of the Emerald Claw (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 614 | Ill Wind in Friezford | Listing unavailable | Confirmed DMsGuild product 187771, "Ill Wind in Friezford (3.0)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 616 | Legend of the Silver Skeleton | Listing unavailable | Confirmed DMsGuild product 177395, "Legend of the Silver Skeleton (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 625 | Red Hand of Doom | Listing unavailable | Confirmed DMsGuild product 28797, "Red Hand of Doom (3e)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 626 | Return to the Temple of Elemental Evil | Listing unavailable | Confirmed DMsGuild product 28447, "Return to the Temple of Elemental Evil (3e)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 628 | Road to Oblivion | Listing unavailable | Confirmed DMsGuild product 184752, "Road to Oblivion (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 629 | Scourge of the Howling Horde | Listing unavailable | Confirmed DMsGuild product 54393, "Scourge of the Howling Horde (3e)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 634 | Shrine of the Feathered Serpent | Listing unavailable | Confirmed DMsGuild product 186460, "Shrine of the Feathered Serpent (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 641 | The Burning Plague | Listing unavailable | Confirmed DMsGuild product 169622, "The Burning Plague (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 642 | The Crumbling Hall of the Frost Giant Jarl | Listing unavailable | Confirmed DMsGuild product 183191, "The Crumbling Hall of the Frost Giant Jarl (3.0)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 649 | The Ministry of Winds | Listing unavailable | Confirmed DMsGuild product 177396, "The Ministry of Winds (3.0)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 651 | The Secret of the Windswept Wall | Listing unavailable | Confirmed DMsGuild product 170941, "The Secret of the Windswept Wall (3.0)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 653 | The Sinister Spire | Listing unavailable | Confirmed DMsGuild product 50001, "DD2 The Sinister Spire (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 659 | The Tower of Deception | Listing unavailable | Confirmed DMsGuild product 181981, "The Tower of Deception (3.0)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 660 | The Treasure of the Black Veils | Listing unavailable | Confirmed DMsGuild product 178792, "The Treasure of the Black Veils (3.0)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 661 | The Vessel of Stars | Listing unavailable | Confirmed DMsGuild product 174202, "The Vessel of Stars (3.0)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 664 | To Quell the Rising Storm | Listing unavailable | Confirmed DMsGuild product 184122, "To Quell the Rising Storm (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 668 | War of Dragons | Listing unavailable | Confirmed DMsGuild product 189669, "War of Dragons (3.5)". A same-named unrelated 5e product also exists on DMsGuild — do not confuse. | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 669 | Whispers of the Vampire's Blade | Listing unavailable | Confirmed DMsGuild product 28712, "EBERRON: Whispers of the Vampire's Blade (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 672 | Dungeon Master's Guide: Core Rulebook II | Listing unavailable | Only the 3.5-revised DMG exists on DMsGuild (product 149132, "Dungeon Master's Guide (3.5)") — the original 3.0 printing isn't sold separately. Note: product 25841 ("Dungeon Master's Guide II") is a different, unrelated sequel book — do not confuse. | None — enriched with product 149132. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 674 | Monster Manual: Core Rulebook III | Listing unavailable | Only the 3.5-revised Monster Manual exists on DMsGuild (product 148765, "Monster Manual (3.5)") — the original 3.0 printing isn't sold separately. Note: product 25927 ("Monster Manual III") is a different, unrelated sequel book — do not confuse. | None — enriched with product 148765. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 675 | Player's Handbook: Core Rulebook I | Listing unavailable | Confirmed DMsGuild product 148008, "Player's Handbook (3.5)" — the original 3.0 printing isn't sold separately. | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 677 | Manual of the Planes | Listing unavailable | Confirmed DMsGuild product 25109, "Manual of the Planes (3e)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 680 | Book of Vile Darkness | Listing unavailable | Confirmed DMsGuild product 3723, "Book of Vile Darkness (3e)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 681 | Defenders of the Faith | Listing unavailable | Confirmed DMsGuild product 3725, "Defenders of the Faith: A Guidebook to Clerics and Paladins (3e)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 688 | Psionics Handbook | Listing unavailable | Only the Expanded (2004) revision exists on DMsGuild (product 25857) — the original 2001 Psionics Handbook isn't sold separately. | None — enriched with product 25857. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 921 | The Grand History of the Realms | Metadata conflict | Merged in from the D&D 4e report. The exact matching official listing is `Grand History of the Realms (3.5)`, product 51644 — this collection record was filed under D&D 4e. | None — moved to D&D 3e and enriched with the cited DMsGuild product. | Resolved — moved and enriched in mini_tracker.db 2026-09-14 |
| 938 | Magic of Faerun | Listing unavailable | Confirmed DMsGuild product 3731, "Magic of Faerûn (3e)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 941 | Races of Faerun | Listing unavailable | Confirmed DMsGuild product 25986, "Races of Faerûn (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |
| 945 | Unapproachable East | Listing unavailable | Confirmed DMsGuild product 28722, "Unapproachable East (3.5)". | None — enriched with the cited DMsGuild product. | Resolved — enriched in mini_tracker.db 2026-09-11 |

Only unresolved or materially noteworthy exceptions belong in this table.
Completed records are reported through the collection itself and the batch
summary, not duplicated here.
