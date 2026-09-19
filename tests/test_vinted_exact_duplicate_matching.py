from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from app.services.vinted_export_service import (
    VintedExportListing,
    _find_exact_detail_matches,
    _local_stable_signature,
    _vinted_stable_signature,
)


def make_listing(
    *,
    title: str = "Black T-Shirt",
    description: str = "Great condition",
    price: str = "10.00",
    brand: str | None = "Test Brand",
) -> VintedExportListing:
    return VintedExportListing(
        item_id="12345",
        title=title,
        description=description,
        price=Decimal(
            price
        ),
        currency="EUR",
        brand=brand,
        size="M",
        condition="Very good",
        colour="Black",
        material="Cotton",
        parcel_size="Small",
        original_created_date=datetime(
            2026,
            1,
            1,
        ),
        photo_paths=[],
        views=None,
        favourites=None,
        sold=False,
        hidden=False,
    )


def test_signature_ignores_case_whitespace_and_price(
) -> None:
    exported = make_listing(
        title="  BLACK   T-Shirt ",
        price="8.00",
    )

    local = SimpleNamespace(
        title="black t-shirt",
        description="great CONDITION",
        currency="eur",
        brand="test brand",
        size="m",
        condition="very GOOD",
        colour="black",
        material="cotton",
        parcel_size="small",
    )

    assert (
        _vinted_stable_signature(
            exported
        )
        == _local_stable_signature(
            local
        )
    )


def test_same_title_different_metadata_is_allowed(
) -> None:
    incoming = make_listing(
        brand="Brand A"
    )

    existing = make_listing(
        brand="Brand B"
    )

    candidates = {
        _vinted_stable_signature(
            existing
        ): [
            99
        ]
    }

    assert (
        _find_exact_detail_matches(
            incoming,
            candidates,
        )
        == []
    )


def test_one_exact_match_returns_local_id(
) -> None:
    incoming = make_listing()

    candidates = {
        _vinted_stable_signature(
            incoming
        ): [
            42
        ]
    }

    assert (
        _find_exact_detail_matches(
            incoming,
            candidates,
        )
        == [
            42
        ]
    )


def test_multiple_exact_matches_remain_ambiguous(
) -> None:
    incoming = make_listing()

    candidates = {
        _vinted_stable_signature(
            incoming
        ): [
            10,
            11,
        ]
    }

    assert (
        _find_exact_detail_matches(
            incoming,
            candidates,
        )
        == [
            10,
            11,
        ]
    )
