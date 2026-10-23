import pytest

from app.database import get_db
from app.main import app
from app.models import DwarvenForgePiece, DwarvenForgeSet
from imports.dwarven_forge import import_collection, parse_rows
from imports.dwarven_forge_links import LINKS_TSV, apply_links

HEADER = ["Code", "Name", "Count", "Set Name", "SKU", "Bundle Name", "Paint Type", "Hand Painted?"]


def rows(*lines):
    return [dict(zip(HEADER, line.split("|"))) for line in lines]


WALLS = [
    "4-WS-001|Castle Solid Wall|3|Castles|4-WALLSR-U|Basic Walls|Unpainted|No",
    "4-ST-003|Short Stairs|1|Castles|4-WALLSR-U|Basic Walls|Unpainted|No",
]
WATCHTOWER = ["4-ST-003|Short Stairs|2|Castles|4-WA-U|Watchtower Set|Unpainted|No"]
VOLCANO = ["LV-101||1|Hellscape|6.6-A162-U|The Volcano|N/A|N/A"]


@pytest.fixture()
def db(client):
    session = next(app.dependency_overrides[get_db]())
    yield session
    session.close()


class TestParseRows:
    def test_repeated_block_is_another_copy(self):
        # The sheet lists a set once per copy owned, so its rows repeat as a block.
        (walls,), _ = parse_rows(rows(*WALLS, *WALLS))
        assert walls.copies == 2
        assert walls.pieces == {"4-WS-001": 3, "4-ST-003": 1}

    def test_uneven_repeats_fail_loudly(self):
        # A piece repeated without the rest of its set isn't a copy; don't guess.
        with pytest.raises(ValueError, match="4-WALLSR-U"):
            parse_rows(rows(*WALLS, WALLS[0]))

    def test_blank_and_na_values_become_empty(self):
        (volcano,), names = parse_rows(rows(*VOLCANO))
        assert volcano.paint_type is None
        assert names == {"LV-101": None}


class TestImportCollection:
    def test_counts_pieces_across_sets_and_copies(self, db):
        result = import_collection(db, rows(*WALLS, *WALLS, *WATCHTOWER, *VOLCANO))
        assert (result.sets_added, result.pieces_added) == (3, 3)

        walls = db.query(DwarvenForgeSet).filter_by(sku="4-WALLSR-U").one()
        assert (walls.copies, walls.pieces_per_copy, walls.piece_total) == (2, 4, 8)
        # Short Stairs: 1 in each of 2 Basic Walls copies + 2 in the Watchtower.
        stairs = db.query(DwarvenForgePiece).filter_by(code="4-ST-003").one()
        assert stairs.owned_total == 4
        assert sorted(e.set.name for e in stairs.set_entries) == ["Basic Walls", "Watchtower Set"]

    def test_loose_pieces_add_to_the_total(self, db):
        import_collection(db, rows(*WATCHTOWER))
        stairs = db.query(DwarvenForgePiece).filter_by(code="4-ST-003").one()
        stairs.loose_quantity = 3
        assert stairs.owned_total == 5

    def test_rerun_keeps_edits_and_adds_only_new_sets(self, db):
        import_collection(db, rows(*WALLS))
        walls = db.query(DwarvenForgeSet).filter_by(sku="4-WALLSR-U").one()
        walls.copies = 5
        db.commit()

        result = import_collection(db, rows(*WALLS, *WATCHTOWER))
        assert (result.sets_added, result.sets_skipped, result.pieces_added) == (1, 1, 0)
        db.refresh(walls)
        assert walls.copies == 5
        assert db.query(DwarvenForgePiece).count() == 2


class TestApplyLinks:
    def test_fills_links_and_pictures(self, db):
        import_collection(db, rows(*WALLS, *VOLCANO))
        result = apply_links(db, [
            ["S", "4-WALLSR-U", "sku", "walls-regular-unpainted", "https://cdn.example/walls.jpg"],
            ["P", "4-ST-003", "sku", "in-4-st-003-u-short-stairs", "https://cdn.example/stairs.jpg"],
        ])
        assert (result.links_added, result.images_added) == (2, 2)
        walls = db.query(DwarvenForgeSet).filter_by(sku="4-WALLSR-U").one()
        assert walls.source_url == "https://www.dwarvenforge.com/products/walls-regular-unpainted"
        assert walls.image_url == "https://cdn.example/walls.jpg"

    def test_set_found_only_by_picture_gets_no_link(self, db):
        # The picture sat on a bigger bundle's page; linking there points at the wrong product.
        import_collection(db, rows(*VOLCANO))
        apply_links(db, [["S", "6.6-A162-U", "image", "some-bundle", "https://cdn.example/v.jpg"]])
        volcano = db.query(DwarvenForgeSet).one()
        assert (volcano.source_url, volcano.image_url) == (None, "https://cdn.example/v.jpg")

    def test_keeps_values_set_by_hand(self, db):
        import_collection(db, rows(*WALLS))
        walls = db.query(DwarvenForgeSet).one()
        walls.image_url = "https://my.photos/walls.jpg"
        db.commit()
        result = apply_links(db, [
            ["S", "4-WALLSR-U", "sku", "walls", "https://cdn.example/walls.jpg"],
            ["P", "NOT-OWNED", "sku", "x", "https://cdn.example/x.jpg"],
        ])
        assert walls.image_url == "https://my.photos/walls.jpg"
        assert (result.links_added, result.images_added, result.unknown_keys) == (1, 0, 1)

    def test_shipped_links_file_is_well_formed(self):
        with LINKS_TSV.open(encoding="utf-8") as f:
            lines = [line.rstrip("\n").split("\t") for line in f]
        assert all(len(f) == 5 and f[0] in ("S", "P") for f in lines)
        assert all(f[4].startswith("https://cdn.shopify.com/") for f in lines)
