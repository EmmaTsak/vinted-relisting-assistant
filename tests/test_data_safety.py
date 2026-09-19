from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from decimal import Decimal

import pytest

import app.database as database
import app.services.lifecycle_service as lifecycle_service
from app.database import session_scope
from app.models import (
    Listing,
    ListingStatus,
)
from app.services.lifecycle_service import (
    InvalidLifecycleActionError,
    LifecycleError,
    delete_permanently,
)
from app.services.listing_service import (
    ListingInput,
    append_listing_note_line,
    create_listing,
    get_listing,
    update_listing_price,
)


TEST_DATE = date(
    2026,
    1,
    1,
)


def _make_local_listing_directory(
    tmp_path,
    listing_id: int,
):
    directory = (
        tmp_path
        / str(listing_id)
    )

    photos = (
        directory
        / "photos"
    )

    photos.mkdir(
        parents=True
    )

    photo = (
        photos
        / "listing-photo.txt"
    )

    photo.write_text(
        "test photo data",
        encoding="utf-8",
    )

    return (
        directory,
        photo,
    )


def test_permanent_delete_requires_archive(
    make_listing,
    tmp_path,
    monkeypatch,
) -> None:
    listing_id = make_listing(
        title="Active Delete Guard",
        original_created_date=TEST_DATE,
    )

    directory, photo = (
        _make_local_listing_directory(
            tmp_path,
            listing_id,
        )
    )

    monkeypatch.setattr(
        lifecycle_service,
        "get_listing_directory",
        lambda _: directory,
    )

    with pytest.raises(
        InvalidLifecycleActionError
    ):
        delete_permanently(
            listing_id
        )

    with session_scope() as session:
        assert (
            session.get(
                Listing,
                listing_id,
            )
            is not None
        )

    assert directory.exists()
    assert photo.exists()


def test_permanent_delete_removes_archived_listing_and_local_directory(
    make_listing,
    tmp_path,
    monkeypatch,
) -> None:
    listing_id = make_listing(
        title="Delete Archived",
        original_created_date=TEST_DATE,
        status=ListingStatus.ARCHIVED,
        archived=True,
    )

    directory, _ = (
        _make_local_listing_directory(
            tmp_path,
            listing_id,
        )
    )

    monkeypatch.setattr(
        lifecycle_service,
        "get_listing_directory",
        lambda _: directory,
    )

    delete_permanently(
        listing_id
    )

    with session_scope() as session:
        assert (
            session.get(
                Listing,
                listing_id,
            )
            is None
        )

    assert not directory.exists()

    assert list(
        tmp_path.glob(
            (
                f".{listing_id}"
                ".delete-pending-*"
            )
        )
    ) == []


def test_database_delete_failure_restores_staged_photos(
    make_listing,
    tmp_path,
    monkeypatch,
) -> None:
    listing_id = make_listing(
        title="Delete Rollback",
        original_created_date=TEST_DATE,
        status=ListingStatus.ARCHIVED,
        archived=True,
    )

    directory, photo = (
        _make_local_listing_directory(
            tmp_path,
            listing_id,
        )
    )

    monkeypatch.setattr(
        lifecycle_service,
        "get_listing_directory",
        lambda _: directory,
    )

    @contextmanager
    def failing_session_scope():
        session = database.SessionLocal()

        try:
            yield session

            raise RuntimeError(
                "simulated database commit failure"
            )

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    monkeypatch.setattr(
        lifecycle_service,
        "session_scope",
        failing_session_scope,
    )

    with pytest.raises(
        RuntimeError,
        match="simulated database commit failure",
    ):
        delete_permanently(
            listing_id
        )

    with database.session_scope() as session:
        assert (
            session.get(
                Listing,
                listing_id,
            )
            is not None
        )

    assert directory.exists()
    assert photo.exists()

    assert list(
        tmp_path.glob(
            (
                f".{listing_id}"
                ".delete-pending-*"
            )
        )
    ) == []


def test_cleanup_failure_preserves_staged_photos(
    make_listing,
    tmp_path,
    monkeypatch,
) -> None:
    listing_id = make_listing(
        title="Cleanup Failure",
        original_created_date=TEST_DATE,
        status=ListingStatus.ARCHIVED,
        archived=True,
    )

    directory, _ = (
        _make_local_listing_directory(
            tmp_path,
            listing_id,
        )
    )

    monkeypatch.setattr(
        lifecycle_service,
        "get_listing_directory",
        lambda _: directory,
    )

    def fail_cleanup(_):
        raise OSError(
            "simulated cleanup failure"
        )

    monkeypatch.setattr(
        lifecycle_service.shutil,
        "rmtree",
        fail_cleanup,
    )

    with pytest.raises(
        LifecycleError,
        match="photos were preserved",
    ):
        delete_permanently(
            listing_id
        )

    with session_scope() as session:
        assert (
            session.get(
                Listing,
                listing_id,
            )
            is None
        )

    assert not directory.exists()

    staged = list(
        tmp_path.glob(
            (
                f".{listing_id}"
                ".delete-pending-*"
            )
        )
    )

    assert len(staged) == 1

    assert (
        staged[0]
        / "photos"
        / "listing-photo.txt"
    ).exists()


def test_price_only_update_preserves_other_listing_fields(
) -> None:
    listing_id = create_listing(
        ListingInput(
            title="Keep My Details",
            description="Original description",
            price=Decimal("14.50"),
            currency="EUR",
            brand="Test Brand",
            notes="important local note",
            original_created_date=TEST_DATE,
        )
    )

    update_listing_price(
        listing_id,
        Decimal("19.99"),
    )

    listing = get_listing(
        listing_id
    )

    assert listing.price == Decimal("19.99")
    assert listing.title == "Keep My Details"
    assert listing.description == "Original description"
    assert listing.brand == "Test Brand"
    assert listing.notes == "important local note"
    assert listing.original_created_date == TEST_DATE


def test_invalid_price_only_update_preserves_existing_price(
) -> None:
    listing_id = create_listing(
        ListingInput(
            title="Price Guard",
            description="Price should remain",
            price=Decimal("8.75"),
            original_created_date=TEST_DATE,
        )
    )

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        update_listing_price(
            listing_id,
            Decimal("0"),
        )

    assert (
        get_listing(
            listing_id
        ).price
        == Decimal("8.75")
    )


def test_append_note_line_does_not_duplicate_marker(
) -> None:
    listing_id = create_listing(
        ListingInput(
            title="Marker Test",
            description="Marker test",
            price=Decimal("10.00"),
            notes="local note",
            original_created_date=TEST_DATE,
        )
    )

    marker = (
        "[VINTED_EXPORT_ITEM_ID=123456]"
    )

    assert (
        append_listing_note_line(
            listing_id,
            marker,
        )
        is True
    )

    assert (
        append_listing_note_line(
            listing_id,
            marker,
        )
        is False
    )

    lines = (
        get_listing(
            listing_id
        )
        .notes
        .splitlines()
    )

    assert lines.count(
        marker
    ) == 1
