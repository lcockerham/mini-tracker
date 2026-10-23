import re

import pytest

from app.database import get_db
from app.main import app
from app.models import DwarvenForgePiece, DwarvenForgeSet, DwarvenForgeSetPiece


@pytest.fixture()
def db(client):
    session = next(app.dependency_overrides[get_db]())
    yield session
    session.close()


@pytest.fixture()
def collection(db):
    stairs = DwarvenForgePiece(code="4-ST-003", name="Short Stairs")
    wall = DwarvenForgePiece(code="4-WS-001", name="Castle Solid Wall")
    lava = DwarvenForgePiece(code="LV-101")
    walls = DwarvenForgeSet(
        sku="4-WALLSR-U",
        name="Basic Walls",
        terrain_line="Castles",
        paint_type="Unpainted",
        copies=2,
        contents=[
            DwarvenForgeSetPiece(piece=wall, count=3),
            DwarvenForgeSetPiece(piece=stairs, count=1),
        ],
    )
    watchtower = DwarvenForgeSet(
        sku="4-WA-U",
        name="Watchtower Set",
        terrain_line="Castles",
        contents=[DwarvenForgeSetPiece(piece=stairs, count=2)],
    )
    volcano = DwarvenForgeSet(
        sku="6.6-A162-U",
        name="The Volcano",
        terrain_line="Hellscape",
        contents=[DwarvenForgeSetPiece(piece=lava, count=1)],
    )
    db.add_all([walls, watchtower, volcano])
    db.commit()
    return {"walls": walls.id, "watchtower": watchtower.id, "stairs": stairs.id, "lava": lava.id}


def piece_row(page, code):
    return re.search(rf">{re.escape(code)}</a>.*?</tr>", page, re.S).group(0)


class TestSets:
    def test_sets_are_grouped_by_terrain_line(self, client, collection):
        page = client.get("/dwarven-forge").text
        assert page.index("Castles") < page.index("Basic Walls") < page.index("Hellscape")
        assert page.index("Hellscape") < page.index("The Volcano")
        # 2 copies × 4 pieces + 2 + 1
        assert "3 sets · 11 pieces" in page

    def test_one_piece_set_is_marked_single(self, client, collection):
        page = client.get("/dwarven-forge").text
        volcano_row = re.search(r"The Volcano</a>.*?</td>", page, re.S).group(0)
        assert "single" in volcano_row

    def test_search_matches_name_or_sku(self, client, collection):
        assert "Basic Walls" not in client.get("/dwarven-forge?search=volcano").text
        assert "The Volcano" in client.get("/dwarven-forge?search=6.6-A162").text

    def test_set_page_counts_pieces_by_copies(self, client, collection):
        page = client.get(f"/dwarven-forge/sets/{collection['walls']}").text
        assert "4 per copy · 8 owned" in page
        wall_row = piece_row(page, "4-WS-001")
        assert re.findall(r"<td>(\d+)</td>", wall_row) == ["3", "6"]

    def test_editing_copies_changes_piece_totals(self, client, collection, db):
        client.post(
            f"/dwarven-forge/sets/{collection['walls']}/edit",
            data={"sku": "4-WALLSR-U", "name": "Basic Walls", "copies": 3},
        )
        page = client.get(f"/dwarven-forge/pieces/{collection['stairs']}").text
        # 1 per Basic Walls copy × 3 + 2 from the Watchtower.
        assert "5 total" in page

    def test_add_piece_to_set_creates_new_codes(self, client, collection, db):
        client.post(
            f"/dwarven-forge/sets/{collection['watchtower']}/pieces",
            data={"code": "AC-824", "count": 2},
        )
        page = client.get(f"/dwarven-forge/sets/{collection['watchtower']}").text
        assert ">AC-824</a>" in page
        assert db.query(DwarvenForgePiece).filter_by(code="AC-824").one().owned_total == 2

    def test_remove_piece_from_set(self, client, collection):
        client.post(
            f"/dwarven-forge/sets/{collection['watchtower']}/pieces/{collection['stairs']}/remove"
        )
        page = client.get(f"/dwarven-forge/sets/{collection['watchtower']}").text
        assert ">4-ST-003</a>" not in page

    def test_create_and_delete_set(self, client, db):
        response = client.post(
            "/dwarven-forge/sets/new",
            data={"sku": "8-A129-U", "name": "Lowtown Market Dressing", "copies": 1},
        )
        assert "Lowtown Market Dressing" in response.text
        set_id = db.query(DwarvenForgeSet).filter_by(sku="8-A129-U").one().id
        client.post(f"/dwarven-forge/sets/{set_id}/delete")
        assert "Lowtown Market Dressing" not in client.get("/dwarven-forge").text


class TestPieces:
    def test_piece_list_totals_across_sets(self, client, collection):
        page = client.get("/dwarven-forge/pieces").text
        assert "3 piece types · 11 pieces" in page
        stairs_row = piece_row(page, "4-ST-003")
        # Owned 1×2 + 2, from both sets.
        assert "<td>4</td>" in stairs_row
        assert "Basic Walls</a>" in stairs_row and "Watchtower Set</a>" in stairs_row

    def test_unnamed_piece_shows_by_code(self, client, collection):
        assert ">LV-101</a>" in client.get("/dwarven-forge/pieces?search=LV").text

    def test_loose_piece_counts_toward_total(self, client, collection):
        # A piece bought on its own, outside any set.
        client.post("/dwarven-forge/pieces/new", data={"code": "4-ST-003", "loose_quantity": 3})
        page = client.get(f"/dwarven-forge/pieces/{collection['stairs']}").text
        assert "7 total" in page

    def test_new_loose_piece_is_not_part_of_any_set(self, client):
        page = client.post(
            "/dwarven-forge/pieces/new",
            data={"code": "AC-824", "name": "Hand Cart", "loose_quantity": 1},
        ).text
        assert "AC-824 · Hand Cart" in page
        assert "Not part of any set." in page
        assert "1 total" in page

    def test_edit_piece_link_and_image(self, client, collection):
        client.post(
            f"/dwarven-forge/pieces/{collection['lava']}/edit",
            data={
                "code": "LV-101",
                "name": "Volcano",
                "loose_quantity": 0,
                "source_url": "https://www.dwarvenforge.com/products/the-volcano",
                "image_url": "https://cdn.shopify.com/volcano.jpg",
            },
        )
        page = client.get(f"/dwarven-forge/pieces/{collection['lava']}").text
        assert 'href="https://www.dwarvenforge.com/products/the-volcano"' in page
        assert 'src="https://cdn.shopify.com/volcano.jpg?width=800"' in page


class TestImageSizes:
    def test_shopify_pictures_are_resized_for_thumbnails(self, client, collection, db):
        walls = db.query(DwarvenForgeSet).filter_by(sku="4-WALLSR-U").one()
        walls.image_url = "https://cdn.shopify.com/s/files/walls.jpg"
        db.commit()
        assert 'src="https://cdn.shopify.com/s/files/walls.jpg?width=160"' in client.get(
            "/dwarven-forge"
        ).text
        assert 'src="https://cdn.shopify.com/s/files/walls.jpg?width=800"' in client.get(
            f"/dwarven-forge/sets/{walls.id}"
        ).text

    def test_other_pictures_are_left_alone(self, client, collection, db):
        walls = db.query(DwarvenForgeSet).filter_by(sku="4-WALLSR-U").one()
        walls.image_url = "https://my.photos/walls.jpg"
        db.commit()
        assert 'src="https://my.photos/walls.jpg"' in client.get("/dwarven-forge").text


class TestSourceLinks:
    def test_non_web_links_are_not_rendered(self, client, collection, db):
        # A javascript: URL typed into the link field must never become a clickable link.
        walls = db.query(DwarvenForgeSet).filter_by(sku="4-WALLSR-U").one()
        walls.source_url = "javascript:alert(1)"
        stairs = db.get(DwarvenForgePiece, collection["stairs"])
        stairs.source_url = "JavaScript:alert(1)"
        db.commit()
        pages = [
            "/dwarven-forge",
            f"/dwarven-forge/sets/{walls.id}",
            f"/dwarven-forge/pieces/{stairs.id}",
        ]
        for path in pages:
            assert 'href="javascript:' not in client.get(path).text.lower()
