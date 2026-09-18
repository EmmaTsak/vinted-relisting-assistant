from __future__ import annotations

import os

from pathlib import Path


APP_DATA_FOLDER_NAME = (
    "VintedRelistingAssistant"
)


def _get_application_data_root() -> Path:
    """
    Return a persistent per-user Windows storage directory.

    This location is deliberately independent from:
    - the source-code directory
    - build/
    - dist/
    - the location of the executable

    Therefore rebuilding or replacing the EXE never deletes
    the user's database, photos, settings, history or backups.
    """
    local_app_data = os.environ.get(
        "LOCALAPPDATA"
    )

    if local_app_data:
        return (
            Path(
                local_app_data
            )
            / APP_DATA_FOLDER_NAME
        )

    return (
        Path.home()
        / "AppData"
        / "Local"
        / APP_DATA_FOLDER_NAME
    )


# Kept as PROJECT_ROOT for compatibility with existing services.
#
# In the application this now means the persistent runtime root,
# NOT the source-code/build directory.
PROJECT_ROOT = (
    _get_application_data_root()
)

DATA_DIR = (
    PROJECT_ROOT
    / "data"
)

BACKUP_DIR = (
    PROJECT_ROOT
    / "backups"
)

LOG_DIR = (
    PROJECT_ROOT
    / "logs"
)

ASSETS_DIR = (
    PROJECT_ROOT
    / "assets"
)

DATABASE_PATH = (
    DATA_DIR
    / "database.sqlite"
)

LISTINGS_DIR = (
    DATA_DIR
    / "listings"
)

THUMBNAILS_DIR = (
    DATA_DIR
    / "thumbnails"
)


def ensure_app_directories() -> None:
    """
    Create all persistent application directories.
    """
    directories = (
        PROJECT_ROOT,
        DATA_DIR,
        BACKUP_DIR,
        LOG_DIR,
        ASSETS_DIR,
        LISTINGS_DIR,
        THUMBNAILS_DIR,
    )

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


def get_photo_storage_root() -> Path:
    """
    Return the configured photo-storage directory.

    Falls back to the persistent listings directory if settings
    are unavailable.
    """
    try:
        from app.services.settings_service import (
            load_settings,
        )

        settings = load_settings()

        return Path(
            settings.photo_storage_directory
        )

    except Exception:
        return LISTINGS_DIR


def get_listing_directory(
    listing_id: int,
) -> Path:
    return (
        get_photo_storage_root()
        / str(
            listing_id
        )
    )


def get_listing_photos_directory(
    listing_id: int,
) -> Path:
    return (
        get_listing_directory(
            listing_id
        )
        / "photos"
    )


def get_listing_thumbnails_directory(
    listing_id: int,
) -> Path:
    return (
        get_listing_directory(
            listing_id
        )
        / "thumbnails"
    )


def ensure_listing_directories(
    listing_id: int,
) -> None:
    get_listing_photos_directory(
        listing_id
    ).mkdir(
        parents=True,
        exist_ok=True,
    )

    get_listing_thumbnails_directory(
        listing_id
    ).mkdir(
        parents=True,
        exist_ok=True,
    )