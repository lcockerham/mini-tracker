import enum
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MiniStatus(str, enum.Enum):
    UNPAINTED = "Unpainted"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    PRE_PAINTED = "Pre-painted"


mini_paint_association = Table(
    "mini_paint",
    Base.metadata,
    Column("mini_id", Integer, ForeignKey("minis.id"), primary_key=True),
    Column("paint_id", Integer, ForeignKey("paints.id"), primary_key=True),
)


class Mini(Base):
    __tablename__ = "minis"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    creature_type: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    manufacturer: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    product_line: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    set_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    mini_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rarity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[MiniStatus] = mapped_column(
        Enum(MiniStatus), default=MiniStatus.UNPAINTED
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    completion_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    photos: Mapped[list["Photo"]] = relationship(
        back_populates="mini", cascade="all, delete-orphan"
    )
    paints: Mapped[list["Paint"]] = relationship(
        secondary=mini_paint_association, back_populates="minis"
    )


class Paint(Base):
    __tablename__ = "paints"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    minis: Mapped[list["Mini"]] = relationship(
        secondary=mini_paint_association, back_populates="paints"
    )


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    mini_id: Mapped[int] = mapped_column(ForeignKey("minis.id"))
    url: Mapped[str] = mapped_column(String(500))

    mini: Mapped["Mini"] = relationship(back_populates="photos")


class WishlistItem(Base):
    __tablename__ = "wishlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    manufacturer: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )


class GameSystem(Base):
    __tablename__ = "game_systems"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    books: Mapped[list["Book"]] = relationship(back_populates="game_system")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    game_system_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("game_systems.id"), nullable=True
    )
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    owns_physical: Mapped[bool] = mapped_column(default=False)
    owns_digital: Mapped[bool] = mapped_column(default=False)
    physical_location: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    drivethrurpg_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    isbn: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    acquired_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    game_system: Mapped[Optional["GameSystem"]] = relationship(back_populates="books")
    image_links: Mapped[list["BookImage"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
        order_by="BookImage.sort_order",
    )

    @property
    def primary_image(self) -> Optional["BookImage"]:
        return next((link for link in self.image_links if link.is_primary), None)


class ImageAsset(Base):
    __tablename__ = "image_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    local_path: Mapped[str] = mapped_column(String(500))
    remote_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    thumbnail_path: Mapped[str] = mapped_column(String(500))
    detail_path: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    byte_size: Mapped[int] = mapped_column(Integer)
    provider: Mapped[str] = mapped_column(String(50))
    provider_identifier: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    source_page_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    source_file_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    creator: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    attribution_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    license_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    license_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    rights_status: Mapped[str] = mapped_column(String(50), default="unknown")
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    book_links: Mapped[list["BookImage"]] = relationship(
        back_populates="image_asset",
        cascade="all, delete-orphan",
    )


class BookImage(Base):
    __tablename__ = "book_images"
    __table_args__ = (
        Index(
            "uq_book_images_primary",
            "book_id",
            unique=True,
            sqlite_where=text("is_primary = 1"),
        ),
    )

    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), primary_key=True
    )
    image_asset_id: Mapped[int] = mapped_column(
        ForeignKey("image_assets.id", ondelete="CASCADE"), primary_key=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    book: Mapped["Book"] = relationship(back_populates="image_links")
    image_asset: Mapped["ImageAsset"] = relationship(back_populates="book_links")
