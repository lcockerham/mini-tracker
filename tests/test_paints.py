def create_paint(client, brand="Citadel", name="Nuln Oil", quantity=1):
    response = client.post("/paints", data={"brand": brand, "name": name, "quantity": quantity})
    assert response.status_code == 200
    return response


class TestPaints:
    def test_empty_paint_list(self, client):
        response = client.get("/paints")
        assert response.status_code == 200

    def test_add_paint(self, client):
        create_paint(client, brand="Citadel", name="Nuln Oil")
        response = client.get("/paints")
        assert "Citadel" in response.text
        assert "Nuln Oil" in response.text

    def test_add_multiple_paints(self, client):
        create_paint(client, brand="Citadel", name="Nuln Oil")
        create_paint(client, brand="Vallejo", name="Black")
        response = client.get("/paints")
        assert "Citadel" in response.text
        assert "Vallejo" in response.text

    def test_update_paint(self, client):
        create_paint(client, brand="Citadel", name="Nuln Oil", quantity=1)
        list_resp = client.get("/paints")
        import re
        paint_id = re.search(r'/paints/(\d+)/edit', list_resp.text).group(1)

        client.post(f"/paints/{paint_id}/edit", data={"brand": "Citadel", "name": "Nuln Oil", "quantity": 3})
        response = client.get("/paints")
        assert "3" in response.text


class TestMiniPaintLink:
    def test_link_paint_to_mini(self, client):
        client.post("/minis/new", data={"name": "Orc", "status": "In Progress"})
        create_paint(client, brand="Citadel", name="Nuln Oil")

        minis_resp = client.get("/minis")
        import re
        mini_id = re.search(r'href="/minis/(\d+)"', minis_resp.text).group(1)

        paints_resp = client.get("/paints")
        paint_id = re.search(r'/paints/(\d+)/edit', paints_resp.text).group(1)

        client.post(f"/minis/{mini_id}/paints", data={"paint_id": paint_id})
        detail = client.get(f"/minis/{mini_id}")
        assert "Nuln Oil" in detail.text
