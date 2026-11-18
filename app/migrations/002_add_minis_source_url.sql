-- Was ADDED_COLUMNS ("minis", "source_url", "VARCHAR(500)") before versioned migrations.
ALTER TABLE minis ADD COLUMN source_url VARCHAR(500);
