from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

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


DAILY_RELIST_LIMIT = 50
DEFAULT_MINIMUM_RELIST_AGE_DAYS = 14


class QueueError(Exception):
    """Base queue error."""


class DailyLimitReachedError(
    QueueError
):
    """
    Raised when an attempt is made to complete more relists
    than today's configured limit.
    """


class QueueEntryNotFoundError(
    QueueError
):
    """Raised when a listing is not in today's active queue."""


@dataclass(slots=True)
class QueueItem:
    listing: Listing
    days_since_relisted: int
    never_relisted: bool


@dataclass(slots=True)
class QueueSnapshot:
    queue_date: date
    configured_limit: int
    completed_count: int
    queued_items: list[QueueItem]

    @property
    def remaining_completions(
        self,
    ) -> int:
        return max(
            0,
            (
                self.configured_limit
                - self.completed_count
            ),
        )

    @property
    def is_complete(
        self,
    ) -> bool:
        return (
            self.completed_count
            >= self.configured_limit
        )


def normalize_daily_limit(
    configured_limit: int,
) -> int:
    """
    Allow a user-selected daily limit from 1 to 50.
    """
    if configured_limit < 1:
        return 1

    return min(
        configured_limit,
        DAILY_RELIST_LIMIT,
    )


def get_today_queue(
    configured_limit: int = DAILY_RELIST_LIMIT,
    minimum_age_days: int = DEFAULT_MINIMUM_RELIST_AGE_DAYS,
    today: date | None = None,
) -> QueueSnapshot:
    """
    Return today's queue and fill all available queue slots.

    Important rules:

    - Completed listings consume today's relist allowance.
    - Listings manually skipped with Skip Today stay excluded
      for the remainder of the calendar day.
    - Entries removed automatically because settings changed
      are deleted rather than marked SKIPPED.
    - Increasing the daily limit later can therefore refill
      the queue correctly.
    - Changing minimum age can also rebuild the queue correctly.
    """
    target_date = (
        today
        or date.today()
    )

    limit = normalize_daily_limit(
        configured_limit
    )

    minimum_age_days = max(
        0,
        minimum_age_days,
    )

    with session_scope() as session:
        _reactivate_expired_pauses(
            session,
            target_date,
        )

        completed_count = (
            _completed_count(
                session,
                target_date,
            )
        )

        if completed_count >= limit:
            return QueueSnapshot(
                queue_date=target_date,
                configured_limit=limit,
                completed_count=completed_count,
                queued_items=[],
            )

        active_entries = list(
            session.scalars(
                select(
                    DailyQueueEntry
                )
                .where(
                    (
                        DailyQueueEntry.queue_date
                        == target_date
                    ),
                    (
                        DailyQueueEntry.status
                        == QueueEntryStatus.QUEUED
                    ),
                )
                .order_by(
                    DailyQueueEntry.id
                )
            ).all()
        )

        valid_active_entries: list[
            DailyQueueEntry
        ] = []

        automatic_entries_removed = False

        for entry in active_entries:
            listing = session.get(
                Listing,
                entry.listing_id,
            )

            if (
                listing is not None
                and _is_base_eligible(
                    listing,
                    target_date,
                    minimum_age_days,
                )
            ):
                valid_active_entries.append(
                    entry
                )

            else:
                # This was NOT manually skipped.
                #
                # It only became invalid because the listing
                # or settings changed. Delete the temporary
                # queue row so it may become eligible again
                # if the user changes settings later.
                session.delete(
                    entry
                )

                automatic_entries_removed = True

        allowed_active_count = max(
            0,
            (
                limit
                - completed_count
            ),
        )

        if (
            len(
                valid_active_entries
            )
            > allowed_active_count
        ):
            overflow = (
                valid_active_entries[
                    allowed_active_count:
                ]
            )

            for entry in overflow:
                # Lowering the daily limit is not the same
                # as pressing Skip Today.
                #
                # Remove overflow queue rows instead of
                # permanently excluding those listings
                # from the rest of the day.
                session.delete(
                    entry
                )

                automatic_entries_removed = True

            valid_active_entries = (
                valid_active_entries[
                    :allowed_active_count
                ]
            )

        if automatic_entries_removed:
            # SessionLocal uses autoflush=False.
            #
            # Flush deletes now so the used-ID query below
            # does not continue seeing rows we just removed.
            session.flush()

        missing_slots = (
            allowed_active_count
            - len(
                valid_active_entries
            )
        )

        if missing_slots > 0:
            # ALL remaining rows for today are intentional:
            #
            # - COMPLETED
            # - manually SKIPPED
            # - currently QUEUED
            #
            # Those listing IDs should not be selected again.
            used_listing_ids = set(
                session.scalars(
                    select(
                        DailyQueueEntry.listing_id
                    )
                    .where(
                        (
                            DailyQueueEntry.queue_date
                            == target_date
                        )
                    )
                ).all()
            )

            candidates = list(
                session.scalars(
                    select(
                        Listing
                    )
                ).all()
            )

            eligible_candidates = [
                listing
                for listing in candidates
                if (
                    listing.id
                    not in used_listing_ids
                    and _is_base_eligible(
                        listing,
                        target_date,
                        minimum_age_days,
                    )
                )
            ]

            eligible_candidates.sort(
                key=_selection_sort_key
            )

            selected = (
                eligible_candidates[
                    :missing_slots
                ]
            )

            for listing in selected:
                entry = DailyQueueEntry(
                    listing_id=listing.id,
                    queue_date=target_date,
                    status=(
                        QueueEntryStatus.QUEUED
                    ),
                )

                session.add(
                    entry
                )

                session.flush()

                valid_active_entries.append(
                    entry
                )

        queue_items: list[
            QueueItem
        ] = []

        for entry in (
            valid_active_entries
        ):
            listing = session.get(
                Listing,
                entry.listing_id,
            )

            if listing is None:
                continue

            item = QueueItem(
                listing=listing,
                days_since_relisted=(
                    _days_since_relist(
                        listing,
                        target_date,
                    )
                ),
                never_relisted=(
                    listing.last_relisted_date
                    is None
                ),
            )

            session.expunge(
                listing
            )

            queue_items.append(
                item
            )

        return QueueSnapshot(
            queue_date=target_date,
            configured_limit=limit,
            completed_count=completed_count,
            queued_items=queue_items,
        )


def skip_today(
    listing_id: int,
    configured_limit: int = DAILY_RELIST_LIMIT,
    minimum_age_days: int = DEFAULT_MINIMUM_RELIST_AGE_DAYS,
    today: date | None = None,
) -> QueueSnapshot:
    """
    Manually skip one queue entry for this calendar day.

    A manually skipped listing remains excluded for the rest
    of today.

    It does NOT count toward the successful relist limit.

    Another eligible item may replace it.
    """
    target_date = (
        today
        or date.today()
    )

    with session_scope() as session:
        entry = session.scalar(
            select(
                DailyQueueEntry
            )
            .where(
                (
                    DailyQueueEntry.queue_date
                    == target_date
                ),
                (
                    DailyQueueEntry.listing_id
                    == listing_id
                ),
                (
                    DailyQueueEntry.status
                    == QueueEntryStatus.QUEUED
                ),
            )
        )

        if entry is None:
            raise QueueEntryNotFoundError(
                (
                    f"Listing #{listing_id} is not "
                    "in today's active queue."
                )
            )

        entry.status = (
            QueueEntryStatus.SKIPPED
        )

        entry.skipped_at = (
            datetime.now()
        )

    return get_today_queue(
        configured_limit=configured_limit,
        minimum_age_days=minimum_age_days,
        today=target_date,
    )


def mark_as_relisted(
    listing_id: int,
    configured_limit: int = DAILY_RELIST_LIMIT,
    minimum_age_days: int = DEFAULT_MINIMUM_RELIST_AGE_DAYS,
    today: date | None = None,
) -> QueueSnapshot:
    """
    Record manual confirmation that a queued listing was
    successfully published on Vinted.

    The configured daily completion limit is enforced in the
    service layer independently of the GUI.
    """
    target_date = (
        today
        or date.today()
    )

    limit = normalize_daily_limit(
        configured_limit
    )

    with session_scope() as session:
        completed_count = (
            _completed_count(
                session,
                target_date,
            )
        )

        if completed_count >= limit:
            raise DailyLimitReachedError(
                (
                    "Today's relisting limit has "
                    "already been reached "
                    f"({limit}/{limit})."
                )
            )

        entry = session.scalar(
            select(
                DailyQueueEntry
            )
            .where(
                (
                    DailyQueueEntry.queue_date
                    == target_date
                ),
                (
                    DailyQueueEntry.listing_id
                    == listing_id
                ),
                (
                    DailyQueueEntry.status
                    == QueueEntryStatus.QUEUED
                ),
            )
        )

        if entry is None:
            raise QueueEntryNotFoundError(
                (
                    f"Listing #{listing_id} is not "
                    "in today's active queue."
                )
            )

        listing = session.get(
            Listing,
            listing_id,
        )

        if listing is None:
            raise QueueEntryNotFoundError(
                (
                    f"Listing #{listing_id} "
                    "no longer exists."
                )
            )

        previous_date = (
            listing.last_relisted_date
        )

        listing.last_relisted_date = (
            target_date
        )

        listing.number_of_times_relisted += 1

        history = RelistHistory(
            listing_id=listing.id,
            relisted_date=target_date,
            previous_relisted_date=(
                previous_date
            ),
        )

        session.add(
            history
        )

        entry.status = (
            QueueEntryStatus.COMPLETED
        )

        entry.completed_at = (
            datetime.now()
        )

    return get_today_queue(
        configured_limit=limit,
        minimum_age_days=minimum_age_days,
        today=target_date,
    )


def get_completed_count(
    today: date | None = None,
) -> int:
    target_date = (
        today
        or date.today()
    )

    with session_scope() as session:
        return _completed_count(
            session,
            target_date,
        )


def _completed_count(
    session,
    target_date: date,
) -> int:
    value = session.scalar(
        select(
            func.count(
                DailyQueueEntry.id
            )
        )
        .where(
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

    return int(
        value
        or 0
    )


def _reactivate_expired_pauses(
    session,
    target_date: date,
) -> None:
    """
    Automatically reactivate temporary pauses after their
    end date.

    Indefinite pauses are never automatically changed.
    """
    expired = list(
        session.scalars(
            select(
                Listing
            )
            .where(
                (
                    Listing.status
                    == ListingStatus.PAUSED
                ),
                (
                    Listing.paused_indefinitely
                    .is_(False)
                ),
                (
                    Listing.paused_until
                    .is_not(None)
                ),
                (
                    Listing.paused_until
                    < target_date
                ),
            )
        ).all()
    )

    for listing in expired:
        listing.status = (
            ListingStatus.ACTIVE
        )

        listing.paused_until = None


def _is_base_eligible(
    listing: Listing,
    target_date: date,
    minimum_age_days: int,
) -> bool:
    if listing.sold:
        return False

    if listing.archived:
        return False

    if listing.manually_excluded:
        return False

    if (
        listing.status
        != ListingStatus.ACTIVE
    ):
        return False

    if listing.paused_indefinitely:
        return False

    if (
        listing.paused_until
        is not None
        and listing.paused_until
        >= target_date
    ):
        return False

    threshold = (
        target_date
        - timedelta(
            days=minimum_age_days
        )
    )

    if (
        listing.last_relisted_date
        is None
    ):
        return (
            listing.original_created_date
            <= threshold
        )

    return (
        listing.last_relisted_date
        <= threshold
    )


def _selection_sort_key(
    listing: Listing,
) -> tuple:
    """
    Queue priority:

    1. Never relisted
    2. Oldest last-relisted date
    3. Oldest original listing
    4. High / Normal / Low priority as tie-breaker
    """
    priority_order = {
        ListingPriority.HIGH: 0,
        ListingPriority.NORMAL: 1,
        ListingPriority.LOW: 2,
    }

    if (
        listing.last_relisted_date
        is None
    ):
        return (
            0,
            listing.original_created_date,
            listing.original_created_date,
            priority_order[
                listing.priority
            ],
            listing.id,
        )

    return (
        1,
        listing.last_relisted_date,
        listing.original_created_date,
        priority_order[
            listing.priority
        ],
        listing.id,
    )


def _days_since_relist(
    listing: Listing,
    target_date: date,
) -> int:
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