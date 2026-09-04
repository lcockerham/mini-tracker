# AD&D 2e DMsGuild enrichment runbook

## Purpose

Use this procedure to enrich an existing AD&D 2e book record with its canonical
DMsGuild product URL, signed-in digital-ownership status, and full-size cover.
The procedure does not add image metadata or alter the database schema.

## Preconditions

- Use the signed-in DMsGuild browser session belonging to the collection owner.
- Confirm the local Mini-Tracker site is running and reachable.
- Identify the collection record's numeric ID, exact title, publisher, edition,
  and any product or module code in its notes.
- Do not overwrite an existing URL or cover until the existing value has been
  checked and found to be incorrect.

## Authoritative matching criteria

A DMsGuild result is an accepted match only when all available evidence agrees:

1. The title is exact or differs only by an edition or module-code prefix.
2. The product is for AD&D 2nd Edition, not a conversion or later-edition
   product with a similar name.
3. The publisher is TSR or Wizards of the Coast for an official catalog record.
4. The module or product code agrees with the collection notes when a code is
   available.

Never select a result merely because it is first in the search results. Record
an exception when the evidence is missing, ambiguous, or contradictory.

## Procedure

1. Open DMsGuild and search for the collection title. Search results load
   asynchronously: wait at least two seconds after the results shell appears
   and check a second time before concluding that there are no matches. Add the
   module or product code, or retry with a shorter distinctive title phrase,
   when the title alone produces ambiguous or empty results.
2. Open the accepted result and save its canonical `/en/product/...` URL in the
   collection record's **DriveThruRPG URL** field.
3. Wait for the product heading and account-specific controls to finish loading,
   then inspect the page for the exact **You own this title** banner. Before
   recording an unowned result, allow at least 1.5 seconds after the main product
   content appears and check the banner a second time; ownership controls can
   arrive after the public product content.
4. Set **Own Digital Copy** when the banner is visible. Leave the flag unchecked
   when the banner is absent. Search-card labels and cart state are supporting
   clues only; the product-page banner is authoritative.
5. Click the product cover to open the full-size image. Accept only a resolved
   non-thumbnail, non-placeholder image. If the dialog uses a lazy or malformed
   source, verify the main product image's resolved source after the click.
6. Save that image under `app/static/images/books/` using the collection's
   numeric ID and the source image's supported extension, for example
   `951.webp`.
7. Open the local book detail page and save the URL and ownership flag.
8. Verify the saved page shows the correct URL and ownership state. Confirm the
   cover is in the right column beside the editable information on desktop and
   moves above the form at narrow widths.
9. Confirm the database values and that the saved cover is a valid image.

The detail route recognizes `.webp`, `.jpg`, `.jpeg`, and `.png` files named for
the book ID. A correctly named file is sufficient to display the cover.

## Batch controls

- Process records in small batches and verify each batch before continuing.
- Preserve existing collection data other than the three fields in scope:
  **DriveThruRPG URL**, **Own Digital Copy**, and the convention-based cover.
- Use the exception log for every record that cannot be completed exactly.
- An exception must include the collection ID, title, category, evidence, and
  the next action required. Do not guess past an exception.

## Exception categories

- **No listing**: no plausible official DMsGuild product was found.
- **Ambiguous match**: multiple plausible products remain after checking edition,
  publisher, and product code.
- **Metadata conflict**: the collection and product page disagree materially.
- **Ownership unavailable**: the signed-in ownership banner cannot be checked.
- **Cover unavailable**: the product has no usable full-size cover image.
- **Local update failed**: the URL, ownership flag, image, or detail page could
  not be saved or verified.
- **Duplicate collection record**: two collection records resolve to the same
  canonical product; enrich both, but flag the duplication for collection
  cleanup rather than silently choosing one.

## Completion criteria

A record is complete only when the canonical URL, ownership flag, and cover are
all saved and verified. A record with any unresolved element remains an
exception and is not counted as complete.
