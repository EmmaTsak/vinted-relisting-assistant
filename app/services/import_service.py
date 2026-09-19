from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.database import session_scope
from app.models import (
    Listing,
    ListingPriority,
    ListingStatus,
)
from app.services.photo_service import (
    import_photos,
)


class ImportFileError(Exception):
    """Raised when an import file cannot be read."""


@dataclass(slots=True)
class ImportRowError:
    row_number: int
    message: str


@dataclass(slots=True)
class ImportRowWarning:
    row_number: int
    message: str


@dataclass(slots=True)
class ImportResult:
    total_rows: int = 0
    imported_count: int = 0
    skipped_count: int = 0
    imported_ids: list[int] = field(
        default_factory=list
    )
    errors: list[ImportRowError] = field(
        default_factory=list
    )
    warnings: list[
        ImportRowWarning
    ] = field(
        default_factory=list
    )
    rows_with_photos: int = 0
    photos_imported: int = 0


FIELD_ALIASES = {
    "color": "colour",
    "original_date": "original_created_date",
    "created_date": "original_created_date",
    "last_relisted": "last_relisted_date",
    "relist_count": "number_of_times_relisted",
    "excluded": "manually_excluded",
}


IMPORT_DUPLICATE_FIELDS = (
    "title",
    "description",
    "price",
    "currency",
    "category",
    "subcategory",
    "brand",
    "size",
    "condition",
    "colour",
    "material",
    "parcel_size",
    "isbn",
    "notes",
)


def _signature_text(
    value: Any,
) -> str:
    if value is None:
        return ""

    return " ".join(
        str(
            value
        ).split()
    ).casefold()


def _import_signature_from_row(
    row: dict[str, Any],
) -> tuple[Any, ...]:
    title = _required_text(
        row.get(
            "title"
        ),
        "title",
    )

    price = _parse_price(
        row.get(
            "price"
        )
    )

    currency = (
        _optional_text(
            row.get(
                "currency"
            )
        )
        or "EUR"
    ).upper()

    values = {
        "title": title,
        "description": (
            _optional_text(
                row.get(
                    "description"
                )
            )
            or ""
        ),
        "price": price,
        "currency": currency,
        "category": _optional_text(
            row.get(
                "category"
            )
        ),
        "subcategory": _optional_text(
            row.get(
                "subcategory"
            )
        ),
        "brand": _optional_text(
            row.get(
                "brand"
            )
        ),
        "size": _optional_text(
            row.get(
                "size"
            )
        ),
        "condition": _optional_text(
            row.get(
                "condition"
            )
        ),
        "colour": _optional_text(
            row.get(
                "colour"
            )
        ),
        "material": _optional_text(
            row.get(
                "material"
            )
        ),
        "parcel_size": _optional_text(
            row.get(
                "parcel_size"
            )
        ),
        "isbn": _optional_text(
            row.get(
                "isbn"
            )
        ),
        "notes": (
            _optional_text(
                row.get(
                    "notes"
                )
            )
            or ""
        ),
    }

    return tuple(
        (
            values[field]
            if field == "price"
            else _signature_text(
                values[field]
            )
        )
        for field
        in IMPORT_DUPLICATE_FIELDS
    )


def _import_signature_from_listing(
    listing: Listing,
) -> tuple[Any, ...]:
    return tuple(
        (
            getattr(
                listing,
                field,
                None,
            )
            if field == "price"
            else _signature_text(
                getattr(
                    listing,
                    field,
                    None,
                )
            )
        )
        for field
        in IMPORT_DUPLICATE_FIELDS
    )


def _load_existing_import_signatures(
) -> set[tuple[Any, ...]]:
    with session_scope() as session:
        listings = list(
            session.scalars(
                select(
                    Listing
                )
            ).all()
        )

        return {
            _import_signature_from_listing(
                listing
            )
            for listing
            in listings
        }


def import_listings_file(
    file_path: str | Path,
) -> ImportResult:
    path = Path(
        file_path
    )

    if not path.exists():
        raise ImportFileError(
            (
                "The selected file does not exist:\n"
                f"{path}"
            )
        )

    suffix = (
        path.suffix.lower()
    )

    if suffix == ".json":
        rows = _load_json(
            path
        )

    elif suffix == ".csv":
        rows = _load_csv(
            path
        )

    else:
        raise ImportFileError(
            (
                "Unsupported file type. "
                "Choose .csv or .json."
            )
        )

    result = ImportResult(
        total_rows=len(
            rows
        )
    )

    # Snapshot only listings that existed BEFORE this import.
    # This prevents importing the same file again while still
    # allowing intentionally identical rows inside one file.
    existing_import_signatures = (
        _load_existing_import_signatures()
    )

    for row_number, raw_row in enumerate(
        rows,
        start=1,
    ):
        try:
            normalized = _normalize_row(
                raw_row
            )

            import_signature = (
                _import_signature_from_row(
                    normalized
                )
            )

            if (
                import_signature
                in existing_import_signatures
            ):
                result.skipped_count += 1

                result.warnings.append(
                    ImportRowWarning(
                        row_number=row_number,
                        message=(
                            "Duplicate already exists in "
                            "your local inventory. "
                            "This row was skipped."
                        ),
                    )
                )

                continue

            photo_paths = _parse_photos(
                normalized.get(
                    "photos"
                ),
                import_file=path,
            )

            if photo_paths:
                result.rows_with_photos += 1

            listing_id = (
                _import_single_listing(
                    normalized
                )
            )

            result.imported_ids.append(
                listing_id
            )

            result.imported_count += 1

            if photo_paths:
                try:
                    photo_ids = import_photos(
                        listing_id,
                        photo_paths,
                    )

                    result.photos_imported += len(
                        photo_ids
                    )

                except Exception as exc:
                    result.warnings.append(
                        ImportRowWarning(
                            row_number=row_number,
                            message=(
                                "Listing imported, but "
                                "its photos could not all "
                                f"be imported: {exc}"
                            ),
                        )
                    )

        except Exception as exc:
            result.skipped_count += 1

            result.errors.append(
                ImportRowError(
                    row_number=row_number,
                    message=str(
                        exc
                    ),
                )
            )

    return result


def _load_json(
    path: Path,
) -> list[dict[str, Any]]:
    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as file:
            data = json.load(
                file
            )

    except json.JSONDecodeError as exc:
        raise ImportFileError(
            f"Invalid JSON file:\n{exc}"
        ) from exc

    except OSError as exc:
        raise ImportFileError(
            (
                "Could not read the JSON "
                f"file:\n{exc}"
            )
        ) from exc

    if isinstance(
        data,
        dict,
    ):
        return [
            data
        ]

    if isinstance(
        data,
        list,
    ):
        rows = []

        for index, item in enumerate(
            data,
            start=1,
        ):
            if not isinstance(
                item,
                dict,
            ):
                raise ImportFileError(
                    (
                        "Every JSON array item "
                        "must be an object. "
                        f"Item {index} is invalid."
                    )
                )

            rows.append(
                item
            )

        return rows

    raise ImportFileError(
        (
            "JSON must contain either "
            "one listing object or an "
            "array of listing objects."
        )
    )


def _load_csv(
    path: Path,
) -> list[dict[str, Any]]:
    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(
                file
            )

            if not reader.fieldnames:
                raise ImportFileError(
                    (
                        "The CSV file does not "
                        "contain a header row."
                    )
                )

            return [
                dict(
                    row
                )
                for row in reader
            ]

    except ImportFileError:
        raise

    except OSError as exc:
        raise ImportFileError(
            (
                "Could not read the CSV "
                f"file:\n{exc}"
            )
        ) from exc


def _normalize_row(
    row: dict[str, Any],
) -> dict[str, Any]:
    normalized = {}

    for key, value in row.items():
        if key is None:
            continue

        clean_key = (
            str(
                key
            )
            .strip()
            .lower()
            .replace(
                " ",
                "_",
            )
        )

        clean_key = (
            FIELD_ALIASES.get(
                clean_key,
                clean_key,
            )
        )

        normalized[
            clean_key
        ] = value

    return normalized


def _parse_photos(
    value: Any,
    import_file: Path,
) -> list[Path]:
    """
    Parse photo paths from JSON.

    Relative paths are resolved relative to the JSON file.
    """
    if value in {
        None,
        "",
    }:
        return []

    raw_paths: list[str]

    if isinstance(
        value,
        list,
    ):
        raw_paths = [
            str(
                item
            ).strip()
            for item in value
            if str(
                item
            ).strip()
        ]

    elif isinstance(
        value,
        str,
    ):
        raw_paths = [
            part.strip()
            for part in value.split(
                "|"
            )
            if part.strip()
        ]

    else:
        raise ValueError(
            (
                "photos must be a JSON list "
                "or a | separated CSV value."
            )
        )

    paths: list[Path] = []

    for raw_path in raw_paths:
        path = Path(
            raw_path
        )

        if not path.is_absolute():
            path = (
                import_file.parent
                / path
            )

        paths.append(
            path
        )

    return paths


def _import_single_listing(
    row: dict[str, Any],
) -> int:
    title = _required_text(
        row.get(
            "title"
        ),
        "title",
    )

    description = (
        _optional_text(
            row.get(
                "description"
            )
        )
        or ""
    )

    price = _parse_price(
        row.get(
            "price"
        )
    )

    if price <= 0:
        raise ValueError(
            "Price must be greater than 0."
        )

    currency = (
        _optional_text(
            row.get(
                "currency"
            )
        )
        or "EUR"
    ).upper()

    if len(
        currency
    ) != 3:
        raise ValueError(
            (
                "Currency must be a "
                "three-letter code such as EUR."
            )
        )

    original_created_date = (
        _parse_date(
            row.get(
                "original_created_date"
            ),
            default=date.today(),
        )
    )

    last_relisted_date = (
        _parse_date(
            row.get(
                "last_relisted_date"
            ),
            default=None,
        )
    )

    relist_count = (
        _parse_non_negative_int(
            row.get(
                "number_of_times_relisted",
                0,
            )
        )
    )

    if (
        last_relisted_date
        is not None
        and relist_count == 0
    ):
        relist_count = 1

    priority = _parse_priority(
        row.get(
            "priority"
        )
    )

    sold = _parse_bool(
        row.get(
            "sold"
        ),
        default=False,
    )

    archived = _parse_bool(
        row.get(
            "archived"
        ),
        default=False,
    )

    manually_excluded = (
        _parse_bool(
            row.get(
                "manually_excluded"
            ),
            default=False,
        )
    )

    paused_indefinitely = (
        _parse_bool(
            row.get(
                "paused_indefinitely"
            ),
            default=False,
        )
    )

    paused_until = _parse_date(
        row.get(
            "paused_until"
        ),
        default=None,
    )

    status = _parse_status(
        row.get(
            "status"
        )
    )

    if sold:
        status = (
            ListingStatus.SOLD
        )

    elif archived:
        status = (
            ListingStatus.ARCHIVED
        )

    elif (
        paused_indefinitely
        or paused_until
        is not None
    ):
        status = (
            ListingStatus.PAUSED
        )

    if (
        status
        == ListingStatus.SOLD
    ):
        sold = True

    if (
        status
        == ListingStatus.ARCHIVED
    ):
        archived = True

    with session_scope() as session:
        listing = Listing(
            title=title,
            description=description,
            price=price,
            currency=currency,
            category=_optional_text(
                row.get(
                    "category"
                )
            ),
            subcategory=_optional_text(
                row.get(
                    "subcategory"
                )
            ),
            brand=_optional_text(
                row.get(
                    "brand"
                )
            ),
            size=_optional_text(
                row.get(
                    "size"
                )
            ),
            condition=_optional_text(
                row.get(
                    "condition"
                )
            ),
            colour=_optional_text(
                row.get(
                    "colour"
                )
            ),
            material=_optional_text(
                row.get(
                    "material"
                )
            ),
            parcel_size=_optional_text(
                row.get(
                    "parcel_size"
                )
            ),
            notes=(
                _optional_text(
                    row.get(
                        "notes"
                    )
                )
                or ""
            ),
            original_created_date=(
                original_created_date
            ),
            last_relisted_date=(
                last_relisted_date
            ),
            number_of_times_relisted=(
                relist_count
            ),
            priority=priority,
            status=status,
            sold=sold,
            archived=archived,
            manually_excluded=(
                manually_excluded
            ),
            paused_until=(
                paused_until
            ),
            paused_indefinitely=(
                paused_indefinitely
            ),
        )

        session.add(
            listing
        )

        session.flush()

        return listing.id


def _required_text(
    value: Any,
    field_name: str,
) -> str:
    text = _optional_text(
        value
    )

    if not text:
        raise ValueError(
            (
                "Missing required field: "
                f"{field_name}"
            )
        )

    return text


def _optional_text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    text = str(
        value
    ).strip()

    return (
        text
        if text
        else None
    )


def _parse_price(
    value: Any,
) -> Decimal:
    if value is None:
        raise ValueError(
            "Missing required field: price"
        )

    if isinstance(
        value,
        Decimal,
    ):
        return value

    if isinstance(
        value,
        (
            int,
            float,
        ),
    ):
        return Decimal(
            str(
                value
            )
        )

    text = (
        str(
            value
        )
        .strip()
        .replace(
            "€",
            "",
        )
        .replace(
            "$",
            "",
        )
        .replace(
            "£",
            "",
        )
        .replace(
            " ",
            "",
        )
    )

    if (
        ","
        in text
        and "."
        not in text
    ):
        text = text.replace(
            ",",
            ".",
        )

    try:
        return Decimal(
            text
        )

    except InvalidOperation as exc:
        raise ValueError(
            f"Invalid price: {value}"
        ) from exc


def _parse_non_negative_int(
    value: Any,
) -> int:
    if value in {
        None,
        "",
    }:
        return 0

    try:
        parsed = int(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            (
                "Invalid integer value: "
                f"{value}"
            )
        ) from exc

    if parsed < 0:
        raise ValueError(
            (
                "Relist count cannot "
                "be negative."
            )
        )

    return parsed


def _parse_priority(
    value: Any,
) -> ListingPriority:
    text = (
        _optional_text(
            value
        )
        or "normal"
    ).lower()

    mapping = {
        "high": (
            ListingPriority.HIGH
        ),
        "normal": (
            ListingPriority.NORMAL
        ),
        "low": (
            ListingPriority.LOW
        ),
    }

    if text not in mapping:
        raise ValueError(
            (
                "Priority must be High, "
                "Normal, or Low."
            )
        )

    return mapping[
        text
    ]


def _parse_status(
    value: Any,
) -> ListingStatus:
    text = (
        _optional_text(
            value
        )
        or "active"
    ).lower()

    mapping = {
        "active": (
            ListingStatus.ACTIVE
        ),
        "paused": (
            ListingStatus.PAUSED
        ),
        "sold": (
            ListingStatus.SOLD
        ),
        "archived": (
            ListingStatus.ARCHIVED
        ),
    }

    if text not in mapping:
        raise ValueError(
            (
                "Status must be Active, "
                "Paused, Sold, or Archived."
            )
        )

    return mapping[
        text
    ]


def _parse_bool(
    value: Any,
    default: bool,
) -> bool:
    if value is None:
        return default

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        return (
            value
            != 0
        )

    text = (
        str(
            value
        )
        .strip()
        .lower()
    )

    if text in {
        "true",
        "yes",
        "y",
        "1",
        "on",
    }:
        return True

    if text in {
        "false",
        "no",
        "n",
        "0",
        "off",
        "",
    }:
        return False

    raise ValueError(
        (
            "Invalid true/false "
            f"value: {value}"
        )
    )


def _parse_date(
    value: Any,
    default: date | None,
) -> date | None:
    if value in {
        None,
        "",
    }:
        return default

    if isinstance(
        value,
        datetime,
    ):
        return (
            value.date()
        )

    if isinstance(
        value,
        date,
    ):
        return value

    text = str(
        value
    ).strip()

    formats = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
    )

    for date_format in formats:
        try:
            return datetime.strptime(
                text,
                date_format,
            ).date()

        except ValueError:
            continue

    raise ValueError(
        (
            f"Invalid date: {value}. "
            "Use YYYY-MM-DD or DD/MM/YYYY."
        )
    )