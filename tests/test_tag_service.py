from __future__ import annotations

from datetime import date

import pytest

from app.services.tag_service import (
    bulk_add_tags,
    bulk_remove_tags,
    get_existing_tags,
    get_tag_listing_summaries,
    normalize_tag_name,
)


def test_tag_name_is_normalized() -> None:
    display, normalized = (
        normalize_tag_name(
            "  Quick   Sale  "
        )
    )

    assert display == "Quick Sale"
    assert normalized == "quick sale"


def test_empty_tag_is_rejected() -> None:
    with pytest.raises(
        ValueError
    ):
        normalize_tag_name(
            "   "
        )


def test_bulk_add_tag_to_multiple_listings(
    make_listing,
) -> None:
    first = make_listing(
        title="Winter Coat",
        original_created_date=date(
            2026,
            1,
            1,
        ),
    )

    second = make_listing(
        title="Wool Jumper",
        original_created_date=date(
            2026,
            1,
            2,
        ),
    )

    result = bulk_add_tags(
        [
            first,
            second,
        ],
        [
            "Winter",
        ],
    )

    assert result.listings_changed == 2
    assert result.associations_changed == 2
    assert result.already_in_state == 0

    summaries = {
        item.listing_id: item
        for item
        in get_tag_listing_summaries()
    }

    assert summaries[
        first
    ].tags == (
        "Winter",
    )

    assert summaries[
        second
    ].tags == (
        "Winter",
    )


def test_tag_matching_is_case_insensitive(
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
        title="Scarf",
        original_created_date=date(
            2026,
            1,
            2,
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
            "  winter  ",
        ],
    )

    assert get_existing_tags() == [
        "Winter",
    ]


def test_bulk_add_is_idempotent(
    make_listing,
) -> None:
    listing_id = make_listing(
        title="Boots",
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
            "Winter",
        ],
    )

    result = bulk_add_tags(
        [
            listing_id,
        ],
        [
            "winter",
        ],
    )

    assert result.listings_changed == 0
    assert result.associations_changed == 0
    assert result.already_in_state == 1


def test_listing_can_have_multiple_tags(
    make_listing,
) -> None:
    listing_id = make_listing(
        title="Party Dress",
        original_created_date=date(
            2026,
            1,
            1,
        ),
    )

    result = bulk_add_tags(
        [
            listing_id,
        ],
        [
            "Winter",
            "Christmas",
        ],
    )

    assert result.associations_changed == 2

    summary = next(
        item
        for item
        in get_tag_listing_summaries()
        if item.listing_id
        == listing_id
    )

    assert set(
        summary.tags
    ) == {
        "Winter",
        "Christmas",
    }


def test_remove_one_tag_preserves_other_tags(
    make_listing,
) -> None:
    listing_id = make_listing(
        title="Dress",
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
            "Winter",
            "Christmas",
        ],
    )

    result = bulk_remove_tags(
        [
            listing_id,
        ],
        [
            "Winter",
        ],
    )

    assert result.listings_changed == 1
    assert result.associations_changed == 1

    summary = next(
        item
        for item
        in get_tag_listing_summaries()
        if item.listing_id
        == listing_id
    )

    assert summary.tags == (
        "Christmas",
    )


def test_missing_listing_is_reported() -> None:
    result = bulk_add_tags(
        [
            999_999,
        ],
        [
            "Winter",
        ],
    )

    assert result.missing_listings == 1
    assert result.listings_changed == 0
