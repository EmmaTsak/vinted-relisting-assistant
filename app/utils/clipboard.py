from __future__ import annotations

from PySide6.QtWidgets import QApplication


class ClipboardError(RuntimeError):
    """Raised when the application clipboard is unavailable."""


def copy_text(text: str) -> None:
    """
    Copy text to the Windows clipboard.
    """
    application = QApplication.instance()

    if application is None:
        raise ClipboardError(
            "The application clipboard is not available."
        )

    clipboard = application.clipboard()

    clipboard.setText(
        str(text)
    )