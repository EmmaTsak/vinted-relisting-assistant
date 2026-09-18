from __future__ import annotations

from datetime import date, timedelta

from app.database import session_scope
from app.models import (
    Listing,
    ListingStatus,
)
from app.services.lifecycle_service import (
    archive_listing,
    get_archived_listings,
    get_sold_listings,
    mark_sold,
    pause_listing,
    restore_to_active,
    set_queue_excluded,
)


TODAY = date(
    2026,
    9,
    13,
)


def test_mark_sold(
    make_listing,
):
    listing_id = make_listing(
        title="Sold Test",
        original_created_date=(
            TODAY
            - timedelta(
                days=100
            )
        ),
    )

    mark_sold(
        listing_id
    )

    with session_scope() as session:
        listing = session.get(
            Listing,
            listing_id,
        )

        assert listing is not None

        assert (
            listing.status
            == ListingStatus.SOLD
        )

        assert listing.sold is True
        assert listing.archived is False

    sold_ids = {
        listing.id
        for listing in get_sold_listings()
    }

    assert listing_id in sold_ids


def test_archive_and_restore(
    make_listing,
):
    listing_id = make_listing(
        title="Archive Test",
        original_created_date=(
            TODAY
            - timedelta(
                days=100
            )
        ),
    )

    archive_listing(
        listing_id
    )

    archived_ids = {
        listing.id
        for listing
        in get_archived_listings()
    }

    assert listing_id in archived_ids

    restore_to_active(
        listing_id
    )

    with session_scope() as session:
        listing = session.get(
            Listing,
            listing_id,
        )

        assert listing is not None

        assert (
            listing.status
            == ListingStatus.ACTIVE
        )

        assert listing.archived is False
        assert listing.sold is False


def test_pause_indefinitely_and_resume(
    make_listing,
):
    listing_id = make_listing(
        title="Pause Test",
        original_created_date=(
            TODAY
            - timedelta(
                days=100
            )
        ),
    )

    pause_listing(
        listing_id,
        days=None,
    )

    with session_scope() as session:
        listing = session.get(
            Listing,
            listing_id,
        )

        assert listing is not None

        assert (
            listing.status
            == ListingStatus.PAUSED
        )

        assert (
            listing.paused_indefinitely
            is True
        )

        assert (
            listing.paused_until
            is None
        )

    restore_to_active(
        listing_id
    )

    with session_scope() as session:
        listing = session.get(
            Listing,
            listing_id,
        )

        assert listing is not None

        assert (
            listing.status
            == ListingStatus.ACTIVE
        )

        assert (
            listing.paused_indefinitely
            is False
        )

        assert (
            listing.paused_until
            is None
        )


def test_manual_queue_exclusion_toggle(
    make_listing,
):
    listing_id = make_listing(
        title="Exclusion Test",
        original_created_date=(
            TODAY
            - timedelta(
                days=100
            )
        ),
    )

    set_queue_excluded(
        listing_id,
        True,
    )

    with session_scope() as session:
        listing = session.get(
            Listing,
            listing_id,
        )

        assert listing is not None

        assert (
            listing.manually_excluded
            is True
        )

    set_queue_excluded(
        listing_id,
        False,
    )

    with session_scope() as session:
        listing = session.get(
            Listing,
            listing_id,
        )

        assert listing is not None

        assert (
            listing.manually_excluded
            is False
        )