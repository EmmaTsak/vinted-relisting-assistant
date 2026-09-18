from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FriendlyEmptyState(QFrame):
    """
    Warm empty state for safe, non-critical moments.

    Uses the application's own branded icon instead of emoji
    or unrelated decorative artwork.
    """

    def __init__(
        self,
        title: str,
        message: str,
        action_text: str | None = None,
        action: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.setObjectName(
            "emptyState"
        )

        self.setMinimumHeight(
            260
        )

        self._build_ui(
            title=title,
            message=message,
            action_text=action_text,
            action=action,
        )

    def _build_ui(
        self,
        title: str,
        message: str,
        action_text: str | None,
        action: Callable[[], None] | None,
    ) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            40,
            32,
            40,
            32,
        )

        layout.setSpacing(
            10
        )

        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # -------------------------------------------------
        # Illustration
        # -------------------------------------------------

        icon_label = QLabel()

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon_label.setFixedSize(
            90,
            90,
        )

        icon_label.setObjectName(
            "emptyStateIllustration"
        )

        app = QApplication.instance()

        if app is not None:
            icon = app.windowIcon()

            if not icon.isNull():
                icon_label.setPixmap(
                    icon.pixmap(
                        82,
                        82,
                    )
                )

        layout.addWidget(
            icon_label,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )

        layout.addSpacing(
            4
        )

        # -------------------------------------------------
        # Copy
        # -------------------------------------------------

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "placeholderTitle"
        )

        title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title_label.setWordWrap(
            True
        )

        layout.addWidget(
            title_label
        )

        message_label = QLabel(
            message
        )

        message_label.setObjectName(
            "informationText"
        )

        message_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        message_label.setWordWrap(
            True
        )

        message_label.setMaximumWidth(
            500
        )

        layout.addWidget(
            message_label,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )

        # -------------------------------------------------
        # Optional safe action
        # -------------------------------------------------

        if (
            action_text
            and action is not None
        ):
            layout.addSpacing(
                8
            )

            button = QPushButton(
                action_text
            )

            button.setObjectName(
                "primaryButton"
            )

            button.setMinimumHeight(
                40
            )

            button.setMinimumWidth(
                140
            )

            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            button.clicked.connect(
                lambda checked=False:
                action()
            )

            layout.addWidget(
                button,
                0,
                Qt.AlignmentFlag.AlignHCenter,
            )