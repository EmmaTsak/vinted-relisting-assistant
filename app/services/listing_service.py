from __future__ import annotations

import re

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.database import (
    session_scope,
)
from app.models import (
    Listing,
    ListingPhoto,
    ListingPriority,
)


class ListingNotFoundError(Exception):
    """Raised when a requested listing does not exist."""


class InvalidISBNError(ValueError):
    """Raised when an ISBN is not a valid ISBN-10 or ISBN-13."""


@dataclass(slots=True)
class ListingInput:
    """
    Data required to create or update a listing.
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

    isbn: str | None = None

    notes: str = ""

    original_created_date: date | None = None

    priority: ListingPriority = (
        ListingPriority.NORMAL
    )


def _clean_optional_text(
    value: str | None,
) -> str | None:
    """
    Convert empty/whitespace-only optional text to None.
    """
    if value is None:
        return None

    cleaned = value.strip()

    return (
        cleaned
        if cleaned
        else None
    )


def normalize_isbn(
    value: str | None,
) -> str | None:
    """
    Normalize and validate an optional ISBN.

    Accepts:
    - ISBN-10
    - ISBN-13
    - spaces
    - hyphens
    - ISBN-10 ending in X

    Stored format contains digits only, or X as the final
    ISBN-10 character.
    """
    if value is None:
        return None

    raw = value.strip()

    if not raw:
        return None

    normalized = re.sub(
        r"[\s-]+",
        "",
        raw,
    ).upper()

    if (
        len(normalized) == 10
        and _is_valid_isbn10(
            normalized
        )
    ):
        return normalized

    if (
        len(normalized) == 13
        and _is_valid_isbn13(
            normalized
        )
    ):
        return normalized

    raise InvalidISBNError(
        (
            "ISBN must be a valid ISBN-10 "
            "or ISBN-13."
        )
    )


def _is_valid_isbn10(
    value: str,
) -> bool:
    if not re.fullmatch(
        r"\d{9}[\dX]",
        value,
    ):
        return False

    total = 0

    for index, character in enumerate(
        value
    ):
        if (
            index == 9
            and character == "X"
        ):
            digit = 10

        else:
            digit = int(
                character
            )

        weight = 10 - index

        total += (
            digit
            * weight
        )

    return (
        total % 11
        == 0
    )


def _is_valid_isbn13(
    value: str,
) -> bool:
    if not value.isdigit():
        return False

    if len(value) != 13:
        return False

    total = 0

    for index, character in enumerate(
        value[:12]
    ):
        digit = int(
            character
        )

        multiplier = (
            1
            if index % 2 == 0
            else 3
        )

        total += (
            digit
            * multiplier
        )

    check_digit = (
        10
        - (
            total
            % 10
        )
    ) % 10

    return (
        check_digit
        == int(
            value[-1]
        )
    )


def _prepare_input(
    data: ListingInput,
) -> ListingInput:
    """
    Normalize listing form input before storing it.
    """
    return ListingInput(
        title=(
            data.title.strip()
        ),
        description=(
            data.description.strip()
        ),
        price=data.price,
        currency=(
            data.currency
            .strip()
            .upper()
        ),
        category=_clean_optional_text(
            data.category
        ),
        subcategory=_clean_optional_text(
            data.subcategory
        ),
        brand=_clean_optional_text(
            data.brand
        ),
        size=_clean_optional_text(
            data.size
        ),
        condition=_clean_optional_text(
            data.condition
        ),
        colour=_clean_optional_text(
            data.colour
        ),
        material=_clean_optional_text(
            data.material
        ),
        parcel_size=_clean_optional_text(
            data.parcel_size
        ),
        isbn=normalize_isbn(
            data.isbn
        ),
        notes=(
            data.notes.strip()
        ),
        original_created_date=(
            data.original_created_date
            or date.today()
        ),
        priority=data.priority,
    )


def create_listing(
    data: ListingInput,
) -> int:
    """
    Create a listing and return its generated database ID.
    """
    prepared = _prepare_input(
        data
    )

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
            isbn=prepared.isbn,
            notes=prepared.notes,
            original_created_date=(
                prepared.original_created_date
            ),
            priority=prepared.priority,
        )

        session.add(
            listing
        )

        session.flush()

        listing_id = (
            listing.id
        )

    return listing_id


def update_listing(
    listing_id: int,
    data: ListingInput,
) -> None:
    """
    Update an existing listing.
    """
    prepared = _prepare_input(
        data
    )

    with session_scope() as session:
        listing = session.get(
            Listing,
            listing_id,
        )

        if listing is None:
            raise ListingNotFoundError(
                (
                    "Listing with ID "
                    f"{listing_id} does not exist."
                )
            )

        listing.title = (
            prepared.title
        )

        listing.description = (
            prepared.description
        )

        listing.price = (
            prepared.price
        )

        listing.currency = (
            prepared.currency
        )

        listing.category = (
            prepared.category
        )

        listing.subcategory = (
            prepared.subcategory
        )

        listing.brand = (
            prepared.brand
        )

        listing.size = (
            prepared.size
        )

        listing.condition = (
            prepared.condition
        )

        listing.colour = (
            prepared.colour
        )

        listing.material = (
            prepared.material
        )

        listing.parcel_size = (
            prepared.parcel_size
        )

        listing.isbn = (
            prepared.isbn
        )

        listing.notes = (
            prepared.notes
        )

        listing.original_created_date = (
            prepared.original_created_date
        )

        listing.priority = (
            prepared.priority
        )


def get_listing(
    listing_id: int,
) -> Listing:
    """
    Retrieve one listing by ID.
    """
    with session_scope() as session:
        listing = session.get(
            Listing,
            listing_id,
        )

        if listing is None:
            raise ListingNotFoundError(
                (
                    "Listing with ID "
                    f"{listing_id} does not exist."
                )
            )

        session.expunge(
            listing
        )

        return listing


def get_all_listings() -> list[Listing]:
    """
    Return all listings, newest database records first.
    """
    with session_scope() as session:
        statement = (
            select(
                Listing
            )
            .order_by(
                Listing.id.desc()
            )
        )

        listings = list(
            session.scalars(
                statement
            ).all()
        )

        for listing in listings:
            session.expunge(
                listing
            )

        return listings


def get_listing_photos_for_listings(
    listing_ids: list[int],
) -> dict[
    int,
    list[ListingPhoto],
]:
    """
    Load photos for multiple listings in one database query.

    This avoids one separate database query for every visible card.
    """
    if not listing_ids:
        return {}

    unique_ids = list(
        dict.fromkeys(
            listing_ids
        )
    )

    result: dict[
        int,
        list[ListingPhoto],
    ] = {
        listing_id: []
        for listing_id in unique_ids
    }

    with session_scope() as session:
        photos = list(
            session.scalars(
                select(
                    ListingPhoto
                )
                .where(
                    ListingPhoto.listing_id.in_(
                        unique_ids
                    )
                )
                .order_by(
                    ListingPhoto.listing_id,
                    ListingPhoto.display_order,
                    ListingPhoto.id,
                )
            ).all()
        )

        for photo in photos:
            result.setdefault(
                photo.listing_id,
                [],
            ).append(
                photo
            )

        for photo in photos:
            session.expunge(
                photo
            )

    return result