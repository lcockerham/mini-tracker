import html
import re

from app.routers import maps


def create_map(client, name="Green Valley", **kwargs):
    data = {"name": name, **kwargs}
    response = client.post("/maps/new", data=data)
    assert response.status_code in (200, 303)
    return response


def map_id_for_name(response_text, name):
    match = re.search(
        rf'href="/maps/(\d+)[^"]*">{re.escape(html.escape(name))}</a>',
        response_text,
    )
    assert match is not None
    return match.group(1)


class TestMaps:
    def test_empty_maps(self, client):
        response = client.get("/maps")
        assert response.status_code == 200

    def test_add_map(self, client):
        create_map(client, name="Green Valley")
        response = client.get("/maps")
        assert "Green Valley" in response.text

    def test_map_detail_shows_fields(self, client):
        create_map(
            client,
            name="Ruined Town",
            source="D&D Tactical Maps Reincarnated",
            size="21x30",
        )
        list_resp = client.get("/maps")
        map_id = map_id_for_name(list_resp.text, "Ruined Town")
        detail = client.get(f"/maps/{map_id}")
        assert "D&amp;D Tactical Maps Reincarnated" in detail.text
        assert "21x30" in detail.text

    def test_add_map_physical_and_digital(self, client):
        create_map(
            client,
            name="Snowy City Gate",
            owns_physical="on",
            owns_digital="on",
        )
        list_resp = client.get("/maps")
        map_id = map_id_for_name(list_resp.text, "Snowy City Gate")
        detail = client.get(f"/maps/{map_id}")
        assert 'name="owns_physical" style="width: auto;" checked' in detail.text
        assert 'name="owns_digital" style="width: auto;" checked' in detail.text

    def test_search_by_name(self, client):
        create_map(client, name="Bandit's Checkpoint")
        create_map(client, name="Arcane Hideout")
        response = client.get("/maps", params={"search": "Bandit"})
        assert "Bandit&#39;s Checkpoint" in response.text or "Bandit's Checkpoint" in response.text
        assert "Arcane Hideout" not in response.text

    def test_filter_by_ownership(self, client):
        create_map(client, name="Physical Only", owns_physical="on")
        create_map(client, name="Digital Only", owns_digital="on")
        response = client.get("/maps", params={"ownership": "physical"})
        assert "Physical Only" in response.text
        assert "Digital Only" not in response.text

    def test_edit_map(self, client):
        create_map(client, name="Old Name")
        list_resp = client.get("/maps")
        map_id = map_id_for_name(list_resp.text, "Old Name")
        client.post(f"/maps/{map_id}/edit", data={"name": "New Name"})
        detail = client.get(f"/maps/{map_id}")
        assert "New Name" in detail.text
        assert "Old Name" not in detail.text

    def test_delete_map(self, client):
        create_map(client, name="Deleted Map")
        list_resp = client.get("/maps")
        map_id = map_id_for_name(list_resp.text, "Deleted Map")
        client.post(f"/maps/{map_id}/delete")
        response = client.get("/maps")
        assert "Deleted Map" not in response.text

    def test_map_detail_shows_convention_based_image(self, client, tmp_path, monkeypatch):
        create_map(client, name="Portal Chamber")
        list_resp = client.get("/maps")
        map_id = map_id_for_name(list_resp.text, "Portal Chamber")
        (tmp_path / f"{map_id}.webp").write_bytes(b"image")
        monkeypatch.setattr(maps, "MAP_IMAGE_DIR", tmp_path)

        detail = client.get(f"/maps/{map_id}")

        assert f'src="/static/images/maps/{map_id}.webp"' in detail.text
        assert 'alt="Portal Chamber image"' in detail.text

    def test_maps_nav_link_present(self, client):
        response = client.get("/minis")
        assert 'href="/maps"' in response.text

    def test_map_detail_navigates_in_name_order(self, client):
        create_map(client, name="Charlie")
        create_map(client, name="Alpha")
        create_map(client, name="Bravo")
        list_response = client.get("/maps")
        alpha_id = map_id_for_name(list_response.text, "Alpha")
        bravo_id = map_id_for_name(list_response.text, "Bravo")
        charlie_id = map_id_for_name(list_response.text, "Charlie")

        detail = client.get(f"/maps/{bravo_id}")

        assert f'href="/maps/{alpha_id}" rel="prev"' in detail.text
        assert f'href="/maps/{charlie_id}" rel="next"' in detail.text
        assert '<span class="item-navigation-position">2 of 3</span>' in detail.text

    def test_map_navigation_preserves_filtered_list(self, client):
        create_map(client, name="Alpha Quest", owns_physical="on")
        create_map(client, name="Beta Quest", owns_physical="on")
        create_map(client, name="Gamma Quest", owns_digital="on")
        create_map(client, name="Delta Item", owns_physical="on")
        params = {"search": "Quest", "ownership": "physical"}
        navigation_query = "search=Quest&amp;ownership=physical"
        list_response = client.get("/maps", params=params)
        alpha_id = map_id_for_name(list_response.text, "Alpha Quest")
        beta_id = map_id_for_name(list_response.text, "Beta Quest")

        assert "Gamma Quest" not in list_response.text
        assert "Delta Item" not in list_response.text
        assert f'href="/maps/{alpha_id}?{navigation_query}"' in list_response.text

        first_detail = client.get(f"/maps/{alpha_id}", params=params)
        assert f'href="/maps/{beta_id}?{navigation_query}" rel="next"' in first_detail.text
        assert '<span class="item-navigation-position">1 of 2</span>' in first_detail.text
        assert f'href="/maps?{navigation_query}"' in first_detail.text

        second_detail = client.get(f"/maps/{beta_id}", params=params)
        assert f'href="/maps/{alpha_id}?{navigation_query}" rel="prev"' in second_detail.text
        assert '<span class="item-navigation-position">2 of 2</span>' in second_detail.text

    def test_edit_keeps_map_navigation_filters(self, client):
        create_map(client, name="Filtered Map", owns_physical="on")
        list_response = client.get("/maps")
        map_id = map_id_for_name(list_response.text, "Filtered Map")
        query = "search=Filtered&ownership=physical"

        response = client.post(
            f"/maps/{map_id}/edit?{query}",
            data={"name": "Filtered Map", "owns_physical": "on"},
        )

        assert response.url.path == f"/maps/{map_id}"
        assert response.url.query.decode() == query
        assert '<span class="item-navigation-position">1 of 1</span>' in response.text
