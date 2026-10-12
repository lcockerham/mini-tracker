import html
import re
from datetime import datetime

import pytest

from app.database import get_db
from app.main import app
from app.models import Mini, MiniCandidate, MiniStatus, Photo
from imports import minisgallery_sync as sync_module
from imports.minisgallery_sync import (
    find_new_minis,
    link_sources,
    parse_index_links,
    parse_set_page,
    sync,
)

IMG = "https://www.minisgallery.com/images/minis/dungeons-and-dragons-icons-of-the-realms"


def minibox(mg_id, name, number=None, size="Medium", rarity="Common", image="x.jpg", promo=False):
    kind = "Promo" if promo else "Standard"
    number_html = (
        f'<div class="miniInfo2 miniInfo2_num miniInfoBackgroundWhite">({number})</div>'
        if number
        else ""
    )
    return (
        f'<div class="minibox{kind}">'
        f'<div class="miniName"><div class="miniNameNormal">{name}</div></div>'
        f'<div class="miniRarity rarity_x">{rarity}</div><div class="miniSize">{size}</div>'
        f'<div class="miniImage"><div class="miniImage{kind}">'
        f'<a href="index.php?id={mg_id}&task=image&imageName=x" target="_blank">'
        f'<img src="images/minis/dungeons-and-dragons-icons-of-the-realms/{image}" '
        f'alt="{name}"></a>'
        f'</div></div>{number_html}<div class="miniboxBottom"></div></div>'
    )


def set_page(title, *boxes, release="May 6, 2026"):
    return (
        f'<div class="productTitle">{title}</div><div class="productInfo">'
        f'<div class="productInfoRow"></div>'
        f'<div class="productInfoRow">{len(boxes)} Miniatures</div>'
        f'<div class="productInfoRow">{release}</div></div>'
        f'<div class="galleryContainer">{"".join(boxes)}</div>'
    )


def index_page(*page_ids):
    links = "".join(f'<a href="index.php?id={page_id}"><div>x</div></a>' for page_id in page_ids)
    return (
        '<ul class="pageMenu"><li><a href="index.php?id=main-menu">Main</a></li></ul>'
        f'<div class="tabsMenuContainerSingle">{links}</div>'
    )


@pytest.fixture()
def db(client):
    # Share the client's in-memory database so route tests see rows seeded here.
    session = next(app.dependency_overrides[get_db]())
    yield session
    session.close()


class TestParsing:
    def test_set_page_reads_mini_details(self):
        page = parse_set_page(
            "icons-of-the-realms-mm2",
            set_page(
                "Monster Manual Collection 2",
                minibox(10964, "Animated Armor", "1", image="mm2/aa.jpg"),
            ),
        )
        assert page.title == "Monster Manual Collection 2"
        assert page.release_date == "May 6, 2026"
        mini = page.minis[0]
        assert (mini.mg_id, mini.name, mini.mini_number) == (10964, "Animated Armor", "1")
        # Collection rarities are lowercase ("common", "ultra-rare"); keep new rows consistent.
        assert mini.rarity == "common"
        # Photos are hotlinked, so the image URL must be absolute to render on the site.
        assert mini.image_url == f"{IMG}/mm2/aa.jpg"

    def test_unreleased_placeholders_are_skipped(self):
        # Pre-release sets list guesses like "Unknown Lich?"; adding those would create junk minis
        # that never get corrected, so wait until the gallery names them.
        page = parse_set_page(
            "deadfall",
            set_page(
                "Arcana Unleashed: Deadfall",
                minibox(1, "Unknown Lich?", rarity="Unknown", size="Large"),
                minibox(2, "Szass Tam", "47", rarity="Unknown", size="Unknown"),
            ),
        )
        assert [m.name for m in page.minis] == ["Szass Tam"]
        assert page.minis[0].rarity is None
        assert page.minis[0].size is None

    def test_non_web_image_urls_are_dropped(self):
        # Image URLs are rendered as links on the review and detail pages; a javascript: URL
        # from a compromised gallery page would run in the app when clicked.
        html = set_page("S", minibox(1, "A")).replace(
            'src="images/minis/dungeons-and-dragons-icons-of-the-realms/x.jpg"',
            'src="javascript:alert(1)"',
        )
        assert parse_set_page("s", html).minis[0].image_url is None

    def test_index_links_ignore_site_navigation(self):
        # Following the menu would crawl every game line on the site (Star Wars, Heroclix, ...).
        assert parse_index_links(index_page("icons-of-the-realms-ghost-light")) == [
            "icons-of-the-realms-ghost-light"
        ]

    def test_index_page_is_not_a_set_page(self):
        assert parse_set_page("x", index_page("a")) is None


class TestFindNewMinis:
    def test_existing_minis_are_recognized_despite_renamed_sets(self, db):
        # The collection says "Monster Menagerie III" and "Goblin (mace)"; the gallery says
        # "Monster Menagerie 3" and "Goblin". Re-suggesting owned minis every month would bury
        # the genuinely new ones.
        db.add_all(
            [
                Mini(name="Kobold", set_name="Monster Menagerie III", mini_number="7"),
                Mini(name="Goblin (mace)", set_name="Monster Menagerie III", mini_number="8"),
                Mini(
                    name="City Guard (polearm)", set_name="Monster Menagerie III", mini_number="4A"
                ),
            ]
        )
        db.commit()
        page = parse_set_page(
            "mm3",
            set_page(
                "Monster Menagerie 3",
                minibox(1, "Kobold", "7"),
                minibox(2, "Goblin", "99"),
                minibox(3, "City Guard", "4a"),
                minibox(4, "Kraken", "45A"),
            ),
        )
        new = find_new_minis(db, [page])
        assert [(set_name, mini.name) for _, set_name, mini in new] == [
            ("Monster Menagerie III", "Kraken")
        ]

    def test_set_matched_through_linked_photos(self, db):
        # "Dragon Heist" vs gallery title "Waterdeep: Dragon Heist" only line up via photos.
        for number in ("1", "2", "3"):
            mini = Mini(name=f"Owned {number}", set_name="Dragon Heist", mini_number=number)
            mini.photos.append(Photo(url=f"{IMG}/dh/{number}.jpg"))
            db.add(mini)
        db.add(Mini(name="Noble (white)", set_name="Dragon Heist", mini_number="5A"))
        db.commit()
        page = parse_set_page(
            "dh",
            set_page(
                "Waterdeep: Dragon Heist",
                *(minibox(n, f"Owned {n}", str(n), image=f"dh/{n}.jpg") for n in (1, 2, 3)),
                minibox(5, "Noble", "5a"),
                minibox(6, "Brand New", "60"),
            ),
        )
        new = find_new_minis(db, [page])
        assert [(set_name, mini.name) for _, set_name, mini in new] == [
            ("Dragon Heist", "Brand New")
        ]

    def test_same_name_in_another_set_is_still_new(self, db):
        # A 2026 "Zombie" is a different sculpt from the 2015 one; only matches within the
        # corresponding set count as already owned.
        db.add(Mini(name="Zombie", set_name="Elemental Evil", mini_number="10"))
        db.commit()
        page = parse_set_page(
            "mm1", set_page("Monster Manual Collection 1", minibox(1, "Zombie", "10"))
        )
        new = find_new_minis(db, [page])
        assert [(set_name, mini.name) for _, set_name, mini in new] == [
            ("Monster Manual Collection 1", "Zombie")
        ]


class TestLinkSources:
    def owned(self, db, name, number, set_name="Dragon Heist", photo=None, source_url=None):
        mini = Mini(name=name, set_name=set_name, mini_number=number, source_url=source_url)
        if photo:
            mini.photos.append(Photo(url=f"{IMG}/{photo}"))
        db.add(mini)
        db.commit()
        return mini

    def test_links_existing_minis_to_their_gallery_page(self, db):
        by_photo = self.owned(db, "Cranium Rat Swarm", "1", photo="dh/crs.jpg")
        by_number = self.owned(db, "Darkling (one short sword)", "2")
        page = parse_set_page(
            "dh",
            set_page(
                "Dragon Heist",
                minibox(101, "Cranium Rat Swarm", "1", image="dh/crs.jpg"),
                minibox(102, "Darkling", "2", image="dh/darkling-2.jpg"),
            ),
        )
        assert link_sources(db, [page]) == 2
        assert by_photo.source_url.endswith("id=101&task=image")
        assert by_number.source_url.endswith("id=102&task=image")

    def test_does_not_guess_when_number_or_name_disagree(self, db):
        # A wrong link is worse than none: the collection merges sub-sets that reuse numbers
        # (50th Anniversary has two #1s), and a premium page can share a number with the base set.
        twin_a = self.owned(db, "Lemure", "1", set_name="50th Anniversary")
        twin_b = self.owned(db, "Blue Wizard", "1", set_name="50th Anniversary")
        renamed = self.owned(db, "Paladin in Hell", "3", set_name="50th Anniversary")
        page = parse_set_page(
            "50th",
            set_page(
                "50th Anniversary",
                minibox(201, "Lemure 5e", "1"),
                minibox(203, "Kobold", "3"),
            ),
        )
        assert link_sources(db, [page]) == 0
        assert (twin_a.source_url, twin_b.source_url, renamed.source_url) == (None, None, None)

    def test_keeps_a_source_url_set_by_hand(self, db):
        mini = self.owned(db, "Darkling", "2", photo="dh/d.jpg", source_url="https://example.com/d")
        page = parse_set_page(
            "dh", set_page("Dragon Heist", minibox(102, "Darkling", "2", image="dh/d.jpg"))
        )
        assert link_sources(db, [page]) == 0
        assert mini.source_url == "https://example.com/d"


class TestSync:
    def fake_site(self, monkeypatch, pages):
        monkeypatch.setattr(sync_module, "ROOT_PAGES", ["root"])
        return lambda page_id: pages[page_id]

    def test_queues_new_minis_once(self, db, monkeypatch):
        fetch = self.fake_site(
            monkeypatch,
            {
                "root": index_page("sub-index"),
                "sub-index": index_page("set-a"),
                "set-a": set_page(
                    "Ghost Light", minibox(10673, "Girallon Zombie", "12", image="gl/gz.jpg")
                ),
            },
        )
        result = sync(db, fetch)
        assert result.set_pages == 1
        assert result.new_candidates == {"Ghost Light": 1}
        candidate = db.query(MiniCandidate).one()
        assert (candidate.name, candidate.status) == ("Girallon Zombie", "pending")
        assert candidate.source_url.endswith("index.php?id=set-a")

        # Monthly re-runs must not duplicate what's already waiting for review.
        assert sum(sync(db, fetch).new_candidates.values()) == 0
        assert db.query(MiniCandidate).count() == 1

    def test_rejected_minis_are_not_suggested_again(self, db, monkeypatch):
        fetch = self.fake_site(
            monkeypatch,
            {"root": index_page("set-a"), "set-a": set_page("Ghost Light", minibox(7, "Rowboat"))},
        )
        sync(db, fetch)
        db.query(MiniCandidate).one().status = "rejected"
        db.commit()
        assert sum(sync(db, fetch).new_candidates.values()) == 0

    def test_failed_page_is_reported_not_fatal(self, db, monkeypatch):
        def fetch(page_id):
            if page_id == "broken":
                raise RuntimeError("503")
            return {"root": index_page("broken", "set-a"), "set-a": set_page("S", minibox(1, "A"))}[
                page_id
            ]

        monkeypatch.setattr(sync_module, "ROOT_PAGES", ["root"])
        result = sync(db, fetch)
        assert result.failed_pages == ["broken: 503"]
        assert result.new_candidates == {"S": 1}


def add_candidate(db, mg_id, name, set_name="Ghost Light", **kwargs):
    candidate = MiniCandidate(
        mg_id=mg_id,
        name=name,
        set_name=set_name,
        source_url="https://www.minisgallery.com/index.php?id=x",
        status="pending",
        found_at=datetime(2026, 10, 11),
        **kwargs,
    )
    db.add(candidate)
    db.commit()
    return candidate


class TestReviewPage:
    def test_approve_adds_unowned_prepainted_mini_with_gallery_photo(self, client, db):
        candidate = add_candidate(
            db, 1, "Girallon Zombie", mini_number="12", size="Large", image_url=f"{IMG}/gl/gz.jpg"
        )
        response = client.post(f"/minis/review/{candidate.id}/approve")
        assert response.status_code == 200
        mini = db.query(Mini).one()
        # Catalog entries aren't owned until the quantity is set, matching existing WizKids rows.
        assert (mini.quantity, mini.status, mini.manufacturer) == (
            0,
            MiniStatus.PRE_PAINTED,
            "Wizkids",
        )
        assert (mini.set_name, mini.mini_number, mini.size) == ("Ghost Light", "12", "Large")
        assert [photo.url for photo in mini.photos] == [f"{IMG}/gl/gz.jpg"]
        # Link back to the gallery's page for this exact mini, not just its set.
        assert mini.source_url == "https://www.minisgallery.com/index.php?id=1&task=image"
        db.refresh(candidate)
        assert (candidate.status, candidate.mini_id) == ("approved", mini.id)
        assert "Nothing to review" in client.get("/minis/review").text

    def test_reject_keeps_mini_out_of_collection(self, client, db):
        candidate = add_candidate(db, 1, "Rowboat")
        client.post(f"/minis/review/{candidate.id}/reject")
        assert db.query(Mini).count() == 0
        db.refresh(candidate)
        assert candidate.status == "rejected"

    def test_set_actions_only_touch_that_set(self, client, db):
        add_candidate(db, 1, "A", set_name="Ghost Light")
        add_candidate(db, 2, "B", set_name="Ghost Light")
        add_candidate(db, 3, "C", set_name="Yawning Portal")
        client.post("/minis/review/set", data={"set_name": "Ghost Light", "action": "approve"})
        client.post("/minis/review/set", data={"set_name": "Yawning Portal", "action": "reject"})
        assert sorted(name for (name,) in db.query(Mini.name)) == ["A", "B"]
        assert db.query(MiniCandidate).filter_by(status="pending").count() == 0

    def test_review_page_flags_possible_duplicates(self, client, db):
        # Sync only matches within a set, so a renamed one-off figure can slip through;
        # surfacing a same-named mini lets the reviewer reject the duplicate.
        db.add(
            Mini(name="Red Ghost Dragon", manufacturer="Wizkids", set_name="Adult Red Ghost Dragon")
        )
        db.commit()
        add_candidate(db, 1, "Red Ghost Dragon", set_name="Red Ghost Dragon")
        page = client.get("/minis/review").text
        assert "Possibly already have" in page
        assert "(Adult Red Ghost Dragon)" in page

    def test_minis_list_links_to_pending_review(self, client, db):
        assert "Review new minis" not in client.get("/minis").text
        add_candidate(db, 1, "Girallon Zombie")
        assert "Review new minis (1)" in client.get("/minis").text

    def test_review_route_not_shadowed_by_mini_detail(self, client):
        assert client.get("/minis/review").status_code == 200


class TestSourceLink:
    def test_reaper_minis_link_to_their_product_page_by_sku(self):
        # Every Reaper mini has a SKU, so they all get a source link without a stored URL.
        mini = Mini(name="Skeletal Spearmen", manufacturer="Reaper", mini_number="77001")
        assert mini.source_link == "https://www.reapermini.com/search/77001"

    def test_stored_url_wins_and_only_web_links_render(self):
        assert Mini(
            manufacturer="Reaper", mini_number="1", source_url="https://x.test/a"
        ).source_link == ("https://x.test/a")
        # The link is rendered as an href; a pasted javascript: URL must not become clickable.
        assert Mini(name="X", source_url="javascript:alert(1)").source_link is None

    def test_detail_page_links_to_source_and_saves_edits(self, client, db):
        mini = Mini(name="Darkling", status=MiniStatus.PRE_PAINTED, quantity=1)
        db.add(mini)
        db.commit()
        url = "https://www.minisgallery.com/index.php?id=102&task=image"
        response = client.post(
            f"/minis/{mini.id}/edit",
            data={"name": "Darkling", "status": "Pre-painted", "quantity": 1, "source_url": url},
        )
        assert response.status_code == 200
        assert f'href="{html.escape(url)}"' in client.get(f"/minis/{mini.id}").text
        assert "View source" in client.get(f"/minis/{mini.id}").text

    def test_unowned_catalog_minis_stay_editable(self, client, db):
        # Catalog minis have quantity 0; a min="1" input made the browser reject the whole
        # autosave form, so their notes and source URL could never be saved.
        mini = Mini(name="Goblin (mace)", status=MiniStatus.PRE_PAINTED, quantity=0)
        db.add(mini)
        db.commit()
        page = client.get(f"/minis/{mini.id}").text
        quantity_input = re.search(r'<input type="number" id="quantity"[^>]*>', page).group(0)
        assert 'min="0"' in quantity_input
