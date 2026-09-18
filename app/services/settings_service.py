from __future__ import annotations

import json
from dataclasses import (
    asdict,
    dataclass,
)
from pathlib import Path
from urllib.parse import urlparse

from app.utils.paths import (
    BACKUP_DIR,
    DATA_DIR,
    LISTINGS_DIR,
    PROJECT_ROOT,
)


DEFAULT_PHOTO_DIRECTORY = LISTINGS_DIR
DEFAULT_BACKUP_DIRECTORY = BACKUP_DIR

SETTINGS_PATH = (
    DATA_DIR
    / "settings.json"
)


class SettingsError(Exception):
    """Raised when application settings cannot be read or saved."""


@dataclass(slots=True)
class AppSettings:
    daily_relist_limit: int = 50

    minimum_relist_age_days: int = 14

    vinted_url: str = (
        "https://www.vinted.gr/"
    )

    currency: str = "EUR"

    photo_storage_directory: str = str(
        DEFAULT_PHOTO_DIRECTORY
    )

    backup_directory: str = str(
        DEFAULT_BACKUP_DIRECTORY
    )

    theme: str = "system"


def default_settings() -> AppSettings:
    """
    Return a fresh set of application defaults.
    """
    return AppSettings()


def load_settings() -> AppSettings:
    """
    Load local settings.

    If settings have never been saved, defaults are returned.
    """
    if not SETTINGS_PATH.exists():
        return default_settings()

    try:
        with SETTINGS_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            raw = json.load(
                file
            )

    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise SettingsError(
            (
                "The settings file could not "
                "be read.\n\n"
                f"{exc}"
            )
        ) from exc

    if not isinstance(
        raw,
        dict,
    ):
        raise SettingsError(
            (
                "The settings file has "
                "an invalid format."
            )
        )

    settings = AppSettings(
        daily_relist_limit=raw.get(
            "daily_relist_limit",
            50,
        ),
        minimum_relist_age_days=raw.get(
            "minimum_relist_age_days",
            14,
        ),
        vinted_url=raw.get(
            "vinted_url",
            "https://www.vinted.gr/",
        ),
        currency=raw.get(
            "currency",
            "EUR",
        ),
        photo_storage_directory=raw.get(
            "photo_storage_directory",
            str(
                DEFAULT_PHOTO_DIRECTORY
            ),
        ),
        backup_directory=raw.get(
            "backup_directory",
            str(
                DEFAULT_BACKUP_DIRECTORY
            ),
        ),
        theme=raw.get(
            "theme",
            "system",
        ),
    )

    return validate_settings(
        settings
    )


def save_settings(
    settings: AppSettings,
) -> AppSettings:
    """
    Validate and save settings atomically.
    """
    normalized = validate_settings(
        settings
    )

    photo_directory = Path(
        normalized.photo_storage_directory
    )

    backup_directory = Path(
        normalized.backup_directory
    )

    try:
        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        photo_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        backup_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    except OSError as exc:
        raise SettingsError(
            (
                "One of the selected storage "
                "directories could not be created.\n\n"
                f"{exc}"
            )
        ) from exc

    temporary_path = (
        SETTINGS_PATH
        .with_suffix(
            ".json.tmp"
        )
    )

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                asdict(
                    normalized
                ),
                file,
                indent=2,
                ensure_ascii=False,
            )

        temporary_path.replace(
            SETTINGS_PATH
        )

    except OSError as exc:
        try:
            temporary_path.unlink(
                missing_ok=True
            )

        except OSError:
            pass

        raise SettingsError(
            (
                "The settings file could "
                "not be saved.\n\n"
                f"{exc}"
            )
        ) from exc

    return normalized


def validate_settings(
    settings: AppSettings,
) -> AppSettings:
    """
    Validate and normalize settings without writing them.
    """
    try:
        daily_limit = int(
            settings.daily_relist_limit
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise SettingsError(
            (
                "Daily relist limit must "
                "be a number."
            )
        ) from exc

    if not (
        1
        <= daily_limit
        <= 50
    ):
        raise SettingsError(
            (
                "Daily relist limit must "
                "be between 1 and 50."
            )
        )

    try:
        minimum_age = int(
            settings.minimum_relist_age_days
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise SettingsError(
            (
                "Minimum relist age must "
                "be a number."
            )
        ) from exc

    if not (
        0
        <= minimum_age
        <= 3650
    ):
        raise SettingsError(
            (
                "Minimum relist age must "
                "be between 0 and 3650 days."
            )
        )

    vinted_url = (
        str(
            settings.vinted_url
        )
        .strip()
    )

    parsed_url = urlparse(
        vinted_url
    )

    if (
        parsed_url.scheme
        not in {
            "http",
            "https",
        }
        or not parsed_url.netloc
    ):
        raise SettingsError(
            (
                "Vinted website must be "
                "a valid http:// or https:// address."
            )
        )

    currency = (
        str(
            settings.currency
        )
        .strip()
        .upper()
    )

    if (
        len(
            currency
        )
        != 3
        or not currency.isalpha()
    ):
        raise SettingsError(
            (
                "Currency must be a three-letter "
                "code such as EUR."
            )
        )

    photo_directory = (
        _normalize_directory(
            settings.photo_storage_directory
        )
    )

    backup_directory = (
        _normalize_directory(
            settings.backup_directory
        )
    )

    theme = (
        str(
            settings.theme
        )
        .strip()
        .lower()
    )

    if theme not in {
        "system",
        "light",
        "dark",
    }:
        raise SettingsError(
            (
                "Theme must be System, "
                "Light, or Dark."
            )
        )

    return AppSettings(
        daily_relist_limit=(
            daily_limit
        ),
        minimum_relist_age_days=(
            minimum_age
        ),
        vinted_url=(
            vinted_url
        ),
        currency=(
            currency
        ),
        photo_storage_directory=str(
            photo_directory
        ),
        backup_directory=str(
            backup_directory
        ),
        theme=(
            theme
        ),
    )


def _normalize_directory(
    value: str,
) -> Path:
    text = str(
        value
    ).strip()

    if not text:
        raise SettingsError(
            (
                "Storage directories "
                "cannot be empty."
            )
        )

    path = Path(
        text
    ).expanduser()

    if not path.is_absolute():
        path = (
            PROJECT_ROOT
            / path
        )

    return path.resolve()