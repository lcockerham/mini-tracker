from __future__ import annotations

import hashlib
import io
import os
import warnings
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Optional
from urllib.parse import urlsplit

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Book, BookImage, ImageAsset

MEDIA_ROOT = Path(
    os.environ.get(
        "MINI_TRACKER_MEDIA_DIR",
        Path(__file__).resolve().parent.parent / "media",
    )
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
LIST_IMAGE_SIZE = (160, 220)
DETAIL_IMAGE_SIZE = (600, 800)

FORMAT_MIME_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}
FORMAT_EXTENSIONS = {
    "JPEG": "jpg",
    "PNG": "png",
    "WEBP": "webp",
}


class ImageValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ProcessedImage:
    sha256: str
    mime_type: str
    extension: str
    width: int
    height: int
    original: bytes
    list_thumbnail: bytes
    detail_image: bytes

    @property
    def byte_size(self) -> int:
        return len(self.original)


def ensure_media_directories() -> None:
    for variant in ("original", "list", "detail"):
        (MEDIA_ROOT / "images" / variant).mkdir(parents=True, exist_ok=True)


def _save_image(image: Image.Image, image_format: str) -> bytes:
    output = io.BytesIO()
    if image_format == "JPEG":
        if image.mode not in ("L", "RGB"):
            image = image.convert("RGB")
        image.save(output, "JPEG", quality=90, optimize=True, progressive=True)
    elif image_format == "PNG":
        image.save(output, "PNG", optimize=True)
    else:
        image.save(output, "WEBP", quality=88, method=6)
    return output.getvalue()


def _derivative(image: Image.Image, size: tuple[int, int], image_format: str) -> bytes:
    derivative = image.copy()
    derivative.thumbnail(size, Image.Resampling.LANCZOS)
    return _save_image(derivative, image_format)


def validate_and_process(contents: bytes, declared_mime_type: Optional[str]) -> ProcessedImage:
    if not contents:
        raise ImageValidationError("Choose a non-empty image file.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise ImageValidationError("Image files must be 10 MB or smaller.")

    declared_mime_type = (declared_mime_type or "").partition(";")[0].strip().lower()
    if declared_mime_type not in FORMAT_MIME_TYPES.values():
        raise ImageValidationError("Only JPEG, PNG, and WebP images are supported.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(contents)) as opened:
                image_format = opened.format
                if image_format not in FORMAT_MIME_TYPES:
                    raise ImageValidationError("Only JPEG, PNG, and WebP images are supported.")
                width, height = opened.size
                if width * height > MAX_IMAGE_PIXELS:
                    raise ImageValidationError(
                        "Image dimensions are too large (40 megapixels maximum)."
                    )
                opened.verify()

            with Image.open(io.BytesIO(contents)) as opened:
                image = ImageOps.exif_transpose(opened)
                image.load()
                image = image.copy()
    except ImageValidationError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ImageValidationError(
            "Image dimensions are too large (40 megapixels maximum)."
        ) from None
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise ImageValidationError("The uploaded file is not a valid image.") from None

    actual_mime_type = FORMAT_MIME_TYPES[image_format]
    if declared_mime_type != actual_mime_type:
        raise ImageValidationError("The file contents do not match its media type.")

    normalized = _save_image(image, image_format)
    return ProcessedImage(
        sha256=hashlib.sha256(normalized).hexdigest(),
        mime_type=actual_mime_type,
        extension=FORMAT_EXTENSIONS[image_format],
        width=image.width,
        height=image.height,
        original=normalized,
        list_thumbnail=_derivative(image, LIST_IMAGE_SIZE, image_format),
        detail_image=_derivative(image, DETAIL_IMAGE_SIZE, image_format),
    )


def _relative_paths(image: ProcessedImage) -> tuple[str, str, str]:
    filename = f"{image.sha256}.{image.extension}"
    return (
        str(PurePosixPath("images", "original", filename)),
        str(PurePosixPath("images", "list", filename)),
        str(PurePosixPath("images", "detail", filename)),
    )


def _write_processed_image(image: ProcessedImage) -> tuple[str, str, str]:
    ensure_media_directories()
    paths = _relative_paths(image)
    for relative_path, contents in zip(
        paths,
        (image.original, image.list_thumbnail, image.detail_image),
        strict=True,
    ):
        destination = MEDIA_ROOT / relative_path
        if not destination.exists():
            destination.write_bytes(contents)
    return paths


def _optional_http_url(value: Optional[str], label: str) -> Optional[str]:
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ImageValidationError(f"{label} must be a valid HTTP or HTTPS URL.")
    return value


def attach_uploaded_image(
    db: Session,
    book: Book,
    contents: bytes,
    declared_mime_type: Optional[str],
    *,
    make_primary: bool = True,
    creator: Optional[str] = None,
    attribution_text: Optional[str] = None,
    license_name: Optional[str] = None,
    license_url: Optional[str] = None,
    source_page_url: Optional[str] = None,
    rights_status: str = "user_owned",
) -> BookImage:
    license_url = _optional_http_url(license_url, "License URL")
    source_page_url = _optional_http_url(source_page_url, "Source page URL")
    processed = validate_and_process(contents, declared_mime_type)
    asset = db.query(ImageAsset).filter(ImageAsset.sha256 == processed.sha256).one_or_none()

    if asset is None:
        local_path, thumbnail_path, detail_path = _write_processed_image(processed)
        asset = ImageAsset(
            local_path=local_path,
            thumbnail_path=thumbnail_path,
            detail_path=detail_path,
            sha256=processed.sha256,
            mime_type=processed.mime_type,
            width=processed.width,
            height=processed.height,
            byte_size=processed.byte_size,
            provider="manual",
            creator=creator or None,
            attribution_text=attribution_text or None,
            license_name=license_name or None,
            license_url=license_url or None,
            source_page_url=source_page_url or None,
            rights_status=rights_status,
        )
        db.add(asset)
        db.flush()
    else:
        metadata = {
            "creator": creator,
            "attribution_text": attribution_text,
            "license_name": license_name,
            "license_url": license_url,
            "source_page_url": source_page_url,
        }
        for field, value in metadata.items():
            if value and not getattr(asset, field):
                setattr(asset, field, value)
        if asset.rights_status == "unknown" and rights_status != "unknown":
            asset.rights_status = rights_status

    existing_link = db.get(BookImage, (book.id, asset.id))
    if existing_link is not None:
        if make_primary and not existing_link.is_primary:
            set_primary_image(db, book, existing_link)
        else:
            db.commit()
        return existing_link

    has_images = bool(book.image_links)
    should_be_primary = make_primary or not has_images
    if should_be_primary:
        for link in book.image_links:
            link.is_primary = False
        db.flush()

    max_sort_order = (
        db.query(func.max(BookImage.sort_order)).filter(BookImage.book_id == book.id).scalar()
    )
    link = BookImage(
        book=book,
        image_asset=asset,
        is_primary=should_be_primary,
        sort_order=(max_sort_order if max_sort_order is not None else -1) + 1,
    )
    db.add(link)
    db.commit()
    return link


def set_primary_image(db: Session, book: Book, link: BookImage) -> None:
    if link.book_id != book.id:
        raise ValueError("Image does not belong to this book.")
    for image_link in book.image_links:
        image_link.is_primary = False
    db.flush()
    link.is_primary = True
    db.commit()


def _resolved_media_path(relative_path: str) -> Path:
    media_root = MEDIA_ROOT.resolve()
    path = (media_root / relative_path).resolve()
    if media_root not in path.parents:
        raise ValueError("Invalid stored media path.")
    return path


def _remove_asset_files(asset: ImageAsset) -> None:
    for relative_path in (asset.local_path, asset.thumbnail_path, asset.detail_path):
        path = _resolved_media_path(relative_path)
        if path.is_file():
            path.unlink()


def remove_book_image(db: Session, book: Book, link: BookImage) -> None:
    if link.book_id != book.id:
        raise ValueError("Image does not belong to this book.")

    asset = link.image_asset
    was_primary = link.is_primary
    db.delete(link)
    db.flush()

    if was_primary:
        replacement = (
            db.query(BookImage)
            .filter(BookImage.book_id == book.id)
            .order_by(BookImage.sort_order, BookImage.image_asset_id)
            .first()
        )
        if replacement is not None:
            replacement.is_primary = True

    remaining_uses = db.query(BookImage).filter(BookImage.image_asset_id == asset.id).count()
    delete_asset = remaining_uses == 0
    if delete_asset:
        db.delete(asset)
    db.commit()

    if delete_asset:
        _remove_asset_files(asset)


def delete_book_with_images(db: Session, book: Book) -> None:
    assets = [link.image_asset for link in book.image_links]
    db.delete(book)
    db.flush()

    orphaned_assets = []
    for asset in assets:
        remaining_uses = db.query(BookImage).filter(BookImage.image_asset_id == asset.id).count()
        if remaining_uses == 0:
            orphaned_assets.append(asset)
            db.delete(asset)
    db.commit()

    for asset in orphaned_assets:
        _remove_asset_files(asset)
