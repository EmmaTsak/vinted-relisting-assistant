from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.database import session_scope
from app.models import Listing


@dataclass(slots=True)
class CategoryListingSummary:
    """
    Lightweight listing information used by the bulk
    category manager.
    """

    listing_id: int
    title: str
    category: str | None
    subcategory: str | None
    brand: str | None
    status: str


@dataclass(slots=True)
class BulkCategoryResult:
    """
    Result of a bulk category update.
    """

    updated: int = 0
    skipped_existing: int = 0
    missing: int = 0


def get_category_listing_summaries(
    search_text: str = "",
) -> list[CategoryListingSummary]:
    """
    Return lightweight listing data for category management.

    Search checks:
    - title
    - category
    - subcategory
    - brand
    """
    normalized_search = (
        search_text
        .strip()
        .casefold()
    )

    with session_scope() as session:
        listings = list(
            session.scalars(
                select(Listing)
                .order_by(
                    Listing.title.asc(),
                    Listing.id.asc(),
                )
            ).all()
        )

        results: list[
            CategoryListingSummary
        ] = []

        for listing in listings:
            searchable = " ".join(
                value
                for value in (
                    listing.title,
                    listing.category,
                    listing.subcategory,
                    listing.brand,
                )
                if value
            ).casefold()

            if (
                normalized_search
                and normalized_search
                not in searchable
            ):
                continue

            results.append(
                CategoryListingSummary(
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
                )
            )

        return results


def get_existing_categories() -> list[str]:
    """
    Return every unique category currently used.
    """
    with session_scope() as session:
        values = session.scalars(
            select(
                Listing.category
            )
            .where(
                Listing.category.is_not(
                    None
                )
            )
        ).all()

    return sorted(
        {
            value.strip()
            for value in values
            if (
                value
                and value.strip()
            )
        },
        key=str.casefold,
    )


def get_existing_subcategories() -> list[str]:
    """
    Return every unique subcategory currently used.
    """
    with session_scope() as session:
        values = session.scalars(
            select(
                Listing.subcategory
            )
            .where(
                Listing.subcategory.is_not(
                    None
                )
            )
        ).all()

    return sorted(
        {
            value.strip()
            for value in values
            if (
                value
                and value.strip()
            )
        },
        key=str.casefold,
    )


def bulk_assign_category(
    listing_ids: list[int],
    category: str,
    subcategory: str | None = None,
    *,
    overwrite_existing: bool = False,
    update_subcategory: bool = True,
) -> BulkCategoryResult:
    """
    Assign a category to several listings.

    Existing categories are protected by default.

    Set overwrite_existing=True only when the user has
    explicitly chosen to replace them.
    """
    cleaned_category = (
        category.strip()
    )

    if not cleaned_category:
        raise ValueError(
            "Category cannot be empty."
        )

    cleaned_subcategory = None

    if subcategory is not None:
        cleaned = (
            subcategory.strip()
        )

        if cleaned:
            cleaned_subcategory = (
                cleaned
            )

    unique_ids = list(
        dict.fromkeys(
            listing_ids
        )
    )

    result = (
        BulkCategoryResult()
    )

    if not unique_ids:
        return result

    with session_scope() as session:
        listings = list(
            session.scalars(
                select(Listing)
                .where(
                    Listing.id.in_(
                        unique_ids
                    )
                )
            ).all()
        )

        found_ids = {
            listing.id
            for listing in listings
        }

        result.missing = len(
            set(unique_ids)
            - found_ids
        )

        for listing in listings:
            has_existing_category = bool(
                listing.category
                and listing.category.strip()
            )

            if (
                has_existing_category
                and not overwrite_existing
            ):
                result.skipped_existing += 1
                continue

            listing.category = (
                cleaned_category
            )

            if update_subcategory:
                listing.subcategory = (
                    cleaned_subcategory
                )

            result.updated += 1

    return result