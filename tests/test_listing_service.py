from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models import ListingPriority
from app.services.listing_service import (
    ListingInput,
    create_listing,
    get_listing,
    update_listing,
)


def test_create_listing_keeps_decimal_price():
    listing_id = create_listing(
        ListingInput(
            title="Price Test",
            description="Testing price storage.",
            price=Decimal(
                "12.50"
            ),
            currency="EUR",
            original_created_date=date(
                2026,
                1,
                1,
            ),
            priority=(
                ListingPriority.NORMAL
            ),
        )
    )

    listing = get_listing(
        listing_id
    )

    assert (
        listing.price
        == Decimal(
            "12.50"
        )
    )


def test_editing_listing_does_not_reset_price_to_zero():
    listing_id = create_listing(
        ListingInput(
            title="Original Listing",
            description="Original description",
            price=Decimal(
                "17.95"
            ),
            currency="EUR",
            category="Bags",
            brand="Test Brand",
            original_created_date=date(
                2025,
                5,
                10,
            ),
            priority=(
                ListingPriority.NORMAL
            ),
        )
    )

    existing = get_listing(
        listing_id
    )

    update_listing(
        listing_id,
        ListingInput(
            title="Edited Listing",
            description=(
                "Edited description"
            ),
            price=Decimal(
                str(
                    existing.price
                )
            ),
            currency=(
                existing.currency
            ),
            category=(
                existing.category
            ),
            brand=(
                existing.brand
            ),
            original_created_date=(
                existing.original_created_date
            ),
            priority=(
                existing.priority
            ),
        ),
    )

    updated = get_listing(
        listing_id
    )

    assert (
        updated.price
        == Decimal(
            "17.95"
        )
    )

    assert (
        updated.title
        == "Edited Listing"
    )