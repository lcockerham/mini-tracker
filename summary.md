# Mini-Tracker

## About
Application for tracking RPG miniatures - both as collectibles and managing painting progress for unpainted minis.

## User Stories
AS A DM
I WANT an inventory of all my miniatures, painted, unpainted, and pre-painted
SO THAT I can search through my inventory by monster name, mini manufacturer, and status (painted or unpainted) and find the best mini for my adventure

AS A mini painter
I WANT to be able to track what miniatures I painted and what paints I used to paint them with
SO THAT I can pick up where I left off on painting a mini, and remember what paints worked well

AS A mini painter
I WANT to be able to take pictures of painted minis 
SO THAT I can see and share it from my phone camera

AS A Mini collector
I WANT to support a lot of different mini formats, including pre-painted minis from wizkids, bones unpainted minis from reaper, terrian from dwarven forge, and minis from board games
SO THAT I can track everything in one place. 

AS A Mini collector
I WANT visualizations of my collection
SO THAT I can see how much I have painted and when it was painted, and other fun visualizations. 

AS A Mini collector
I WANT to be able to build collection information from existing spreadsheets I have
SO THAT I don't have to enter everything manually.

AS A mini painter
I WANT to track my paint inventory (brand, paint name, quantity)
SO THAT I know what paints I have and can see which minis I've used them on.

AS A mini collector
I WANT to maintain a wishlist of minis I want to buy
SO THAT I can track what I'm looking for. When I buy one, I can check it off and set a quantity to add it to my collection.

AS A mini painter
I WANT to set a status on each mini (Unpainted, In Progress, Done, Pre-painted)
SO THAT I can track my painting progress.

AS A mini painter
I WANT to record when I completed painting a mini
SO THAT I can see my painting history and track progress over time.

AS A mini collector
I WANT to manually add new minis to my collection
SO THAT I can track minis I acquire.

AS A mini collector
I WANT to view details of an individual mini (name, manufacturer, status, photos, paints used, notes)
SO THAT I can see all information about a specific mini in one place.

AS A mini collector
I WANT to edit my minis (especially quantities/counts)
SO THAT I can keep my inventory accurate when I buy duplicates or lose minis.  

## NFRs

Prefer python
Local database using sqlalchemy
Need to be able to at least upload pics from my phone (could maybe connect to google drive)

## resources
mini tracker excel file in my downloads
mini gallery for wotc and wizkids dnd minis: https://www.minisgallery.com/index.php?id=icons-of-the-realms-premium-sets


## Data Model

### Mini
| Field | Type | Notes |
|-------|------|-------|
| id | int | PK |
| name | string | e.g., "Beholder" |
| creature_type | string | e.g., "Aberration", "Dragon" |
| manufacturer | string | Wizkids, Reaper, Dwarven Forge, etc. |
| product_line | string | e.g., "Icons of the Realms", "Bones" |
| set_name | string | nullable, e.g., "Angelfire", "Spelljammer", "Waterdeep", "Bones 2" |
| mini_number | string | nullable, SKU (e.g., "77001") or set number (e.g., "1/80") |
| size | string | nullable, Small/Medium/Large/Huge/Gargantuan |
| status | enum | Unpainted, In Progress, Done, Pre-painted |
| quantity | int | default 1 |
| completion_date | date | nullable |
| notes | text | free-form painting notes |

### Paint
| Field | Type | Notes |
|-------|------|-------|
| id | int | PK |
| brand | string | Citadel, Vallejo, Army Painter, etc. |
| name | string | e.g., "Nuln Oil" |
| quantity | int | how many you own |

### MiniPaint (join table - many to many)
| Field | Type | Notes |
|-------|------|-------|
| mini_id | FK | |
| paint_id | FK | |

### Photo (many to one - many photos per mini)
| Field | Type | Notes |
|-------|------|-------|
| id | int | PK |
| mini_id | FK | |
| url | string | Google Drive link |

### Wishlist
| Field | Type | Notes |
|-------|------|-------|
| id | int | PK |
| name | string | |
| manufacturer | string | nullable |
| notes | text | nullable |

## Architecture

### Stack
- **Backend:** Python + FastAPI
- **Frontend:** Jinja2 templates (MVP), API-first design allows SPA frontend later
- **Database:** SQLite + SQLAlchemy (local, single-user)
- **Photo storage:** Google Drive API (store links in DB)
- **Spreadsheet import:** pandas or openpyxl
- **Validation:** Pydantic models

### Project Structure
```
mini-tracker/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, startup
│   ├── database.py           # SQLAlchemy engine, session
│   ├── models.py             # SQLAlchemy ORM models
│   ├── schemas.py            # Pydantic request/response models
│   ├── routers/
│   │   ├── minis.py          # Mini CRUD + search
│   │   ├── paints.py         # Paint inventory CRUD
│   │   ├── wishlist.py       # Wishlist CRUD + convert to mini
│   │   ├── photos.py         # Photo link management
│   │   └── dashboard.py      # Dashboard visualizations
│   ├── templates/
│   │   ├── base.html         # Layout
│   │   ├── minis/
│   │   │   ├── list.html     # Collection view + search
│   │   │   ├── detail.html   # Individual mini view
│   │   │   └── create.html   # Add new mini form
│   │   ├── paints/
│   │   │   └── list.html     # Paint inventory
│   │   ├── wishlist/
│   │   │   └── list.html     # Wishlist view
│   │   ├── dashboard.html    # Visualizations
│   │   └── import.html       # Spreadsheet import
│   └── static/
│       └── css/
├── imports/                   # Spreadsheet import utilities
├── mini_tracker.db            # SQLite database (gitignored)
├── requirements.txt
└── summary.md
```

### API Design
- `GET/POST /minis` - list (with search params) / create
- `GET/PUT /minis/{id}` - detail / update
- `GET/POST /paints` - list / create
- `PUT /paints/{id}` - update
- `GET/POST /wishlist` - list / create
- `POST /wishlist/{id}/purchase` - convert to mini in collection
- `POST /minis/{id}/photos` - add photo link
- `GET /dashboard` - visualizations

## Implementation Status

### Completed (MVP)
- [x] Project scaffolding (FastAPI, SQLAlchemy, Jinja2)
- [x] Database models and Pydantic schemas
- [x] Mini CRUD with search/filter (name, creature type, manufacturer, status, set dropdown — exact match; single-mini sets live under "Individual")
- [x] Mini detail view with edit form
- [x] Paint inventory CRUD with inline editing
- [x] Link paints to minis (many-to-many)
- [x] Wishlist with purchase-to-collection flow
- [x] Photo URL management (Google Drive links)
- [x] Spreadsheet import with flexible column mapping
- [x] Dashboard with Chart.js visualizations (status breakdown, manufacturer chart, painting timeline)
- [x] Status badge `white-space: nowrap` fix (pre-painted was wrapping across two lines)
- [x] Ruff linter + GitHub Actions CI (lint and test workflows on every PR)
- [x] Pytest test suite (25 tests: mini CRUD/search/filter, wishlist purchase flow, paint inventory, paint-mini linking)
- [x] Updated to Starlette 1.0 `TemplateResponse` API (request as first arg)
- [x] Dashboard "Painting Breakdown" — renamed from "Status Breakdown", excludes pre-painted, "Done" → "Painted", percent tooltips on pie chart
- [x] Books dashboard chart filter — Physical includes physical-only and both-format books; Digital includes digital-only and both-format books; chart shows ownership percentage for the selected format (PR #24 merged)
- [x] Normalized manufacturer data (WizKids → Wizkids via SQL)
- [x] Minis Gallery sync — `imports/minisgallery_sync.py` crawls minisgallery.com's Icons of the Realms / Onslaught indexes and queues WizKids minis not yet in the collection (skips sets whose listed release date hasn't passed yet — month-only dates like "Feb 2027" wait until the month is over — plus "Unknown …?" placeholders and anything previously rejected; pending minis from a set that turns out to be unreleased are withdrawn until it ships); review at `/minis/review` (approve adds Pre-painted, qty 0, Minis Gallery image as photo; bulk approve backs up the DB first). Runs monthly via launchd (`make install-sync-schedule`); run by hand with `make sync-minis`
- [x] Mini source links — `minis.source_url` (editable on the detail page, with a "View source" link). Minis Gallery minis link to their per-mini page: set on approval, and filled for existing minis by the monthly sync (photo match, else unambiguous set number + agreeing name); DDM and Tanares were backfilled once. Reaper minis fall back to `reapermini.com/search/<SKU>`
- [x] Set completion — `/minis/sets` lists started sets closest to complete first, with links to each missing mini. One of every figure completes a set: variants sharing a base number (10A/10B, "46/6" invisibles) count once, unnumbered minis match on name minus parenthesized notes/"Invisible", and chase figures, standalone variants (invisible / alternate paint or sculpt) and "Individual" are left out
- [x] Dwarven Forge tab — `/dwarven-forge` tracks DF terrain by set (each SKU you own, grouped by terrain line, with copies) and by piece (`/dwarven-forge/pieces`: code, total owned across sets plus loose pieces bought on their own, which sets it comes from). Tables `df_sets`, `df_pieces`, `df_set_pieces` (count per copy). Imported once from `mini-data/Dwarven Forge - Sheet1.csv` (`make import-dwarven-forge`; repeated row blocks = extra copies). Store links and pictures come from dwarvenforge.com's product catalog, matched by SKU (pieces sell as `IN-<code>-U/P`) and saved in `imports/dwarven_forge_links.tsv` (`make link-dwarven-forge` fills empty fields only); the site rate-limits scripts, so the catalog was read through a browser. Shopify pictures are requested resized (`?width=`)

### To Run
```bash
cd /Users/lucascockerham/Developer/mini-tracker
source .venv/bin/activate
uvicorn app.main:app --reload
```
Open http://localhost:8000

### GitHub
https://github.com/lcockerham/mini-tracker

## Future Enhancements (Not in MVP)
- Organization via categories/tags/folders
- Alembic migrations (currently delete DB to reset)
- Direct Google Drive integration for photo upload
- Mobile-optimized UI
- Manual pass over the physical book collection to verify `owns_physical` — replaces the unfinished bookshelf-photo cataloging (unread shelf sections dropped; "Monster Manual Expanded" I/II still need a check to confirm they're official books)
  
