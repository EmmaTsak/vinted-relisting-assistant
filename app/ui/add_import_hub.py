from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class AddImportHub(QWidget):
    """
    Friendly entry point for building the local inventory.

    The hub does not perform any imports itself.
    It only routes the user to the application's existing
    manual, Vinted Export and CSV / JSON workflows.
    """

    def __init__(
        self,
        add_manual: Callable[[], None],
        import_vinted: Callable[[], None],
        import_generic: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.add_manual = add_manual
        self.import_vinted = import_vinted
        self.import_generic = import_generic

        self.status_label = QLabel(
            ""
        )

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.setSpacing(
            0
        )

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()

        layout = QVBoxLayout(
            content
        )

        layout.setContentsMargins(
            0,
            0,
            8,
            10,
        )

        layout.setSpacing(
            14
        )

        # =================================================
        # Introduction
        # =================================================

        intro = QFrame()

        intro.setObjectName(
            "informationBox"
        )

        intro_layout = QVBoxLayout(
            intro
        )

        intro_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        intro_layout.setSpacing(
            5
        )

        eyebrow = QLabel(
            "BUILD YOUR INVENTORY"
        )

        eyebrow.setObjectName(
            "sectionHeading"
        )

        heading = QLabel(
            "How would you like to add your listings?"
        )

        heading.setObjectName(
            "placeholderTitle"
        )

        heading.setWordWrap(
            True
        )

        explanation = QLabel(
            (
                "Choose the option that matches what you already have. "
                "You can mix these methods whenever you need to."
            )
        )

        explanation.setObjectName(
            "informationText"
        )

        explanation.setWordWrap(
            True
        )

        intro_layout.addWidget(
            eyebrow
        )

        intro_layout.addWidget(
            heading
        )

        intro_layout.addWidget(
            explanation
        )

        layout.addWidget(
            intro
        )

        # =================================================
        # Vinted Export
        # =================================================

        vinted_card = self._create_option_card(
            step="RECOMMENDED",
            title="Import your Vinted Export",
            description=(
                "Already have listings on Vinted? Import your official "
                "Vinted data export and let the assistant add listings "
                "that are not already in your local inventory."
            ),
            detail=(
                "Existing imported Vinted items are detected by their "
                "item ID and are not overwritten."
            ),
            button_text="IMPORT VINTED EXPORT",
            action=self.import_vinted,
            primary=True,
        )

        layout.addWidget(
            vinted_card
        )

        # =================================================
        # Manual listing
        # =================================================

        manual_card = self._create_option_card(
            step="MANUAL",
            title="Add one listing yourself",
            description=(
                "Create a single listing and enter exactly the details "
                "you want to keep in your local workspace."
            ),
            detail=(
                "Best for new items, one-off additions, or listings "
                "you want to prepare individually."
            ),
            button_text="ADD NEW LISTING",
            action=self.add_manual,
            primary=False,
        )

        layout.addWidget(
            manual_card
        )

        # =================================================
        # Generic import
        # =================================================

        generic_card = self._create_option_card(
            step="ADVANCED",
            title="Import CSV or JSON",
            description=(
                "Bring in listing data from another spreadsheet, script, "
                "backup, or compatible structured file."
            ),
            detail=(
                "This is the generic importer. Re-importing the same "
                "generic file may create duplicates, so use it carefully."
            ),
            button_text="IMPORT CSV / JSON",
            action=self.import_generic,
            primary=False,
        )

        layout.addWidget(
            generic_card
        )

        # =================================================
        # Status
        # =================================================

        self.status_label.setObjectName(
            "successText"
        )

        self.status_label.setWordWrap(
            True
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
        )

        layout.addWidget(
            self.status_label
        )

        layout.addStretch()

        scroll.setWidget(
            content
        )

        root_layout.addWidget(
            scroll
        )

    def _create_option_card(
        self,
        step: str,
        title: str,
        description: str,
        detail: str,
        button_text: str,
        action: Callable[[], None],
        primary: bool,
    ) -> QFrame:
        card = QFrame()

        card.setObjectName(
            "settingsFrame"
        )

        card_layout = QHBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        card_layout.setSpacing(
            22
        )

        # -------------------------------------------------
        # Text
        # -------------------------------------------------

        information = QVBoxLayout()

        information.setSpacing(
            5
        )

        badge = QLabel(
            step
        )

        if primary:
            badge.setObjectName(
                "activeBadge"
            )

        else:
            badge.setObjectName(
                "priorityBadge"
            )

        badge.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        badge.setMaximumWidth(
            110
        )

        heading = QLabel(
            title
        )

        heading.setObjectName(
            "placeholderTitle"
        )

        heading.setWordWrap(
            True
        )

        description_label = QLabel(
            description
        )

        description_label.setObjectName(
            "informationText"
        )

        description_label.setWordWrap(
            True
        )

        detail_label = QLabel(
            detail
        )

        detail_label.setObjectName(
            "settingsNoteText"
        )

        detail_label.setWordWrap(
            True
        )

        information.addWidget(
            badge,
            0,
            Qt.AlignmentFlag.AlignLeft,
        )

        information.addWidget(
            heading
        )

        information.addWidget(
            description_label
        )

        information.addWidget(
            detail_label
        )

        card_layout.addLayout(
            information,
            1,
        )

        # -------------------------------------------------
        # Action
        # -------------------------------------------------

        button = QPushButton(
            button_text
        )

        if primary:
            button.setObjectName(
                "primaryButton"
            )

        else:
            button.setObjectName(
                "secondaryButton"
            )

        button.setMinimumHeight(
            42
        )

        button.setMinimumWidth(
            190
        )

        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        button.clicked.connect(
            lambda checked=False:
            action()
        )

        card_layout.addWidget(
            button,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

        return card