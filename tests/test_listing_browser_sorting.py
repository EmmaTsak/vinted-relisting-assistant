from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from app.services.listing_browser_service import (
    SORT_LAST_RELISTED,
    _sort_listings,
)


def test_last_relisted_sort_is_newest_first_and_never_last():
    listings = [
        SimpleNamespace(
            id=1,
            title="Never relisted",
            last_relisted_date=None,
        ),
        SimpleNamespace(
            id=2,
            title="Older relist",
            last_relisted_date=date(
                2026,
                8,
                20,
            ),
        ),
        SimpleNamespace(
            id=3,
            title="Newest relist",
            last_relisted_date=date(
                2026,
                9,
                18,
            ),
        ),
    ]

    _sort_listings(
        listings,
        SORT_LAST_RELISTED,
    )

    assert [
        listing.title
        for listing in listings
    ] == [
        "Newest relist",
        "Older relist",
        "Never relisted",
    ]
