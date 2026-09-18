from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models import (
    Listing,
)
from app.services.lifecycle_service import (
    get_archived_listings,
    get_sold_listings,
)
from app.services.listing_service import (
    get_listing_photos_for_listings,
)
from app.ui.listing_card import (
    ListingCard,
)


class StatusListingsPage(QWidget):
    """
    Reusable inventory page for Sold and Archived listings.

    Listings are loaded once during refresh and search is
    performed locally for fast filtering.
    """

    edit_requested = Signal(int)
    manage_requested = Signal(int)

    def __init__(
        self,
        section_name: str,
        description: str,
        empty_message: str,
        search_placeholder: str,
        loader: Callable[[], list[Listing]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.section_name = section_name

        self.description = description

        self.empty_message = empty_message

        self.search_placeholder = (
            search_placeholder
        )

        self.loader = loader

        self._all_listings: list[
            Listing
        ] = []

        self._photos_by_listing = None

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
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

        # -------------------------------------------------
        # Summary
        # -------------------------------------------------

        summary = QFrame()

        summary.setObjectName(
            "informationBox"
        )

        summary_layout = QHBoxLayout(
            summary
        )

        summary_layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        summary_layout.setSpacing(
            16
        )

        summary_text_layout = (
            QVBoxLayout()
        )

        summary_text_layout.setSpacing(
            4
        )

        self.count_label = QLabel(
            (
                f"0 {self.section_name.upper()} "
                "LISTINGS"
            )
        )

        self.count_label.setObjectName(
            "sectionHeading"
        )

        description_label = QLabel(
            self.description
        )

        description_label.setObjectName(
            "informationText"
        )

        description_label.setWordWrap(
            True
        )

        summary_text_layout.addWidget(
            self.count_label
        )

        summary_text_layout.addWidget(
            description_label
        )

        summary_layout.addLayout(
            summary_text_layout,
            1,
        )

        layout.addWidget(
            summary
        )

        # -------------------------------------------------
        # Search
        # -------------------------------------------------

        search_frame = QFrame()

        search_frame.setObjectName(
            "searchFrame"
        )

        search_layout = QHBoxLayout(
            search_frame
        )

        search_layout.setContentsMargins(
            14,
            10,
            14,
            10,
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            self.search_placeholder
        )

        self.search_input.setClearButtonEnabled(
            True
        )

        self.search_input.setMinimumHeight(
            42
        )

        self.search_input.textChanged.connect(
            self._apply_search
        )

        search_layout.addWidget(
            self.search_input
        )

        layout.addWidget(
            search_frame
        )

        # -------------------------------------------------
        # Results information
        # -------------------------------------------------

        information_row = QHBoxLayout()

        self.results_label = QLabel(
            ""
        )

        self.results_label.setObjectName(
            "informationText"
        )

        information_row.addWidget(
            self.results_label
        )

        information_row.addStretch()

        layout.addLayout(
            information_row
        )

        # -------------------------------------------------
        # Listings
        # -------------------------------------------------

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
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
            10
        )

        self.cards_layout.addStretch()

        self.scroll_area.setWidget(
            self.container
        )

        layout.addWidget(
            self.scroll_area,
            1,
        )

        self.refresh()

    # =====================================================
    # Data
    # =====================================================

    def refresh(
        self,
    ) -> None:
        """
        Reload the underlying Sold/Archived inventory.

        Photo metadata is loaded in one batch so ListingCard
        does not need one photo query per visible listing.
        """
        try:
            listings = list(
                self.loader()
            )

        except Exception as exc:
            self._all_listings = []

            self._photos_by_listing = {}

            self.count_label.setText(
                "UNABLE TO LOAD LISTINGS"
            )

            self.results_label.setText(
                ""
            )

            self._clear_cards()

            self._show_message(
                (
                    "Unable to load listings.\n\n"
                    f"{exc}"
                )
            )

            return

        self._all_listings = listings

        count = len(
            listings
        )

        self.count_label.setText(
            self._count_text(
                count
            )
        )

        listing_ids = [
            listing.id
            for listing in listings
        ]

        if listing_ids:
            try:
                self._photos_by_listing = (
                    get_listing_photos_for_listings(
                        listing_ids
                    )
                )

            except Exception:
                # Cards can still fall back to their normal
                # per-listing photo lookup if batching fails.
                self._photos_by_listing = None

        else:
            self._photos_by_listing = {}

        self._apply_search()

    def _apply_search(
        self,
    ) -> None:
        query = (
            self.search_input
            .text()
            .strip()
            .casefold()
        )

        if not query:
            filtered = list(
                self._all_listings
            )

        else:
            filtered = [
                listing
                for listing in self._all_listings
                if self._matches_search(
                    listing,
                    query,
                )
            ]

        self._render_listings(
            filtered
        )

        total = len(
            self._all_listings
        )

        visible = len(
            filtered
        )

        if not query:
            if total == 1:
                self.results_label.setText(
                    "1 item"
                )
            else:
                self.results_label.setText(
                    f"{total} items"
                )

        else:
            self.results_label.setText(
                (
                    f"Showing {visible} of "
                    f"{total} listings"
                )
            )

    def _matches_search(
        self,
        listing: Listing,
        query: str,
    ) -> bool:
        values = (
            listing.title,
            listing.description,
            listing.brand,
            listing.category,
            listing.subcategory,
            listing.size,
            listing.condition,
            listing.colour,
            listing.material,
            listing.isbn,
        )

        return any(
            query
            in str(value).casefold()
            for value in values
            if value
        )

    # =====================================================
    # Rendering
    # =====================================================

    def _render_listings(
        self,
        listings: list[Listing],
    ) -> None:
        self.container.setUpdatesEnabled(
            False
        )

        try:
            self._clear_cards()

            if not listings:
                if (
                    self.search_input
                    .text()
                    .strip()
                ):
                    self._show_message(
                        (
                            "No listings match your "
                            "current search."
                        )
                    )

                else:
                    self._show_message(
                        self.empty_message
                    )

                return

            for index, listing in enumerate(
                listings
            ):
                if (
                    self._photos_by_listing
                    is None
                ):
                    photos = None

                else:
                    photos = (
                        self._photos_by_listing.get(
                            listing.id,
                            [],
                        )
                    )

                card = ListingCard(
                    listing=listing,
                    photos=photos,
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

        finally:
            self.container.setUpdatesEnabled(
                True
            )

            self.container.update()

    def _show_message(
        self,
        text: str,
    ) -> None:
        frame = QFrame()

        frame.setObjectName(
            "informationBox"
        )

        frame_layout = QVBoxLayout(
            frame
        )

        frame_layout.setContentsMargins(
            24,
            34,
            24,
            34,
        )

        label = QLabel(
            text
        )

        label.setObjectName(
            "informationText"
        )

        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        label.setWordWrap(
            True
        )

        frame_layout.addWidget(
            label
        )

        self.cards_layout.insertWidget(
            0,
            frame,
        )

    def _clear_cards(
        self,
    ) -> None:
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

    def _count_text(
        self,
        count: int,
    ) -> str:
        noun = (
            "LISTING"
            if count == 1
            else "LISTINGS"
        )

        return (
            f"{count} "
            f"{self.section_name.upper()} "
            f"{noun}"
        )


class SoldListingsPage(
    StatusListingsPage
):
    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            section_name="Sold",
            description=(
                "Items marked as sold remain stored locally "
                "with their listing information and photos."
            ),
            empty_message=(
                "No sold listings yet.\n\n"
                "When you mark an item as sold, "
                "it will appear here."
            ),
            search_placeholder=(
                "Search sold listings by title, ISBN, "
                "brand, category..."
            ),
            loader=get_sold_listings,
            parent=parent,
        )


class ArchivedListingsPage(
    StatusListingsPage
):
    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            section_name="Archived",
            description=(
                "Archived listings remain stored locally "
                "and stay outside the relisting rotation."
            ),
            empty_message=(
                "No archived listings.\n\n"
                "Archived items are kept safely until you "
                "restore them or permanently delete them."
            ),
            search_placeholder=(
                "Search archived listings by title, ISBN, "
                "brand, category..."
            ),
            loader=get_archived_listings,
            parent=parent,
        )