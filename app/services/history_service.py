from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import select

from app.database import session_scope
from app.models import Listing, RelistHistory


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