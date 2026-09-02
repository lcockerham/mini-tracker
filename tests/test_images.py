import io
import re

import pytest
from PIL import Image, PngImagePlugin
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import image_service
from app.database import Base
from app.image_service import (
    ImageValidationError,
    attach_uploaded_image,
    remove_book_image,
    set_primary_image,
    validate_and_process,
)
from app.models import Book, BookImage, ImageAsset


def image_bytes(
    image_format="PNG",
    size=(80, 120),
    color="navy",
    *,
    exif=None,
    pnginfo=None,
):
    output = io.BytesIO()
    Image.new("RGB", size, color).save(
        output,
        image_format,
        exif=exif,
        pnginfo=pnginfo,
    )
    return output.getvalue()


@pytest.fixture()
def image_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = testing_session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestImageProcessing:
    def test_normalizes_and_strips_metadata(self):
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("private-note", "do not retain")
        processed = validate_and_process(
            image_bytes(pnginfo=metadata),
            "image/png",
        )

        assert processed.mime_type == "image/png"
        assert (processed.width, processed.height) == (80, 120)
        with Image.open(io.BytesIO(processed.original)) as normalized:
            assert "private-note" not in normalized.info

    def test_corrects_exif_orientation(self):
        exif = Image.Exif()
        exif[274] = 6
        processed = validate_and_process(
            image_bytes("JPEG", size=(80, 120), exif=exif),
            "image/jpeg",
        )

        assert (processed.width, processed.height) == (120, 80)

    def test_never_upscales_derivatives(self):
        processed = validate_and_process(image_bytes(size=(40, 60)), "image/png")

        with Image.open(io.BytesIO(processed.list_thumbnail)) as thumbnail:
            assert thumbnail.size == (40, 60)
        with Image.open(io.BytesIO(processed.detail_image)) as detail:
            assert detail.size == (40, 60)

    @pytest.mark.parametrize(
        ("contents", "mime_type", "message"),
        [
            (b"<svg></svg>", "image/svg+xml", "Only JPEG, PNG, and WebP"),
            (b"not an image", "image/png", "not a valid image"),
            (image_bytes(), "image/jpeg", "do not match"),
        ],
    )
    def test_rejects_unsupported_invalid_and_mislabeled_files(
        self,
        contents,
        mime_type,
        message,
    ):
        with pytest.raises(ImageValidationError, match=message):
            validate_and_process(contents, mime_type)

    def test_rejects_excessive_dimensions(self, monkeypatch):
        monkeypatch.setattr(image_service, "MAX_IMAGE_PIXELS", 100)

        with pytest.raises(ImageValidationError, match="dimensions are too large"):
            validate_and_process(image_bytes(size=(11, 10)), "image/png")


class TestImageStorage:
    def test_deduplicates_bytes_and_removes_only_unreferenced_files(
        self,
        image_db,
        tmp_path,
        monkeypatch,
    ):
        monkeypatch.setattr(image_service, "MEDIA_ROOT", tmp_path)
        first_book = Book(title="First")
        second_book = Book(title="Second")
        image_db.add_all([first_book, second_book])
        image_db.commit()
        contents = image_bytes()

        first_link = attach_uploaded_image(
            image_db,
            first_book,
            contents,
            "image/png",
        )
        second_link = attach_uploaded_image(
            image_db,
            second_book,
            contents,
            "image/png",
        )

        assert image_db.query(ImageAsset).count() == 1
        assert image_db.query(BookImage).count() == 2
        original_path = tmp_path / first_link.image_asset.local_path
        assert original_path.is_file()

        remove_book_image(image_db, first_book, first_link)
        assert image_db.query(ImageAsset).count() == 1
        assert original_path.is_file()

        remove_book_image(image_db, second_book, second_link)
        assert image_db.query(ImageAsset).count() == 0
        assert not original_path.exists()

    def test_database_enforces_one_primary_per_book(self, image_db):
        book = Book(title="One Cover")
        assets = [
            ImageAsset(
                local_path=f"images/original/{number}.png",
                thumbnail_path=f"images/list/{number}.png",
                detail_path=f"images/detail/{number}.png",
                sha256=str(number) * 64,
                mime_type="image/png",
                width=10,
                height=10,
                byte_size=100,
                provider="manual",
                rights_status="user_owned",
            )
            for number in (1, 2)
        ]
        image_db.add_all([book, *assets])
        image_db.flush()
        image_db.add_all(
            [BookImage(book=book, image_asset=asset, is_primary=True) for asset in assets]
        )

        with pytest.raises(IntegrityError):
            image_db.commit()

    def test_can_switch_primary_in_both_directions(
        self,
        image_db,
        tmp_path,
        monkeypatch,
    ):
        monkeypatch.setattr(image_service, "MEDIA_ROOT", tmp_path)
        book = Book(title="Switch Covers")
        image_db.add(book)
        image_db.commit()
        first = attach_uploaded_image(
            image_db,
            book,
            image_bytes(color="red"),
            "image/png",
        )
        second = attach_uploaded_image(
            image_db,
            book,
            image_bytes(color="blue"),
            "image/png",
            make_primary=False,
        )

        set_primary_image(image_db, book, second)
        set_primary_image(image_db, book, first)

        primary_links = [link for link in book.image_links if link.is_primary]
        assert primary_links == [first]


class TestBookImageRoutes:
    def test_upload_display_and_remove_image(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(image_service, "MEDIA_ROOT", tmp_path)
        response = client.post("/books/new", data={"title": "Illustrated Book"})
        book_id = re.search(r"/books/(\d+)", response.url.path).group(1)

        upload = client.post(
            f"/books/{book_id}/images",
            files={"image": ("cover.png", image_bytes(), "image/png")},
            data={
                "make_primary": "on",
                "creator": "Cover Artist",
                "attribution_text": "Cover art used with permission",
                "license_name": "Personal use",
            },
        )

        assert upload.status_code == 200
        assert "Cover Artist" in upload.text
        assert "Cover art used with permission" in upload.text
        assert "/media/images/detail/" in upload.text
        assert len(list((tmp_path / "images" / "original").iterdir())) == 1
        list_page = client.get("/books")
        assert "/media/images/list/" in list_page.text
        assert 'loading="lazy"' in list_page.text

        image_asset_id = re.search(
            rf"/books/{book_id}/images/(\d+)/remove",
            upload.text,
        ).group(1)
        removed = client.post(
            f"/books/{book_id}/images/{image_asset_id}/remove",
        )
        assert "No cover image" in removed.text
        assert not list((tmp_path / "images" / "original").iterdir())

    def test_rejects_svg_upload(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(image_service, "MEDIA_ROOT", tmp_path)
        response = client.post("/books/new", data={"title": "Safe Book"})
        book_id = re.search(r"/books/(\d+)", response.url.path).group(1)

        response = client.post(
            f"/books/{book_id}/images",
            files={"image": ("cover.svg", b"<svg></svg>", "image/svg+xml")},
        )

        assert response.status_code == 400
        assert "Only JPEG, PNG, and WebP" in response.text
        assert not (tmp_path / "images").exists()

    def test_rejects_unsafe_attribution_url(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(image_service, "MEDIA_ROOT", tmp_path)
        response = client.post("/books/new", data={"title": "Safe Links"})
        book_id = re.search(r"/books/(\d+)", response.url.path).group(1)

        response = client.post(
            f"/books/{book_id}/images",
            files={"image": ("cover.png", image_bytes(), "image/png")},
            data={"source_page_url": "javascript:alert(1)"},
        )

        assert response.status_code == 400
        assert "must be a valid HTTP or HTTPS URL" in response.text
        assert not (tmp_path / "images").exists()

    def test_deleting_book_removes_orphaned_image(
        self,
        client,
        tmp_path,
        monkeypatch,
    ):
        monkeypatch.setattr(image_service, "MEDIA_ROOT", tmp_path)
        response = client.post("/books/new", data={"title": "Disposable Book"})
        book_id = re.search(r"/books/(\d+)", response.url.path).group(1)
        client.post(
            f"/books/{book_id}/images",
            files={"image": ("cover.png", image_bytes(), "image/png")},
        )

        response = client.post(f"/books/{book_id}/delete")

        assert "Disposable Book" not in response.text
        assert not list((tmp_path / "images" / "original").iterdir())

    def test_book_list_is_paginated(self, client):
        for number in range(51):
            client.post("/books/new", data={"title": f"Book {number:03d}"})

        first_page = client.get("/books")
        second_page = client.get("/books", params={"page": 2})

        assert "Showing 1&ndash;50 of 51 books" in first_page.text
        assert "Book 049" in first_page.text
        assert "Book 050" not in first_page.text
        assert "Page 1 of 2" in first_page.text
        assert "Book 050" in second_page.text
        assert "Showing 51&ndash;51 of 51 books" in second_page.text
