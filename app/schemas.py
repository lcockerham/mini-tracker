from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.models import MiniStatus

# --- Mini ---

class MiniCreate(BaseModel):
    name: str
    creature_type: Optional[str] = None
    manufacturer: Optional[str] = None
    product_line: Optional[str] = None
    set_name: Optional[str] = None
    mini_number: Optional[str] = None
    size: Optional[str] = None
    rarity: Optional[str] = None
    status: MiniStatus = MiniStatus.UNPAINTED
    quantity: int = 1
    completion_date: Optional[date] = None
    notes: Optional[str] = None


class MiniUpdate(BaseModel):
    name: Optional[str] = None
    creature_type: Optional[str] = None
    manufacturer: Optional[str] = None
    product_line: Optional[str] = None
    set_name: Optional[str] = None
    mini_number: Optional[str] = None
    size: Optional[str] = None
    rarity: Optional[str] = None
    status: Optional[MiniStatus] = None
    quantity: Optional[int] = None
    completion_date: Optional[date] = None
    notes: Optional[str] = None


class MiniResponse(BaseModel):
    id: int
    name: str
    creature_type: Optional[str]
    manufacturer: Optional[str]
    product_line: Optional[str]
    set_name: Optional[str]
    mini_number: Optional[str]
    size: Optional[str]
    rarity: Optional[str]
    status: MiniStatus
    quantity: int
    completion_date: Optional[date]
    notes: Optional[str]

    model_config = {"from_attributes": True}


# --- Paint ---

class PaintCreate(BaseModel):
    brand: str
    name: str
    quantity: int = 1


class PaintUpdate(BaseModel):
    brand: Optional[str] = None
    name: Optional[str] = None
    quantity: Optional[int] = None


class PaintResponse(BaseModel):
    id: int
    brand: str
    name: str
    quantity: int

    model_config = {"from_attributes": True}


# --- Photo ---

class PhotoCreate(BaseModel):
    url: str


class PhotoResponse(BaseModel):
    id: int
    mini_id: int
    url: str

    model_config = {"from_attributes": True}


# --- Wishlist ---

class WishlistCreate(BaseModel):
    name: str
    manufacturer: Optional[str] = None
    notes: Optional[str] = None


class WishlistResponse(BaseModel):
    id: int
    name: str
    manufacturer: Optional[str]
    notes: Optional[str]

    model_config = {"from_attributes": True}


class WishlistPurchase(BaseModel):
    quantity: int = 1


# --- Book ---

class BookCreate(BaseModel):
    title: str
    game_system_id: Optional[int] = None
    publisher: Optional[str] = None
    category: Optional[str] = None
    owns_physical: bool = False
    owns_digital: bool = False
    physical_location: Optional[str] = None
    pdf_url: Optional[str] = None
    drivethrurpg_url: Optional[str] = None
    isbn: Optional[str] = None
    acquired_date: Optional[date] = None
    notes: Optional[str] = None


class BookUpdate(BaseModel):
    title: Optional[str] = None
    game_system_id: Optional[int] = None
    publisher: Optional[str] = None
    category: Optional[str] = None
    owns_physical: Optional[bool] = None
    owns_digital: Optional[bool] = None
    physical_location: Optional[str] = None
    pdf_url: Optional[str] = None
    drivethrurpg_url: Optional[str] = None
    isbn: Optional[str] = None
    acquired_date: Optional[date] = None
    notes: Optional[str] = None


class BookResponse(BaseModel):
    id: int
    title: str
    game_system_id: Optional[int]
    publisher: Optional[str]
    category: Optional[str]
    owns_physical: bool
    owns_digital: bool
    physical_location: Optional[str]
    pdf_url: Optional[str]
    drivethrurpg_url: Optional[str]
    isbn: Optional[str]
    acquired_date: Optional[date]
    notes: Optional[str]

    model_config = {"from_attributes": True}
