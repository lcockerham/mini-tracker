import enum
from datetime import date
from typing import Optional

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, String, Table, Text
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
