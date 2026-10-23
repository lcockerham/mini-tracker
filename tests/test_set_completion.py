import re

from app.database import get_db
from app.main import app
from app.models import Mini, MiniStatus
from app.routers.set_completion import set_progress, slot_key


def mini(name, number=None, quantity=0, set_name="Monster Menagerie III", rarity=None):
    return Mini(
        name=name,
        mini_number=number,
        quantity=quantity,
        set_name=set_name,
        rarity=rarity,
        status=MiniStatus.PRE_PAINTED,
    )


def progress_for(minis):
    (entry,) = set_progress(minis)
    return entry


class TestSlotKey:
    def test_lettered_variants_share_a_figure(self):
        assert slot_key("10A", "Vampire Spawn (yellow shirt)") == slot_key("10B", "Vampire Spawn")

    def test_slash_number_is_a_variant_of_the_second_number(self):
        # "46/6 Invisible Cazi" is figure 46 in the box but a variant of #6.
        assert slot_key("46/6", "Invisible Cazi Alphelandra") == slot_key("6", "Cazi Alphelandra")
        assert slot_key("51/34A", "Invisible Mind Flayer") == slot_key("34B", "Mind Flayer")

    def test_numbers_ignore_leading_zeros(self):
        assert slot_key("07", "Goblin") == slot_key("7", "Goblin")

    def test_unnumbered_minis_match_on_name_without_variant_notes(self):
        assert slot_key(None, "Goblin (mace)") == slot_key("", "Goblin (sword)")
        assert slot_key(None, "Invisible Goblin") == slot_key(None, "Goblin")
        assert slot_key(None, "Goblin") != slot_key(None, "Goblin Boss")


class TestSetProgress:
    def test_one_of_each_figure_completes_the_set(self):
        # Owning either 10A or 10B fills #10, so the user isn't asked to chase both colorways.
        entry = progress_for([
            mini("Magmin", "1", quantity=1),
            mini("Vampire Spawn (yellow shirt)", "10A", quantity=1),
            mini("Vampire Spawn (brown shirt)", "10B"),
        ])
        assert (entry.owned, entry.total, entry.missing) == (2, 2, [])

    def test_missing_figure_lists_all_its_variants(self):
        entry = progress_for([
            mini("Magmin", "1", quantity=1),
            mini("Tiefling Rogue (purple cloak)", "35A"),
            mini("Invisible Tiefling Rogue", "35A"),
        ])
        assert (entry.owned, entry.total) == (1, 2)
        assert [[m.name for m in figure] for figure in entry.missing] == [
            ["Tiefling Rogue (purple cloak)", "Invisible Tiefling Rogue"]
        ]
        assert entry.percent == 50

    def test_variant_with_its_own_number_is_optional(self):
        # Tyranny of Dragons numbers its invisible Drizzt #46 with no link back to the base figure.
        entry = progress_for([
            mini("Drizzt", "12", quantity=1),
            mini("Drow Elf Ranger Drizzt (Invisible)", "46"),
            mini("Wood Elf Druid (alternate paint)", "47"),
        ])
        assert (entry.owned, entry.total) == (1, 1)

    def test_set_of_only_variants_is_not_counted(self):
        alternate = mini("Wood Elf Druid (alternate paint)", "1", set_name="Starter")
        assert set_progress([alternate]) == []


class TestSetCompletionPage:
    def add(self, *minis):
        db = next(app.dependency_overrides[get_db]())
        db.add_all(minis)
        db.commit()
        db.close()

    def test_sets_closest_to_complete_come_first(self, client):
        self.add(
            mini("Owlbear", "1", quantity=1, set_name="Mostly Done"),
            mini("Gnoll", "2", quantity=1, set_name="Mostly Done"),
            mini("Kobold", "3", quantity=1, set_name="Mostly Done"),
            mini("Hydra", "4", set_name="Mostly Done"),
            mini("Beholder", "1", quantity=1, set_name="Barely Started"),
            mini("Lich", "2", set_name="Barely Started"),
            mini("Tarrasque", "3", set_name="Barely Started"),
        )
        page = client.get("/minis/sets").text
        assert page.index("Mostly Done") < page.index("Barely Started")
        assert "3 / 4" in page
        assert "75%" in page
        # Missing minis link to their page, keeping Previous/Next within the set.
        assert re.search(r'href="/minis/\d+\?set_name=Mostly%20Done">Hydra</a>', page)

    def test_chase_figures_and_untouched_sets_are_left_out(self, client):
        self.add(
            mini("Blue Wizard", "1", quantity=1, set_name="50th Anniversary"),
            mini("Shadowheart", "44", set_name="50th Anniversary", rarity="chase"),
            mini("Venger", "60", set_name="Not Started"),
            mini("Adult Black Dragon", quantity=1, set_name="Individual"),
        )
        page = client.get("/minis/sets").text
        # Missing only the chase figure still counts as complete.
        assert "Complete sets (1)" in page
        assert "Shadowheart" not in page
        assert "1 not started" in page
        assert "Individual</a>" not in page
