from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.database import session_scope
from app.models import Listing, ListingPriority


class ListingNotFoundError(Exception):
    """Raised when a requested listing does not exist."""


@dataclass(slots=True)
class ListingInput:
    """
    Data required to create or update a listing.

    Photo handling is intentionally not included yet.
    That is implemented in Stage 6.
    """

    title: str
    description: str
    price: Decimal
    currency: str = "EUR"

    category: str | None = None
    subcategory: str | None = None
    brand: str | None = None
    size: str | None = None
    condition: str | None = None
    colour: str | None = None
    material: str | None = None
    parcel_size: str | None = None

    notes: str = ""

    original_created_date: date | None = None

    priority: ListingPriority = ListingPriority.NORMAL


def _clean_optional_text(value: str | None) -> str | None:
    """
    Convert empty/whitespace-only optional text to None.
    """
    if value is None:
        return None

    cleaned = value.strip()

    return cleaned if cleaned else None


def _prepare_input(data: ListingInput) -> ListingInput:
    """
    Normalize listing form input before storing it.
    """
    return ListingInput(
        title=data.title.strip(),
        description=data.description.strip(),
        price=data.price,
        currency=data.currency.strip().upper(),
        category=_clean_optional_text(data.category),
        subcategory=_clean_optional_text(data.subcategory),
        brand=_clean_optional_text(data.brand),
        size=_clean_optional_text(data.size),
        condition=_clean_optional_text(data.condition),
        colour=_clean_optional_text(data.colour),
        material=_clean_optional_text(data.material),
        parcel_size=_clean_optional_text(data.parcel_size),
        notes=data.notes.strip(),
        original_created_date=(
            data.original_created_date or date.today()
        ),
        priority=data.priority,
    )


def create_listing(data: ListingInput) -> int:
    """
    Create a listing and return its generated database ID.
    """
    prepared = _prepare_input(data)

    with session_scope() as session:
        listing = Listing(
            title=prepared.title,
            description=prepared.description,
            price=prepared.price,
            currency=prepared.currency,
            category=prepared.category,
            subcategory=prepared.subcategory,
            brand=prepared.brand,
            size=prepared.size,
            condition=prepared.condition,
            colour=prepared.colour,
            material=prepared.material,
            parcel_size=prepared.parcel_size,
            notes=prepared.notes,
            original_created_date=prepared.original_created_date,
            priority=prepared.priority,
        )

        session.add(listing)
        session.flush()

        listing_id = listing.id

    return listing_id


def update_listing(
    listing_id: int,
    data: ListingInput,
) -> None:
    """
    Update an existing listing.
    """
    prepared = _prepare_input(data)

    with session_scope() as session:
        listing = session.get(Listing, listing_id)

        if listing is None:
            raise ListingNotFoundError(
                f"Listing with ID {listing_id} does not exist."
            )

        listing.title = prepared.title
        listing.description = prepared.description
        listing.price = prepared.price
        listing.currency = prepared.currency

        listing.category = prepared.category
        listing.subcategory = prepared.subcategory
        listing.brand = prepared.brand
        listing.size = prepared.size
        listing.condition = prepared.condition
        listing.colour = prepared.colour
        listing.material = prepared.material
        listing.parcel_size = prepared.parcel_size

        listing.notes = prepared.notes
        listing.original_created_date = prepared.original_created_date
        listing.priority = prepared.priority


def get_listing(listing_id: int) -> Listing:
    """
    Retrieve one listing by ID.

    The returned object is detached from the database session and is
    intended for reading its ordinary scalar fields.
    """
    with session_scope() as session:
        listing = session.get(Listing, listing_id)

        if listing is None:
            raise ListingNotFoundError(
                f"Listing with ID {listing_id} does not exist."
            )

        session.expunge(listing)

        return listing


def get_all_listings() -> list[Listing]:
    """
    Return all listings, newest database records first.

    This function will be expanded during Stage 7 and Stage 12 when
    browsing, searching, filtering, and sorting are implemented.
    """
    with session_scope() as session:
        statement = select(Listing).order_by(Listing.id.desc())

        listings = list(
            session.scalars(statement).all()
        )

        for listing in listings:
            session.expunge(listing)

        return listings