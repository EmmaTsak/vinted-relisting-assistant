from __future__ import annotations

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class BrandedSuccessDialog(QDialog):
    """
    Warm branded confirmation for successful, harmless moments.

    This should not be used for:
    - destructive confirmations
    - warnings
    - errors
    - decisions requiring careful user attention
    """

    def __init__(
        self,
        title: str,
        message: str,
        detail: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.setWindowTitle(
            title
        )

        self.setModal(
            True
        )

        self.setMinimumWidth(
            430
        )

        self.setMaximumWidth(
            520
        )

        self._build_ui(
            title=title,
            message=message,
            detail=detail,
        )

    def _build_ui(
        self,
        title: str,
        message: str,
        detail: str,
    ) -> None:
        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            22,
            22,
            22,
            22,
        )

        root_layout.setSpacing(
            0
        )

        card = QFrame()

        card.setObjectName(
            "informationBox"
        )

        card_layout = QVBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            30,
            26,
            30,
            26,
        )

        card_layout.setSpacing(
            10
        )

        card_layout.setAlignment(
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
            86,
            86,
        )

        app = QApplication.instance()

        if app is not None:
            icon = app.windowIcon()

            if not icon.isNull():
                icon_label.setPixmap(
                    icon.pixmap(
                        78,
                        78,
                    )
                )

        card_layout.addWidget(
            icon_label,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )

        # -------------------------------------------------
        # Success copy
        # -------------------------------------------------

        eyebrow = QLabel(
            "DONE"
        )

        eyebrow.setObjectName(
            "sectionHeading"
        )

        eyebrow.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        card_layout.addWidget(
            eyebrow
        )

        heading = QLabel(
            title
        )

        heading.setObjectName(
            "preparationHeading"
        )

        heading.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        heading.setWordWrap(
            True
        )

        card_layout.addWidget(
            heading
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
            390
        )

        card_layout.addWidget(
            message_label,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )

        if detail:
            card_layout.addSpacing(
                4
            )

            detail_frame = QFrame()

            detail_frame.setObjectName(
                "settingsNote"
            )

            detail_layout = QVBoxLayout(
                detail_frame
            )

            detail_layout.setContentsMargins(
                14,
                10,
                14,
                10,
            )

            detail_label = QLabel(
                detail
            )

            detail_label.setObjectName(
                "settingsNoteText"
            )

            detail_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            detail_label.setWordWrap(
                True
            )

            detail_layout.addWidget(
                detail_label
            )

            card_layout.addWidget(
                detail_frame
            )

        card_layout.addSpacing(
            8
        )

        done_button = QPushButton(
            "DONE"
        )

        done_button.setObjectName(
            "primaryButton"
        )

        done_button.setMinimumHeight(
            42
        )

        done_button.setMinimumWidth(
            120
        )

        done_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        done_button.clicked.connect(
            self.accept
        )

        card_layout.addWidget(
            done_button,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )

        root_layout.addWidget(
            card
        )