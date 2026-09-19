from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import select

from app.database import session_scope
from app.models import Listing, RelistHistory
from app.models import (
    DailyQueueEntry,
    QueueEntryStatus,
)


class HistoryUndoError(Exception):
    """Base error for relist-history rollback."""


class HistoryEntryNotFoundError(
    HistoryUndoError
):
    """Raised when a history record no longer exists."""


class RelistUndoNotAllowedError(
    HistoryUndoError
):
    """
    Raised when attempting to undo an older relist while
    a newer relist for the same listing still exists.
    """


@dataclass(frozen=True, slots=True)
class HistoryRecord:
    """
    Read-only representation of one recorded relisting event.
    """

    id: int
    listing_id: int
    title: str

    relisted_date: date
    previous_relisted_date: date | None

    recorded_at: datetime

    current_relist_count: int

    @property
    def days_since_previous(self) -> int | None:
        """
        Return the number of days between this relist and
        the previous known relist date.
        """
        if self.previous_relisted_date is None:
            return None

        return max(
            0,
            (
                self.relisted_date
                - self.previous_relisted_date
            ).days,
        )


@dataclass(frozen=True, slots=True)
class HistorySummary:
    """
    Small statistics summary for the History page.
    """

    total_recorded_relists: int
    unique_listings: int
    recorded_this_month: int


def get_relist_history() -> list[HistoryRecord]:
    """
    Return all recorded relisting history, newest first.

    Listing titles and current relist counts come from
    the current Listing record.
    """
    with session_scope() as session:
        rows = session.execute(
            select(
                RelistHistory,
                Listing,
            )
            .join(
                Listing,
                Listing.id
                == RelistHistory.listing_id,
            )
            .order_by(
                RelistHistory.relisted_date.desc(),
                RelistHistory.recorded_at.desc(),
                RelistHistory.id.desc(),
            )
        ).all()

        return [
            HistoryRecord(
                id=history.id,
                listing_id=listing.id,
                title=listing.title,
                relisted_date=(
                    history.relisted_date
                ),
                previous_relisted_date=(
                    history.previous_relisted_date
                ),
                recorded_at=(
                    history.recorded_at
                ),
                current_relist_count=(
                    listing.number_of_times_relisted
                ),
            )
            for history, listing in rows
        ]




def get_history_summary() -> HistorySummary:
    """
    Calculate basic history statistics.
    """
    history = get_relist_history()

    today = date.today()

    unique_listing_ids = {
        record.listing_id
        for record in history
    }

    this_month_count = sum(
        1
        for record in history
        if (
            record.relisted_date.year
            == today.year
            and record.relisted_date.month
            == today.month
        )
    )

    return HistorySummary(
        total_recorded_relists=len(
            history
        ),
        unique_listings=len(
            unique_listing_ids
        ),
        recorded_this_month=(
            this_month_count
        ),
    )

def undo_relist(
    history_id: int,
    *,
    today: date | None = None,
) -> int:
    """
    Undo the most recent recorded relist for one listing.

    The operation restores:
    - the listing's previous relist date;
    - the relist counter;
    - today's queue entry when the relist happened today.

    Only the newest history entry for a listing can be undone.
    This prevents breaking a later relist's history chain.

    Returns the affected listing ID.
    """
    target_date = (
        today
        or date.today()
    )

    with session_scope() as session:
        history = session.get(
            RelistHistory,
            history_id,
        )

        if history is None:
            raise HistoryEntryNotFoundError(
                (
                    "This relist history entry "
                    "no longer exists."
                )
            )

        latest_history = session.scalar(
            select(
                RelistHistory
            )
            .where(
                RelistHistory.listing_id
                == history.listing_id
            )
            .order_by(
                RelistHistory.recorded_at.desc(),
                RelistHistory.id.desc(),
            )
            .limit(
                1
            )
        )

        if (
            latest_history is None
            or latest_history.id
            != history.id
        ):
            raise RelistUndoNotAllowedError(
                (
                    "Only the most recent relist "
                    "for a listing can be undone."
                )
            )

        listing = session.get(
            Listing,
            history.listing_id,
        )

        if listing is None:
            raise HistoryEntryNotFoundError(
                (
                    "The listing linked to this "
                    "history entry no longer exists."
                )
            )

        listing.last_relisted_date = (
            history.previous_relisted_date
        )

        listing.number_of_times_relisted = max(
            0,
            (
                listing.number_of_times_relisted
                - 1
            ),
        )

        if (
            history.relisted_date
            == target_date
        ):
            queue_entry = session.scalar(
                select(
                    DailyQueueEntry
                )
                .where(
                    (
                        DailyQueueEntry.listing_id
                        == listing.id
                    ),
                    (
                        DailyQueueEntry.queue_date
                        == target_date
                    ),
                    (
                        DailyQueueEntry.status
                        == QueueEntryStatus.COMPLETED
                    ),
                )
            )

            if queue_entry is not None:
                queue_entry.status = (
                    QueueEntryStatus.QUEUED
                )

                queue_entry.completed_at = None

                queue_entry.skipped_at = None

        listing_id = (
            listing.id
        )

        session.delete(
            history
        )

    return listing_id

