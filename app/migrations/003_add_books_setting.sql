-- Was ADDED_COLUMNS ("books", "setting", "VARCHAR(50)") before versioned migrations.
ALTER TABLE books ADD COLUMN setting VARCHAR(50);
