from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from pathlib import Path

import pytest
from PIL import Image

import app.database as database
import app.services.photo_service as photo_service
from app.database import session_scope
from app.models import (
    ListingPhoto,
)
from app.services.photo_service import (
    get_listing_photos,
    remove_photo,
    replace_photo,
    rotate_photo,
    set_cover_photo,
)


TEST_DATE = date(
    2026,
    1,
    1,
)


def _create_image(
    path: Path,
    *,
    size=(20, 10),
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image = Image.new(
        "RGB",
        size,
        "white",
    )

    image.save(
        path
    )


def _add_photo(
    listing_id: int,
    path: Path,
    *,
    order: int,
    cover: bool,
) -> int:
    with session_scope() as session:
        photo = ListingPhoto(
            listing_id=listing_id,
            file_path=str(
                path.resolve()
            ),
            display_order=order,
            is_cover=cover,
            rotation_degrees=0,
        )

        session.add(
            photo
        )

        session.flush()

        return photo.id


def test_replace_photo_commit_failure_keeps_old_file_and_cleans_new_files(
    make_listing,
    tmp_path,
    monkeypatch,
) -> None:
    listing_id = make_listing(
        title="Replace Rollback",
        original_created_date=TEST_DATE,
    )

    managed = (
        tmp_path
        / "managed"
    )

    photos = (
        managed
        / "photos"
    )

    thumbnails = (
        managed
        / "thumbnails"
    )

    old_path = (
        photos
        / "old.png"
    )

    replacement = (
        tmp_path
        / "replacement.png"
    )

    _create_image(
        old_path
    )

    _create_image(
        replacement,
        size=(30, 15),
    )

    photo_id = _add_photo(
        listing_id,
        old_path,
        order=0,
        cover=True,
    )

    monkeypatch.setattr(
        photo_service,
        "get_listing_photos_directory",
        lambda _: photos,
    )

    monkeypatch.setattr(
        photo_service,
        "get_listing_thumbnails_directory",
        lambda _: thumbnails,
    )

    @contextmanager
    def failing_session_scope():
        session = database.SessionLocal()

        try:
            yield session

            raise RuntimeError(
                "simulated commit failure"
            )

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    monkeypatch.setattr(
        photo_service,
        "session_scope",
        failing_session_scope,
    )

    with pytest.raises(
        RuntimeError,
        match="simulated commit failure",
    ):
        replace_photo(
            photo_id,
            replacement,
        )

    assert old_path.exists()

    managed_files = [
        path
        for path in photos.glob("*")
        if path.is_file()
    ]

    assert managed_files == [
        old_path
    ]

    assert not thumbnails.exists() or list(
        thumbnails.glob("*")
    ) == []

    with database.session_scope() as session:
        photo = session.get(
            ListingPhoto,
            photo_id,
        )

        assert photo is not None

        assert (
            Path(
                photo.file_path
            ).resolve()
            == old_path.resolve()
        )


def test_successful_replace_removes_old_managed_file(
    make_listing,
    tmp_path,
    monkeypatch,
) -> None:
    listing_id = make_listing(
        title="Replace Success",
        original_created_date=TEST_DATE,
    )

    photos = (
        tmp_path
        / "photos"
    )

    thumbnails = (
        tmp_path
        / "thumbs"
    )

    old_path = (
        photos
        / "old.png"
    )

    replacement = (
        tmp_path
        / "replacement.png"
    )

    _create_image(
        old_path
    )

    _create_image(
        replacement,
        size=(40, 20),
    )

    photo_id = _add_photo(
        listing_id,
        old_path,
        order=0,
        cover=True,
    )

    monkeypatch.setattr(
        photo_service,
        "get_listing_photos_directory",
        lambda _: photos,
    )

    monkeypatch.setattr(
        photo_service,
        "get_listing_thumbnails_directory",
        lambda _: thumbnails,
    )

    replace_photo(
        photo_id,
        replacement,
    )

    assert not old_path.exists()

    with session_scope() as session:
        photo = session.get(
            ListingPhoto,
            photo_id,
        )

        assert photo is not None

        new_path = Path(
            photo.file_path
        )

        assert new_path.exists()

        assert photo.rotation_degrees == 0

        assert (
            thumbnails
            / f"{new_path.stem}.jpg"
        ).exists()


def test_rotate_commit_failure_restores_original_image_and_metadata(
    make_listing,
    tmp_path,
    monkeypatch,
) -> None:
    listing_id = make_listing(
        title="Rotate Rollback",
        original_created_date=TEST_DATE,
    )

    source = (
        tmp_path
        / "photo.png"
    )

    thumbnails = (
        tmp_path
        / "thumbs"
    )

    _create_image(
        source,
        size=(30, 10),
    )

    original_bytes = (
        source.read_bytes()
    )

    photo_id = _add_photo(
        listing_id,
        source,
        order=0,
        cover=True,
    )

    monkeypatch.setattr(
        photo_service,
        "get_listing_thumbnails_directory",
        lambda _: thumbnails,
    )

    @contextmanager
    def failing_session_scope():
        session = database.SessionLocal()

        try:
            yield session

            raise RuntimeError(
                "simulated commit failure"
            )

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    monkeypatch.setattr(
        photo_service,
        "session_scope",
        failing_session_scope,
    )

    with pytest.raises(
        RuntimeError,
        match="simulated commit failure",
    ):
        rotate_photo(
            photo_id,
            90,
        )

    assert (
        source.read_bytes()
        == original_bytes
    )

    with database.session_scope() as session:
        photo = session.get(
            ListingPhoto,
            photo_id,
        )

        assert photo is not None
        assert photo.rotation_degrees == 0

    assert list(
        tmp_path.glob(
            ".photo.png.rotate-backup-*"
        )
    ) == []


def test_successful_rotation_updates_file_metadata_and_thumbnail(
    make_listing,
    tmp_path,
    monkeypatch,
) -> None:
    listing_id = make_listing(
        title="Rotate Success",
        original_created_date=TEST_DATE,
    )

    source = (
        tmp_path
        / "photo.png"
    )

    thumbnails = (
        tmp_path
        / "thumbs"
    )

    _create_image(
        source,
        size=(30, 10),
    )

    photo_id = _add_photo(
        listing_id,
        source,
        order=0,
        cover=True,
    )

    monkeypatch.setattr(
        photo_service,
        "get_listing_thumbnails_directory",
        lambda _: thumbnails,
    )

    rotate_photo(
        photo_id,
        90,
    )

    with Image.open(
        source
    ) as image:
        assert image.size == (
            10,
            30,
        )

    with session_scope() as session:
        photo = session.get(
            ListingPhoto,
            photo_id,
        )

        assert photo is not None
        assert photo.rotation_degrees == 90

    assert (
        thumbnails
        / "photo.jpg"
    ).exists()

    assert list(
        tmp_path.glob(
            ".photo.png.rotate-backup-*"
        )
    ) == []


def test_remove_cover_photo_promotes_next_and_compacts_order(
    make_listing,
    tmp_path,
    monkeypatch,
) -> None:
    listing_id = make_listing(
        title="Remove Cover",
        original_created_date=TEST_DATE,
    )

    thumbnails = (
        tmp_path
        / "thumbs"
    )

    monkeypatch.setattr(
        photo_service,
        "get_listing_thumbnails_directory",
        lambda _: thumbnails,
    )

    paths = [
        tmp_path / "1.png",
        tmp_path / "2.png",
        tmp_path / "3.png",
    ]

    for path in paths:
        _create_image(
            path
        )

    first = _add_photo(
        listing_id,
        paths[0],
        order=0,
        cover=True,
    )

    _add_photo(
        listing_id,
        paths[1],
        order=1,
        cover=False,
    )

    _add_photo(
        listing_id,
        paths[2],
        order=2,
        cover=False,
    )

    remove_photo(
        first
    )

    remaining = get_listing_photos(
        listing_id
    )

    assert len(remaining) == 2

    assert [
        photo.display_order
        for photo in remaining
    ] == [
        0,
        1,
    ]

    assert remaining[0].is_cover is True
    assert remaining[1].is_cover is False

    assert not paths[0].exists()


def test_set_cover_photo_keeps_exactly_one_cover(
    make_listing,
    tmp_path,
) -> None:
    listing_id = make_listing(
        title="Cover Selection",
        original_created_date=TEST_DATE,
    )

    first_path = (
        tmp_path
        / "first.png"
    )

    second_path = (
        tmp_path
        / "second.png"
    )

    _create_image(
        first_path
    )

    _create_image(
        second_path
    )

    _add_photo(
        listing_id,
        first_path,
        order=0,
        cover=True,
    )

    second = _add_photo(
        listing_id,
        second_path,
        order=1,
        cover=False,
    )

    set_cover_photo(
        second
    )

    photos = get_listing_photos(
        listing_id
    )

    covers = [
        photo
        for photo in photos
        if photo.is_cover
    ]

    assert len(covers) == 1
    assert covers[0].id == second
