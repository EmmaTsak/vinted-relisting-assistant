from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models import Listing
from app.services.lifecycle_service import (
    get_archived_listings,
    get_sold_listings,
)
from app.ui.listing_card import ListingCard


class StatusListingsPage(QWidget):
    """
    Reusable listing page for Sold and Archived sections.
    """

    edit_requested = Signal(int)
    manage_requested = Signal(int)

    def __init__(
        self,
        empty_message: str,
        loader: Callable[[], list[Listing]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.empty_message = empty_message
        self.loader = loader

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            14
        )

        top_row = QHBoxLayout()

        self.count_label = QLabel(
            "0 listings"
        )

        self.count_label.setObjectName(
            "statusCount"
        )

        top_row.addWidget(
            self.count_label
        )

        top_row.addStretch()

        refresh_button = QPushButton(
            "REFRESH"
        )

        refresh_button.setObjectName(
            "statusRefreshButton"
        )

        refresh_button.clicked.connect(
            self.refresh
        )

        top_row.addWidget(
            refresh_button
        )

        layout.addLayout(
            top_row
        )

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.container = QWidget()

        self.cards_layout = QVBoxLayout(
            self.container
        )

        self.cards_layout.setContentsMargins(
            0,
            0,
            6,
            0,
        )

        self.cards_layout.setSpacing(
            12
        )

        self.cards_layout.addStretch()

        self.scroll_area.setWidget(
            self.container
        )

        layout.addWidget(
            self.scroll_area,
            1,
        )

        self.setStyleSheet(
            """
            #statusCount {
                color: #6b7280;
                font-weight: 600;
            }

            #statusRefreshButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }

            #statusRefreshButton:hover {
                background-color: #f3f4f6;
            }

            #statusEmpty {
                background-color: white;
                color: #6b7280;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 40px;
                font-size: 15px;
            }
            """
        )

        self.refresh()

    def refresh(self) -> None:
        self._clear_cards()

        try:
            listings = self.loader()

        except Exception as exc:
            self.count_label.setText(
                "Unable to load listings"
            )

            self._show_message(
                f"Unable to load listings:\n\n{exc}"
            )

            return

        count = len(
            listings
        )

        self.count_label.setText(
            (
                "1 listing"
                if count == 1
                else f"{count} listings"
            )
        )

        if not listings:
            self._show_message(
                self.empty_message
            )

            return

        for index, listing in enumerate(
            listings
        ):
            card = ListingCard(
                listing
            )

            card.edit_requested.connect(
                self.edit_requested.emit
            )

            card.manage_requested.connect(
                self.manage_requested.emit
            )

            self.cards_layout.insertWidget(
                index,
                card,
            )

    def _show_message(
        self,
        text: str,
    ) -> None:
        label = QLabel(
            text
        )

        label.setObjectName(
            "statusEmpty"
        )

        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        label.setWordWrap(
            True
        )

        self.cards_layout.insertWidget(
            0,
            label,
        )

    def _clear_cards(self) -> None:
        while (
            self.cards_layout.count()
            > 1
        ):
            item = self.cards_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()


class SoldListingsPage(StatusListingsPage):
    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            empty_message=(
                "No sold listings yet.\n\n"
                "Listings marked as sold will appear here "
                "while keeping their information and photos."
            ),
            loader=get_sold_listings,
            parent=parent,
        )


class ArchivedListingsPage(StatusListingsPage):
    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            empty_message=(
                "No archived listings.\n\n"
                "Archive acts as a safety step before "
                "permanent deletion."
            ),
            loader=get_archived_listings,
            parent=parent,
        )