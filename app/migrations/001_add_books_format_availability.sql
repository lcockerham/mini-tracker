-- Was ADDED_COLUMNS ("books", "format_availability", "VARCHAR(20)") before versioned migrations.
ALTER TABLE books ADD COLUMN format_availability VARCHAR(20);
