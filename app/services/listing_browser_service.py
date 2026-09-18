from __future__ import annotations

import re

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.models import (
    Listing,
    ListingPriority,
    ListingStatus,
)
from app.services.listing_service import (
    get_all_listings,
)


SORT_NEWEST = "newest"
SORT_OLDEST = "oldest"
SORT_LAST_RELISTED = "last_relisted"
SORT_PRICE_LOW_HIGH = "price_low_high"
SORT_PRICE_HIGH_LOW = "price_high_low"
SORT_MOST_RELISTED = "most_relisted"
SORT_LEAST_RELISTED = "least_relisted"


AGE_ALL = "all"
AGE_NEVER_RELISTED = "never_relisted"
AGE_14_PLUS = "14_plus"
AGE_30_PLUS = "30_plus"
AGE_60_PLUS = "60_plus"
AGE_90_PLUS = "90_plus"


@dataclass(slots=True)
class ListingBrowserFilters:
    """
    Filters used by the All Listings browser.
    """

    search_text: str = ""

    status: ListingStatus | None = None
    age_filter: str = AGE_ALL
    priority: ListingPriority | None = None

    category: str | None = None
    brand: str | None = None

    subcategory: str | None = None
    condition: str | None = None
    size: str | None = None
    colour: str | None = None

    minimum_price: Decimal | None = None
    maximum_price: Decimal | None = None

    sort_by: str = SORT_NEWEST


@dataclass(slots=True)
class ListingBrowserResult:
    """
    Result returned to the All Listings UI.
    """

    listings: list[Listing]

    total_count: int
    filtered_count: int

    # Keep the original order of categories and brands so older
    # callers remain compatible.
    categories: list[str] = field(
        default_factory=list
    )

    brands: list[str] = field(
        default_factory=list
    )

    subcategories: list[str] = field(
        default_factory=list
    )

    conditions: list[str] = field(
        default_factory=list
    )

    sizes: list[str] = field(
        default_factory=list
    )

    colours: list[str] = field(
        default_factory=list
    )


def get_listing_browser_result(
    filters: ListingBrowserFilters,
    today: date | None = None,
) -> ListingBrowserResult:
    """
    Load listings and apply browser filters and sorting.
    """
    target_date = (
        today
        or date.today()
    )

    all_listings = (
        get_all_listings()
    )

    categories = _unique_values(
        all_listings,
        "category",
    )

    brands = _unique_values(
        all_listings,
        "brand",
    )

    subcategories = _unique_values(
        all_listings,
        "subcategory",
    )

    conditions = _unique_values(
        all_listings,
        "condition",
    )

    sizes = _unique_values(
        all_listings,
        "size",
    )

    colours = _unique_values(
        all_listings,
        "colour",
    )

    filtered = [
        listing
        for listing in all_listings
        if _matches_filters(
            listing,
            filters,
            target_date,
        )
    ]

    _sort_listings(
        filtered,
        filters.sort_by,
    )

    return ListingBrowserResult(
        listings=filtered,
        total_count=len(
            all_listings
        ),
        filtered_count=len(
            filtered
        ),
        categories=categories,
        brands=brands,
        subcategories=subcategories,
        conditions=conditions,
        sizes=sizes,
        colours=colours,
    )


def _unique_values(
    listings: list[Listing],
    attribute_name: str,
) -> list[str]:
    """
    Collect clean unique values from one Listing text field.
    """
    values: set[str] = set()

    for listing in listings:
        value = getattr(
            listing,
            attribute_name,
            None,
        )

        if (
            value is None
            or not isinstance(
                value,
                str,
            )
        ):
            continue

        cleaned = value.strip()

        if cleaned:
            values.add(
                cleaned
            )

    return sorted(
        values,
        key=str.casefold,
    )


def _matches_filters(
    listing: Listing,
    filters: ListingBrowserFilters,
    today: date,
) -> bool:
    """
    Return True when one listing passes every active filter.
    """
    search_text = (
        filters.search_text
        .strip()
        .casefold()
    )

    if search_text:
        searchable_values = [
            listing.title,
            listing.description,
            listing.category,
            listing.subcategory,
            listing.brand,
            listing.size,
            listing.condition,
            listing.colour,
            listing.material,
            listing.parcel_size,
            listing.isbn,
        ]

        searchable_text = " ".join(
            str(value)
            for value in searchable_values
            if value
        ).casefold()

        ordinary_match = (
            search_text
            in searchable_text
        )

        isbn_match = (
            _matches_isbn_search(
                listing,
                search_text,
            )
        )

        if (
            not ordinary_match
            and not isbn_match
        ):
            return False

    if (
        filters.status is not None
        and listing.status
        != filters.status
    ):
        return False

    if (
        filters.priority is not None
        and listing.priority
        != filters.priority
    ):
        return False

    if not _matches_text_filter(
        listing.category,
        filters.category,
    ):
        return False

    if not _matches_text_filter(
        listing.subcategory,
        filters.subcategory,
    ):
        return False

    if not _matches_text_filter(
        listing.brand,
        filters.brand,
    ):
        return False

    if not _matches_text_filter(
        listing.condition,
        filters.condition,
    ):
        return False

    if not _matches_text_filter(
        listing.size,
        filters.size,
    ):
        return False

    if not _matches_text_filter(
        listing.colour,
        filters.colour,
    ):
        return False

    price = Decimal(
        str(
            listing.price
        )
    )

    if (
        filters.minimum_price
        is not None
        and price
        < filters.minimum_price
    ):
        return False

    if (
        filters.maximum_price
        is not None
        and price
        > filters.maximum_price
    ):
        return False

    if (
        filters.age_filter
        == AGE_NEVER_RELISTED
    ):
        if (
            listing.last_relisted_date
            is not None
        ):
            return False

    elif (
        filters.age_filter
        == AGE_14_PLUS
    ):
        if (
            _days_since_rotation(
                listing,
                today,
            )
            < 14
        ):
            return False

    elif (
        filters.age_filter
        == AGE_30_PLUS
    ):
        if (
            _days_since_rotation(
                listing,
                today,
            )
            < 30
        ):
            return False

    elif (
        filters.age_filter
        == AGE_60_PLUS
    ):
        if (
            _days_since_rotation(
                listing,
                today,
            )
            < 60
        ):
            return False

    elif (
        filters.age_filter
        == AGE_90_PLUS
    ):
        if (
            _days_since_rotation(
                listing,
                today,
            )
            < 90
        ):
            return False

    return True


def _matches_text_filter(
    listing_value: str | None,
    requested_value: str | None,
) -> bool:
    """
    Perform a case-insensitive exact comparison for dropdown filters.
    """
    if not requested_value:
        return True

    if not listing_value:
        return False

    return (
        listing_value
        .strip()
        .casefold()
        ==
        requested_value
        .strip()
        .casefold()
    )


def _matches_isbn_search(
    listing: Listing,
    search_text: str,
) -> bool:
    """
    Match an ISBN even when spaces or hyphens are typed.
    """
    if not listing.isbn:
        return False

    normalized_search = re.sub(
        r"[\s-]+",
        "",
        search_text,
    ).upper()

    normalized_isbn = re.sub(
        r"[\s-]+",
        "",
        listing.isbn,
    ).upper()

    if not normalized_search:
        return False

    if not re.fullmatch(
        r"\d{1,13}X?",
        normalized_search,
    ):
        return False

    return (
        normalized_search
        in normalized_isbn
    )


def _days_since_rotation(
    listing: Listing,
    today: date,
) -> int:
    """
    Age since the most recent relist, or original creation
    when the listing has never been relisted.
    """
    reference_date = (
        listing.last_relisted_date
        or listing.original_created_date
    )

    return max(
        0,
        (
            today
            - reference_date
        ).days,
    )


def _sort_listings(
    listings: list[Listing],
    sort_by: str,
) -> None:
    """
    Sort listing results in place.
    """
    if (
        sort_by
        == SORT_OLDEST
    ):
        listings.sort(
            key=lambda listing: (
                listing.original_created_date,
                listing.id,
            )
        )

        return

    if (
        sort_by
        == SORT_LAST_RELISTED
    ):
        listings.sort(
            key=_last_relisted_sort_key
        )

        return

    if (
        sort_by
        == SORT_PRICE_LOW_HIGH
    ):
        listings.sort(
            key=lambda listing: (
                Decimal(
                    str(
                        listing.price
                    )
                ),
                listing.id,
            )
        )

        return

    if (
        sort_by
        == SORT_PRICE_HIGH_LOW
    ):
        listings.sort(
            key=lambda listing: (
                Decimal(
                    str(
                        listing.price
                    )
                ),
                listing.id,
            ),
            reverse=True,
        )

        return

    if (
        sort_by
        == SORT_MOST_RELISTED
    ):
        listings.sort(
            key=lambda listing: (
                listing.number_of_times_relisted,
                listing.original_created_date,
                listing.id,
            ),
            reverse=True,
        )

        return

    if (
        sort_by
        == SORT_LEAST_RELISTED
    ):
        listings.sort(
            key=lambda listing: (
                listing.number_of_times_relisted,
                listing.original_created_date,
                listing.id,
            )
        )

        return

    listings.sort(
        key=lambda listing: (
            listing.original_created_date,
            listing.id,
        ),
        reverse=True,
    )


def _last_relisted_sort_key(
    listing: Listing,
) -> tuple:
    """
    Never-relisted items first, followed by the oldest
    relisted items.
    """
    if (
        listing.last_relisted_date
        is None
    ):
        return (
            0,
            listing.original_created_date,
            listing.id,
        )

    return (
        1,
        listing.last_relisted_date,
        listing.id,
    )