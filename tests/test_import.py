import logging
import tempfile

import pytest

import app.main
import imports.spreadsheet


@pytest.fixture()
def upload_tmpdir(tmp_path, monkeypatch):
    # Route the upload's temp file into an isolated directory so leftovers are visible.
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    return tmp_path


@pytest.fixture()
def imported_paths(monkeypatch):
    # Stub the importer so these tests never touch mini_tracker.db.
    paths = []

    def fake_import(path, db):
        paths.append(path)
        return {"added": 1, "skipped": 0}

    monkeypatch.setattr(imports.spreadsheet, "import_spreadsheet", fake_import)
    return paths


def upload(client, contents=b"workbook bytes"):
    files = {"file": ("minis.xlsx", contents, "application/octet-stream")}
    return client.post("/import", files=files)


class TestImportUpload:
    def test_temp_file_removed_after_import(self, client, upload_tmpdir, imported_paths):
        # Every import used to leave a copy of the workbook in the temp directory.
        response = upload(client)
        assert response.status_code == 200
        assert "Imported 1 miniature(s)" in response.text
        assert len(imported_paths) == 1
        assert list(upload_tmpdir.iterdir()) == []

    def test_temp_file_removed_when_import_fails(
        self, client, upload_tmpdir, monkeypatch, caplog
    ):
        def failing_import(path, db):
            raise ValueError("pandas internals: Excel file format cannot be determined")

        monkeypatch.setattr(imports.spreadsheet, "import_spreadsheet", failing_import)
        with caplog.at_level(logging.ERROR, logger="app.main"):
            response = upload(client)

        assert list(upload_tmpdir.iterdir()) == []
        # The user gets a short hint; the raw exception goes to the log, not the page.
        assert "Could not import that file" in response.text
        assert "pandas internals" not in response.text
        assert "pandas internals" in caplog.text

    def test_oversized_upload_rejected(
        self, client, upload_tmpdir, imported_paths, monkeypatch
    ):
        monkeypatch.setattr(app.main, "MAX_IMPORT_BYTES", 10)
        monkeypatch.setattr(app.main, "IMPORT_CHUNK_BYTES", 4)
        response = upload(client, contents=b"x" * 11)

        assert response.status_code == 413
        assert "File is too large" in response.text
        assert imported_paths == []
        assert list(upload_tmpdir.iterdir()) == []

    def test_upload_at_limit_is_accepted(
        self, client, upload_tmpdir, imported_paths, monkeypatch
    ):
        monkeypatch.setattr(app.main, "MAX_IMPORT_BYTES", 10)
        monkeypatch.setattr(app.main, "IMPORT_CHUNK_BYTES", 4)
        response = upload(client, contents=b"x" * 10)

        assert response.status_code == 200
        assert len(imported_paths) == 1
