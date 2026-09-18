from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select

from app.database import session_scope
from app.models import (
    DailyQueueEntry,
    Listing,
    ListingStatus,
    QueueEntryStatus,
    RelistHistory,
)


@dataclass(frozen=True, slots=True)
class RecentRelist:
    listing_id: int
    title: str
    relisted_date: date


@dataclass(frozen=True, slots=True)
class DashboardStatistics:
    active_listings: int

    queued_today: int
    completed_today: int

    relisted_this_week: int
    relisted_this_month: int

    sold_items: int

    older_than_30_days: int
    older_than_60_days: int
    older_than_90_days: int

    never_relisted: int

    average_days_between_relists: float | None

    oldest_listing_id: int | None
    oldest_listing_title: str | None
    oldest_listing_days: int | None

    most_relisted_listing_id: int | None
    most_relisted_listing_title: str | None
    most_relisted_count: int | None

    recent_relists: tuple[RecentRelist, ...]


def get_dashboard_statistics(
    today: date | None = None,
) -> DashboardStatistics:
    """
    Calculate dashboard statistics from the local SQLite database.

    Imported relist counts without known historical dates are kept
    in their listing totals, but are not invented as history events.
    """
    target_date = (
        today
        or date.today()
    )

    start_of_week = (
        target_date
        - timedelta(
            days=target_date.weekday()
        )
    )

    start_of_month = target_date.replace(
        day=1
    )

    with session_scope() as session:
        listings = list(
            session.scalars(
                select(Listing)
            ).all()
        )

        active_listings = [
            listing
            for listing in listings
            if (
                listing.status
                == ListingStatus.ACTIVE
                and not listing.sold
                and not listing.archived
            )
        ]

        sold_items = sum(
            1
            for listing in listings
            if (
                listing.status
                == ListingStatus.SOLD
                or listing.sold
            )
        )

        queued_today = int(
            session.scalar(
                select(
                    func.count(
                        DailyQueueEntry.id
                    )
                ).where(
                    DailyQueueEntry.queue_date
                    == target_date,
                    DailyQueueEntry.status
                    == QueueEntryStatus.QUEUED,
                )
            )
            or 0
        )

        completed_today = int(
            session.scalar(
                select(
                    func.count(
                        DailyQueueEntry.id
                    )
                ).where(
                    DailyQueueEntry.queue_date
                    == target_date,
                    DailyQueueEntry.status
                    == QueueEntryStatus.COMPLETED,
                )
            )
            or 0
        )

        relisted_this_week = int(
            session.scalar(
                select(
                    func.count(
                        RelistHistory.id
                    )
                ).where(
                    RelistHistory.relisted_date
                    >= start_of_week,
                    RelistHistory.relisted_date
                    <= target_date,
                )
            )
            or 0
        )

        relisted_this_month = int(
            session.scalar(
                select(
                    func.count(
                        RelistHistory.id
                    )
                ).where(
                    RelistHistory.relisted_date
                    >= start_of_month,
                    RelistHistory.relisted_date
                    <= target_date,
                )
            )
            or 0
        )

        older_than_30_days = sum(
            1
            for listing in active_listings
            if (
                _rotation_age_days(
                    listing,
                    target_date,
                )
                >= 30
            )
        )

        older_than_60_days = sum(
            1
            for listing in active_listings
            if (
                _rotation_age_days(
                    listing,
                    target_date,
                )
                >= 60
            )
        )

        older_than_90_days = sum(
            1
            for listing in active_listings
            if (
                _rotation_age_days(
                    listing,
                    target_date,
                )
                >= 90
            )
        )

        never_relisted = sum(
            1
            for listing in active_listings
            if (
                listing.last_relisted_date
                is None
            )
        )

        history_rows = list(
            session.scalars(
                select(
                    RelistHistory
                )
                .order_by(
                    RelistHistory.relisted_date.desc(),
                    RelistHistory.recorded_at.desc(),
                )
            ).all()
        )

        known_intervals = [
            (
                history.relisted_date
                - history.previous_relisted_date
            ).days
            for history in history_rows
            if (
                history.previous_relisted_date
                is not None
                and history.relisted_date
                >= history.previous_relisted_date
            )
        ]

        if known_intervals:
            average_days_between_relists = (
                sum(
                    known_intervals
                )
                / len(
                    known_intervals
                )
            )

        else:
            average_days_between_relists = None

        oldest_listing = _find_oldest_listing(
            active_listings,
            target_date,
        )

        most_relisted_listing = (
            _find_most_relisted_listing(
                listings
            )
        )

        recent_rows = session.execute(
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
            .limit(5)
        ).all()

        recent_relists = tuple(
            RecentRelist(
                listing_id=listing.id,
                title=listing.title,
                relisted_date=(
                    history.relisted_date
                ),
            )
            for history, listing in recent_rows
        )

        if oldest_listing is None:
            oldest_listing_id = None
            oldest_listing_title = None
            oldest_listing_days = None

        else:
            oldest_listing_id = (
                oldest_listing.id
            )

            oldest_listing_title = (
                oldest_listing.title
            )

            oldest_listing_days = (
                _rotation_age_days(
                    oldest_listing,
                    target_date,
                )
            )

        if most_relisted_listing is None:
            most_relisted_listing_id = None
            most_relisted_listing_title = None
            most_relisted_count = None

        else:
            most_relisted_listing_id = (
                most_relisted_listing.id
            )

            most_relisted_listing_title = (
                most_relisted_listing.title
            )

            most_relisted_count = (
                most_relisted_listing
                .number_of_times_relisted
            )

        return DashboardStatistics(
            active_listings=len(
                active_listings
            ),
            queued_today=queued_today,
            completed_today=completed_today,
            relisted_this_week=(
                relisted_this_week
            ),
            relisted_this_month=(
                relisted_this_month
            ),
            sold_items=sold_items,
            older_than_30_days=(
                older_than_30_days
            ),
            older_than_60_days=(
                older_than_60_days
            ),
            older_than_90_days=(
                older_than_90_days
            ),
            never_relisted=(
                never_relisted
            ),
            average_days_between_relists=(
                average_days_between_relists
            ),
            oldest_listing_id=(
                oldest_listing_id
            ),
            oldest_listing_title=(
                oldest_listing_title
            ),
            oldest_listing_days=(
                oldest_listing_days
            ),
            most_relisted_listing_id=(
                most_relisted_listing_id
            ),
            most_relisted_listing_title=(
                most_relisted_listing_title
            ),
            most_relisted_count=(
                most_relisted_count
            ),
            recent_relists=(
                recent_relists
            ),
        )


def _rotation_age_days(
    listing: Listing,
    target_date: date,
) -> int:
    """
    Number of days since the listing was last refreshed.

    If never relisted, use its original listing date.
    """
    reference = (
        listing.last_relisted_date
        or listing.original_created_date
    )

    return max(
        0,
        (
            target_date
            - reference
        ).days,
    )


def _find_oldest_listing(
    listings: list[Listing],
    target_date: date,
) -> Listing | None:
    """
    Return the active listing that has gone longest without refresh.
    """
    if not listings:
        return None

    return max(
        listings,
        key=lambda listing: (
            _rotation_age_days(
                listing,
                target_date,
            ),
            -listing.id,
        ),
    )


def _find_most_relisted_listing(
    listings: list[Listing],
) -> Listing | None:
    """
    Return the listing with the largest recorded relist count.

    Returns None when no listing has ever been relisted.
    """
    candidates = [
        listing
        for listing in listings
        if (
            listing.number_of_times_relisted
            > 0
        )
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda listing: (
            listing.number_of_times_relisted,
            -listing.id,
        ),
    )