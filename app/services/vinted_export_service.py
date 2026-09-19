from __future__ import annotations

import posixpath
import re
import tempfile
import zipfile

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable

from bs4 import BeautifulSoup
from bs4.element import Tag

from app.models import ListingPriority
from app.services.lifecycle_service import (
    mark_sold,
    set_queue_excluded,
)
from app.services.listing_service import (
    ListingInput,
    append_listing_note_line,
    create_listing,
    get_all_listings,
)
from app.services.photo_service import import_photos


VINTED_ID_PATTERN = re.compile(
    r"photos/(\d+)/"
)

EXISTING_ID_PATTERN = re.compile(
    r"\[VINTED_EXPORT_ITEM_ID=(\d+)\]"
)


class VintedExportError(Exception):
    """Raised when a Vinted personal-data export cannot be imported."""


@dataclass(slots=True)
class VintedExportListing:
    item_id: str
    title: str
    description: str
    price: Decimal
    currency: str
    brand: str | None
    size: str | None
    condition: str | None
    colour: str | None
    material: str | None
    parcel_size: str | None
    original_created_date: datetime
    photo_paths: list[str]
    views: int | None
    favourites: int | None
    sold: bool
    hidden: bool


@dataclass(slots=True)
class VintedImportResult:
    total_found: int = 0
    imported: int = 0
    skipped_existing: int = 0
    relisted_matched: int = 0
    photos_imported: int = 0
    sold_imported: int = 0
    hidden_imported: int = 0
    warnings: list[str] | None = None

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []


ProgressCallback = Callable[
    [int, int, str],
    None,
]


def import_vinted_export(
    source: str | Path,
    progress_callback: ProgressCallback | None = None,
) -> VintedImportResult:
    """
    Import listings from a Vinted personal-data export.

    Supports:
    - Vinted listings ZIP export
    - extracted Vinted listings/index.html

    Existing items are detected conservatively using stored Vinted
    IDs, unique exact-title relist matching, and stable title/detail
    signatures. Existing local listing fields are not overwritten.
    """
    source_path = Path(
        source
    ).expanduser().resolve()

    if not source_path.exists():
        raise VintedExportError(
            f"Export does not exist:\n{source_path}"
        )

    if source_path.suffix.lower() == ".zip":
        return _import_zip(
            source_path,
            progress_callback,
        )

    if (
        source_path.suffix.lower()
        in {
            ".html",
            ".htm",
        }
    ):
        return _import_html_folder(
            source_path,
            progress_callback,
        )

    raise VintedExportError(
        (
            "Select either the Vinted listings ZIP "
            "or its index.html file."
        )
    )


def _import_zip(
    zip_path: Path,
    progress_callback: ProgressCallback | None,
) -> VintedImportResult:
    try:
        archive = zipfile.ZipFile(
            zip_path,
            "r",
        )

    except (
        OSError,
        zipfile.BadZipFile,
    ) as exc:
        raise VintedExportError(
            f"Could not open Vinted ZIP:\n{exc}"
        ) from exc

    with archive:
        html_members = [
            name
            for name in archive.namelist()
            if (
                name.lower().endswith(
                    "/index.html"
                )
                or name.lower()
                == "index.html"
            )
        ]

        if not html_members:
            raise VintedExportError(
                (
                    "No index.html was found "
                    "inside the Vinted ZIP."
                )
            )

        html_member = _choose_listings_html(
            html_members,
            archive,
        )

        try:
            html_text = archive.read(
                html_member
            ).decode(
                "utf-8"
            )

        except Exception as exc:
            raise VintedExportError(
                (
                    "The Vinted listings HTML "
                    f"could not be read:\n{exc}"
                )
            ) from exc

        listings = _parse_html(
            html_text
        )

        result = VintedImportResult(
            total_found=len(
                listings
            )
        )

        existing_ids = (
            _existing_vinted_ids()
        )

        relisted_title_candidates = (
            _existing_relisted_title_candidates()
        )
        exact_detail_candidates = (
            _existing_exact_detail_candidates()
        )


        new_title_counts = (
            _new_export_title_counts(
                listings,
                existing_ids,
            )
        )

        html_directory = (
            posixpath.dirname(
                html_member
            )
        )

        archive_names = set(
            archive.namelist()
        )

        total = len(
            listings
        )

        for index, listing in enumerate(
            listings,
            start=1,
        ):
            if progress_callback is not None:
                progress_callback(
                    index,
                    total,
                    listing.title,
                )

            if listing.item_id in existing_ids:
                result.skipped_existing += 1
                continue

            relisted_listing_id = (
                _find_relisted_title_match(
                    listing,
                    relisted_title_candidates,
                    new_title_counts,
                )
            )

            if relisted_listing_id is not None:
                try:
                    _attach_relisted_vinted_id(
                        relisted_listing_id,
                        listing.item_id,
                    )

                except Exception as exc:
                    result.warnings.append(
                        (
                            f"{listing.title}: looked like a "
                            "relisted title match, but its new "
                            f"Vinted ID could not be attached: {exc}"
                        )
                    )

                    continue

                existing_ids.add(
                    listing.item_id
                )

                result.relisted_matched += 1

                continue

            exact_detail_matches = (
                _find_exact_detail_matches(
                    listing,
                    exact_detail_candidates,
                )
            )

            if exact_detail_matches:
                if len(
                    exact_detail_matches
                ) == 1:
                    matched_listing_id = (
                        exact_detail_matches[0]
                    )

                    try:
                        _attach_relisted_vinted_id(
                            matched_listing_id,
                            listing.item_id,
                        )

                    except Exception as exc:
                        result.skipped_existing += 1

                        result.warnings.append(
                            (
                                f"{listing.title}: exact title/details "
                                "duplicate already exists locally, "
                                "but its new Vinted ID could not be "
                                f"attached: {exc}"
                            )
                        )

                        continue

                    existing_ids.add(
                        listing.item_id
                    )

                    result.skipped_existing += 1

                    result.warnings.append(
                        (
                            f"{listing.title}: exact title/details "
                            "duplicate matched an existing listing. "
                            "Its new Vinted ID was attached and no "
                            "duplicate listing was created."
                        )
                    )

                    continue

                result.skipped_existing += 1

                result.warnings.append(
                    (
                        f"{listing.title}: multiple identical local "
                        "listings already exist. The incoming Vinted "
                        "item was skipped to avoid another duplicate."
                    )
                )

                continue

            if _has_ambiguous_relist_title_match(
                listing,
                relisted_title_candidates,
                new_title_counts,
            ):
                result.warnings.append(
                    (
                        f"{listing.title}: possible relisted item "
                        "had an ambiguous title match, so it was "
                        "treated as a new listing instead."
                    )
                )

            try:
                listing_id = _create_local_listing(
                    listing
                )

            except Exception as exc:
                result.warnings.append(
                    (
                        f"{listing.title}: metadata "
                        f"could not be imported: {exc}"
                    )
                )
                continue

            result.imported += 1
            exact_detail_candidates.setdefault(
                _vinted_stable_signature(
                    listing
                ),
                [],
            ).append(
                listing_id
            )

            existing_ids.add(
                listing.item_id
            )

            if listing.sold:
                try:
                    mark_sold(
                        listing_id
                    )
                    result.sold_imported += 1

                except Exception as exc:
                    result.warnings.append(
                        (
                            f"{listing.title}: imported, "
                            f"but Sold status failed: {exc}"
                        )
                    )

            if listing.hidden:
                try:
                    set_queue_excluded(
                        listing_id,
                        True,
                    )
                    result.hidden_imported += 1

                except Exception as exc:
                    result.warnings.append(
                        (
                            f"{listing.title}: imported, "
                            "but hidden/excluded status "
                            f"failed: {exc}"
                        )
                    )

            if not listing.photo_paths:
                result.warnings.append(
                    (
                        f"{listing.title}: no photos "
                        "were listed in the export."
                    )
                )
                continue

            with tempfile.TemporaryDirectory(
                prefix="vinted_import_"
            ) as temporary_directory:
                temporary_root = Path(
                    temporary_directory
                )

                extracted_photos: list[
                    Path
                ] = []

                for photo_index, relative_path in enumerate(
                    listing.photo_paths,
                    start=1,
                ):
                    archive_photo_path = (
                        posixpath.normpath(
                            posixpath.join(
                                html_directory,
                                relative_path,
                            )
                        )
                    )

                    if (
                        archive_photo_path
                        not in archive_names
                    ):
                        result.warnings.append(
                            (
                                f"{listing.title}: missing "
                                f"photo in ZIP: "
                                f"{relative_path}"
                            )
                        )
                        continue

                    suffix = (
                        Path(
                            relative_path
                        )
                        .suffix
                        .lower()
                    )

                    if not suffix:
                        suffix = ".webp"

                    temporary_photo = (
                        temporary_root
                        / (
                            f"{photo_index:03d}"
                            f"{suffix}"
                        )
                    )

                    try:
                        temporary_photo.write_bytes(
                            archive.read(
                                archive_photo_path
                            )
                        )

                        extracted_photos.append(
                            temporary_photo
                        )

                    except Exception as exc:
                        result.warnings.append(
                            (
                                f"{listing.title}: could not "
                                f"extract {relative_path}: "
                                f"{exc}"
                            )
                        )

                if extracted_photos:
                    try:
                        photo_ids = import_photos(
                            listing_id,
                            extracted_photos,
                        )

                        result.photos_imported += len(
                            photo_ids
                        )

                    except Exception as exc:
                        result.warnings.append(
                            (
                                f"{listing.title}: listing "
                                "was imported but photos "
                                f"failed: {exc}"
                            )
                        )

        return result


def _import_html_folder(
    html_path: Path,
    progress_callback: ProgressCallback | None,
) -> VintedImportResult:
    try:
        html_text = html_path.read_text(
            encoding="utf-8"
        )

    except OSError as exc:
        raise VintedExportError(
            f"Could not read index.html:\n{exc}"
        ) from exc

    listings = _parse_html(
        html_text
    )

    result = VintedImportResult(
        total_found=len(
            listings
        )
    )

    existing_ids = (
        _existing_vinted_ids()
    )

    relisted_title_candidates = (
        _existing_relisted_title_candidates()
    )
    exact_detail_candidates = (
        _existing_exact_detail_candidates()
    )


    new_title_counts = (
        _new_export_title_counts(
            listings,
            existing_ids,
        )
    )

    total = len(
        listings
    )

    for index, listing in enumerate(
        listings,
        start=1,
    ):
        if progress_callback is not None:
            progress_callback(
                index,
                total,
                listing.title,
            )

        if listing.item_id in existing_ids:
            result.skipped_existing += 1
            continue

        relisted_listing_id = (
            _find_relisted_title_match(
                listing,
                relisted_title_candidates,
                new_title_counts,
            )
        )

        if relisted_listing_id is not None:
            try:
                _attach_relisted_vinted_id(
                    relisted_listing_id,
                    listing.item_id,
                )

            except Exception as exc:
                result.warnings.append(
                    (
                        f"{listing.title}: looked like a "
                        "relisted title match, but its new "
                        f"Vinted ID could not be attached: {exc}"
                    )
                )

                continue

            existing_ids.add(
                listing.item_id
            )

            result.relisted_matched += 1

            continue

        exact_detail_matches = (
            _find_exact_detail_matches(
                listing,
                exact_detail_candidates,
            )
        )

        if exact_detail_matches:
            if len(
                exact_detail_matches
            ) == 1:
                matched_listing_id = (
                    exact_detail_matches[0]
                )

                try:
                    _attach_relisted_vinted_id(
                        matched_listing_id,
                        listing.item_id,
                    )

                except Exception as exc:
                    result.skipped_existing += 1

                    result.warnings.append(
                        (
                            f"{listing.title}: exact title/details "
                            "duplicate already exists locally, "
                            "but its new Vinted ID could not be "
                            f"attached: {exc}"
                        )
                    )

                    continue

                existing_ids.add(
                    listing.item_id
                )

                result.skipped_existing += 1

                result.warnings.append(
                    (
                        f"{listing.title}: exact title/details "
                        "duplicate matched an existing listing. "
                        "Its new Vinted ID was attached and no "
                        "duplicate listing was created."
                    )
                )

                continue

            result.skipped_existing += 1

            result.warnings.append(
                (
                    f"{listing.title}: multiple identical local "
                    "listings already exist. The incoming Vinted "
                    "item was skipped to avoid another duplicate."
                )
            )

            continue

        if _has_ambiguous_relist_title_match(
            listing,
            relisted_title_candidates,
            new_title_counts,
        ):
            result.warnings.append(
                (
                    f"{listing.title}: possible relisted item "
                    "had an ambiguous title match, so it was "
                    "treated as a new listing instead."
                )
            )

        try:
            listing_id = _create_local_listing(
                listing
            )

        except Exception as exc:
            result.warnings.append(
                (
                    f"{listing.title}: metadata "
                    f"could not be imported: {exc}"
                )
            )
            continue

        result.imported += 1
        exact_detail_candidates.setdefault(
            _vinted_stable_signature(
                listing
            ),
            [],
        ).append(
            listing_id
        )


        existing_ids.add(
            listing.item_id
        )

        if listing.sold:
            try:
                mark_sold(
                    listing_id
                )
                result.sold_imported += 1

            except Exception as exc:
                result.warnings.append(
                    (
                        f"{listing.title}: sold "
                        f"status failed: {exc}"
                    )
                )

        if listing.hidden:
            try:
                set_queue_excluded(
                    listing_id,
                    True,
                )
                result.hidden_imported += 1

            except Exception as exc:
                result.warnings.append(
                    (
                        f"{listing.title}: hidden "
                        f"status failed: {exc}"
                    )
                )

        photo_files: list[
            Path
        ] = []

        for relative_path in (
            listing.photo_paths
        ):
            photo_path = (
                html_path.parent
                / Path(
                    relative_path
                )
            ).resolve()

            if photo_path.exists():
                photo_files.append(
                    photo_path
                )
            else:
                result.warnings.append(
                    (
                        f"{listing.title}: missing "
                        f"photo: {photo_path}"
                    )
                )

        if photo_files:
            try:
                photo_ids = import_photos(
                    listing_id,
                    photo_files,
                )

                result.photos_imported += len(
                    photo_ids
                )

            except Exception as exc:
                result.warnings.append(
                    (
                        f"{listing.title}: listing "
                        "was imported but photos "
                        f"failed: {exc}"
                    )
                )

    return result


def _choose_listings_html(
    html_members: list[str],
    archive: zipfile.ZipFile,
) -> str:
    """
    Prefer the index.html that actually contains
    the Listings section.
    """
    for member in html_members:
        try:
            sample = archive.read(
                member
            ).decode(
                "utf-8",
                errors="ignore",
            )

        except Exception:
            continue

        if (
            "Your listings"
            in sample
            and 'itemprop="title"'
            in sample
        ):
            return member

    return html_members[
        0
    ]


def _parse_html(
    html_text: str,
) -> list[VintedExportListing]:
    soup = BeautifulSoup(
        html_text,
        "html.parser",
    )

    results: list[
        VintedExportListing
    ] = []

    for cell in soup.find_all(
        "div",
        class_="cell",
    ):
        if not isinstance(
            cell,
            Tag,
        ):
            continue

        title_element = cell.find(
            attrs={
                "itemprop": "title"
            },
            recursive=False,
        )

        if title_element is None:
            continue

        photo_paths = [
            str(
                element.get(
                    "src"
                )
            ).strip()
            for element in cell.find_all(
                "img",
                attrs={
                    "itemprop": "item_photo"
                },
            )
            if element.get(
                "src"
            )
        ]

        item_id = _extract_item_id(
            photo_paths
        )

        if item_id is None:
            raise VintedExportError(
                (
                    "A listing did not contain a "
                    "recognisable Vinted item ID:\n"
                    f"{_clean_text(title_element)}"
                )
            )

        price_text = _itemprop_text(
            cell,
            "order_value",
        )

        price, currency = (
            _parse_price(
                price_text
            )
        )

        created_text = _itemprop_text(
            cell,
            "created_at",
        )

        created_at = _parse_datetime(
            created_text
        )

        material_values = [
            _clean_text(
                element
            )
            for element in cell.find_all(
                attrs={
                    "itemprop": "material"
                }
            )
        ]

        material_values = [
            value
            for value in material_values
            if value
        ]

        material = (
            ", ".join(
                dict.fromkeys(
                    material_values
                )
            )
            or None
        )

        hidden = any(
            (
                _clean_text(
                    description
                )
                == "Is hidden"
            )
            for description in cell.find_all(
                "div",
                class_="cell-description",
            )
        )

        sold = (
            cell.find(
                attrs={
                    "itemprop":
                    "marked_as_sold"
                }
            )
            is not None
        )

        results.append(
            VintedExportListing(
                item_id=item_id,
                title=(
                    _clean_text(
                        title_element
                    )
                ),
                description=(
                    _itemprop_text(
                        cell,
                        "description",
                    )
                ),
                price=price,
                currency=currency,
                brand=(
                    _optional_itemprop_text(
                        cell,
                        "brand",
                    )
                ),
                size=(
                    _optional_itemprop_text(
                        cell,
                        "size",
                    )
                ),
                condition=(
                    _optional_itemprop_text(
                        cell,
                        "status",
                    )
                ),
                colour=(
                    _optional_itemprop_text(
                        cell,
                        "color",
                    )
                ),
                material=material,
                parcel_size=(
                    _optional_itemprop_text(
                        cell,
                        "parcel_size",
                    )
                ),
                original_created_date=(
                    created_at
                ),
                photo_paths=(
                    photo_paths
                ),
                views=(
                    _optional_int_itemprop(
                        cell,
                        "views_count",
                    )
                ),
                favourites=(
                    _optional_int_itemprop(
                        cell,
                        "favourite_count",
                    )
                ),
                sold=sold,
                hidden=hidden,
            )
        )

    if not results:
        raise VintedExportError(
            (
                "No Vinted listings were found "
                "in this HTML file."
            )
        )

    return results



def _normalize_vinted_title(
    value: str,
) -> str:
    """
    Normalize a title for conservative exact matching.

    Differences in capitalization and repeated whitespace
    are ignored. Wording itself must still be identical.
    """
    return " ".join(
        value.casefold().split()
    )


def _normalize_vinted_detail(
    value: object,
) -> str:
    """
    Normalize stable metadata for conservative duplicate matching.
    """
    if value is None:
        return ""

    return " ".join(
        str(
            value
        ).casefold().split()
    )


def _vinted_stable_signature(
    listing: VintedExportListing,
) -> tuple[str, ...]:
    """
    Fields expected to describe the same physical listing.

    Price, dates, sold/hidden state, views, favourites and relist
    information are intentionally excluded because they can change.
    """
    return tuple(
        _normalize_vinted_detail(
            value
        )
        for value in (
            listing.title,
            listing.description,
            listing.currency,
            listing.brand,
            listing.size,
            listing.condition,
            listing.colour,
            listing.material,
            listing.parcel_size,
        )
    )


def _local_stable_signature(
    listing: object,
) -> tuple[str, ...]:
    return tuple(
        _normalize_vinted_detail(
            getattr(
                listing,
                field,
                None,
            )
        )
        for field in (
            "title",
            "description",
            "currency",
            "brand",
            "size",
            "condition",
            "colour",
            "material",
            "parcel_size",
        )
    )


def _existing_exact_detail_candidates(
) -> dict[tuple[str, ...], list[int]]:
    """
    Group local listings by normalized title + stable metadata.
    """
    candidates: dict[
        tuple[str, ...],
        list[int],
    ] = {}

    for listing in get_all_listings():
        signature = (
            _local_stable_signature(
                listing
            )
        )

        candidates.setdefault(
            signature,
            [],
        ).append(
            listing.id
        )

    return candidates


def _find_exact_detail_matches(
    listing: VintedExportListing,
    candidates: dict[
        tuple[str, ...],
        list[int],
    ],
) -> list[int]:
    return list(
        candidates.get(
            _vinted_stable_signature(
                listing
            ),
            [],
        )
    )


def _existing_relisted_title_candidates(
) -> dict[str, list[int]]:
    """
    Return existing Vinted-imported listings grouped by their
    normalized exact title.

    Despite the legacy function name, candidates do not need to
    have been manually marked as relisted inside the app.

    This is important when comparing an older Vinted export with
    a newer one: a relisted Vinted item receives a new Vinted ID,
    but the local copy from the older export may never have been
    explicitly marked as relisted.

    Only listings that already contain a Vinted export item-ID
    marker are considered, so ordinary manually-created listings
    are not automatically absorbed into Vinted relist matching.
    """
    candidates: dict[
        str,
        list[int],
    ] = {}

    for listing in get_all_listings():
        notes = (
            listing.notes
            or ""
        )

        # Only listings known to have come from Vinted.
        if (
            EXISTING_ID_PATTERN.search(
                notes
            )
            is None
        ):
            continue

        normalized_title = (
            _normalize_vinted_title(
                listing.title
            )
        )

        if not normalized_title:
            continue

        candidates.setdefault(
            normalized_title,
            [],
        ).append(
            listing.id
        )

    return candidates




def _new_export_title_counts(
    listings: list[VintedExportListing],
    existing_ids: set[str],
) -> dict[str, int]:
    """
    Count titles belonging to genuinely unseen Vinted IDs
    inside this export.

    We only auto-match a title when it occurs once among new
    IDs, which avoids attaching two same-title products to one
    local listing.
    """
    counts: dict[
        str,
        int,
    ] = {}

    for listing in listings:
        if listing.item_id in existing_ids:
            continue

        normalized_title = (
            _normalize_vinted_title(
                listing.title
            )
        )

        if not normalized_title:
            continue

        counts[
            normalized_title
        ] = (
            counts.get(
                normalized_title,
                0,
            )
            + 1
        )

    return counts


def _find_relisted_title_match(
    listing: VintedExportListing,
    candidates: dict[str, list[int]],
    new_title_counts: dict[str, int],
) -> int | None:
    """
    Return a local listing ID only when the title match is
    completely unambiguous.
    """
    normalized_title = (
        _normalize_vinted_title(
            listing.title
        )
    )

    if not normalized_title:
        return None

    # There must be only one new Vinted item with this title.
    if (
        new_title_counts.get(
            normalized_title,
            0,
        )
        != 1
    ):
        return None

    local_matches = (
        candidates.get(
            normalized_title,
            [],
        )
    )

    # There must also be only one eligible local listing.
    if len(local_matches) != 1:
        return None

    return local_matches[0]


def _has_ambiguous_relist_title_match(
    listing: VintedExportListing,
    candidates: dict[str, list[int]],
    new_title_counts: dict[str, int],
) -> bool:
    normalized_title = (
        _normalize_vinted_title(
            listing.title
        )
    )

    if not normalized_title:
        return False

    local_matches = (
        candidates.get(
            normalized_title,
            [],
        )
    )

    if not local_matches:
        return False

    return (
        len(local_matches) != 1
        or (
            new_title_counts.get(
                normalized_title,
                0,
            )
            != 1
        )
    )


def _attach_relisted_vinted_id(
    listing_id: int,
    item_id: str,
) -> None:
    marker = (
        "[VINTED_EXPORT_ITEM_ID="
        f"{item_id}]"
    )

    append_listing_note_line(
        listing_id,
        marker,
    )

def _create_local_listing(
    listing: VintedExportListing,
) -> int:
    notes_lines = [
        (
            "[VINTED_EXPORT_ITEM_ID="
            f"{listing.item_id}]"
        ),
        "Imported from Vinted personal data export.",
    ]

    if listing.views is not None:
        notes_lines.append(
            (
                "Vinted export views: "
                f"{listing.views}"
            )
        )

    if listing.favourites is not None:
        notes_lines.append(
            (
                "Vinted export favourites: "
                f"{listing.favourites}"
            )
        )

    if listing.hidden:
        notes_lines.append(
            (
                "Vinted export state: hidden; "
                "excluded from relisting queue."
            )
        )

    if listing.sold:
        notes_lines.append(
            "Vinted export state: sold."
        )

    return create_listing(
        ListingInput(
            title=listing.title,
            description=listing.description,
            price=listing.price,
            currency=listing.currency,
            brand=listing.brand,
            size=listing.size,
            condition=listing.condition,
            colour=listing.colour,
            material=listing.material,
            parcel_size=listing.parcel_size,
            notes="\n".join(
                notes_lines
            ),
            original_created_date=(
                listing
                .original_created_date
                .date()
            ),
            priority=(
                ListingPriority.NORMAL
            ),
        )
    )


def _existing_vinted_ids() -> set[str]:
    existing: set[str] = set()

    for listing in get_all_listings():
        notes = (
            listing.notes
            or ""
        )

        for match in (
            EXISTING_ID_PATTERN.finditer(
                notes
            )
        ):
            existing.add(
                match.group(
                    1
                )
            )

    return existing


def _extract_item_id(
    photo_paths: list[str],
) -> str | None:
    for path in photo_paths:
        match = VINTED_ID_PATTERN.search(
            path.replace(
                "\\",
                "/",
            )
        )

        if match:
            return match.group(
                1
            )

    return None


def _itemprop_text(
    cell: Tag,
    itemprop: str,
) -> str:
    element = cell.find(
        attrs={
            "itemprop": itemprop
        }
    )

    if element is None:
        return ""

    return _clean_text(
        element
    )


def _optional_itemprop_text(
    cell: Tag,
    itemprop: str,
) -> str | None:
    value = _itemprop_text(
        cell,
        itemprop,
    )

    return (
        value
        if value
        else None
    )


def _optional_int_itemprop(
    cell: Tag,
    itemprop: str,
) -> int | None:
    value = _itemprop_text(
        cell,
        itemprop,
    )

    if not value:
        return None

    try:
        return int(
            value
        )

    except ValueError:
        return None


def _parse_price(
    value: str,
) -> tuple[Decimal, str]:
    parts = value.strip().split()

    if not parts:
        raise VintedExportError(
            "A listing has no price."
        )

    try:
        price = Decimal(
            parts[
                0
            ].replace(
                ",",
                ".",
            )
        )

    except InvalidOperation as exc:
        raise VintedExportError(
            f"Invalid Vinted price: {value}"
        ) from exc

    currency = (
        parts[
            1
        ].upper()
        if len(
            parts
        ) >= 2
        else "EUR"
    )

    return (
        price,
        currency,
    )


def _parse_datetime(
    value: str,
) -> datetime:
    value = value.strip()

    formats = (
        "%Y-%m-%d %H:%M:%S %z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    )

    for date_format in formats:
        try:
            return datetime.strptime(
                value,
                date_format,
            )

        except ValueError:
            continue

    raise VintedExportError(
        (
            "Could not understand Vinted "
            f"upload date: {value}"
        )
    )


def _clean_text(
    element: Tag,
) -> str:
    return (
        element.get_text(
            "\n",
            strip=True,
        )
        .replace(
            "\r\n",
            "\n",
        )
        .replace(
            "\r",
            "\n",
        )
        .strip()
    )