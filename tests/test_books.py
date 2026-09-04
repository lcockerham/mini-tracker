import html
import re

from app.routers import books


def create_book(client, title="Monster Manual", **kwargs):
    data = {"title": title, **kwargs}
    response = client.post("/books/new", data=data)
    assert response.status_code in (200, 303)
    return response


def book_id_for_title(response_text, title):
    match = re.search(
        rf'href="/books/(\d+)[^"]*">{re.escape(html.escape(title))}</a>',
        response_text,
    )
    assert match is not None
    return match.group(1)


def game_system_id_for_name(client, name):
    response = client.get("/books")
    match = re.search(
        rf'<option value="(\d+)"[^>]*>{re.escape(html.escape(name))}</option>',
        response.text,
    )
    assert match is not None
    return match.group(1)


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

    def test_book_detail_shows_convention_based_cover(self, client, tmp_path, monkeypatch):
        create_book(client, title="Dark Sun Boxed Set")
        list_resp = client.get("/books")
        book_id = re.search(r"/books/(\d+)", list_resp.text).group(1)
        (tmp_path / f"{book_id}.webp").write_bytes(b"cover")
        monkeypatch.setattr(books, "BOOK_COVER_DIR", tmp_path)

        detail = client.get(f"/books/{book_id}")

        assert f'src="/static/images/books/{book_id}.webp"' in detail.text
        assert 'alt="Dark Sun Boxed Set cover"' in detail.text

    def test_book_detail_navigates_in_title_order(self, client):
        create_book(client, title="Charlie")
        create_book(client, title="Alpha")
        create_book(client, title="Bravo")
        list_response = client.get("/books")
        alpha_id = book_id_for_title(list_response.text, "Alpha")
        bravo_id = book_id_for_title(list_response.text, "Bravo")
        charlie_id = book_id_for_title(list_response.text, "Charlie")

        detail = client.get(f"/books/{bravo_id}")

        assert f'href="/books/{alpha_id}" rel="prev"' in detail.text
        assert f'href="/books/{charlie_id}" rel="next"' in detail.text
        assert '<span class="book-navigation-position">2 of 3</span>' in detail.text

    def test_book_navigation_preserves_filtered_list(self, client):
        dnd_id = game_system_id_for_name(client, "D&D 5e")
        pathfinder_id = game_system_id_for_name(client, "Pathfinder 2e")
        create_book(
            client,
            title="Alpha Quest",
            game_system_id=dnd_id,
            owns_physical="on",
        )
        create_book(
            client,
            title="Beta Quest",
            game_system_id=dnd_id,
            owns_physical="on",
        )
        create_book(
            client,
            title="Gamma Quest",
            game_system_id=dnd_id,
            owns_digital="on",
        )
        create_book(
            client,
            title="Delta Quest",
            game_system_id=pathfinder_id,
            owns_physical="on",
        )
        params = {
            "search": "Quest",
            "game_system_id": dnd_id,
            "ownership": "physical",
        }
        navigation_query = (
            f"search=Quest&amp;game_system_id={dnd_id}&amp;ownership=physical"
        )
        list_response = client.get("/books", params=params)
        alpha_id = book_id_for_title(list_response.text, "Alpha Quest")
        beta_id = book_id_for_title(list_response.text, "Beta Quest")

        assert "Gamma Quest" not in list_response.text
        assert "Delta Quest" not in list_response.text
        assert (
            f'href="/books/{alpha_id}?{navigation_query}"' in list_response.text
        )

        first_detail = client.get(f"/books/{alpha_id}", params=params)
        assert f'href="/books/{beta_id}?{navigation_query}" rel="next"' in first_detail.text
        assert '<span class="book-navigation-position">1 of 2</span>' in first_detail.text
        assert f'href="/books?{navigation_query}"' in first_detail.text

        second_detail = client.get(f"/books/{beta_id}", params=params)
        assert f'href="/books/{alpha_id}?{navigation_query}" rel="prev"' in second_detail.text
        assert '<span class="book-navigation-position">2 of 2</span>' in second_detail.text

    def test_edit_keeps_book_navigation_filters(self, client):
        dnd_id = game_system_id_for_name(client, "D&D 5e")
        create_book(
            client,
            title="Filtered Book",
            game_system_id=dnd_id,
            owns_physical="on",
        )
        list_response = client.get("/books")
        book_id = book_id_for_title(list_response.text, "Filtered Book")
        query = f"search=Filtered&game_system_id={dnd_id}&ownership=physical"

        response = client.post(
            f"/books/{book_id}/edit?{query}",
            data={
                "title": "Filtered Book",
                "game_system_id": dnd_id,
                "owns_physical": "on",
            },
        )

        assert response.url.path == f"/books/{book_id}"
        assert response.url.query.decode() == query
        assert '<span class="book-navigation-position">1 of 1</span>' in response.text

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
