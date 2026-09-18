from __future__ import annotations

import json
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from app import APP_VERSION
from app.database import (
    engine,
    session_scope,
)
from app.models import ListingPhoto
from app.services.settings_service import (
    AppSettings,
    SETTINGS_PATH,
    load_settings,
    validate_settings,
)
from app.utils.paths import (
    DATABASE_PATH,
    PROJECT_ROOT,
)


BACKUP_FORMAT_VERSION = 1


class BackupError(Exception):
    """Base backup/restore error."""


class InvalidBackupError(BackupError):
    """Raised when a backup cannot safely be restored."""


@dataclass(frozen=True, slots=True)
class BackupInfo:
    name: str
    path: Path
    created_at: datetime

    photo_count: int
    total_size_bytes: int

    warnings: tuple[str, ...]

    @property
    def total_size_mb(self) -> float:
        return (
            self.total_size_bytes
            / 1024
            / 1024
        )


@dataclass(frozen=True, slots=True)
class RestoreResult:
    restored_backup: Path
    safety_backup: BackupInfo

    photos_restored: int
    warnings: tuple[str, ...]


def create_backup(
    prefix: str = "backup",
) -> BackupInfo:
    """
    Create a complete local backup.

    Includes:
    - SQLite database
    - application settings
    - every managed original photo referenced by SQLite

    Thumbnails are not required because the app can regenerate them.
    """
    settings = load_settings()

    backup_root = Path(
        settings.backup_directory
    )

    try:
        backup_root.mkdir(
            parents=True,
            exist_ok=True,
        )

    except OSError as exc:
        raise BackupError(
            (
                "The backup directory could not "
                "be created.\n\n"
                f"{exc}"
            )
        ) from exc

    created_at = datetime.now()

    timestamp = created_at.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    backup_directory = (
        backup_root
        / f"{prefix}_{timestamp}"
    )

    counter = 1

    while backup_directory.exists():
        backup_directory = (
            backup_root
            / (
                f"{prefix}_{timestamp}_"
                f"{counter}"
            )
        )

        counter += 1

    try:
        backup_directory.mkdir(
            parents=True,
        )

    except OSError as exc:
        raise BackupError(
            (
                "The backup folder could not "
                "be created.\n\n"
                f"{exc}"
            )
        ) from exc

    database_backup = (
        backup_directory
        / "database.sqlite"
    )

    settings_backup = (
        backup_directory
        / "settings.json"
    )

    photos_backup = (
        backup_directory
        / "photos"
    )

    warnings: list[str] = []

    try:
        _backup_database(
            database_backup
        )

        with settings_backup.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                asdict(
                    settings
                ),
                file,
                indent=2,
                ensure_ascii=False,
            )

        photo_records = (
            _get_photo_records()
        )

        photo_entries: list[dict] = []

        photos_backup.mkdir(
            parents=True,
            exist_ok=True,
        )

        copied_photo_count = 0

        for (
            photo_id,
            database_path,
        ) in photo_records:
            source = (
                _resolve_database_photo_path(
                    database_path
                )
            )

            entry = {
                "photo_id": photo_id,
                "database_path": database_path,
                "backup_file": None,
            }

            if not source.exists():
                warnings.append(
                    (
                        f"Photo #{photo_id} was missing "
                        f"and could not be backed up: "
                        f"{source}"
                    )
                )

                photo_entries.append(
                    entry
                )

                continue

            suffix = (
                source.suffix.lower()
                or ".img"
            )

            backup_filename = (
                f"{photo_id}{suffix}"
            )

            destination = (
                photos_backup
                / backup_filename
            )

            shutil.copy2(
                source,
                destination,
            )

            entry[
                "backup_file"
            ] = (
                Path("photos")
                / backup_filename
            ).as_posix()

            photo_entries.append(
                entry
            )

            copied_photo_count += 1

        manifest = {
            "format_version": (
                BACKUP_FORMAT_VERSION
            ),
            "app_version": (
                APP_VERSION
            ),
            "created_at": (
                created_at.isoformat()
            ),
            "database_file": (
                "database.sqlite"
            ),
            "settings_file": (
                "settings.json"
            ),
            "photo_count": (
                copied_photo_count
            ),
            "photos": (
                photo_entries
            ),
            "warnings": (
                warnings
            ),
        }

        manifest_path = (
            backup_directory
            / "manifest.json"
        )

        with manifest_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                manifest,
                file,
                indent=2,
                ensure_ascii=False,
            )

        return BackupInfo(
            name=backup_directory.name,
            path=backup_directory,
            created_at=created_at,
            photo_count=(
                copied_photo_count
            ),
            total_size_bytes=(
                _directory_size(
                    backup_directory
                )
            ),
            warnings=tuple(
                warnings
            ),
        )

    except Exception as exc:
        try:
            shutil.rmtree(
                backup_directory,
                ignore_errors=True,
            )

        except OSError:
            pass

        if isinstance(
            exc,
            BackupError,
        ):
            raise

        raise BackupError(
            (
                "The backup could not be "
                f"completed.\n\n{exc}"
            )
        ) from exc


def list_backups() -> list[BackupInfo]:
    """
    Return valid backups from the configured backup directory.
    """
    settings = load_settings()

    backup_root = Path(
        settings.backup_directory
    )

    if not backup_root.exists():
        return []

    backups: list[
        BackupInfo
    ] = []

    try:
        directories = list(
            backup_root.iterdir()
        )

    except OSError as exc:
        raise BackupError(
            (
                "The backup directory could not "
                f"be read.\n\n{exc}"
            )
        ) from exc

    for directory in directories:
        if not directory.is_dir():
            continue

        manifest_path = (
            directory
            / "manifest.json"
        )

        if not manifest_path.exists():
            continue

        try:
            manifest = _read_manifest(
                directory
            )

            created_at = (
                datetime.fromisoformat(
                    manifest[
                        "created_at"
                    ]
                )
            )

            backups.append(
                BackupInfo(
                    name=directory.name,
                    path=directory,
                    created_at=(
                        created_at
                    ),
                    photo_count=int(
                        manifest.get(
                            "photo_count",
                            0,
                        )
                    ),
                    total_size_bytes=(
                        _directory_size(
                            directory
                        )
                    ),
                    warnings=tuple(
                        manifest.get(
                            "warnings",
                            [],
                        )
                    ),
                )
            )

        except Exception:
            continue

    backups.sort(
        key=lambda backup: (
            backup.created_at
        ),
        reverse=True,
    )

    return backups


def restore_backup(
    backup_path: str | Path,
) -> RestoreResult:
    """
    Restore one backup.

    Before changing current data, a full safety backup of the
    current state is automatically created.

    Existing unrelated files are never deleted.
    """
    backup_directory = Path(
        backup_path
    ).resolve()

    manifest = validate_backup(
        backup_directory
    )

    safety_backup = create_backup(
        prefix="pre-restore"
    )

    warnings: list[str] = []

    photos_restored = 0

    try:
        photos = manifest.get(
            "photos",
            [],
        )

        for entry in photos:
            backup_file = entry.get(
                "backup_file"
            )

            database_path = entry.get(
                "database_path"
            )

            photo_id = entry.get(
                "photo_id"
            )

            if not (
                backup_file
                and database_path
            ):
                warnings.append(
                    (
                        f"Photo #{photo_id} was not "
                        "available in this backup."
                    )
                )

                continue

            source = (
                backup_directory
                / backup_file
            )

            if not source.exists():
                warnings.append(
                    (
                        f"Backup photo #{photo_id} "
                        "is missing."
                    )
                )

                continue

            target = (
                _resolve_database_photo_path(
                    database_path
                )
            )

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            temporary_target = (
                target.parent
                / (
                    f".{target.name}"
                    ".restore_tmp"
                )
            )

            shutil.copy2(
                source,
                temporary_target,
            )

            temporary_target.replace(
                target
            )

            photos_restored += 1

        database_source = (
            backup_directory
            / manifest[
                "database_file"
            ]
        )

        settings_source = (
            backup_directory
            / manifest[
                "settings_file"
            ]
        )

        engine.dispose()

        _remove_sqlite_sidecars()

        _atomic_copy(
            database_source,
            DATABASE_PATH,
        )

        _atomic_copy(
            settings_source,
            SETTINGS_PATH,
        )

        engine.dispose()

        return RestoreResult(
            restored_backup=(
                backup_directory
            ),
            safety_backup=(
                safety_backup
            ),
            photos_restored=(
                photos_restored
            ),
            warnings=tuple(
                warnings
            ),
        )

    except Exception as exc:
        engine.dispose()

        raise BackupError(
            (
                "Restore could not be completed.\n\n"
                "A safety backup was created before "
                "the restore attempt at:\n"
                f"{safety_backup.path}\n\n"
                f"Error: {exc}"
            )
        ) from exc


def validate_backup(
    backup_path: str | Path,
) -> dict:
    """
    Validate the manifest, settings and SQLite database.
    """
    backup_directory = Path(
        backup_path
    ).resolve()

    if not backup_directory.exists():
        raise InvalidBackupError(
            "The selected backup folder does not exist."
        )

    manifest = _read_manifest(
        backup_directory
    )

    if (
        manifest.get(
            "format_version"
        )
        != BACKUP_FORMAT_VERSION
    ):
        raise InvalidBackupError(
            (
                "This backup uses an unsupported "
                "backup format."
            )
        )

    database_filename = (
        manifest.get(
            "database_file"
        )
    )

    settings_filename = (
        manifest.get(
            "settings_file"
        )
    )

    if not database_filename:
        raise InvalidBackupError(
            "The backup does not identify a database file."
        )

    if not settings_filename:
        raise InvalidBackupError(
            "The backup does not identify a settings file."
        )

    database_path = (
        backup_directory
        / database_filename
    )

    settings_path = (
        backup_directory
        / settings_filename
    )

    if not database_path.exists():
        raise InvalidBackupError(
            "The backup database is missing."
        )

    if not settings_path.exists():
        raise InvalidBackupError(
            "The backup settings file is missing."
        )

    _validate_database(
        database_path
    )

    _validate_settings_file(
        settings_path
    )

    return manifest


def delete_backup(
    backup_path: str | Path,
) -> None:
    """
    Delete one backup directory only after verifying it looks
    like one of our backups.
    """
    backup_directory = Path(
        backup_path
    ).resolve()

    validate_backup(
        backup_directory
    )

    try:
        shutil.rmtree(
            backup_directory
        )

    except OSError as exc:
        raise BackupError(
            (
                "The backup could not be deleted.\n\n"
                f"{exc}"
            )
        ) from exc


def _backup_database(
    destination: Path,
) -> None:
    """
    Use SQLite's backup API for a consistent live snapshot.
    """
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        source_connection = (
            sqlite3.connect(
                str(
                    DATABASE_PATH
                )
            )
        )

        destination_connection = (
            sqlite3.connect(
                str(
                    destination
                )
            )
        )

        try:
            source_connection.backup(
                destination_connection
            )

        finally:
            destination_connection.close()
            source_connection.close()

    except sqlite3.Error as exc:
        raise BackupError(
            (
                "The SQLite database could not "
                f"be backed up.\n\n{exc}"
            )
        ) from exc


def _get_photo_records(
    ) -> list[tuple[int, str]]:
    with session_scope() as session:
        photos = list(
            session.scalars(
                select(
                    ListingPhoto
                )
                .order_by(
                    ListingPhoto.id
                )
            ).all()
        )

        return [
            (
                photo.id,
                photo.file_path,
            )
            for photo in photos
        ]


def _resolve_database_photo_path(
    database_path: str,
) -> Path:
    path = Path(
        database_path
    )

    if path.is_absolute():
        return path

    return (
        PROJECT_ROOT
        / path
    )


def _read_manifest(
    backup_directory: Path,
) -> dict:
    manifest_path = (
        backup_directory
        / "manifest.json"
    )

    if not manifest_path.exists():
        raise InvalidBackupError(
            (
                "The selected folder does not "
                "contain manifest.json."
            )
        )

    try:
        with manifest_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            manifest = json.load(
                file
            )

    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise InvalidBackupError(
            (
                "The backup manifest could not "
                f"be read.\n\n{exc}"
            )
        ) from exc

    if not isinstance(
        manifest,
        dict,
    ):
        raise InvalidBackupError(
            "The backup manifest has an invalid format."
        )

    return manifest


def _validate_database(
    database_path: Path,
) -> None:
    try:
        connection = sqlite3.connect(
            (
                "file:"
                f"{database_path.as_posix()}"
                "?mode=ro"
            ),
            uri=True,
        )

        try:
            result = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()

            if (
                not result
                or result[0]
                != "ok"
            ):
                raise InvalidBackupError(
                    (
                        "SQLite integrity check failed "
                        "for this backup."
                    )
                )

            tables = {
                row[0]
                for row
                in connection.execute(
                    (
                        "SELECT name "
                        "FROM sqlite_master "
                        "WHERE type='table'"
                    )
                ).fetchall()
            }

            if "listings" not in tables:
                raise InvalidBackupError(
                    (
                        "The selected database does not "
                        "contain the listings table."
                    )
                )

        finally:
            connection.close()

    except sqlite3.Error as exc:
        raise InvalidBackupError(
            (
                "The backup database could not "
                f"be validated.\n\n{exc}"
            )
        ) from exc


def _validate_settings_file(
    settings_path: Path,
) -> None:
    try:
        with settings_path.open(
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
        raise InvalidBackupError(
            (
                "The backup settings file could "
                f"not be validated.\n\n{exc}"
            )
        ) from exc

    if not isinstance(
        raw,
        dict,
    ):
        raise InvalidBackupError(
            (
                "The backup settings file "
                "has an invalid format."
            )
        )

    settings = AppSettings(
        daily_relist_limit=raw.get(
            "daily_relist_limit",
            3,
        ),
        minimum_relist_age_days=raw.get(
            "minimum_relist_age_days",
            30,
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
                PROJECT_ROOT
                / "data"
                / "listings"
            ),
        ),
        backup_directory=raw.get(
            "backup_directory",
            str(
                PROJECT_ROOT
                / "backups"
            ),
        ),
        theme=raw.get(
            "theme",
            "system",
        ),
    )

    validate_settings(
        settings
    )


def _atomic_copy(
    source: Path,
    destination: Path,
) -> None:
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = (
        destination.parent
        / (
            f".{destination.name}"
            ".restore_tmp"
        )
    )

    shutil.copy2(
        source,
        temporary,
    )

    temporary.replace(
        destination
    )


def _remove_sqlite_sidecars() -> None:
    for suffix in (
        "-wal",
        "-shm",
        "-journal",
    ):
        path = Path(
            f"{DATABASE_PATH}{suffix}"
        )

        try:
            path.unlink(
                missing_ok=True
            )

        except OSError:
            pass


def _directory_size(
    directory: Path,
) -> int:
    total = 0

    for path in directory.rglob(
        "*"
    ):
        if not path.is_file():
            continue

        try:
            total += (
                path.stat().st_size
            )

        except OSError:
            continue

    return total