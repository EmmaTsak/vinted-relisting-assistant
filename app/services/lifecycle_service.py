from __future__ import annotations

import shutil
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

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


def _stage_listing_directory(
    listing_directory: Path,
) -> Path | None:
    """
    Move an assistant-owned listing directory aside before deleting
    the database row.

    Renaming within the same parent directory is intentionally used
    instead of deleting photos first. This gives the delete workflow
    a recovery point if the database transaction later fails.
    """
    if not listing_directory.exists():
        return None

    staged_directory = (
        listing_directory.with_name(
            (
                f".{listing_directory.name}"
                ".delete-pending-"
                f"{uuid4().hex}"
            )
        )
    )

    try:
        listing_directory.replace(
            staged_directory
        )

    except OSError as exc:
        raise LifecycleError(
            (
                "Permanent delete was cancelled because the "
                "local listing directory could not be prepared "
                "safely. No listing data was removed.\n\n"
                f"{exc}"
            )
        ) from exc

    return staged_directory


def _restore_staged_listing_directory(
    staged_directory: Path,
    listing_directory: Path,
) -> None:
    """
    Restore a staged listing directory when the database delete fails.
    """
    if not staged_directory.exists():
        return

    if listing_directory.exists():
        raise LifecycleError(
            (
                "The database delete failed and the staged photo "
                "directory could not be restored automatically "
                "because the original directory already exists.\n\n"
                f"Staged directory:\n{staged_directory}"
            )
        )

    try:
        staged_directory.replace(
            listing_directory
        )

    except OSError as exc:
        raise LifecycleError(
            (
                "The database delete failed and the local listing "
                "directory could not be restored automatically. "
                "The staged photos have been preserved at:\n"
                f"{staged_directory}\n\n"
                f"{exc}"
            )
        ) from exc


def delete_permanently(
    listing_id: int,
) -> None:
    """
    Permanently delete an archived listing.

    A listing MUST be archived first.

    The assistant-owned local listing directory is staged before the
    database transaction. If the transaction fails, that directory is
    restored. External/original source photos are never touched.
    """
    listing_directory = get_listing_directory(
        listing_id
    )

    staged_directory: Path | None = None

    try:
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

            staged_directory = (
                _stage_listing_directory(
                    listing_directory
                )
            )

            session.delete(
                listing
            )

    except Exception as exc:
        if staged_directory is not None:
            try:
                _restore_staged_listing_directory(
                    staged_directory,
                    listing_directory,
                )

            except LifecycleError as restore_exc:
                raise restore_exc from exc

        raise

    if (
        staged_directory is None
        or not staged_directory.exists()
    ):
        return

    try:
        shutil.rmtree(
            staged_directory
        )

    except OSError as exc:
        raise LifecycleError(
            (
                "The listing was removed from the database, "
                "but its staged local photo directory could not "
                "be cleaned up. The photos were preserved at:\n"
                f"{staged_directory}\n\n"
                "You can remove that folder manually after "
                "confirming the listing is gone from the app.\n\n"
                f"{exc}"
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