from __future__ import annotations

from dataclasses import dataclass
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

    categories: list[str]
    brands: list[str]


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

    all_listings = get_all_listings()

    categories = sorted(
        {
            listing.category.strip()
            for listing in all_listings
            if (
                listing.category
                and listing.category.strip()
            )
        },
        key=str.casefold,
    )

    brands = sorted(
        {
            listing.brand.strip()
            for listing in all_listings
            if (
                listing.brand
                and listing.brand.strip()
            )
        },
        key=str.casefold,
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
        searchable_text = (
            f"{listing.title} "
            f"{listing.description}"
        ).casefold()

        if search_text not in searchable_text:
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

    if filters.category:
        requested_category = (
            filters.category
            .strip()
            .casefold()
        )

        listing_category = (
            listing.category
            or ""
        ).casefold()

        if (
            requested_category
            not in listing_category
        ):
            return False

    if filters.brand:
        requested_brand = (
            filters.brand
            .strip()
            .casefold()
        )

        listing_brand = (
            listing.brand
            or ""
        ).casefold()

        if (
            requested_brand
            not in listing_brand
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


def _days_since_rotation(
    listing: Listing,
    today: date,
) -> int:
    """
    Age used by the 30+/60+/90+ filters.

    If the listing has been relisted, use the most recent relist date.

    Otherwise use its original listing date.
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
    Sort never-relisted items first, then the oldest relisted items.

    This makes the sort useful for identifying listings that have
    gone longest without refreshing.
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