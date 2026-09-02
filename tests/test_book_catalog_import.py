import io


class TestBookCatalogImport:
    def test_import_catalog_leaves_ownership_unset(self, client):
        csv_content = (
            "title,game_system,category,publisher,owns_physical,owns_digital,notes\n"
            "Curse of Strahd,D&D 5e,Adventure,Wizards of the Coast,,,\n"
        )
        response = client.post(
            "/books/import-catalog",
            files={"file": ("catalog.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert response.status_code == 200
        assert "Imported 1 book" in response.text

        books = client.get("/books")
        assert "Curse of Strahd" in books.text
        assert "Wizards of the Coast" in books.text

    def test_import_catalog_creates_missing_game_system(self, client):
        csv_content = (
            "title,game_system,category,publisher,owns_physical,owns_digital,notes\n"
            "Keep on the Borderlands,AD&D 1e,Module,TSR,,,Code: B2\n"
        )
        response = client.post(
            "/books/import-catalog",
            files={"file": ("catalog.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert response.status_code == 200
        list_resp = client.get("/books")
        import re
        book_id = re.search(r"/books/(\d+)", list_resp.text).group(1)
        detail = client.get(f"/books/{book_id}")
        assert "AD&amp;D 1e" in detail.text

    def test_import_catalog_skips_duplicate_title_and_system(self, client):
        csv_content = (
            "title,game_system,category,publisher,owns_physical,owns_digital,notes\n"
            "Tomb of Horrors,AD&D 1e,Module,TSR,,,\n"
            "Tomb of Horrors,AD&D 1e,Module,TSR,,,\n"
        )
        response = client.post(
            "/books/import-catalog",
            files={"file": ("catalog.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert "Imported 1 book" in response.text
        assert "1 row(s) skipped" in response.text

    def test_import_catalog_respects_owned_flag(self, client):
        csv_content = (
            "title,game_system,category,publisher,owns_physical,owns_digital,notes\n"
            "Player's Handbook,D&D 5e,Core Rulebook,Wizards of the Coast,true,,\n"
        )
        client.post(
            "/books/import-catalog",
            files={"file": ("catalog.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        list_resp = client.get("/books", params={"ownership": "physical"})
        assert "Player" in list_resp.text
