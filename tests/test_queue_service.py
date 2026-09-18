from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import func, select

from app.database import session_scope
from app.models import (
    DailyQueueEntry,
    Listing,
    ListingPriority,
    ListingStatus,
    QueueEntryStatus,
    RelistHistory,
)
from app.services.queue_service import (
    DailyLimitReachedError,
    get_completed_count,
    get_today_queue,
    mark_as_relisted,
    skip_today,
)


TODAY = date(
    2026,
    9,
    13,
)


def test_queue_selects_never_relisted_first(
    make_listing,
):
    never_old = make_listing(
        title="Never Old",
        original_created_date=(
            TODAY
            - timedelta(
                days=120
            )
        ),
        priority=(
            ListingPriority.LOW
        ),
    )

    never_newer_high_priority = make_listing(
        title="Never Newer High",
        original_created_date=(
            TODAY
            - timedelta(
                days=90
            )
        ),
        priority=(
            ListingPriority.HIGH
        ),
    )

    relisted_old = make_listing(
        title="Relisted Old",
        original_created_date=(
            TODAY
            - timedelta(
                days=250
            )
        ),
        last_relisted_date=(
            TODAY
            - timedelta(
                days=150
            )
        ),
    )

    snapshot = get_today_queue(
        configured_limit=50,
        minimum_age_days=14,
        today=TODAY,
    )

    ids = [
        item.listing.id
        for item in snapshot.queued_items
    ]

    assert ids == [
        never_old,
        never_newer_high_priority,
        relisted_old,
    ]


def test_minimum_age_rule_is_fourteen_days(
    make_listing,
):
    too_new = make_listing(
        title="13 Days Old",
        original_created_date=(
            TODAY
            - timedelta(
                days=13
            )
        ),
    )

    exactly_eligible = make_listing(
        title="14 Days Old",
        original_created_date=(
            TODAY
            - timedelta(
                days=14
            )
        ),
    )

    snapshot = get_today_queue(
        configured_limit=50,
        minimum_age_days=14,
        today=TODAY,
    )

    ids = {
        item.listing.id
        for item in snapshot.queued_items
    }

    assert exactly_eligible in ids
    assert too_new not in ids


def test_sold_and_archived_are_excluded(
    make_listing,
):
    active = make_listing(
        title="Active",
        original_created_date=(
            TODAY
            - timedelta(
                days=100
            )
        ),
    )

    sold = make_listing(
        title="Sold",
        original_created_date=(
            TODAY
            - timedelta(
                days=100
            )
        ),
        status=ListingStatus.SOLD,
        sold=True,
    )

    archived = make_listing(
        title="Archived",
        original_created_date=(
            TODAY
            - timedelta(
                days=100
            )
        ),
        status=ListingStatus.ARCHIVED,
        archived=True,
    )

    snapshot = get_today_queue(
        today=TODAY,
    )

    ids = {
        item.listing.id
        for item in snapshot.queued_items
    }

    assert active in ids
    assert sold not in ids
    assert archived not in ids


def test_manual_exclusion_is_respected(
    make_listing,
):
    included = make_listing(
        title="Included",
        original_created_date=(
            TODAY
            - timedelta(
                days=100
            )
        ),
    )

    excluded = make_listing(
        title="Excluded",
        original_created_date=(
            TODAY
            - timedelta(
                days=120
            )
        ),
        manually_excluded=True,
    )

    snapshot = get_today_queue(
        today=TODAY,
    )

    ids = {
        item.listing.id
        for item in snapshot.queued_items
    }

    assert included in ids
    assert excluded not in ids


def test_skip_today_does_not_count_and_replaces_item(
    make_listing,
):
    listing_ids = [
        make_listing(
            title=f"Listing {index}",
            original_created_date=(
                TODAY
                - timedelta(
                    days=(
                        100
                        - index
                    )
                )
            ),
        )
        for index in range(
            4
        )
    ]

    first_snapshot = get_today_queue(
        configured_limit=3,
        today=TODAY,
    )

    assert len(
        first_snapshot.queued_items
    ) == 3

    skipped_id = (
        first_snapshot
        .queued_items[1]
        .listing
        .id
    )

    replacement_candidate = (
        listing_ids[3]
    )

    new_snapshot = skip_today(
        listing_id=skipped_id,
        configured_limit=3,
        today=TODAY,
    )

    new_ids = {
        item.listing.id
        for item in new_snapshot.queued_items
    }

    assert skipped_id not in new_ids

    assert (
        replacement_candidate
        in new_ids
    )

    assert (
        new_snapshot.completed_count
        == 0
    )

    assert (
        get_completed_count(
            today=TODAY
        )
        == 0
    )

    with session_scope() as session:
        entry = session.scalar(
            select(
                DailyQueueEntry
            )
            .where(
                (
                    DailyQueueEntry.queue_date
                    == TODAY
                ),
                (
                    DailyQueueEntry.listing_id
                    == skipped_id
                ),
            )
        )

        assert entry is not None

        assert (
            entry.status
            == QueueEntryStatus.SKIPPED
        )


def test_mark_as_relisted_updates_listing_and_history(
    make_listing,
):
    listing_id = make_listing(
        title="Relist Me",
        original_created_date=(
            TODAY
            - timedelta(
                days=100
            )
        ),
    )

    snapshot = get_today_queue(
        configured_limit=3,
        today=TODAY,
    )

    assert (
        snapshot
        .queued_items[0]
        .listing
        .id
        == listing_id
    )

    result = mark_as_relisted(
        listing_id=listing_id,
        configured_limit=3,
        today=TODAY,
    )

    assert (
        result.completed_count
        == 1
    )

    with session_scope() as session:
        listing = session.get(
            Listing,
            listing_id,
        )

        assert listing is not None

        assert (
            listing.last_relisted_date
            == TODAY
        )

        assert (
            listing.number_of_times_relisted
            == 1
        )

        history_count = session.scalar(
            select(
                func.count(
                    RelistHistory.id
                )
            )
            .where(
                (
                    RelistHistory.listing_id
                    == listing_id
                )
            )
        )

        assert (
            history_count
            == 1
        )

        queue_entry = session.scalar(
            select(
                DailyQueueEntry
            )
            .where(
                (
                    DailyQueueEntry.listing_id
                    == listing_id
                ),
                (
                    DailyQueueEntry.queue_date
                    == TODAY
                ),
            )
        )

        assert (
            queue_entry
            is not None
        )

        assert (
            queue_entry.status
            == QueueEntryStatus.COMPLETED
        )


def test_configured_limit_can_be_lowered(
    make_listing,
):
    for index in range(
        5
    ):
        make_listing(
            title=f"Listing {index}",
            original_created_date=(
                TODAY
                - timedelta(
                    days=(
                        100
                        + index
                    )
                )
            ),
        )

    snapshot = get_today_queue(
        configured_limit=2,
        today=TODAY,
    )

    assert (
        snapshot.configured_limit
        == 2
    )

    assert len(
        snapshot.queued_items
    ) == 2


def test_daily_limit_can_never_be_configured_above_fifty(
    make_listing,
):
    for index in range(
        60
    ):
        make_listing(
            title=f"Listing {index}",
            original_created_date=(
                TODAY
                - timedelta(
                    days=(
                        100
                        + index
                    )
                )
            ),
        )

    snapshot = get_today_queue(
        configured_limit=99,
        today=TODAY,
    )

    assert (
        snapshot.configured_limit
        == 50
    )

    assert len(
        snapshot.queued_items
    ) == 50


def test_configured_limit_of_three_rejects_fourth_completed_relist(
    make_listing,
):
    """
    The application allows a maximum of 50 relists per day,
    but a lower user-configured limit must still be respected.

    Here the user selected a daily limit of 3, so a fourth
    completion on the same day must be rejected.
    """
    listing_ids = [
        make_listing(
            title=f"Listing {index}",
            original_created_date=(
                TODAY
                - timedelta(
                    days=(
                        100
                        + index
                    )
                )
            ),
        )
        for index in range(
            4
        )
    ]

    snapshot = get_today_queue(
        configured_limit=3,
        today=TODAY,
    )

    queued_ids = [
        item.listing.id
        for item in snapshot.queued_items
    ]

    assert len(
        queued_ids
    ) == 3

    for listing_id in queued_ids:
        mark_as_relisted(
            listing_id=listing_id,
            configured_limit=3,
            today=TODAY,
        )

    assert (
        get_completed_count(
            today=TODAY
        )
        == 3
    )

    fourth_id = next(
        listing_id
        for listing_id in listing_ids
        if listing_id not in queued_ids
    )

    # Simulate a future UI/programming bug trying to insert
    # another queue item after the configured daily limit
    # has already been reached.
    with session_scope() as session:
        session.add(
            DailyQueueEntry(
                listing_id=fourth_id,
                queue_date=TODAY,
                status=(
                    QueueEntryStatus.QUEUED
                ),
            )
        )

    with pytest.raises(
        DailyLimitReachedError
    ):
        mark_as_relisted(
            listing_id=fourth_id,
            configured_limit=3,
            today=TODAY,
        )

    with session_scope() as session:
        fourth_listing = session.get(
            Listing,
            fourth_id,
        )

        assert (
            fourth_listing
            is not None
        )

        assert (
            fourth_listing
            .number_of_times_relisted
            == 0
        )

        history_count = session.scalar(
            select(
                func.count(
                    RelistHistory.id
                )
            )
            .where(
                (
                    RelistHistory.listing_id
                    == fourth_id
                )
            )
        )

        assert (
            history_count
            == 0
        )

def test_expired_temporary_pause_reactivates(
    make_listing,
):
    listing_id = make_listing(
        title="Expired Pause",
        original_created_date=(
            TODAY
            - timedelta(
                days=100
            )
        ),
        status=ListingStatus.PAUSED,
        paused_until=(
            TODAY
            - timedelta(
                days=1
            )
        ),
        paused_indefinitely=False,
    )

    snapshot = get_today_queue(
        today=TODAY,
    )

    ids = {
        item.listing.id
        for item in snapshot.queued_items
    }

    assert (
        listing_id
        in ids
    )

    with session_scope() as session:
        listing = session.get(
            Listing,
            listing_id,
        )

        assert (
            listing
            is not None
        )

        assert (
            listing.status
            == ListingStatus.ACTIVE
        )

        assert (
            listing.paused_until
            is None
        )


def test_indefinite_pause_does_not_reactivate(
    make_listing,
):
    listing_id = make_listing(
        title="Indefinitely Paused",
        original_created_date=(
            TODAY
            - timedelta(
                days=100
            )
        ),
        status=ListingStatus.PAUSED,
        paused_until=None,
        paused_indefinitely=True,
    )

    snapshot = get_today_queue(
        today=TODAY,
    )

    ids = {
        item.listing.id
        for item in snapshot.queued_items
    }

    assert (
        listing_id
        not in ids
    )