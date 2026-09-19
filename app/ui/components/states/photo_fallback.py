from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


def show_photo_fallback(
    label: QLabel,
    *,
    preview_unavailable: bool = False,
    object_name: str = "noPhoto",
) -> None:
    """
    Show a compact, friendly placeholder when a listing has
    no local photo or when its preview cannot be loaded.
    """
    label.clear()

    label.setObjectName(
        object_name
    )

    label.setProperty(
        "photoFallback",
        True,
    )

    label.setAlignment(
        Qt.AlignmentFlag.AlignCenter
    )

    label.setWordWrap(
        True
    )

    if preview_unavailable:
        label.setText(
            "Preview unavailable\n"
            "Edit photos to fix"
        )

        label.setToolTip(
            "The listing has photo data, but its local preview "
            "could not be loaded."
        )

    else:
        label.setText(
            "No photo\n"
            "Edit listing to add"
        )

        label.setToolTip(
            "This listing does not have a local photo yet."
        )
