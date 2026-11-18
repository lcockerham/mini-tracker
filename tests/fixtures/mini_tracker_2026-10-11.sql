-- A mini_tracker.db from before versioned migrations: the schema create_all() built at
-- 7141fd5 (2026-10-11), the commit before the ADDED_COLUMNS startup patch, plus a few rows.
-- It has books.format_availability but not minis.source_url, books.setting or the df_* tables.
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE minis (
	id INTEGER NOT NULL,
	name VARCHAR(255) NOT NULL,
	creature_type VARCHAR(255),
	manufacturer VARCHAR(255),
	product_line VARCHAR(255),
	set_name VARCHAR(255),
	mini_number VARCHAR(100),
	size VARCHAR(50),
	rarity VARCHAR(50),
	status VARCHAR(11) NOT NULL,
	quantity INTEGER NOT NULL,
	completion_date DATE,
	notes TEXT,
	PRIMARY KEY (id)
);
INSERT INTO minis VALUES(1,'Owlbear',NULL,'WizKids',NULL,'Monster Menagerie',NULL,NULL,NULL,'UNPAINTED',1,NULL,NULL);
CREATE TABLE paints (
	id INTEGER NOT NULL,
	brand VARCHAR(255) NOT NULL,
	name VARCHAR(255) NOT NULL,
	quantity INTEGER NOT NULL,
	PRIMARY KEY (id)
);
CREATE TABLE wishlist (
	id INTEGER NOT NULL,
	name VARCHAR(255) NOT NULL,
	manufacturer VARCHAR(255),
	notes TEXT,
	PRIMARY KEY (id)
);
CREATE TABLE game_systems (
	id INTEGER NOT NULL,
	name VARCHAR(100) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name)
);
INSERT INTO game_systems VALUES(1,'D&D 5e');
CREATE TABLE maps (
	id INTEGER NOT NULL,
	name VARCHAR(255) NOT NULL,
	source VARCHAR(255),
	size VARCHAR(100),
	owns_physical BOOLEAN NOT NULL,
	owns_digital BOOLEAN NOT NULL,
	PRIMARY KEY (id)
);
CREATE TABLE mini_paint (
	mini_id INTEGER NOT NULL,
	paint_id INTEGER NOT NULL,
	PRIMARY KEY (mini_id, paint_id),
	FOREIGN KEY(mini_id) REFERENCES minis (id),
	FOREIGN KEY(paint_id) REFERENCES paints (id)
);
CREATE TABLE photos (
	id INTEGER NOT NULL,
	mini_id INTEGER NOT NULL,
	url VARCHAR(500) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(mini_id) REFERENCES minis (id)
);
CREATE TABLE books (
	id INTEGER NOT NULL,
	title VARCHAR(255) NOT NULL,
	game_system_id INTEGER,
	publisher VARCHAR(255),
	category VARCHAR(100),
	format_availability VARCHAR(20),
	owns_physical BOOLEAN NOT NULL,
	owns_digital BOOLEAN NOT NULL,
	physical_location VARCHAR(255),
	drivethrurpg_url VARCHAR(500),
	acquired_date DATE,
	notes TEXT,
	PRIMARY KEY (id),
	FOREIGN KEY(game_system_id) REFERENCES game_systems (id)
);
INSERT INTO books VALUES(1,'Monster Manual',1,NULL,NULL,'both',1,0,NULL,NULL,NULL,NULL);
CREATE TABLE mini_candidates (
	id INTEGER NOT NULL,
	mg_id INTEGER NOT NULL,
	set_name VARCHAR(255) NOT NULL,
	source_url VARCHAR(500) NOT NULL,
	name VARCHAR(255) NOT NULL,
	mini_number VARCHAR(100),
	size VARCHAR(50),
	rarity VARCHAR(50),
	image_url VARCHAR(500),
	release_date VARCHAR(50),
	status VARCHAR(20) NOT NULL,
	found_at DATETIME NOT NULL,
	mini_id INTEGER,
	PRIMARY KEY (id),
	UNIQUE (mg_id),
	FOREIGN KEY(mini_id) REFERENCES minis (id)
);
COMMIT;
