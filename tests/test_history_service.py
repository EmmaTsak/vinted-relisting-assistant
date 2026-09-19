from __future__ import annotations

from datetime import (
    date,
    datetime,
    timedelta,
)

import pytest
from sqlalchemy import select

import app.database as database
from app.models import (
    DailyQueueEntry,
    Listing,
    QueueEntryStatus,
    RelistHistory,
)
from app.services.history_service import (
    RelistUndoNotAllowedError,
    undo_relist,
)


def test_undo_latest_relist_restores_listing_and_queue(
    make_listing,
) -> None:
    today = date.today()

    previous_date = (
        today
        - timedelta(
            days=30
        )
    )

    listing_id = make_listing(
        title="Undo test",
        original_created_date=(
            today
            - timedelta(
                days=120
            )
        ),
        last_relisted_date=today,
        relist_count=2,
    )

    with database.session_scope() as session:
        listing = session.get(
            Listing,
            listing_id,
        )

        listing.last_relisted_date = (
            today
        )

        history = RelistHistory(
            listing_id=listing_id,
            relisted_date=today,
            previous_relisted_date=(
                previous_date
            ),
        )

        queue_entry = DailyQueueEntry(
            listing_id=listing_id,
            queue_date=today,
            status=(
                QueueEntryStatus.COMPLETED
            ),
            completed_at=datetime.now(),
        )

        session.add(
            history
        )

        session.add(
            queue_entry
        )

        session.flush()

        history_id = (
            history.id
        )

    affected_listing_id = undo_relist(
        history_id,
        today=today,
    )

    assert (
        affected_listing_id
        == listing_id
    )

    with database.session_scope() as session:
        listing = session.get(
            Listing,
            listing_id,
        )

        assert (
            listing.last_relisted_date
            == previous_date
        )

        assert (
            listing.number_of_times_relisted
            == 1
        )

        history = session.get(
            RelistHistory,
            history_id,
        )

        assert history is None

        queue_entry = session.scalar(
            select(
                DailyQueueEntry
            )
            .where(
                DailyQueueEntry.listing_id
                == listing_id
            )
        )

        assert (
            queue_entry.status
            == QueueEntryStatus.QUEUED
        )

        assert (
            queue_entry.completed_at
            is None
        )


def test_cannot_undo_older_relist(
    make_listing,
) -> None:
    today = date.today()

    listing_id = make_listing(
        title="Undo ordering test",
        original_created_date=(
            today
            - timedelta(
                days=180
            )
        ),
        last_relisted_date=today,
        relist_count=2,
    )

    with database.session_scope() as session:
        older = RelistHistory(
            listing_id=listing_id,
            relisted_date=(
                today
                - timedelta(
                    days=30
                )
            ),
            previous_relisted_date=None,
            recorded_at=(
                datetime.now()
                - timedelta(
                    minutes=10
                )
            ),
        )

        newer = RelistHistory(
            listing_id=listing_id,
            relisted_date=today,
            previous_relisted_date=(
                today
                - timedelta(
                    days=30
                )
            ),
            recorded_at=datetime.now(),
        )

        session.add_all(
            [
                older,
                newer,
            ]
        )

        session.flush()

        older_id = (
            older.id
        )

    with pytest.raises(
        RelistUndoNotAllowedError
    ):
        undo_relist(
            older_id,
            today=today,
        )
