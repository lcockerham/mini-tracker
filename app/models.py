import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Table, Text
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
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    photos: Mapped[list["Photo"]] = relationship(
        back_populates="mini", cascade="all, delete-orphan"
    )

    @property
    def source_link(self) -> Optional[str]:
        """Where this mini's catalog details come from, for linking back to the source."""
        if self.source_url and self.source_url.lower().startswith(("http://", "https://")):
            return self.source_url
        # Reaper's product search resolves a SKU straight to its product page.
        if self.manufacturer == "Reaper" and self.mini_number:
            return f"https://www.reapermini.com/search/{self.mini_number}"
        return None
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
    format_availability: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    owns_physical: Mapped[bool] = mapped_column(default=False)
    owns_digital: Mapped[bool] = mapped_column(default=False)
    physical_location: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    drivethrurpg_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    acquired_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    game_system: Mapped[Optional["GameSystem"]] = relationship(back_populates="books")


class MiniCandidate(Base):
    """A mini found on Minis Gallery that is waiting for review before joining the collection."""

    __tablename__ = "mini_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Minis Gallery's per-mini image id (index.php?id=<mg_id>&task=image); stable across syncs.
    mg_id: Mapped[int] = mapped_column(Integer, unique=True)
    set_name: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(String(500))
    name: Mapped[str] = mapped_column(String(255))
    mini_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rarity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    release_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    found_at: Mapped[datetime] = mapped_column(DateTime)
    mini_id: Mapped[Optional[int]] = mapped_column(ForeignKey("minis.id"), nullable=True)

    @property
    def gallery_url(self) -> str:
        return mini_gallery_url(self.mg_id)


def mini_gallery_url(mg_id: int) -> str:
    """Minis Gallery's page for a single mini (rarity, size, set, release date)."""
    return f"https://www.minisgallery.com/index.php?id={mg_id}&task=image"


class Map(Base):
    __tablename__ = "maps"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    owns_physical: Mapped[bool] = mapped_column(default=False)
    owns_digital: Mapped[bool] = mapped_column(default=False)


class DwarvenForgeSet(Base):
    """A Dwarven Forge product you own (a pack or a one-piece item), identified by its SKU."""

    __tablename__ = "df_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    # Dwarven Forge's terrain line: Cities, Cavern, Wilderness, ...
    terrain_line: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    paint_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    copies: Mapped[int] = mapped_column(Integer, default=1)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    contents: Mapped[list["DwarvenForgeSetPiece"]] = relationship(
        back_populates="set", cascade="all, delete-orphan"
    )

    @property
    def pieces_per_copy(self) -> int:
        return sum(entry.count for entry in self.contents)

    @property
    def piece_total(self) -> int:
        return self.pieces_per_copy * self.copies


class DwarvenForgePiece(Base):
    """A Dwarven Forge piece by its code (e.g. AC-824), wherever it came from."""

    __tablename__ = "df_pieces"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Bought on its own rather than as part of a set.
    loose_quantity: Mapped[int] = mapped_column(Integer, default=0)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    set_entries: Mapped[list["DwarvenForgeSetPiece"]] = relationship(
        back_populates="piece", cascade="all, delete-orphan"
    )

    @property
    def owned_total(self) -> int:
        return self.loose_quantity + sum(
            entry.count * entry.set.copies for entry in self.set_entries
        )


class DwarvenForgeSetPiece(Base):
    """How many of a piece one copy of a set contains."""

    __tablename__ = "df_set_pieces"

    set_id: Mapped[int] = mapped_column(ForeignKey("df_sets.id"), primary_key=True)
    piece_id: Mapped[int] = mapped_column(ForeignKey("df_pieces.id"), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=1)

    set: Mapped["DwarvenForgeSet"] = relationship(back_populates="contents")
    piece: Mapped["DwarvenForgePiece"] = relationship(back_populates="set_entries")
