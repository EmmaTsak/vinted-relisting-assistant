from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.models import Listing
from app.services.listing_browser_service import (
    ListingBrowserFilters,
    get_listing_browser_result,
)
from app.services.queue_service import (
    get_manual_selection_unavailable_ids,
    is_listing_relist_eligible,
)


@dataclass(slots=True)
class ManualRelistResult:
    listings: list[Listing]

    categories: list[str]
    subcategories: list[str]
    tags: list[str]
    brands: list[str]
    sizes: list[str]


def get_manual_relist_result(
    filters: ListingBrowserFilters,
    *,
    minimum_age_days: int,
    today: date | None = None,
) -> ManualRelistResult:
    """
    Return listings that may actually be chosen for relisting.

    The normal listing-browser filter engine is reused, but lifecycle
    eligibility comes from queue_service so Smart and Manual modes
    cannot disagree about which listings are valid.
    """
    target_date = (
        today
        or date.today()
    )

    browser = (
        get_listing_browser_result(
            filters,
            today=target_date,
        )
    )

    unavailable_ids = (
        get_manual_selection_unavailable_ids(
            today=target_date
        )
    )

    eligible = [
        listing
        for listing in browser.listings
        if (
            listing.id
            not in unavailable_ids
            and is_listing_relist_eligible(
                listing,
                minimum_age_days,
                today=target_date,
            )
        )
    ]

    return ManualRelistResult(
        listings=eligible,
        categories=browser.categories,
        subcategories=(
            browser.subcategories
        ),
        tags=browser.tags,
        brands=browser.brands,
        sizes=browser.sizes,
    )
