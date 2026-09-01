import re


def create_book(client, title="Monster Manual", **kwargs):
    data = {"title": title, **kwargs}
    response = client.post("/books/new", data=data)
    assert response.status_code in (200, 303)
    return response


class TestBooks:
    def test_empty_books(self, client):
        response = client.get("/books")
        assert response.status_code == 200

    def test_add_book(self, client):
        create_book(client, title="Monster Manual")
        response = client.get("/books")
        assert "Monster Manual" in response.text

    def test_search_with_blank_dropdown_params(self, client):
        # The list.html form always submits game_system_id and ownership,
        # even when their "All" option (empty string) is selected.
        create_book(client, title="Curse of Strahd")
        create_book(client, title="Tomb of Horrors")
        response = client.get(
            "/books",
            params={"search": "Curse of Strahd", "game_system_id": "", "ownership": ""},
        )
        assert response.status_code == 200
        assert "Curse of Strahd" in response.text
        assert "Tomb of Horrors" not in response.text

    def test_add_book_physical_and_digital(self, client):
        create_book(
            client,
            title="Curse of Strahd",
            owns_physical="on",
            owns_digital="on",
        )
        list_resp = client.get("/books")
        book_id = re.search(r"/books/(\d+)", list_resp.text).group(1)
        detail = client.get(f"/books/{book_id}")
        assert 'name="owns_physical" style="width: auto;" checked' in detail.text
        assert 'name="owns_digital" style="width: auto;" checked' in detail.text

    def test_book_detail_shows_fields(self, client):
        create_book(
            client,
            title="Tome of Beasts",
            publisher="Kobold Press",
            drivethrurpg_url="https://www.drivethrurpg.com/product/12345",
        )
        list_resp = client.get("/books")
        book_id = re.search(r"/books/(\d+)", list_resp.text).group(1)
        detail = client.get(f"/books/{book_id}")
        assert "Kobold Press" in detail.text
        assert "drivethrurpg.com/product/12345" in detail.text

    def test_edit_book(self, client):
        create_book(client, title="Old Title")
        list_resp = client.get("/books")
        book_id = re.search(r"/books/(\d+)", list_resp.text).group(1)
        client.post(f"/books/{book_id}/edit", data={"title": "New Title"})
        detail = client.get(f"/books/{book_id}")
        assert "New Title" in detail.text
        assert "Old Title" not in detail.text

    def test_delete_book(self, client):
        create_book(client, title="Deleted Book")
        list_resp = client.get("/books")
        book_id = re.search(r"/books/(\d+)", list_resp.text).group(1)
        client.post(f"/books/{book_id}/delete")
        response = client.get("/books")
        assert "Deleted Book" not in response.text

    def test_filter_by_ownership(self, client):
        create_book(client, title="Physical Only", owns_physical="on")
        create_book(client, title="Digital Only", owns_digital="on")
        response = client.get("/books", params={"ownership": "physical"})
        assert "Physical Only" in response.text
        assert "Digital Only" not in response.text

    def test_game_systems_seeded(self, client):
        response = client.get("/books/new")
        assert "D&amp;D 5e" in response.text
        assert "Pathfinder 2e" in response.text

    def test_import_route_not_shadowed_by_book_id(self, client):
        response = client.get("/books/import")
        assert response.status_code == 200
