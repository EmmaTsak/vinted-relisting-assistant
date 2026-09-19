from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

import app.services.backup_service as backup_service
from app.services.backup_service import (
    InvalidBackupError,
    validate_backup,
)


def _make_backup(
    tmp_path: Path,
    *,
    database_file: str = "database.sqlite",
    settings_file: str = "settings.json",
    photos=None,
) -> Path:
    backup = (
        tmp_path
        / "backup"
    )

    backup.mkdir()

    database = (
        backup
        / "database.sqlite"
    )

    connection = sqlite3.connect(
        database
    )

    try:
        connection.execute(
            """
            CREATE TABLE listings (
                id INTEGER PRIMARY KEY
            )
            """
        )

        connection.commit()

    finally:
        connection.close()

    settings = {
        "daily_relist_limit": 50,
        "minimum_relist_age_days": 14,
        "vinted_url": "https://www.vinted.gr/",
        "currency": "EUR",
        "photo_storage_directory": str(
            tmp_path
            / "photos"
        ),
        "backup_directory": str(
            tmp_path
            / "backups"
        ),
        "theme": "system",
    }

    (
        backup
        / "settings.json"
    ).write_text(
        json.dumps(
            settings
        ),
        encoding="utf-8",
    )

    manifest = {
        "format_version": (
            backup_service
            .BACKUP_FORMAT_VERSION
        ),
        "database_file": database_file,
        "settings_file": settings_file,
        "photos": (
            []
            if photos is None
            else photos
        ),
    }

    (
        backup
        / "manifest.json"
    ).write_text(
        json.dumps(
            manifest
        ),
        encoding="utf-8",
    )

    return backup


def test_valid_backup_passes_validation(
    tmp_path,
) -> None:
    backup = _make_backup(
        tmp_path
    )

    manifest = validate_backup(
        backup
    )

    assert (
        manifest[
            "database_file"
        ]
        == "database.sqlite"
    )


def test_database_path_cannot_escape_backup_directory(
    tmp_path,
) -> None:
    backup = _make_backup(
        tmp_path,
        database_file=(
            "../outside.sqlite"
        ),
    )

    with pytest.raises(
        InvalidBackupError,
        match="outside the backup folder",
    ):
        validate_backup(
            backup
        )


def test_absolute_database_path_is_rejected(
    tmp_path,
) -> None:
    outside = (
        tmp_path
        / "outside.sqlite"
    ).resolve()

    backup = _make_backup(
        tmp_path,
        database_file=str(
            outside
        ),
    )

    with pytest.raises(
        InvalidBackupError,
        match="relative path",
    ):
        validate_backup(
            backup
        )


def test_photo_backup_path_cannot_escape_backup_directory(
    tmp_path,
) -> None:
    backup = _make_backup(
        tmp_path,
        photos=[
            {
                "photo_id": 1,
                "database_path": (
                    "data/listings/1/photos/a.jpg"
                ),
                "backup_file": (
                    "../outside.jpg"
                ),
            }
        ],
    )

    with pytest.raises(
        InvalidBackupError,
        match="outside the backup folder",
    ):
        validate_backup(
            backup
        )


def test_absolute_photo_backup_path_is_rejected(
    tmp_path,
) -> None:
    outside = (
        tmp_path
        / "outside.jpg"
    ).resolve()

    backup = _make_backup(
        tmp_path,
        photos=[
            {
                "photo_id": 1,
                "database_path": (
                    "data/listings/1/photos/a.jpg"
                ),
                "backup_file": str(
                    outside
                ),
            }
        ],
    )

    with pytest.raises(
        InvalidBackupError,
        match="relative path",
    ):
        validate_backup(
            backup
        )


def test_malformed_photo_manifest_is_rejected(
    tmp_path,
) -> None:
    backup = _make_backup(
        tmp_path,
        photos={
            "not": "a list"
        },
    )

    with pytest.raises(
        InvalidBackupError,
        match="photo manifest",
    ):
        validate_backup(
            backup
        )


def test_missing_internal_backup_photo_is_allowed_for_warning(
    tmp_path,
) -> None:
    backup = _make_backup(
        tmp_path,
        photos=[
            {
                "photo_id": 1,
                "database_path": (
                    "data/listings/1/photos/missing.jpg"
                ),
                "backup_file": (
                    "photos/missing.jpg"
                ),
            }
        ],
    )

    manifest = validate_backup(
        backup
    )

    assert len(
        manifest[
            "photos"
        ]
    ) == 1


def test_atomic_copy_removes_partial_temp_file_on_failure(
    tmp_path,
    monkeypatch,
) -> None:
    source = (
        tmp_path
        / "source.txt"
    )

    source.write_text(
        "source",
        encoding="utf-8",
    )

    destination = (
        tmp_path
        / "destination.txt"
    )

    temporary = (
        tmp_path
        / ".destination.txt.restore_tmp"
    )

    def failing_copy(
        source_path,
        destination_path,
    ):
        del source_path

        Path(
            destination_path
        ).write_text(
            "partial",
            encoding="utf-8",
        )

        raise OSError(
            "simulated copy failure"
        )

    monkeypatch.setattr(
        backup_service.shutil,
        "copy2",
        failing_copy,
    )

    with pytest.raises(
        OSError,
        match="simulated copy failure",
    ):
        backup_service._atomic_copy(
            source,
            destination,
        )

    assert not temporary.exists()
    assert not destination.exists()
