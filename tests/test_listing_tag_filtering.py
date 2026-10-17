from __future__ import annotations

from datetime import date

from app.services.listing_browser_service import (
    ListingBrowserFilters,
    get_listing_browser_result,
)
from app.services.tag_service import (
    bulk_add_tags,
)


def _titles(
    result,
) -> set[str]:
    return {
        listing.title
        for listing
        in result.listings
    }


def test_filter_by_one_tag(
    make_listing,
) -> None:
    winter = make_listing(
        title="Winter Coat",
        original_created_date=date(
            2026,
            1,
            1,
        ),
    )

    make_listing(
        title="Summer Dress",
        original_created_date=date(
            2026,
            1,
            1,
        ),
    )

    bulk_add_tags(
        [
            winter,
        ],
        [
            "Winter",
        ],
    )

    result = get_listing_browser_result(
        ListingBrowserFilters(
            tags=(
                "Winter",
            )
        )
    )

    assert _titles(
        result
    ) == {
        "Winter Coat",
    }


def test_multiple_tags_match_any_selected_tag(
    make_listing,
) -> None:
    winter = make_listing(
        title="Winter Coat",
        original_created_date=date(
            2026,
            1,
            1,
        ),
    )

    christmas = make_listing(
        title="Christmas Dress",
        original_created_date=date(
            2026,
            1,
            1,
        ),
    )

    make_listing(
        title="Summer Top",
        original_created_date=date(
            2026,
            1,
            1,
        ),
    )

    bulk_add_tags(
        [
            winter,
        ],
        [
            "Winter",
        ],
    )

    bulk_add_tags(
        [
            christmas,
        ],
        [
            "Christmas",
        ],
    )

    result = get_listing_browser_result(
        ListingBrowserFilters(
            tags=(
                "Winter",
                "Christmas",
            )
        )
    )

    assert _titles(
        result
    ) == {
        "Winter Coat",
        "Christmas Dress",
    }


def test_search_matches_tag_name(
    make_listing,
) -> None:
    listing_id = make_listing(
        title="Black Coat",
        original_created_date=date(
            2026,
            1,
            1,
        ),
    )

    make_listing(
        title="Blue Shirt",
        original_created_date=date(
            2026,
            1,
            1,
        ),
    )

    bulk_add_tags(
        [
            listing_id,
        ],
        [
            "Cold Weather",
        ],
    )

    result = get_listing_browser_result(
        ListingBrowserFilters(
            search_text="cold weather"
        )
    )

    assert _titles(
        result
    ) == {
        "Black Coat",
    }


def test_browser_result_exposes_available_tags(
    make_listing,
) -> None:
    first = make_listing(
        title="Coat",
        original_created_date=date(
            2026,
            1,
            1,
        ),
    )

    second = make_listing(
        title="Dress",
        original_created_date=date(
            2026,
            1,
            1,
        ),
    )

    bulk_add_tags(
        [
            first,
        ],
        [
            "Winter",
        ],
    )

    bulk_add_tags(
        [
            second,
        ],
        [
            "Christmas",
        ],
    )

    result = get_listing_browser_result(
        ListingBrowserFilters()
    )

    assert result.tags == [
        "Christmas",
        "Winter",
    ]
