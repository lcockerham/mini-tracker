# Tracked Item Images Plan

## Summary

Add cover images to books first, then extend the same image system to miniatures and
other tracked items. The implementation should keep personal data and image files out
of Git, avoid scraping provider websites, respect licensing and attribution, and make
external requests only through explicit user actions or controlled background jobs.

The repository can remain public. Application code will be kept separate from private
collection data, downloaded covers, uploads, credentials, and provider caches. Making
the repository private may reduce accidental exposure, but it does not grant image
rights or remove licensing obligations.

## Goals

- Display a primary cover for each book on book list and detail pages.
- Allow manual image uploads for books and, eventually, every tracked item.
- Find book-cover candidates through supported provider interfaces.
- Avoid repeated or excessive requests to image providers.
- Store source, creator, license, and attribution metadata with each image.
- Support both locally stored images and provider-hosted images.
- Reuse one image architecture across books, miniatures, wishlist entries, and future
  tracked item types.
- Keep private images, catalog data, database files, and credentials out of Git.

## Non-goals

- Scraping Wikipedia, DM's Guild, DriveThruRPG, or publisher HTML pages.
- Automatically treating every image visible on Wikipedia as reusable.
- Committing downloaded covers or personal photos to the repository.
- Building a general-purpose public image mirror.
- Running uncontrolled or highly parallel bulk-import jobs.

## Privacy and Repository Boundary

Use a **public code, private data** model:

- Keep source code, templates, tests, and schema definitions in Git.
- Store user media under a dedicated `media/` directory outside `app/static/`.
- Add `media/`, `imports/*.csv`, `*.heic`, and other private import artifacts to
  `.gitignore` before implementing image support.
- Continue ignoring SQLite databases, backups, spreadsheets, `.env`, and credentials.
- Never place provider keys in templates, URLs, logs, CI variables, or committed files.
- Do not include downloaded covers in releases, test fixtures, Docker images, CI
  artifacts, screenshots, or documentation.
- Serve the application locally or behind authentication.
- If media or credentials are ever committed, remove them from Git history; adding an
  ignore rule afterward is not sufficient.

Repository privacy is defense-in-depth, not a licensing control. A private repository
only restricts who can view repository contents. It does not authorize copying an
image, and it does not protect images exposed by a publicly reachable application.

## Source Policy

### 1. Manual Upload

Manual upload is the universal fallback and the first provider to implement.

- Accept JPEG, PNG, and WebP initially.
- Reject SVG initially because it can contain active content.
- Apply an upload-size limit and a decoded-pixel limit.
- Correct EXIF orientation and strip unnecessary metadata.
- Generate optimized thumbnails for list and detail views.
- Allow replacement, removal, selection of a primary image, and optional attribution.

### 2. Open Library

Use Open Library as the primary automatic source for books with an exact ISBN.

- Look up only exact ISBNs for automatic matching.
- Store the Open Library identifier, source page, and cover URL.
- Follow Open Library's documented cover-display guidance.
- Do not crawl its cover repository or use the API as a bulk-data backend.
- Use lazy-loaded thumbnails and paginated book lists.
- Cache successful lookup metadata for 180 days and missing results for 30 days.
- Use a descriptive `User-Agent` containing application and contact information.
- Cap background lookups at 10 requests per minute, below the documented ISBN-cover
  limit of 100 requests per five minutes.

Documentation: <https://openlibrary.org/dev/docs/api/covers>

### 3. Wikimedia Commons

Use Wikimedia Commons only as a freely licensed fallback.

- Search for title, publisher, and game system together.
- Restrict PageImages results to `pilicense=free`.
- Retrieve `imageinfo` extended metadata before accepting a candidate.
- Store creator, credit, license name, license URL, source page, and canonical file
  identifier.
- Present candidates for manual confirmation; do not auto-select title-only matches.
- Download a selected reusable file once and serve the local derivative afterward.
- Link attribution to the Commons file-description page.

Relevant documentation:

- <https://www.mediawiki.org/wiki/Extension:PageImages/en>
- <https://www.mediawiki.org/wiki/API:Imageinfo/en>
- <https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia>

### 4. Wikipedia

Wikipedia may help identify candidates, but ordinary Wikipedia cover images must not
be automatically copied. English Wikipedia can host copyrighted images under
Wikipedia-specific non-free-use rules. Only accept images whose metadata confirms a
reusable license, preferably by resolving them through Wikimedia Commons.

### 5. DM's Guild and DriveThruRPG

Treat DM's Guild and DriveThruRPG as a separate integration phase.

- Do not scrape product pages or parse their HTML.
- Extract an exact numeric product identifier from an existing marketplace URL.
- Investigate the account Application Key interface using a dedicated test key.
- Contact provider support to confirm whether third-party personal catalog apps may
  retrieve or display product-cover thumbnails and what request limits apply.
- Implement the provider only after the supported interface and image-use policy are
  understood.
- If approved, request one product or one library page at a time, cache its metadata,
  and begin with a maximum of one request every five seconds.
- Stop automatically on authentication failures, HTTP 429, persistent 5xx responses,
  or an unexpected response schema.
- Do not commit the Application Key; load it from an environment variable.

The official help center documents Application Keys for the DriveThruRPG Library App,
but it does not currently provide a first-party contract for third-party cover-image
retrieval:

<https://help.drivethrurpg.com/hc/en-us/articles/12723264458647-Library-App-Frequently-Asked-Questions>

## Data Model

Create a reusable image asset instead of adding only `cover_url` to `Book`.

### `image_assets`

Suggested fields:

| Field | Purpose |
| --- | --- |
| `id` | Primary key |
| `storage_kind` | `local`, `provider`, or `cached_provider` |
| `local_path` | Relative path for locally stored media |
| `remote_url` | Provider-hosted display URL when applicable |
| `thumbnail_path` | Locally generated thumbnail path when applicable |
| `sha256` | Deduplication and integrity check |
| `mime_type` | Validated media type |
| `width`, `height` | Original dimensions |
| `byte_size` | Validated file size |
| `provider` | `manual`, `open_library`, `wikimedia`, or `drivethrurpg` |
| `provider_identifier` | Stable provider-side identifier |
| `source_page_url` | Human-readable provenance link |
| `source_file_url` | Original file location, if distinct |
| `creator` | Creator or copyright holder when known |
| `attribution_text` | Display-ready credit |
| `license_name` | License or rights label |
| `license_url` | Link to license terms |
| `rights_status` | `user_owned`, `licensed`, `provider_embedded`, or `unknown` |
| `fetched_at` | When the file or metadata was obtained |
| `last_checked_at` | When provider metadata was last checked |

### Typed Associations

Use typed association models to preserve database foreign keys:

- `book_images`: `book_id`, `image_asset_id`, `role`, `is_primary`, `sort_order`
- Later `mini_images`: `mini_id`, `image_asset_id`, `role`, `is_primary`, `sort_order`
- Add equivalent tables for other item types only when needed.

Avoid a generic `owner_type + owner_id` table because SQLite cannot enforce that the
referenced owner exists. Typed associations also make cascading deletion and ORM
relationships clearer.

The existing mini-only `Photo` model can be migrated to `ImageAsset` and `MiniImage`
after the book implementation proves the design.

## Storage and Image Processing

- Mount a gitignored `media/` directory at a dedicated `/media/` route.
- Store files by content hash rather than by user-supplied filename.
- Suggested layout:

  ```text
  media/
  └── images/
      ├── original/
      ├── list/
      └── detail/
  ```

- Generate a small list thumbnail and a medium detail image.
- Preserve aspect ratio and never upscale originals.
- Use fixed HTML width and height attributes to avoid layout shift.
- Add `loading="lazy"` and `decoding="async"` to list thumbnails.
- Validate the response MIME type rather than trusting the filename or URL extension.
- Limit redirects and reject redirects to a non-allow-listed host.
- Apply short connection/read timeouts and maximum response sizes.
- Prevent server-side request forgery by allowing server downloads only from explicit
  provider hostnames; do not accept arbitrary server-fetch URLs.
- Deduplicate identical files through SHA-256 before storing derivatives.

## Provider Interface

Give each provider the same application-facing contract:

```python
class ImageProvider:
    def search(self, item) -> list[ImageCandidate]: ...
    def resolve(self, candidate) -> ResolvedImage: ...
```

An `ImageCandidate` should contain:

- Provider and stable identifier
- Thumbnail preview
- Source page
- Match confidence and reasons
- Creator and license metadata
- Whether it may be stored locally or should remain provider-hosted

Provider-specific code should not write directly to item tables. A shared image
service should validate, persist, deduplicate, associate, and audit selected images.

## Matching Rules

Use conservative match confidence:

1. Exact marketplace product ID: high confidence.
2. Exact normalized ISBN: high confidence.
3. Exact title plus publisher: candidate requiring confirmation.
4. Exact title plus game system: candidate requiring confirmation.
5. Title-only or fuzzy search: candidate requiring confirmation.

Never automatically select a title-only result. Display edition, publisher, source,
and license beside each candidate so the user can make the final choice.

## Request Scheduling and Caching

External lookups must never run during normal list or detail rendering.

- Trigger lookups only through a “Find image” action or explicit enrichment job.
- Run provider requests serially, with no parallel bulk downloads.
- Add a persistent lookup cache containing provider, lookup key, response status,
  selected identifiers, checked time, and expiration.
- Cache successful metadata for 180 days.
- Cache `not found` results for 30 days.
- Never fetch a selected local image again unless the user explicitly refreshes it.
- Honor `Retry-After` and provider caching headers.
- Use exponential backoff for 429 and 503 responses.
- Retry no more than three times.
- Record request count, last request time, response status, and failure reason.
- Pause a provider automatically after repeated failures.

For Wikimedia background work:

- Use a meaningful `User-Agent`.
- Make requests one at a time.
- Batch multiple titles in one query where supported.
- Set `maxlag=5`.
- Wait at least five seconds between background API calls.

Wikimedia etiquette:
<https://www.mediawiki.org/wiki/API:Etiquette/en>

## User Experience

### Book Detail

- Display the primary cover beside the editable metadata.
- Add “Upload image,” “Find image,” “Change,” and “Remove” actions.
- Show provider, source, creator, and license beneath the cover.
- Preview provider candidates before selection.

### Book List

- Add a small cover thumbnail or placeholder.
- Paginate the list so a single page does not load the whole collection.
- Lazy-load thumbnails.
- Keep the table usable when no image exists.

### Bulk Enrichment

- Add a “Find missing covers” administration screen.
- Default to a dry-run preview.
- Process at most 25 books in one run.
- Show matched, needs-review, not-found, skipped, and failed counts.
- Allow pause and resume.
- Require confirmation before saving uncertain matches.
- Never use bulk enrichment for DM's Guild until provider permission and limits are
  confirmed.

## Backup and Migration

Before any schema migration or bulk image association:

1. Back up `mini_tracker.db` according to `CLAUDE.md`.
2. Verify the backup opens successfully.
3. Keep at most the three newest database backups.
4. Make the initial schema change additive: new image and association tables only.
5. Roll out manual uploads before running provider enrichment.
6. Add media-directory backup guidance because database backups will contain metadata
   but not the image files themselves.

Introduce Alembic before migrating existing `Photo` rows or making destructive schema
changes. The initial additive tables can be created safely, but future image migrations
need repeatable, versioned database changes.

## Delivery Sequence

Implement after the book-tracking PR is merged.

### PR 1: Image Foundation and Manual Uploads

- Add ignore rules and media mount.
- Add `ImageAsset` and `BookImage` models.
- Add upload validation and thumbnail generation.
- Add book detail and list image UI.
- Add replace, remove, primary-image, and attribution support.
- Add unit and route tests.

### PR 2: Open Library and Wikimedia Providers

- Add the provider interface and shared image service.
- Add exact-ISBN Open Library lookup.
- Add free-only Wikimedia Commons candidate search.
- Add provenance, licensing, caching, throttling, and retry handling.
- Add candidate review UI and mocked provider tests.

### PR 3: Controlled Bulk Enrichment

- Add dry-run and review workflow.
- Add persistent job state and request counters.
- Enforce per-provider budgets and serial execution.
- Add pause/resume and failure reporting.

### PR 4: DM's Guild / DriveThruRPG Provider

- Complete a small API feasibility spike.
- Confirm provider permission and rate limits.
- Add secure Application Key configuration.
- Match only exact product IDs from existing URLs.
- Add a conservative, cached provider client and contract tests.

### PR 5: Generalize to Other Tracked Items

- Add `MiniImage` and other typed associations as needed.
- Migrate existing mini `Photo` records.
- Reuse upload, gallery, attribution, and primary-image UI.
- Extend backup/restore coverage to the media directory.

## Testing

### Model and Storage Tests

- Image assets and associations cascade correctly.
- A book can have multiple images and exactly one primary cover.
- Duplicate bytes resolve to one asset.
- Invalid MIME types, oversized responses, and excessive dimensions are rejected.
- Derivative dimensions and orientation are correct.

### Provider Tests

- Exact ISBN and product-ID matching works.
- Title-only matches are never automatically accepted.
- Only free Wikimedia results are selectable.
- Attribution and license metadata are retained.
- Positive and negative cache entries prevent repeat calls.
- `Retry-After`, exponential backoff, and retry limits work.
- Provider tests use mocked HTTP responses and never call live services in CI.

### Security Tests

- Arbitrary hosts and private-network URLs cannot be fetched by the server.
- Redirects cannot escape the provider allow-list.
- Upload filenames cannot control filesystem paths.
- SVG and mislabeled content are rejected.
- Provider credentials never appear in rendered HTML or logs.

### UI Tests

- Missing images render a placeholder.
- List thumbnails are lazy-loaded and paginated.
- Source and attribution are visible on the detail page.
- Upload, select, replace, and remove flows work on mobile-sized screens.

## Acceptance Criteria

- No external provider query occurs during ordinary page rendering.
- External lookup jobs are serialized, rate-limited, cached, and observable.
- Images and credentials are excluded from Git and CI artifacts.
- Exact ISBN/product-ID matches can be found with minimal traffic.
- Ambiguous matches require user approval.
- Wikimedia images without confirmed reusable licenses are rejected.
- Every stored or displayed image retains its source and rights metadata.
- Books work normally without images or without internet access.
- The design supports future item types without duplicating provider and storage logic.
- The database and media directory have a documented backup and restore path.

## Remaining Decisions

- Whether Open Library images should remain provider-hosted or be cached locally for
  offline use. Default to the provider's documented display guidance.
- The maximum upload size and decoded-pixel limit.
- Exact thumbnail dimensions and list-page size.
- The contact identity to use in provider `User-Agent` headers.
- Whether this repository should remain public for collaboration or become private as
  an additional privacy safeguard. This does not change the licensing policy above.

## Reference Guidance

- GitHub repository visibility:
  <https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories>
- U.S. Copyright Office fair-use overview:
  <https://www.copyright.gov/fair-use/more-info.html>
- Open Library Covers API:
  <https://openlibrary.org/dev/docs/api/covers>
- Wikimedia API etiquette:
  <https://www.mediawiki.org/wiki/API:Etiquette/en>
- Wikimedia PageImages API:
  <https://www.mediawiki.org/wiki/Extension:PageImages/en>
- Wikimedia image metadata API:
  <https://www.mediawiki.org/wiki/API:Imageinfo/en>
- Wikimedia Commons reuse guidance:
  <https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia>
- DriveThruRPG Library App Application Key guidance:
  <https://help.drivethrurpg.com/hc/en-us/articles/12723264458647-Library-App-Frequently-Asked-Questions>
