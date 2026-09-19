from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps
from sqlalchemy import select

from app.database import session_scope
from app.models import Listing, ListingPhoto
from app.utils.paths import (
    PROJECT_ROOT,
    ensure_listing_directories,
    get_listing_photos_directory,
    get_listing_thumbnails_directory,
)


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
}


class PhotoError(Exception):
    """Base exception for photo management errors."""


class InvalidPhotoError(PhotoError):
    """Raised when a selected file is not a valid image."""


class PhotoNotFoundError(PhotoError):
    """Raised when a stored photo cannot be found."""


def validate_image_file(
    file_path: str | Path,
) -> Path:
    path = Path(
        file_path
    )

    if not path.exists():
        raise InvalidPhotoError(
            f"Photo does not exist: {path}"
        )

    if not path.is_file():
        raise InvalidPhotoError(
            f"Photo path is not a file: {path}"
        )

    if (
        path.suffix.lower()
        not in SUPPORTED_IMAGE_EXTENSIONS
    ):
        raise InvalidPhotoError(
            (
                "Unsupported image format: "
                f"{path.suffix or 'unknown'}"
            )
        )

    try:
        with Image.open(
            path
        ) as image:
            image.verify()

    except Exception as exc:
        raise InvalidPhotoError(
            f"Could not read image: {path.name}"
        ) from exc

    return path


def import_photos(
    listing_id: int,
    source_paths: list[str | Path],
) -> list[int]:
    """
    Copy photos into application-owned storage.
    """
    if not source_paths:
        return []

    validated_paths = [
        validate_image_file(
            path
        )
        for path in source_paths
    ]

    ensure_listing_directories(
        listing_id
    )

    photos_directory = (
        get_listing_photos_directory(
            listing_id
        )
    )

    thumbnails_directory = (
        get_listing_thumbnails_directory(
            listing_id
        )
    )

    created_files: list[Path] = []
    created_thumbnails: list[Path] = []

    try:
        with session_scope() as session:
            listing = session.get(
                Listing,
                listing_id,
            )

            if listing is None:
                raise PhotoError(
                    (
                        f"Listing #{listing_id} "
                        "does not exist."
                    )
                )

            existing_photos = list(
                session.scalars(
                    select(
                        ListingPhoto
                    )
                    .where(
                        ListingPhoto.listing_id
                        == listing_id
                    )
                    .order_by(
                        ListingPhoto.display_order,
                        ListingPhoto.id,
                    )
                ).all()
            )

            next_order = len(
                existing_photos
            )

            has_cover = any(
                photo.is_cover
                for photo in existing_photos
            )

            created_ids: list[int] = []

            for source_path in validated_paths:
                suffix = (
                    source_path
                    .suffix
                    .lower()
                )

                unique_name = (
                    f"{uuid4().hex}{suffix}"
                )

                destination = (
                    photos_directory
                    / unique_name
                )

                shutil.copy2(
                    source_path,
                    destination,
                )

                created_files.append(
                    destination
                )

                thumbnail_path = (
                    thumbnails_directory
                    / f"{destination.stem}.jpg"
                )

                _create_thumbnail(
                    destination,
                    thumbnail_path,
                )

                created_thumbnails.append(
                    thumbnail_path
                )

                stored_path = (
                    _path_for_database(
                        destination
                    )
                )

                photo = ListingPhoto(
                    listing_id=listing_id,
                    file_path=stored_path,
                    display_order=next_order,
                    is_cover=not has_cover,
                    rotation_degrees=0,
                )

                if not has_cover:
                    has_cover = True

                session.add(
                    photo
                )

                session.flush()

                created_ids.append(
                    photo.id
                )

                next_order += 1

            return created_ids

    except Exception:
        for path in created_files:
            try:
                path.unlink(
                    missing_ok=True
                )
            except OSError:
                pass

        for path in created_thumbnails:
            try:
                path.unlink(
                    missing_ok=True
                )
            except OSError:
                pass

        raise


def get_listing_photos(
    listing_id: int,
) -> list[ListingPhoto]:
    with session_scope() as session:
        photos = list(
            session.scalars(
                select(
                    ListingPhoto
                )
                .where(
                    ListingPhoto.listing_id
                    == listing_id
                )
                .order_by(
                    ListingPhoto.display_order,
                    ListingPhoto.id,
                )
            ).all()
        )

        for photo in photos:
            session.expunge(
                photo
            )

        return photos


def resolve_photo_path(
    photo: ListingPhoto,
) -> Path:
    """
    Resolve both legacy relative paths and new absolute paths.
    """
    path = Path(
        photo.file_path
    )

    if path.is_absolute():
        return path

    return (
        PROJECT_ROOT
        / path
    )


def get_thumbnail_path(
    photo: ListingPhoto,
) -> Path:
    source = resolve_photo_path(
        photo
    )

    thumbnail_directory = (
        get_listing_thumbnails_directory(
            photo.listing_id
        )
    )

    thumbnail_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    thumbnail = (
        thumbnail_directory
        / f"{source.stem}.jpg"
    )

    if (
        not thumbnail.exists()
        and source.exists()
    ):
        _create_thumbnail(
            source,
            thumbnail,
        )

    return thumbnail


def set_cover_photo(
    photo_id: int,
) -> None:
    with session_scope() as session:
        selected = session.get(
            ListingPhoto,
            photo_id,
        )

        if selected is None:
            raise PhotoNotFoundError(
                f"Photo #{photo_id} does not exist."
            )

        photos = list(
            session.scalars(
                select(
                    ListingPhoto
                ).where(
                    ListingPhoto.listing_id
                    == selected.listing_id
                )
            ).all()
        )

        for photo in photos:
            photo.is_cover = (
                photo.id
                == selected.id
            )


def move_photo(
    photo_id: int,
    direction: int,
) -> None:
    if direction not in {
        -1,
        1,
    }:
        raise ValueError(
            "Direction must be -1 or 1."
        )

    with session_scope() as session:
        selected = session.get(
            ListingPhoto,
            photo_id,
        )

        if selected is None:
            raise PhotoNotFoundError(
                f"Photo #{photo_id} does not exist."
            )

        photos = list(
            session.scalars(
                select(
                    ListingPhoto
                )
                .where(
                    ListingPhoto.listing_id
                    == selected.listing_id
                )
                .order_by(
                    ListingPhoto.display_order,
                    ListingPhoto.id,
                )
            ).all()
        )

        current_index = next(
            (
                index
                for index, photo
                in enumerate(
                    photos
                )
                if photo.id
                == selected.id
            ),
            None,
        )

        if current_index is None:
            return

        new_index = (
            current_index
            + direction
        )

        if not (
            0
            <= new_index
            < len(
                photos
            )
        ):
            return

        photos[
            current_index
        ], photos[
            new_index
        ] = (
            photos[new_index],
            photos[current_index],
        )

        for index, photo in enumerate(
            photos
        ):
            photo.display_order = (
                index
            )


def rotate_photo(
    photo_id: int,
    degrees: int,
) -> None:
    """
    Rotate one managed image while keeping the image file and database
    rotation metadata consistent if the transaction fails.
    """
    if degrees not in {
        -90,
        90,
        180,
    }:
        raise ValueError(
            (
                "Rotation must be "
                "-90, 90, or 180."
            )
        )

    source: Path | None = None
    backup_path: Path | None = None
    thumbnail: Path | None = None

    try:
        with session_scope() as session:
            photo = session.get(
                ListingPhoto,
                photo_id,
            )

            if photo is None:
                raise PhotoNotFoundError(
                    f"Photo #{photo_id} does not exist."
                )

            source = resolve_photo_path(
                photo
            )

            if not source.exists():
                raise PhotoNotFoundError(
                    (
                        "Stored image file is missing:\n"
                        f"{source}"
                    )
                )

            backup_path = (
                source.parent
                / (
                    f".{source.name}"
                    ".rotate-backup-"
                    f"{uuid4().hex}"
                )
            )

            shutil.copy2(
                source,
                backup_path,
            )

            _rotate_image_file(
                source,
                degrees,
            )

            photo.rotation_degrees = (
                photo.rotation_degrees
                + degrees
            ) % 360

            thumbnail = (
                get_listing_thumbnails_directory(
                    photo.listing_id
                )
                / f"{source.stem}.jpg"
            )

    except Exception as exc:
        if (
            source is not None
            and backup_path is not None
            and backup_path.exists()
        ):
            try:
                backup_path.replace(
                    source
                )

            except OSError as restore_exc:
                raise PhotoError(
                    (
                        "Photo rotation failed and the original "
                        "image could not be restored automatically.\n\n"
                        f"Preserved backup:\n{backup_path}\n\n"
                        f"{restore_exc}"
                    )
                ) from exc

        raise

    if backup_path is not None:
        try:
            backup_path.unlink(
                missing_ok=True
            )

        except OSError:
            pass

    # Thumbnail generation happens only after the database commit.
    # If it fails, remove any stale thumbnail; get_thumbnail_path()
    # can regenerate it later from the correctly rotated source.
    if (
        source is not None
        and thumbnail is not None
    ):
        try:
            _create_thumbnail(
                source,
                thumbnail,
            )

        except Exception:
            try:
                thumbnail.unlink(
                    missing_ok=True
                )

            except OSError:
                pass


def replace_photo(
    photo_id: int,
    replacement_path: str | Path,
) -> None:
    """
    Replace one managed photo without leaving orphaned replacement
    files if image processing or the database transaction fails.
    """
    replacement = validate_image_file(
        replacement_path
    )

    old_path: Path | None = None
    old_thumbnail: Path | None = None

    new_path: Path | None = None
    new_thumbnail: Path | None = None

    try:
        with session_scope() as session:
            photo = session.get(
                ListingPhoto,
                photo_id,
            )

            if photo is None:
                raise PhotoNotFoundError(
                    f"Photo #{photo_id} does not exist."
                )

            old_path = resolve_photo_path(
                photo
            )

            photos_directory = (
                get_listing_photos_directory(
                    photo.listing_id
                )
            )

            photos_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            suffix = (
                replacement
                .suffix
                .lower()
            )

            new_path = (
                photos_directory
                / f"{uuid4().hex}{suffix}"
            )

            shutil.copy2(
                replacement,
                new_path,
            )

            old_thumbnail = (
                get_listing_thumbnails_directory(
                    photo.listing_id
                )
                / f"{old_path.stem}.jpg"
            )

            new_thumbnail = (
                get_listing_thumbnails_directory(
                    photo.listing_id
                )
                / f"{new_path.stem}.jpg"
            )

            _create_thumbnail(
                new_path,
                new_thumbnail,
            )

            photo.file_path = (
                _path_for_database(
                    new_path
                )
            )

            photo.rotation_degrees = 0

    except Exception:
        for path in (
            new_path,
            new_thumbnail,
        ):
            if path is None:
                continue

            try:
                path.unlink(
                    missing_ok=True
                )

            except OSError:
                pass

        raise

    # The database commit succeeded. The old managed files are now
    # obsolete, so best-effort cleanup cannot cause data loss.
    if old_path is not None:
        try:
            old_path.unlink(
                missing_ok=True
            )

        except OSError:
            pass

    if old_thumbnail is not None:
        try:
            old_thumbnail.unlink(
                missing_ok=True
            )

        except OSError:
            pass


def remove_photo(
    photo_id: int,
) -> None:
    photo_path: Path | None = None
    thumbnail_path: Path | None = None

    with session_scope() as session:
        photo = session.get(
            ListingPhoto,
            photo_id,
        )

        if photo is None:
            raise PhotoNotFoundError(
                f"Photo #{photo_id} does not exist."
            )

        listing_id = (
            photo.listing_id
        )

        was_cover = (
            photo.is_cover
        )

        photo_path = resolve_photo_path(
            photo
        )

        thumbnail_path = (
            get_listing_thumbnails_directory(
                listing_id
            )
            / f"{photo_path.stem}.jpg"
        )

        session.delete(
            photo
        )

        session.flush()

        remaining = list(
            session.scalars(
                select(
                    ListingPhoto
                )
                .where(
                    ListingPhoto.listing_id
                    == listing_id
                )
                .order_by(
                    ListingPhoto.display_order,
                    ListingPhoto.id,
                )
            ).all()
        )

        for index, item in enumerate(
            remaining
        ):
            item.display_order = (
                index
            )

        if (
            was_cover
            and remaining
        ):
            remaining[
                0
            ].is_cover = True

    if photo_path is not None:
        try:
            photo_path.unlink(
                missing_ok=True
            )
        except OSError:
            pass

    if thumbnail_path is not None:
        try:
            thumbnail_path.unlink(
                missing_ok=True
            )
        except OSError:
            pass


def _path_for_database(
    path: Path,
) -> str:
    """
    Store project-local files relatively and external files absolutely.
    """
    resolved = path.resolve()

    try:
        return (
            resolved
            .relative_to(
                PROJECT_ROOT.resolve()
            )
            .as_posix()
        )

    except ValueError:
        return str(
            resolved
        )


def _create_thumbnail(
    source: Path,
    destination: Path,
) -> None:
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with Image.open(
        source
    ) as image:
        image = ImageOps.exif_transpose(
            image
        )

        image.thumbnail(
            (
                320,
                320,
            )
        )

        if image.mode == "RGBA":
            background = Image.new(
                "RGB",
                image.size,
                "white",
            )

            background.paste(
                image,
                mask=image.getchannel(
                    "A"
                ),
            )

            image = background

        elif image.mode != "RGB":
            image = image.convert(
                "RGB"
            )

        image.save(
            destination,
            format="JPEG",
            quality=85,
        )


def _rotate_image_file(
    path: Path,
    degrees: int,
) -> None:
    temporary_path = (
        path.parent
        / (
            f".{path.stem}_rotating"
            f"{path.suffix}"
        )
    )

    try:
        with Image.open(
            path
        ) as image:
            image = ImageOps.exif_transpose(
                image
            )

            image = image.rotate(
                -degrees,
                expand=True,
            )

            save_kwargs = {}

            if (
                path.suffix.lower()
                in {
                    ".jpg",
                    ".jpeg",
                }
            ):
                if image.mode != "RGB":
                    image = image.convert(
                        "RGB"
                    )

                save_kwargs = {
                    "quality": 95,
                }

            image.save(
                temporary_path,
                **save_kwargs,
            )

        temporary_path.replace(
            path
        )

    except Exception:
        try:
            temporary_path.unlink(
                missing_ok=True
            )

        except OSError:
            pass

        raise

