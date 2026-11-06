# D&D book settings review

Started: 2026-11-05
All 1,236 books classified: 2026-11-05

The `books.setting` field holds one campaign setting per book. Blank means
nobody has classified the book yet. `None` means it was reviewed and has no
setting: it's generic, or its setting is too small to track. When the setting
was unclear, the book was set to `None`.

## How books were classified

1. **Designers & Dragons: Origins, Vols 1-4** (Shannon Appelcline,
   Evil Hat). Each adventure entry has a "Worlds of Adventure" section saying
   where it's set. Those sections were used for OD&D, AD&D 1e and Basic/BECMI
   through Mystara's 2e products. A placement marked "?" or "or Not" in the
   book was treated as unsure, so the book was set to None. A placement TSR
   made official later (such as B1-B9 placed in Karameikos by *B1-9: In Search
   of Adventure*) counts.
2. **DMsGuild world labels.** The 281 AD&D 2e books added from DMsGuild on
   2026-11-05 (ids 1008-1288) have DMsGuild's world filter in `notes`. Those
   labels were used, apart from the overrides listed below.
3. **Product codes and Claude's own knowledge** for everything else, mainly
   2e, 3e, 4e and 5e. Uncertain cases are listed below.

Rules from you:
- Nentir Vale, Ghostwalk, Ravnica, Theros, Strixhaven, Exandria and Radiant
  Citadel are None. Thunder Rift is its own setting.
- Aquaria, Pellham/Celtic and Hyboria are None.
- Rulebooks are None, except the OD&D *Greyhawk* supplement, which is
  Greyhawk.
- Everything Oriental Adventures, including 3e Rokugan (#678), is Kara-Tur.
- Conan modules are None.

Backups:
- `backups/keep/mini_tracker.20261105220301.before-book-settings-batch1.db`
- `backups/keep/mini_tracker.20261105222010.before-book-settings-all.db`
- `backups/keep/mini_tracker.20261106160419.before-thunder-rift.db`

## Result

| Setting | Books | | Setting | Books |
|---|---|---|---|---|
| None | 528 | | Eberron | 27 |
| Forgotten Realms | 185 | | Spelljammer | 21 |
| Mystara | 115 | | Al-Qadim | 14 |
| Greyhawk | 84 | | Kara-Tur | 12 |
| Ravenloft | 71 | | Lankhmar | 9 |
| Dragonlance | 46 | | Historical Reference, Thunder Rift | 7 each |
| Dark Sun | 34 | | Blackmoor | 5 |
| Planescape | 31 | | Maztica | 4 |
| Birthright | 30 | | Council of Wyrms, Feywild, Jakandor | 2 each |

## Open

Nothing open as of 2026-11-06.

## Resolved

- 2026-11-06: your answers to the open questions:
  - Thunder Rift added as a setting. All 7 books moved from None to
    **Thunder Rift**: #435 Thunder Rift, #318 Quest for the Silver Sword,
    #234 Assault on Raven's Ruin, #339 Sword and Shield, #353 The Knight of
    Newts, #319 Rage of the Rakasta, #290 In the Phantom's Wake.
  - Rulebooks stay None (Expert #4, #7; Companion/Master/Immortals #8-10;
    Rules Cyclopedia #224), except the OD&D *Greyhawk* supplement (#903),
    now **Greyhawk**.
  - Aquaria (R1-R3 #183, #152, #136), Pellham/Celtic (C4 #182, C5 #130,
    RPGA3 #144, UK4 #192, I8 #105) and Hyboria (CB1, CB2, RS1 #110) stay None.
  - Everything in the two lists below is confirmed as set.

### Set, and confirmed

| Id | Title | Set to | Why |
|---|---|---|---|
| 1032, 1094, 1095, 1096 | Maztica, Fires of Zatal, Endless Armies, City of Gold | Maztica | DMsGuild says Forgotten Realms. Moved to Maztica, which you kept as a separate setting |
| 1116 | Ninja Wars (FROA1) | Kara-Tur | DMsGuild says Forgotten Realms, but the module is set in Kozakura |
| 1283 | The Horde | Forgotten Realms | DMsGuild says General. It's the FR boxed set for the Endless Waste |
| 1272, 1278, 1279 | Council of Wyrms, Jakandor ×2 | their own settings | DMsGuild says General |
| 213 | The Rogues Gallery | Greyhawk | Designers & Dragons: no explicit Greyhawk references, but many characters come from Greyhawk |
| 31 | AC2 Combat Shield (Treasure of the Hideous One) | Mystara | Designers & Dragons calls the mini-adventure "clearly set in the Known World" |
| 325 | Return to the Tomb of Horrors | Greyhawk | |
| 334 | Slavers | Greyhawk | Sequel to the Slave Lords series, set in the Pomarj |
| 378 | Vecna Reborn | Ravenloft | |
| 279 | Forest Maker | Dark Sun | Dark Sun product number (2430) |
| 736 | The Gauntlgrym Gambit | Forgotten Realms | 4e Dungeon adventure set near Neverwinter |
| 596 | Eyes of the Lich Queen | Eberron | |
| 823 | Ghosts of Saltmarsh | Greyhawk | Greyhawk by default, with notes for other worlds |
| 813, 836, 849, 851, 856 | Confrontation at Candlekeep, One Grung Above, The Lost Kenku, The Tortle Package, Vault of the Dracolich | Forgotten Realms | Smaller 5e products tied to FR adventures |
| 816 | Domains of Delight | Feywild | Witchlight supplement |

### Set to None, and confirmed

**Mystara-era products Designers & Dragons doesn't place:**
- M2 Maze of the Riddling Minotaur (MSOLO2, #86): "Known World (or Not)"
- O1 The Gem and the Staff (#147)
- CM5 Mystery of the Snow Pearls (#90)
- CM6 Where Chaos Reigns (#193): set on another world, Aelos
- The Jade Hare (#352)
- AC7 Master Player Screen (#84)
- M5 Talons of Night (#125): not covered by the book

**1e modules that are generic or not covered by the book:**
- I9 Day of Al'Akbar (#38): the book says it "can't easily be placed in"
  Greyhawk
- Q1 Queen of the Demonweb Pits (#100): set in the Abyss
- I11 Needle (#91), I12 Egg of the Phoenix (#63), I13 Adventure Pack I (#11)
- UK5 (#65), UK7 (#37)
- N2 (#143), N3 (#42)
- RPGA2 (#22), RPGA4 (#137), RPGA7 (#81)

**2e adventures I couldn't place:**
- Possible Greyhawk ties: Axe of the Dwarvish Lords (#237), Crypt of
  Lyzandred the Mad (#246)
- Others: The Doomgrinder (#350), The Star Cairns (#363), The Lost Shrine of
  Bundushatur (#355), A Darkness Gathering (#228), A Hero's Tale (#229), Evil
  Tide (#264), Eye of Doom / Eye of Pain / Eye to Eye (#265, #266, #269),
  Destiny of Kings (#252), Eye of the Wyvern (#268), Dungeons of Despair
  (#262)
- Spans several worlds: Die Vecna Die! (#253, Greyhawk, Ravenloft and
  Planescape)

**3e:**
- The adventure series that started with The Sunless Citadel: #656, #645,
  #654, #655, #612, #589, #619, #585. Generic, but often placed in Greyhawk.
- Expedition to the Demonweb Pits (#594)
- Voyage of the Golden Dragon (#667)
- The ~60 free online mini-adventures, including web versions of Tomb of
  Horrors (#665) and White Plume Mountain (#670)

**4e:**
- Dungeon Magazine adventures other than the clearly Eberron or FR ones,
  e.g. Fist of Mourning (#705), Test of Fire (#733), Legacy of Io (#718),
  Marauders of the Dune Sea (#720)
- Dead in the Eye (#1006)

**5e:**
- Tales from the Yawning Portal (#847)
- Volo's Guide to Monsters (#897)
- Minsc and Boo's Journal of Villainy (#834)
- Locathah Rising (#831)
- Return to the Glory (#841)
- Vecna: Eve of Ruin (#857)
- Quests from the Infinite Staircase (#840)

**Asian-themed books that aren't tied to Kara-Tur:** The Complete Ninja's
Handbook (#504), Warriors of Heaven (#1286)

### Earlier

- 2026-11-05: Oriental Adventures folded into Kara-Tur (your call). Conan
  stays None.
- 2026-11-05: batch 1 corrections from Designers & Dragons:
  - The Desert of Desolation series (I3, I4, I5, I3-5: #97, #94, #82, #41)
    changed from Greyhawk to **Forgotten Realms** (Raurin).
  - Changed to **Greyhawk**: I1 (#61, Hepmonaland), I7 (#19, Keoland), UK1
    (#20) and UK6 (#16), and R4 (#43).
  - Changed to **Mystara**: B1, B3, B5, B7/Rahasia, B8, B9, B1-9, M1, M4, O2,
    MSOLO1, BSOLO, XSOLO, XL1.
  - Changed to **None**: CM5 (#90), I9 (#38), Q1 (#100).
