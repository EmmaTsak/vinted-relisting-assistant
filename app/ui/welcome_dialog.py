from __future__ import annotations

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtGui import (
    QIcon,
)
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class WelcomeDialog(QDialog):
    """
    One-time welcome experience.

    This is intentionally short:
    - explain the workflow
    - explain local/private behavior
    - clarify that publishing stays manual
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        app_icon: QIcon | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.app_icon = app_icon

        self.setWindowTitle(
            "Welcome"
        )

        self.setModal(
            True
        )

        self.resize(
            650,
            610,
        )

        self.setMinimumSize(
            590,
            560,
        )

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            26,
            26,
            26,
            26,
        )

        root_layout.setSpacing(
            16
        )

        # =================================================
        # Brand
        # =================================================

        brand_layout = QHBoxLayout()

        brand_layout.setSpacing(
            18
        )

        icon_label = QLabel()

        icon_label.setFixedSize(
            92,
            92,
        )

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        if (
            self.app_icon is not None
            and not self.app_icon.isNull()
        ):
            icon_label.setPixmap(
                self.app_icon.pixmap(
                    86,
                    86,
                )
            )

        brand_layout.addWidget(
            icon_label,
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        heading_layout = QVBoxLayout()

        heading_layout.setSpacing(
            5
        )

        eyebrow = QLabel(
            "WELCOME"
        )

        eyebrow.setObjectName(
            "sectionHeading"
        )

        title = QLabel(
            "Your relisting routine just got easier"
        )

        title.setObjectName(
            "preparationHeading"
        )

        title.setWordWrap(
            True
        )

        subtitle = QLabel(
            (
                "Keep your listings organised, prepare old items "
                "for relisting, and track what you've already done "
                "— all from one local desktop workspace."
            )
        )

        subtitle.setObjectName(
            "informationText"
        )

        subtitle.setWordWrap(
            True
        )

        heading_layout.addWidget(
            eyebrow
        )

        heading_layout.addWidget(
            title
        )

        heading_layout.addWidget(
            subtitle
        )

        brand_layout.addLayout(
            heading_layout,
            1,
        )

        root_layout.addLayout(
            brand_layout
        )

        # =================================================
        # Workflow
        # =================================================

        workflow = QFrame()

        workflow.setObjectName(
            "informationBox"
        )

        workflow_layout = QVBoxLayout(
            workflow
        )

        workflow_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        workflow_layout.setSpacing(
            14
        )

        workflow_heading = QLabel(
            "HOW IT WORKS"
        )

        workflow_heading.setObjectName(
            "sectionHeading"
        )

        workflow_layout.addWidget(
            workflow_heading
        )

        self._add_step(
            layout=workflow_layout,
            number="1",
            title="ADD OR IMPORT YOUR LISTINGS",
            message=(
                "Build your local inventory manually, from CSV / JSON, "
                "or with your Vinted data export."
            ),
        )

        self._add_step(
            layout=workflow_layout,
            number="2",
            title="CHECK TODAY'S QUEUE",
            message=(
                "The app chooses eligible older listings based on "
                "your daily target and minimum relisting age."
            ),
        )

        self._add_step(
            layout=workflow_layout,
            number="3",
            title="PUBLISH MANUALLY & CONFIRM",
            message=(
                "Copy the details you need, publish on Vinted yourself, "
                "then confirm the relist here so your history stays accurate."
            ),
        )

        root_layout.addWidget(
            workflow
        )

        # =================================================
        # Local / private
        # =================================================

        privacy = QFrame()

        privacy.setObjectName(
            "settingsNote"
        )

        privacy_layout = QVBoxLayout(
            privacy
        )

        privacy_layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        privacy_layout.setSpacing(
            6
        )

        privacy_heading = QLabel(
            "LOCAL BY DESIGN"
        )

        privacy_heading.setObjectName(
            "sectionHeading"
        )

        privacy_text = QLabel(
            (
                "Your listings, photos, settings and relisting history "
                "stay on your computer. The app does not store your Vinted "
                "password, log into your account, or publish listings for you."
            )
        )

        privacy_text.setObjectName(
            "settingsNoteText"
        )

        privacy_text.setWordWrap(
            True
        )

        privacy_layout.addWidget(
            privacy_heading
        )

        privacy_layout.addWidget(
            privacy_text
        )

        root_layout.addWidget(
            privacy
        )

        # =================================================
        # Independence
        # =================================================

        independence = QLabel(
            (
                "Vinted Relisting Assistant is independent software "
                "and is not affiliated with, endorsed by, sponsored by, "
                "or operated by Vinted."
            )
        )

        independence.setObjectName(
            "informationText"
        )

        independence.setWordWrap(
            True
        )

        independence.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        root_layout.addWidget(
            independence
        )

        root_layout.addStretch()

        # =================================================
        # Start
        # =================================================

        start_button = QPushButton(
            "LET'S GET STARTED"
        )

        start_button.setObjectName(
            "primaryButton"
        )

        start_button.setMinimumHeight(
            46
        )

        start_button.setMinimumWidth(
            190
        )

        start_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        start_button.clicked.connect(
            self.accept
        )

        root_layout.addWidget(
            start_button,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )

    def _add_step(
        self,
        layout: QVBoxLayout,
        number: str,
        title: str,
        message: str,
    ) -> None:
        row = QHBoxLayout()

        row.setSpacing(
            12
        )

        number_label = QLabel(
            number
        )

        number_label.setObjectName(
            "activeBadge"
        )

        number_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        number_label.setFixedSize(
            30,
            30,
        )

        row.addWidget(
            number_label,
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            3
        )

        heading = QLabel(
            title
        )

        heading.setObjectName(
            "sectionHeading"
        )

        message_label = QLabel(
            message
        )

        message_label.setObjectName(
            "informationText"
        )

        message_label.setWordWrap(
            True
        )

        text_layout.addWidget(
            heading
        )

        text_layout.addWidget(
            message_label
        )

        row.addLayout(
            text_layout,
            1,
        )

        layout.addLayout(
            row
        )