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
│   │   └── photos.py         # Photo link management
│   ├── templates/
│   │   ├── base.html         # Layout
│   │   ├── minis/
│   │   │   ├── list.html     # Collection view + search
│   │   │   └── detail.html   # Individual mini view
│   │   ├── paints/
│   │   │   └── list.html     # Paint inventory
│   │   ├── wishlist/
│   │   │   └── list.html     # Wishlist view
│   │   └── dashboard.html    # Visualizations
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

## Requirements discussion                                        
  1. The collector story is missing the "SO THAT" clause - what's the benefit of supporting multiple formats? FIXED                                                                       
  2. The DM search story - what would you search by? (creature type, size, painted status, name?)
  FIXED                                                                                                          
  - Adding minis to collection - How do you want to add them? Manual entry, barcode/SKU lookup, import from your Excel file?
  Added story                                                        
  - Organization - Do you want categories, tags, or folders? (e.g., "monsters", "NPCs", "terrain")                                                     Not in the MVP                        
  - Paint inventory - Do you want to track paints you own, or just record what you used on each mini?                                                          I want to track paints I own, the number, and what minis I used them on.       
  - Painting status workflow - Beyond painted/unpainted, do you need states like "primed", "in progress", "based"?    
  Unpainted, In progress, and Done. We also need to be able to differentiate minatures that come prepainted.                                                              
  - Wishlist - Track minis you want to buy?        
  Yes - anything in the inventory sheets should be tracked.                                                       
  Questions:                                                     1. For searching as a DM - what attributes matter most? (creature type, size, setting, painted status?)                                                       
  creature name and type
  2. When tracking paints used, do you also want to track techniques or color recipes (e.g., "base coat X, wash Y, drybrush Z")?                  
  Just free form notes for the MVP                                  
  3. The Excel file in downloads - is that your current collection you'd want to import?                      

  No thats a blank example file - the real one with current collection is in my google drive
  