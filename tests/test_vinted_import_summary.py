from __future__ import annotations

from app.ui.vinted_export_import_dialog import (
    _split_vinted_warnings,
)


def test_successful_exact_duplicate_is_not_shown_as_warning(
) -> None:
    successful_match = (
        "Black T-Shirt: exact title/details duplicate matched "
        "an existing listing. Its new Vinted ID was attached "
        "and no duplicate listing was created."
    )

    real_warning = (
        "Blue Shirt: missing photo in ZIP: photos/example.webp"
    )

    matched, warnings = _split_vinted_warnings(
        [
            successful_match,
            real_warning,
        ]
    )

    assert matched == 1
    assert warnings == [
        real_warning
    ]


def test_warning_split_handles_no_warnings(
) -> None:
    matched, warnings = _split_vinted_warnings(
        None
    )

    assert matched == 0
    assert warnings == []
