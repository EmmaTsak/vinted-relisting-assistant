from __future__ import annotations

import shutil
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import session_scope
from app.models import Listing, ListingStatus
from app.utils.paths import get_listing_directory


class LifecycleError(Exception):
    """Base listing lifecycle error."""


class ListingNotFoundError(LifecycleError):
    """Raised when a listing does not exist."""


class InvalidLifecycleActionError(LifecycleError):
    """Raised when a lifecycle action is not allowed."""


def mark_sold(listing_id: int) -> None:
    """
    Mark a listing as sold.

    Sold listings remain stored locally with their photos and history,
    but they are removed from future relisting rotation.
    """
    with session_scope() as session:
        listing = _get_listing(
            session,
            listing_id,
        )

        listing.status = ListingStatus.SOLD
        listing.sold = True
        listing.archived = False

        listing.paused_until = None
        listing.paused_indefinitely = False


def archive_listing(listing_id: int) -> None:
    """
    Move a listing into the archive.

    Archiving does NOT delete the listing or its photographs.
    """
    with session_scope() as session:
        listing = _get_listing(
            session,
            listing_id,
        )

        listing.status = ListingStatus.ARCHIVED
        listing.archived = True
        listing.sold = False

        listing.paused_until = None
        listing.paused_indefinitely = False


def pause_listing(
    listing_id: int,
    days: int | None = None,
) -> None:
    """
    Pause a listing temporarily or indefinitely.

    days=None:
        pause indefinitely

    days=7:
        pause for seven days

    days=30:
        pause for thirty days
    """
    with session_scope() as session:
        listing = _get_listing(
            session,
            listing_id,
        )

        if listing.archived:
            raise InvalidLifecycleActionError(
                "Archived listings cannot be paused."
            )

        if listing.sold:
            raise InvalidLifecycleActionError(
                "Sold listings cannot be paused."
            )

        if days is not None and days < 1:
            raise InvalidLifecycleActionError(
                "Pause duration must be at least one day."
            )

        listing.status = ListingStatus.PAUSED
        listing.sold = False
        listing.archived = False

        if days is None:
            listing.paused_indefinitely = True
            listing.paused_until = None

        else:
            listing.paused_indefinitely = False
            listing.paused_until = (
                date.today()
                + timedelta(days=days)
            )


def restore_to_active(
    listing_id: int,
) -> None:
    """
    Restore a sold, archived, or paused listing to Active.
    """
    with session_scope() as session:
        listing = _get_listing(
            session,
            listing_id,
        )

        listing.status = ListingStatus.ACTIVE

        listing.sold = False
        listing.archived = False

        listing.paused_until = None
        listing.paused_indefinitely = False


def set_queue_excluded(
    listing_id: int,
    excluded: bool,
) -> None:
    """
    Manually include/exclude a listing from automatic queue selection.
    """
    with session_scope() as session:
        listing = _get_listing(
            session,
            listing_id,
        )

        listing.manually_excluded = excluded


def delete_permanently(
    listing_id: int,
) -> None:
    """
    Permanently delete an archived listing.

    A listing MUST be archived first.

    Database information and the assistant-owned listing directory
    are deleted. External/original source photos are never touched.
    """
    listing_directory = get_listing_directory(
        listing_id
    )

    with session_scope() as session:
        listing = _get_listing(
            session,
            listing_id,
        )

        if (
            not listing.archived
            or listing.status
            != ListingStatus.ARCHIVED
        ):
            raise InvalidLifecycleActionError(
                (
                    "A listing must be archived before "
                    "it can be permanently deleted."
                )
            )

        session.delete(
            listing
        )

    if listing_directory.exists():
        try:
            shutil.rmtree(
                listing_directory
            )

        except OSError as exc:
            raise LifecycleError(
                (
                    "The listing was removed from the database, "
                    "but its local photo directory could not "
                    f"be deleted:\n{exc}"
                )
            ) from exc


def get_sold_listings() -> list[Listing]:
    """
    Return listings currently marked Sold.
    """
    with session_scope() as session:
        listings = list(
            session.scalars(
                select(Listing)
                .where(
                    Listing.status
                    == ListingStatus.SOLD
                )
                .order_by(
                    Listing.updated_at.desc(),
                    Listing.id.desc(),
                )
            ).all()
        )

        for listing in listings:
            session.expunge(
                listing
            )

        return listings


def get_archived_listings() -> list[Listing]:
    """
    Return archived listings.
    """
    with session_scope() as session:
        listings = list(
            session.scalars(
                select(Listing)
                .where(
                    Listing.status
                    == ListingStatus.ARCHIVED
                )
                .order_by(
                    Listing.updated_at.desc(),
                    Listing.id.desc(),
                )
            ).all()
        )

        for listing in listings:
            session.expunge(
                listing
            )

        return listings


def _get_listing(
    session: Session,
    listing_id: int,
) -> Listing:
    listing = session.get(
        Listing,
        listing_id,
    )

    if listing is None:
        raise ListingNotFoundError(
            f"Listing #{listing_id} does not exist."
        )

    return listing