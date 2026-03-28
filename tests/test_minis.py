def create_mini(client, name="Beholder", status="Unpainted", **kwargs):
    data = {"name": name, "status": status, "quantity": 1, **kwargs}
    response = client.post("/minis/new", data=data)
    assert response.status_code == 200  # after redirect
    return response


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
        import re
        match = re.search(r'href="(/minis/\d+)"', response.text)
        assert match
        detail = client.get(match.group(1))
        assert "Lich" in detail.text
        assert "Very spooky" in detail.text


class TestMiniEdit:
    def test_edit_name(self, client):
        create_mini(client, name="Orc")
        list_resp = client.get("/minis")
        import re
        match = re.search(r'href="(/minis/(\d+))"', list_resp.text)
        mini_id = match.group(2)

        client.post(f"/minis/{mini_id}/edit", data={"name": "Orc Warlord", "status": "Unpainted", "quantity": 1})
        detail = client.get(f"/minis/{mini_id}")
        assert "Orc Warlord" in detail.text

    def test_edit_status(self, client):
        create_mini(client, name="Skeleton", status="Unpainted")
        list_resp = client.get("/minis")
        import re
        mini_id = re.search(r'href="/minis/(\d+)"', list_resp.text).group(1)

        client.post(f"/minis/{mini_id}/edit", data={"name": "Skeleton", "status": "Done", "quantity": 1})
        detail = client.get(f"/minis/{mini_id}")
        assert "Done" in detail.text
