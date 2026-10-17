from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import (
    selectinload,
)

from app.database import (
    session_scope,
)
from app.models import (
    Listing,
    Tag,
)


MAX_TAG_LENGTH = 80


@dataclass(slots=True)
class TagListingSummary:
    listing_id: int
    title: str
    category: str | None
    subcategory: str | None
    brand: str | None
    status: str
    tags: tuple[str, ...]


@dataclass(slots=True)
class BulkTagResult:
    listings_changed: int = 0
    associations_changed: int = 0
    already_in_state: int = 0
    missing_listings: int = 0


def normalize_tag_name(
    value: str,
) -> tuple[str, str]:
    """
    Return display and normalized forms of a tag.
    """
    display_name = " ".join(
        value.split()
    )

    if not display_name:
        raise ValueError(
            "Tag cannot be empty."
        )

    if (
        len(display_name)
        > MAX_TAG_LENGTH
    ):
        raise ValueError(
            (
                "Tag must be "
                f"{MAX_TAG_LENGTH} characters "
                "or fewer."
            )
        )

    return (
        display_name,
        display_name.casefold(),
    )


def _clean_tag_names(
    tag_names: list[str],
) -> list[
    tuple[str, str]
]:
    cleaned: list[
        tuple[str, str]
    ] = []

    seen: set[str] = set()

    for value in tag_names:
        display, normalized = (
            normalize_tag_name(
                value
            )
        )

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        cleaned.append(
            (
                display,
                normalized,
            )
        )

    return cleaned


def get_existing_tags() -> list[str]:
    """
    Return all currently defined tags.
    """
    with session_scope() as session:
        tags = list(
            session.scalars(
                select(
                    Tag
                )
            ).all()
        )

        names = [
            tag.name
            for tag in tags
        ]

    return sorted(
        names,
        key=str.casefold,
    )


def get_tag_listing_summaries(
) -> list[TagListingSummary]:
    """
    Return lightweight listing information for the
    Bulk Tags dialog.
    """
    with session_scope() as session:
        listings = list(
            session.scalars(
                select(
                    Listing
                )
                .options(
                    selectinload(
                        Listing.tags
                    )
                )
                .order_by(
                    Listing.title.asc(),
                    Listing.id.asc(),
                )
            ).all()
        )

        return [
            TagListingSummary(
                listing_id=listing.id,
                title=listing.title,
                category=listing.category,
                subcategory=(
                    listing.subcategory
                ),
                brand=listing.brand,
                status=(
                    listing.status.value
                ),
                tags=tuple(
                    sorted(
                        (
                            tag.name
                            for tag
                            in listing.tags
                        ),
                        key=str.casefold,
                    )
                ),
            )
            for listing in listings
        ]


def _resolve_tags(
    session,
    cleaned_names: list[
        tuple[str, str]
    ],
    *,
    create_missing: bool,
) -> list[Tag]:
    normalized_names = [
        normalized
        for (
            _display,
            normalized,
        )
        in cleaned_names
    ]

    if not normalized_names:
        return []

    existing = list(
        session.scalars(
            select(
                Tag
            )
            .where(
                Tag.normalized_name.in_(
                    normalized_names
                )
            )
        ).all()
    )

    by_normalized = {
        tag.normalized_name: tag
        for tag in existing
    }

    if create_missing:
        for (
            display,
            normalized,
        ) in cleaned_names:
            if normalized in by_normalized:
                continue

            tag = Tag(
                name=display,
                normalized_name=normalized,
            )

            session.add(
                tag
            )

            by_normalized[
                normalized
            ] = tag

        session.flush()

    return [
        by_normalized[
            normalized
        ]
        for (
            _display,
            normalized,
        ) in cleaned_names
        if normalized
        in by_normalized
    ]


def _load_listings(
    session,
    listing_ids: list[int],
) -> tuple[
    list[Listing],
    int,
]:
    unique_ids = list(
        dict.fromkeys(
            listing_ids
        )
    )

    if not unique_ids:
        return (
            [],
            0,
        )

    listings = list(
        session.scalars(
            select(
                Listing
            )
            .options(
                selectinload(
                    Listing.tags
                )
            )
            .where(
                Listing.id.in_(
                    unique_ids
                )
            )
        ).all()
    )

    found_ids = {
        listing.id
        for listing
        in listings
    }

    missing = len(
        set(
            unique_ids
        )
        - found_ids
    )

    return (
        listings,
        missing,
    )


def bulk_add_tags(
    listing_ids: list[int],
    tag_names: list[str],
) -> BulkTagResult:
    """
    Add one or more tags to several listings.

    The operation is idempotent. Applying an existing tag
    again does not create a duplicate association.
    """
    cleaned_names = (
        _clean_tag_names(
            tag_names
        )
    )

    result = BulkTagResult()

    if not listing_ids:
        return result

    with session_scope() as session:
        listings, missing = (
            _load_listings(
                session,
                listing_ids,
            )
        )

        result.missing_listings = (
            missing
        )

        tags = _resolve_tags(
            session,
            cleaned_names,
            create_missing=True,
        )

        for listing in listings:
            existing = {
                tag.normalized_name
                for tag
                in listing.tags
            }

            listing_changed = False

            for tag in tags:
                if (
                    tag.normalized_name
                    in existing
                ):
                    result.already_in_state += 1
                    continue

                listing.tags.append(
                    tag
                )

                existing.add(
                    tag.normalized_name
                )

                result.associations_changed += 1
                listing_changed = True

            if listing_changed:
                result.listings_changed += 1

    return result


def bulk_remove_tags(
    listing_ids: list[int],
    tag_names: list[str],
) -> BulkTagResult:
    """
    Remove one or more tags from several listings.

    Removing a tag that is not present is harmless.
    """
    cleaned_names = (
        _clean_tag_names(
            tag_names
        )
    )

    requested_normalized = [
        normalized
        for (
            _display,
            normalized,
        )
        in cleaned_names
    ]

    result = BulkTagResult()

    if not listing_ids:
        return result

    with session_scope() as session:
        listings, missing = (
            _load_listings(
                session,
                listing_ids,
            )
        )

        result.missing_listings = (
            missing
        )

        for listing in listings:
            current = {
                tag.normalized_name: tag
                for tag
                in listing.tags
            }

            listing_changed = False

            for normalized in (
                requested_normalized
            ):
                tag = current.get(
                    normalized
                )

                if tag is None:
                    result.already_in_state += 1
                    continue

                listing.tags.remove(
                    tag
                )

                current.pop(
                    normalized,
                    None,
                )

                result.associations_changed += 1
                listing_changed = True

            if listing_changed:
                result.listings_changed += 1

    return result
