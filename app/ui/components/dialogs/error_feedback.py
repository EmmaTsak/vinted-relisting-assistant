from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
)

from app.services.logging_service import (
    log_exception,
)
from app.ui.components.dialogs.message_dialog import (
    BrandedMessageDialog,
)


def show_logged_error(
    parent: QWidget | None,
    *,
    title: str,
    message: str,
    context: str,
    exception: BaseException,
) -> None:
    """
    Log the technical error locally and show only a short,
    useful message to the user.
    """
    log_exception(
        context,
        exception,
    )

    BrandedMessageDialog.error(
        parent,
        title=title,
        message=(
            f"{message}\n\n"
            "Details were saved to the app log."
        ),
        button_text="OK",
    )


def log_background_error(
    *,
    context: str,
    exception: BaseException,
) -> None:
    """
    Record a non-fatal technical problem without showing
    another popup.
    """
    log_exception(
        context,
        exception,
    )
