# Mini-Tracker Project Review

**Review date:** 2026-10-15  
**Scope:** Current tracked application, tests, CI, project notes and docs, and Git history through `f4d03d5`. No code was changed for this review.

## Project understanding

Mini-Tracker is a personal, single-user FastAPI application for managing tabletop miniature, paint, wishlist, map, and RPG book collections. It uses server-rendered Jinja templates, SQLAlchemy with a local SQLite database, and a small amount of browser JavaScript; maintenance scripts also import spreadsheet data and synchronize catalog candidates from Minis Gallery. This is a practical personal collection tool rather than a multi-user service, and the project's own notes describe database backups and schema migration as local operational concerns. Recent history shows regular, small feature commits and pull-request merges, including book-cover work and the Minis Gallery queue and source-link work.

The repository has no README, CONTRIBUTING guide, or ADRs; `summary.md` is the main project guide. I reviewed all application and test modules, the CI/configuration files, the project notes, and the docs at a structural and representative-content level; the exception catalogs are data-heavy and were not audited record by record. The supplied review prompt refers to an older `fable-review.md` dated 2026-07-06, but that file is absent from the checkout and its Git history, so I could not map its individual findings to current fixes.

## Executive summary

**Overall grade: B.** The project is a coherent, well-tested personal application with useful collection-specific workflows, and recent history shows focused delivery. The main risks are the upload route's unbounded read and persistent temporary files, hand-maintained schema upgrades with no migration history, and route handlers that assume referenced records exist. The highest-leverage improvement is to make database changes and import behavior explicit and repeatable, beginning with safe upload cleanup and a versioned migration path. This assessment applies a proportionate standard for a local single-user tool; internet-facing use would need a separate security review.

## Scorecard

| Dimension | Score | Rationale |
|---|---:|---|
| Architecture & design | 4/5 | The small FastAPI/ORM/template structure maps well to the collection domain; route modules are separated by feature. |
| Code quality & maintainability | 3/5 | Most code is direct and readable, but duplicated CRUD patterns and a few unchecked assumptions make failures less consistent. |
| Correctness & reliability | 3/5 | The gallery sync has thoughtful release gating and tests; import and missing-record paths still have avoidable failure modes. |
| Security | 3/5 | No credentials or obvious injection were found in the reviewed paths; the app assumes a trusted local user and has no authentication or CSRF protection. |
| Testing | 4/5 | Pytest covers core CRUD and the gallery sync, including meaningful parsing and release cases; import and several route edge cases are not covered. |
| Dependencies & build | 2/5 | Dependencies are unpinned and there is no lockfile or contributor setup guide, so recreating an environment is less predictable. |
| CI/CD & operations | 3/5 | Pull requests run lint and tests with read-only repository permissions; the app has no deployment/rollback or diagnostic logging story, appropriate to its current local scope. |
| Documentation & developer experience | 3/5 | `summary.md`, `CLAUDE.md`, and focused workflow docs explain domain context, though setup guidance is tied to one absolute local path and the summary is not a full README. |
| Performance & scalability | 3/5 | Current local-collection scale is modest, but list and navigation views load whole result sets and imports process rows one at a time. |

## Findings, prioritized

### P0 — Fix now

None found for the stated local, single-user use. No secrets or obvious SQL/command injection were identified in the reviewed code. The lack of authentication and CSRF defenses is a boundary assumption, not a P0 finding for the documented localhost workflow; it becomes a release blocker if the app is exposed to an untrusted network.

### P1 — Fix soon

#### Uploaded workbooks are read fully into memory and left in the temporary directory

**Evidence:** [`app/main.py:63-75`](app/main.py) reads the complete upload with `await file.read()`, writes it to a `NamedTemporaryFile(delete=False)`, and retains the path without later unlinking it. The broad handler at lines 84-87 also turns parsing and database errors into an ordinary result page.

**Why it matters:** Repeated imports leave workbook copies behind, and a large upload can consume substantial memory and disk space. This is low exposure on a trusted local machine but makes a core data-entry path needlessly fragile.

**Recommendation:** Stream or impose a conservative size limit, use a context-managed temporary directory/file that is removed in `finally`, and report a concise user-facing error while logging diagnostic details. **Effort: S.**

#### Schema upgrades are unversioned and only handle a fixed list of added columns

**Evidence:** [`app/database.py:22-36`](app/database.py) creates current metadata and conditionally adds columns listed in `ADDED_COLUMNS`; there is no schema version, ordered migration history, or recovery path.

**Why it matters:** As the model evolves, old databases can drift from the current model in ways this list does not handle (renames, constraints, indexes, data conversion). Startup then becomes the migration mechanism, making a bad change difficult to diagnose or reverse. `CLAUDE.md` explicitly warns that bulk database writes should be backed up, so schema changes already have operational risk.

**Recommendation:** Introduce Alembic or a small, explicit versioned migration runner before adding more schema changes; document and test upgrade behavior against an older database. **Effort: M.**

#### Missing or malformed record references can become server errors

**Evidence:** [`app/routers/minis.py:144-145`](app/routers/minis.py) dereferences a possibly missing mini later in the handler; update and paint handlers similarly assume mini existence at lines 198 and 225-227. [`app/routers/books.py:181-182`](app/routers/books.py) can render a missing book, while its query parsing calls `int(game_system_id)` at lines 103 and 182 without handling invalid input.

**Why it matters:** Stale links, a mistyped URL, or malformed query values produce a 500 response instead of a clear not-found or validation response. The collection's owner can recover by navigating back, but the inconsistent response obscures real failures and makes route tests less complete.

**Recommendation:** Centralize record lookup or check for missing rows and return 404; validate query identifiers and return 422 or ignore invalid optional filters consistently. Add tests for these negative cases. **Effort: S.**

### P2 — Opportunistic

#### Dependency versions are unconstrained and setup is not documented generically

**Evidence:** [`requirements.txt:1-10`](requirements.txt) and [`requirements-dev.txt:1-4`](requirements-dev.txt) list bare package names; the only run instructions in [`summary.md:195-201`](summary.md) use `/Users/lucascockerham/Developer/mini-tracker`.

**Why it matters:** A fresh environment can resolve different dependency versions over time, while the absolute path makes the documented first run less useful on another machine. CI pins Python 3.12 but not package versions.

**Recommendation:** Add a reproducible lock or constraints file and document generic setup commands, supported Python version, and the local database location. **Effort: S.**

#### Collection and detail navigation queries load complete result sets

**Evidence:** [`app/routers/minis.py:74-78, 145-149`](app/routers/minis.py) and [`app/routers/books.py:105-109, 183-188`](app/routers/books.py) fetch all matching rows; detail navigation then scans the collection in Python.

**Why it matters:** This is reasonable for a personal catalog today, but it increases response time and memory as the collection grows. The same pattern appears in adjacent collection modules.

**Recommendation:** Defer pagination until real collection size makes this noticeable; then paginate list views and compute previous/next neighbors in SQL. **Effort: M.**

#### CI duplicates the same checks across three workflows

**Evidence:** [`.github/workflows/ci.yml:1-29`](.github/workflows/ci.yml) runs lint and tests on pull requests, while `lint.yml` and `test.yml` separately run on pushes to main and pull requests to main.

**Why it matters:** Pull requests targeting main can run duplicate jobs, increasing CI time and maintenance surface. The three files also use different action major versions.

**Recommendation:** Consolidate around one workflow or divide responsibilities so each event runs each check once; standardize action versions. **Effort: S.**

## What's working well

- The domain model and route boundaries are straightforward, and the user-facing app remains server-rendered rather than carrying unnecessary frontend infrastructure.
- The Minis Gallery integration queues suggestions for human approval instead of silently modifying the collection; it also filters placeholders and gates on release dates ([`imports/minisgallery_sync.py`](imports/minisgallery_sync.py), [`app/routers/mini_review.py`](app/routers/mini_review.py)).
- The bulk review flow backs up before multi-row approval ([`app/routers/mini_review.py:89-97`](app/routers/mini_review.py), [`app/backup.py`](app/backup.py)), matching the project's explicit data-protection guidance.
- The Minis Gallery sync tests exercise parsing, URL handling, release-date logic, matching, and route flows; this is useful behavioral coverage for the most externally variable integration.
- Git history is organized into small feature/fix commits and merged pull requests, and pull-request CI runs both Ruff and pytest with read-only repository permissions.

## Old review findings and subsequent work

The 2026-07-06 review could not be found in this checkout or in the available Git history. I therefore cannot responsibly label any specific old finding as fixed. The history and current code do confirm substantial work after that date: book cover enrichment and alternate covers, book-format tracking and dashboard filters, detail-form autosave, and a Minis Gallery sync/review queue with source links and release-date safeguards. These are verified additions, but without the old finding text they cannot be treated as resolved findings.

## Recommended 30/60/90-day remediation plan

- **Next 30 days:** Clean up temporary workbook files, cap or stream uploads, and make missing-record behavior predictable. Add targeted negative tests alongside these small fixes.
- **By 60 days:** Add schema versioning and exercise at least one upgrade from an older database copy; keep the existing backup guidance part of the process.
- **By 90 days:** Add dependency constraints and portable setup instructions. Consolidate CI checks and assess pagination against actual collection size rather than optimizing speculatively.

No P0 remediation is required for the documented local use. If access expands beyond the local machine, add authentication and CSRF defenses before exposing write routes.

## Quick wins

- Remove temporary workbook files in a `finally` block and reject oversized uploads (under an hour).
- Return a clear 404 for missing mini/book records and handle malformed optional IDs (under an hour).
- Merge duplicate CI triggers and add portable first-run instructions (under an hour).

These are review recommendations only; no implementation was performed. They can be implemented after approval.
