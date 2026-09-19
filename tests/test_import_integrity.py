from __future__ import annotations

import json
from datetime import date

from app.database import session_scope
from app.models import (
    Listing,
    ListingStatus,
)
from app.services.import_service import (
    import_listings_file,
)


def _write_json(
    tmp_path,
    rows,
):
    path = (
        tmp_path
        / "import.json"
    )

    path.write_text(
        json.dumps(
            rows
        ),
        encoding="utf-8",
    )

    return path


def _all_listings():
    with session_scope() as session:
        return list(
            session.query(
                Listing
            ).order_by(
                Listing.id
            ).all()
        )


def test_duplicate_rows_inside_same_file_are_not_imported_twice(
    tmp_path,
) -> None:
    row = {
        "title": "Duplicate Bag",
        "description": "Same item",
        "price": "12.50",
        "currency": "EUR",
        "brand": "Test Brand",
    }

    path = _write_json(
        tmp_path,
        [
            row,
            dict(row),
        ],
    )

    result = import_listings_file(
        path
    )

    assert result.imported_count == 1
    assert result.skipped_count == 1
    assert len(_all_listings()) == 1

    assert any(
        "earlier in this import"
        in warning.message
        for warning
        in result.warnings
    )


def test_reimporting_same_file_creates_no_duplicates(
    tmp_path,
) -> None:
    path = _write_json(
        tmp_path,
        [
            {
                "title": "One Item",
                "description": "Description",
                "price": "9.99",
                "currency": "EUR",
            }
        ],
    )

    first = import_listings_file(
        path
    )

    second = import_listings_file(
        path
    )

    assert first.imported_count == 1
    assert second.imported_count == 0
    assert second.skipped_count == 1
    assert len(_all_listings()) == 1


def test_duplicate_signature_normalizes_case_and_whitespace(
    tmp_path,
) -> None:
    path = _write_json(
        tmp_path,
        [
            {
                "title": "  Black   Bag  ",
                "description": "Nice   condition",
                "price": "10",
                "currency": "eur",
                "brand": "TEST BRAND",
            },
            {
                "title": "black bag",
                "description": "nice condition",
                "price": "10.00",
                "currency": "EUR",
                "brand": "test brand",
            },
        ],
    )

    result = import_listings_file(
        path
    )

    assert result.imported_count == 1
    assert result.skipped_count == 1
    assert len(_all_listings()) == 1


def test_import_preserves_and_normalizes_isbn(
    tmp_path,
) -> None:
    path = _write_json(
        tmp_path,
        [
            {
                "title": "Book",
                "description": "ISBN import",
                "price": "6.50",
                "isbn": "978-0-306-40615-7",
            }
        ],
    )

    result = import_listings_file(
        path
    )

    assert result.imported_count == 1

    listing = _all_listings()[0]

    assert (
        listing.isbn
        == "9780306406157"
    )


def test_invalid_isbn_skips_row_without_creating_listing(
    tmp_path,
) -> None:
    path = _write_json(
        tmp_path,
        [
            {
                "title": "Bad ISBN",
                "description": "Should fail",
                "price": "5.00",
                "isbn": "123-not-valid",
            }
        ],
    )

    result = import_listings_file(
        path
    )

    assert result.imported_count == 0
    assert result.skipped_count == 1
    assert len(result.errors) == 1
    assert len(_all_listings()) == 0


def test_invalid_currency_skips_row(
    tmp_path,
) -> None:
    path = _write_json(
        tmp_path,
        [
            {
                "title": "Bad Currency",
                "description": "Should fail",
                "price": "5.00",
                "currency": "EU1",
            }
        ],
    )

    result = import_listings_file(
        path
    )

    assert result.imported_count == 0
    assert result.skipped_count == 1
    assert len(_all_listings()) == 0


def test_sold_import_clears_conflicting_archive_and_pause_flags(
    tmp_path,
) -> None:
    path = _write_json(
        tmp_path,
        [
            {
                "title": "Sold Conflict",
                "description": "Conflicting legacy state",
                "price": "20.00",
                "sold": True,
                "archived": True,
                "paused_indefinitely": True,
                "paused_until": "2027-01-01",
            }
        ],
    )

    result = import_listings_file(
        path
    )

    assert result.imported_count == 1

    listing = _all_listings()[0]

    assert listing.status == ListingStatus.SOLD
    assert listing.sold is True
    assert listing.archived is False
    assert listing.paused_until is None
    assert listing.paused_indefinitely is False


def test_archived_import_clears_pause_state(
    tmp_path,
) -> None:
    path = _write_json(
        tmp_path,
        [
            {
                "title": "Archived Conflict",
                "description": "Archive wins over pause",
                "price": "11.00",
                "archived": True,
                "paused_indefinitely": True,
                "paused_until": "2027-01-01",
            }
        ],
    )

    result = import_listings_file(
        path
    )

    assert result.imported_count == 1

    listing = _all_listings()[0]

    assert listing.status == ListingStatus.ARCHIVED
    assert listing.archived is True
    assert listing.sold is False
    assert listing.paused_until is None
    assert listing.paused_indefinitely is False


def test_explicit_paused_status_without_date_becomes_indefinite(
    tmp_path,
) -> None:
    path = _write_json(
        tmp_path,
        [
            {
                "title": "Paused Listing",
                "description": "No pause date",
                "price": "7.00",
                "status": "paused",
            }
        ],
    )

    result = import_listings_file(
        path
    )

    assert result.imported_count == 1

    listing = _all_listings()[0]

    assert listing.status == ListingStatus.PAUSED
    assert listing.sold is False
    assert listing.archived is False
    assert listing.paused_until is None
    assert listing.paused_indefinitely is True
