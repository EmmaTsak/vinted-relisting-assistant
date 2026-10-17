from __future__ import annotations

from datetime import (
    date,
    timedelta,
)

from app.models import (
    ListingStatus,
    QueueMode,
)
from app.services.listing_browser_service import (
    AGE_30_PLUS,
    ListingBrowserFilters,
)
from app.services.manual_relist_service import (
    get_manual_relist_result,
)
from app.services.queue_service import (
    add_listings_to_today_queue,
    get_today_queue,
    set_queue_mode,
)
from app.services.tag_service import (
    bulk_add_tags,
)


TODAY = date(
    2026,
    10,
    17,
)


def old(
    days: int = 90,
) -> date:
    return (
        TODAY
        - timedelta(
            days=days
        )
    )


def titles(
    result,
) -> set[str]:
    return {
        listing.title
        for listing
        in result.listings
    }


def test_manual_candidates_exclude_ineligible_lifecycle_states(
    make_listing,
) -> None:
    make_listing(
        title="Eligible Coat",
        original_created_date=old(),
    )

    make_listing(
        title="Sold Coat",
        original_created_date=old(),
        status=ListingStatus.SOLD,
        sold=True,
    )

    make_listing(
        title="Paused Coat",
        original_created_date=old(),
        status=ListingStatus.PAUSED,
        paused_indefinitely=True,
    )

    make_listing(
        title="Archived Coat",
        original_created_date=old(),
        status=ListingStatus.ARCHIVED,
        archived=True,
    )

    result = get_manual_relist_result(
        ListingBrowserFilters(),
        minimum_age_days=14,
        today=TODAY,
    )

    assert titles(
        result
    ) == {
        "Eligible Coat",
    }


def test_manual_candidates_obey_relist_age_filter(
    make_listing,
) -> None:
    make_listing(
        title="Old Coat",
        original_created_date=old(
            60
        ),
    )

    make_listing(
        title="Recent Coat",
        original_created_date=old(
            20
        ),
    )

    result = get_manual_relist_result(
        ListingBrowserFilters(
            age_filter=AGE_30_PLUS
        ),
        minimum_age_days=14,
        today=TODAY,
    )

    assert titles(
        result
    ) == {
        "Old Coat",
    }


def test_manual_candidates_support_tags(
    make_listing,
) -> None:
    winter = make_listing(
        title="Winter Coat",
        original_created_date=old(),
    )

    make_listing(
        title="Summer Dress",
        original_created_date=old(),
    )

    bulk_add_tags(
        [
            winter,
        ],
        [
            "Winter",
        ],
    )

    result = get_manual_relist_result(
        ListingBrowserFilters(
            tags=(
                "Winter",
            )
        ),
        minimum_age_days=14,
        today=TODAY,
    )

    assert titles(
        result
    ) == {
        "Winter Coat",
    }


def test_current_smart_queue_items_can_still_be_selected(
    make_listing,
) -> None:
    first = make_listing(
        title="Smart Coat",
        original_created_date=old(),
    )

    get_today_queue(
        configured_limit=1,
        minimum_age_days=14,
        today=TODAY,
    )

    result = get_manual_relist_result(
        ListingBrowserFilters(),
        minimum_age_days=14,
        today=TODAY,
    )

    assert first in {
        listing.id
        for listing
        in result.listings
    }


def test_existing_manual_queue_items_are_not_offered_again(
    make_listing,
) -> None:
    first = make_listing(
        title="Already Chosen",
        original_created_date=old(),
    )

    second = make_listing(
        title="Still Available",
        original_created_date=old(),
    )

    add_listings_to_today_queue(
        [
            first,
        ],
        configured_limit=5,
        minimum_age_days=14,
        today=TODAY,
    )

    assert (
        get_today_queue(
            configured_limit=5,
            minimum_age_days=14,
            today=TODAY,
        ).mode
        == QueueMode.MANUAL
    )

    result = get_manual_relist_result(
        ListingBrowserFilters(),
        minimum_age_days=14,
        today=TODAY,
    )

    ids = {
        listing.id
        for listing
        in result.listings
    }

    assert first not in ids
    assert second in ids
