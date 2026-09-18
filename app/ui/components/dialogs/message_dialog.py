from __future__ import annotations

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class BrandedMessageDialog(QDialog):
    """
    Compact app-styled popup.

    Intentionally simple:
    - no repeated app logo
    - no long explanation blocks
    - no oversized popup
    - short title
    - short message
    - clear actions
    """

    def __init__(
        self,
        *,
        title: str,
        message: str,
        eyebrow: str = "",
        detail: str = "",
        confirm_text: str = "OK",
        cancel_text: str | None = None,
        parent: QWidget | None = None,
        confirm_object_name: str = "primaryButton",
        default_to_cancel: bool = False,
    ) -> None:
        super().__init__(
            parent
        )

        # Kept for compatibility with existing calls.
        # We deliberately do not display these anymore.
        _ = eyebrow
        _ = detail

        self._confirmed = False

        self.setWindowTitle(
            title
        )

        self.setModal(
            True
        )

        self.setMinimumWidth(
            390
        )

        self.setMaximumWidth(
            500
        )

        self._build_ui(
            title=title,
            message=message,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            confirm_object_name=(
                confirm_object_name
            ),
            default_to_cancel=(
                default_to_cancel
            ),
        )

    def _build_ui(
        self,
        *,
        title: str,
        message: str,
        confirm_text: str,
        cancel_text: str | None,
        confirm_object_name: str,
        default_to_cancel: bool,
    ) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            24,
            22,
            24,
            20,
        )

        layout.setSpacing(
            10
        )

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

        heading = QLabel(
            title
        )

        heading.setObjectName(
            "placeholderTitle"
        )

        heading.setWordWrap(
            True
        )

        heading.setAlignment(
            Qt.AlignmentFlag.AlignLeft
        )

        layout.addWidget(
            heading
        )

        # -------------------------------------------------
        # Message
        # -------------------------------------------------

        message_label = QLabel(
            message
        )

        message_label.setObjectName(
            "informationText"
        )

        message_label.setWordWrap(
            True
        )

        message_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
        )

        layout.addWidget(
            message_label
        )

        layout.addSpacing(
            8
        )

        # -------------------------------------------------
        # Buttons
        # -------------------------------------------------

        button_row = QHBoxLayout()

        button_row.setSpacing(
            8
        )

        button_row.addStretch()

        cancel_button: QPushButton | None = None

        if cancel_text:
            cancel_button = QPushButton(
                cancel_text
            )

            cancel_button.setObjectName(
                "secondaryButton"
            )

            cancel_button.setMinimumHeight(
                38
            )

            cancel_button.setMinimumWidth(
                105
            )

            cancel_button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            cancel_button.clicked.connect(
                self.reject
            )

            button_row.addWidget(
                cancel_button
            )

        confirm_button = QPushButton(
            confirm_text
        )

        confirm_button.setObjectName(
            confirm_object_name
        )

        confirm_button.setMinimumHeight(
            38
        )

        confirm_button.setMinimumWidth(
            110
        )

        confirm_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        confirm_button.clicked.connect(
            self._confirm
        )

        button_row.addWidget(
            confirm_button
        )

        layout.addLayout(
            button_row
        )

        if (
            default_to_cancel
            and cancel_button is not None
        ):
            cancel_button.setDefault(
                True
            )

            cancel_button.setFocus()

        else:
            confirm_button.setDefault(
                True
            )

            confirm_button.setFocus()

    def _confirm(
        self,
    ) -> None:
        self._confirmed = True

        self.accept()

    @property
    def confirmed(
        self,
    ) -> bool:
        return self._confirmed

    # =====================================================
    # Helpers
    # =====================================================

    @classmethod
    def ask(
        cls,
        parent: QWidget | None,
        *,
        title: str,
        message: str,
        eyebrow: str = "",
        detail: str = "",
        confirm_text: str = "CONFIRM",
        cancel_text: str = "CANCEL",
    ) -> bool:
        dialog = cls(
            parent=parent,
            title=title,
            message=message,
            eyebrow=eyebrow,
            detail=detail,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            default_to_cancel=True,
        )

        dialog.exec()

        return dialog.confirmed

    @classmethod
    def notice(
        cls,
        parent: QWidget | None,
        *,
        title: str,
        message: str,
        detail: str = "",
        button_text: str = "OK",
    ) -> None:
        dialog = cls(
            parent=parent,
            title=title,
            message=message,
            detail=detail,
            confirm_text=button_text,
        )

        dialog.exec()

    @classmethod
    def warning(
        cls,
        parent: QWidget | None,
        *,
        title: str,
        message: str,
        detail: str = "",
        button_text: str = "OK",
    ) -> None:
        dialog = cls(
            parent=parent,
            title=title,
            message=message,
            detail=detail,
            confirm_text=button_text,
        )

        dialog.exec()

    @classmethod
    def error(
        cls,
        parent: QWidget | None,
        *,
        title: str,
        message: str,
        detail: str = "",
        button_text: str = "OK",
    ) -> None:
        dialog = cls(
            parent=parent,
            title=title,
            message=message,
            detail=detail,
            confirm_text=button_text,
        )

        dialog.exec()