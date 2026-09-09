import html
import re


def create_mini(client, name="Beholder", status="Unpainted", **kwargs):
    data = {"name": name, "status": status, "quantity": 1, **kwargs}
    response = client.post("/minis/new", data=data)
    assert response.status_code == 200  # after redirect
    return response


def mini_id_for_name(response_text, name):
    match = re.search(
        rf'href="/minis/(\d+)[^"]*">{re.escape(html.escape(name))}</a>',
        response_text,
    )
    assert match is not None
    return match.group(1)


class TestMiniList:
    def test_empty_list(self, client):
        response = client.get("/minis")
        assert response.status_code == 200
        assert "No miniatures found" in response.text

    def test_lists_minis(self, client):
        create_mini(client, name="Beholder")
        response = client.get("/minis")
        assert "Beholder" in response.text

    def test_search_by_name(self, client):
        create_mini(client, name="Beholder")
        create_mini(client, name="Zombie")
        response = client.get("/minis?search=beh")
        assert "Beholder" in response.text
        assert "Zombie" not in response.text

    def test_filter_by_creature_type(self, client):
        create_mini(client, name="Beholder", creature_type="Aberration")
        create_mini(client, name="Zombie", creature_type="Undead")
        response = client.get("/minis?creature_type=Aberration")
        assert "Beholder" in response.text
        assert "Zombie" not in response.text

    def test_filter_by_manufacturer(self, client):
        create_mini(client, name="Beholder", manufacturer="Wizkids")
        create_mini(client, name="Skeleton", manufacturer="Reaper")
        response = client.get("/minis?manufacturer=Wizkids")
        assert "Beholder" in response.text
        assert "Skeleton" not in response.text

    def test_filter_by_status(self, client):
        create_mini(client, name="Beholder", status="Unpainted")
        create_mini(client, name="Dragon", status="Done")
        response = client.get("/minis?status=Done")
        assert "Dragon" in response.text
        assert "Beholder" not in response.text


class TestMiniCreate:
    def test_create_minimal(self, client):
        response = create_mini(client, name="Goblin")
        assert "Goblin" in response.text

    def test_create_with_all_fields(self, client):
        response = create_mini(
            client,
            name="Beholder",
            creature_type="Aberration",
            manufacturer="Wizkids",
            product_line="Icons of the Realms",
            set_name="Spelljammer",
            mini_number="15/45",
            size="Large",
            status="Pre-painted",
            quantity=2,
            notes="Great sculpt",
        )
        assert "Beholder" in response.text
        assert "Aberration" in response.text
        assert "Wizkids" in response.text

    def test_create_redirects_to_detail(self, client):
        response = client.post("/minis/new", data={"name": "Troll", "status": "Unpainted"})
        assert "/minis/" in str(response.url)


class TestMiniDetail:
    def test_detail_page(self, client):
        create_mini(client, name="Lich", notes="Very spooky")
        response = client.get("/minis")
        # grab the detail link
        match = re.search(r'href="(/minis/\d+)"', response.text)
        assert match
        detail = client.get(match.group(1))
        assert "Lich" in detail.text
        assert "Very spooky" in detail.text

    def test_detail_navigates_in_name_order(self, client):
        create_mini(client, name="Charlie")
        create_mini(client, name="Alpha")
        create_mini(client, name="Bravo")
        list_response = client.get("/minis")
        alpha_id = mini_id_for_name(list_response.text, "Alpha")
        bravo_id = mini_id_for_name(list_response.text, "Bravo")
        charlie_id = mini_id_for_name(list_response.text, "Charlie")

        detail = client.get(f"/minis/{bravo_id}")

        assert f'href="/minis/{alpha_id}" rel="prev"' in detail.text
        assert f'href="/minis/{charlie_id}" rel="next"' in detail.text
        assert '<span class="item-navigation-position">2 of 3</span>' in detail.text

    def test_navigation_preserves_filtered_list(self, client):
        create_mini(client, name="Alpha Guard", manufacturer="Wizkids")
        create_mini(client, name="Beta Guard", manufacturer="Wizkids")
        create_mini(client, name="Gamma Guard", manufacturer="Reaper")
        params = {"search": "Guard", "manufacturer": "Wizkids"}
        navigation_query = "search=Guard&amp;manufacturer=Wizkids"
        list_response = client.get("/minis", params=params)
        alpha_id = mini_id_for_name(list_response.text, "Alpha Guard")
        beta_id = mini_id_for_name(list_response.text, "Beta Guard")

        assert "Gamma Guard" not in list_response.text
        assert f'href="/minis/{alpha_id}?{navigation_query}"' in list_response.text

        detail = client.get(f"/minis/{alpha_id}", params=params)
        assert f'href="/minis/{beta_id}?{navigation_query}" rel="next"' in detail.text
        assert '<span class="item-navigation-position">1 of 2</span>' in detail.text
        assert f'href="/minis?{navigation_query}"' in detail.text

    def test_detail_renders_large_photo(self, client):
        create_mini(client, name="Photogenic Lich")
        list_response = client.get("/minis")
        mini_id = mini_id_for_name(list_response.text, "Photogenic Lich")
        image_url = "https://example.com/lich.jpg"
        client.post(f"/minis/{mini_id}/photos", data={"url": image_url})

        detail = client.get(f"/minis/{mini_id}")

        assert 'class="detail-layout mini-detail-layout has-cover"' in detail.text
        assert 'class="cover-panel mini-photo-panel"' in detail.text
        assert 'class="photo-grid mini-detail-photo-grid"' in detail.text
        assert f'src="{image_url}"' in detail.text


class TestMiniEdit:
    def test_edit_name(self, client):
        create_mini(client, name="Orc")
        list_resp = client.get("/minis")
        match = re.search(r'href="(/minis/(\d+))"', list_resp.text)
        mini_id = match.group(2)

        client.post(
            f"/minis/{mini_id}/edit",
            data={"name": "Orc Warlord", "status": "Unpainted", "quantity": 1},
        )
        detail = client.get(f"/minis/{mini_id}")
        assert "Orc Warlord" in detail.text

    def test_edit_status(self, client):
        create_mini(client, name="Skeleton", status="Unpainted")
        list_resp = client.get("/minis")
        mini_id = re.search(r'href="/minis/(\d+)"', list_resp.text).group(1)

        client.post(
            f"/minis/{mini_id}/edit", data={"name": "Skeleton", "status": "Done", "quantity": 1}
        )
        detail = client.get(f"/minis/{mini_id}")
        assert "Done" in detail.text
