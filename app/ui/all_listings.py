from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models import (
    ListingPriority,
    ListingStatus,
)
from app.services.listing_browser_service import (
    AGE_30_PLUS,
    AGE_60_PLUS,
    AGE_90_PLUS,
    AGE_ALL,
    AGE_NEVER_RELISTED,
    SORT_LAST_RELISTED,
    SORT_LEAST_RELISTED,
    SORT_MOST_RELISTED,
    SORT_NEWEST,
    SORT_OLDEST,
    SORT_PRICE_HIGH_LOW,
    SORT_PRICE_LOW_HIGH,
    ListingBrowserFilters,
    get_listing_browser_result,
)
from app.ui.listing_card import ListingCard


class AllListingsPage(QWidget):
    """
    Searchable and filterable browser for locally stored listings.
    """

    edit_requested = Signal(int)
    manage_requested = Signal(int)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._updating_filter_options = False

        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(14)

        main_layout.addWidget(
            self._create_search_bar()
        )

        main_layout.addWidget(
            self._create_filter_panel()
        )

        count_row = QHBoxLayout()

        self.count_label = QLabel(
            "0 listings"
        )

        self.count_label.setObjectName(
            "listingCount"
        )

        count_row.addWidget(
            self.count_label
        )

        count_row.addStretch()

        refresh_button = QPushButton(
            "REFRESH"
        )

        refresh_button.setObjectName(
            "refreshButton"
        )

        refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        refresh_button.clicked.connect(
            self.refresh
        )

        count_row.addWidget(
            refresh_button
        )

        main_layout.addLayout(
            count_row
        )

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

        self.container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        self.cards_layout = QVBoxLayout(
            self.container
        )

        self.cards_layout.setContentsMargins(
            0,
            0,
            6,
            0,
        )

        self.cards_layout.setSpacing(12)

        self.cards_layout.addStretch()

        self.scroll_area.setWidget(
            self.container
        )

        main_layout.addWidget(
            self.scroll_area,
            1,
        )

        self._apply_styles()

        self.refresh()

    def _create_search_bar(
        self,
    ) -> QWidget:
        frame = QFrame()

        frame.setObjectName(
            "searchFrame"
        )

        layout = QHBoxLayout(
            frame
        )

        layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        search_label = QLabel(
            "Search"
        )

        search_label.setObjectName(
            "filterLabel"
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search title or description..."
        )

        self.search_input.setClearButtonEnabled(
            True
        )

        self.search_input.textChanged.connect(
            self.refresh
        )

        layout.addWidget(
            search_label
        )

        layout.addWidget(
            self.search_input,
            1,
        )

        return frame

    def _create_filter_panel(
        self,
    ) -> QWidget:
        frame = QFrame()

        frame.setObjectName(
            "filterFrame"
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        layout.setSpacing(12)

        heading_row = QHBoxLayout()

        heading = QLabel(
            "FILTERS & SORTING"
        )

        heading.setObjectName(
            "filterHeading"
        )

        reset_button = QPushButton(
            "RESET FILTERS"
        )

        reset_button.setObjectName(
            "resetButton"
        )

        reset_button.clicked.connect(
            self._reset_filters
        )

        heading_row.addWidget(
            heading
        )

        heading_row.addStretch()

        heading_row.addWidget(
            reset_button
        )

        layout.addLayout(
            heading_row
        )

        grid = QGridLayout()

        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        self.status_filter = QComboBox()

        self.status_filter.addItem(
            "All Statuses",
            None,
        )

        self.status_filter.addItem(
            "Active",
            ListingStatus.ACTIVE,
        )

        self.status_filter.addItem(
            "Paused",
            ListingStatus.PAUSED,
        )

        self.status_filter.addItem(
            "Sold",
            ListingStatus.SOLD,
        )

        self.status_filter.addItem(
            "Archived",
            ListingStatus.ARCHIVED,
        )

        self.status_filter.currentIndexChanged.connect(
            self.refresh
        )

        self.age_filter = QComboBox()

        self.age_filter.addItem(
            "Any Age",
            AGE_ALL,
        )

        self.age_filter.addItem(
            "Never Relisted",
            AGE_NEVER_RELISTED,
        )

        self.age_filter.addItem(
            "30+ Days",
            AGE_30_PLUS,
        )

        self.age_filter.addItem(
            "60+ Days",
            AGE_60_PLUS,
        )

        self.age_filter.addItem(
            "90+ Days",
            AGE_90_PLUS,
        )

        self.age_filter.currentIndexChanged.connect(
            self.refresh
        )

        self.priority_filter = QComboBox()

        self.priority_filter.addItem(
            "All Priorities",
            None,
        )

        self.priority_filter.addItem(
            "High",
            ListingPriority.HIGH,
        )

        self.priority_filter.addItem(
            "Normal",
            ListingPriority.NORMAL,
        )

        self.priority_filter.addItem(
            "Low",
            ListingPriority.LOW,
        )

        self.priority_filter.currentIndexChanged.connect(
            self.refresh
        )

        self.category_filter = QComboBox()

        self.category_filter.setEditable(
            True
        )

        self.category_filter.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert
        )

        self.category_filter.setPlaceholderText(
            "All Categories"
        )

        self.category_filter.currentTextChanged.connect(
            self.refresh
        )

        self.brand_filter = QComboBox()

        self.brand_filter.setEditable(
            True
        )

        self.brand_filter.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert
        )

        self.brand_filter.setPlaceholderText(
            "All Brands"
        )

        self.brand_filter.currentTextChanged.connect(
            self.refresh
        )

        self.minimum_price_filter = QDoubleSpinBox()

        self.minimum_price_filter.setDecimals(
            2
        )

        self.minimum_price_filter.setRange(
            0,
            9_999_999.99,
        )

        self.minimum_price_filter.setPrefix(
            "€ "
        )

        self.minimum_price_filter.setSpecialValueText(
            "Any"
        )

        self.minimum_price_filter.valueChanged.connect(
            self.refresh
        )

        self.maximum_price_filter = QDoubleSpinBox()

        self.maximum_price_filter.setDecimals(
            2
        )

        self.maximum_price_filter.setRange(
            0,
            9_999_999.99,
        )

        self.maximum_price_filter.setPrefix(
            "€ "
        )

        self.maximum_price_filter.setSpecialValueText(
            "Any"
        )

        self.maximum_price_filter.valueChanged.connect(
            self.refresh
        )

        self.sort_filter = QComboBox()

        self.sort_filter.addItem(
            "Newest",
            SORT_NEWEST,
        )

        self.sort_filter.addItem(
            "Oldest",
            SORT_OLDEST,
        )

        self.sort_filter.addItem(
            "Last Relisted",
            SORT_LAST_RELISTED,
        )

        self.sort_filter.addItem(
            "Price: Low → High",
            SORT_PRICE_LOW_HIGH,
        )

        self.sort_filter.addItem(
            "Price: High → Low",
            SORT_PRICE_HIGH_LOW,
        )

        self.sort_filter.addItem(
            "Most Relisted",
            SORT_MOST_RELISTED,
        )

        self.sort_filter.addItem(
            "Least Relisted",
            SORT_LEAST_RELISTED,
        )

        self.sort_filter.currentIndexChanged.connect(
            self.refresh
        )

        self._add_filter_control(
            grid,
            0,
            0,
            "Status",
            self.status_filter,
        )

        self._add_filter_control(
            grid,
            0,
            1,
            "Relist Age",
            self.age_filter,
        )

        self._add_filter_control(
            grid,
            0,
            2,
            "Priority",
            self.priority_filter,
        )

        self._add_filter_control(
            grid,
            0,
            3,
            "Sort",
            self.sort_filter,
        )

        self._add_filter_control(
            grid,
            1,
            0,
            "Category",
            self.category_filter,
        )

        self._add_filter_control(
            grid,
            1,
            1,
            "Brand",
            self.brand_filter,
        )

        self._add_filter_control(
            grid,
            1,
            2,
            "Minimum Price",
            self.minimum_price_filter,
        )

        self._add_filter_control(
            grid,
            1,
            3,
            "Maximum Price",
            self.maximum_price_filter,
        )

        for column in range(4):
            grid.setColumnStretch(
                column,
                1,
            )

        layout.addLayout(
            grid
        )

        return frame

    def _add_filter_control(
        self,
        layout: QGridLayout,
        row: int,
        column: int,
        title: str,
        widget: QWidget,
    ) -> None:
        container = QWidget()

        container_layout = QVBoxLayout(
            container
        )

        container_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        container_layout.setSpacing(4)

        label = QLabel(
            title
        )

        label.setObjectName(
            "filterLabel"
        )

        container_layout.addWidget(
            label
        )

        container_layout.addWidget(
            widget
        )

        layout.addWidget(
            container,
            row,
            column,
        )

    def refresh(self) -> None:
        """
        Reload listings and apply all current search/filter options.
        """
        if self._updating_filter_options:
            return

        self._clear_cards()

        try:
            filters = self._build_filters()

            result = get_listing_browser_result(
                filters
            )

        except Exception as exc:
            self.count_label.setText(
                "Unable to load listings"
            )

            self._show_message(
                (
                    "There was an error loading "
                    f"the listing database:\n\n{exc}"
                ),
                object_name="errorState",
            )

            return

        self._update_dynamic_filters(
            result.categories,
            result.brands,
        )

        if (
            result.filtered_count
            == result.total_count
        ):
            if result.total_count == 1:
                count_text = "1 listing"

            else:
                count_text = (
                    f"{result.total_count} listings"
                )

        else:
            count_text = (
                f"{result.filtered_count} of "
                f"{result.total_count} listings"
            )

        self.count_label.setText(
            count_text
        )

        if not result.listings:
            if result.total_count == 0:
                message = (
                    "No listings have been stored yet.\n\n"
                    "Use Add Listing or Import CSV / JSON "
                    "to add your existing inventory."
                )

            else:
                message = (
                    "No listings match the current "
                    "search and filters.\n\n"
                    "Change a filter or press RESET FILTERS."
                )

            self._show_message(
                message,
                object_name="emptyState",
            )

            return

        for index, listing in enumerate(
            result.listings
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

    def _build_filters(
        self,
    ) -> ListingBrowserFilters:
        minimum_value = (
            self.minimum_price_filter.value()
        )

        maximum_value = (
            self.maximum_price_filter.value()
        )

        minimum_price = (
            Decimal(
                f"{minimum_value:.2f}"
            )
            if minimum_value > 0
            else None
        )

        maximum_price = (
            Decimal(
                f"{maximum_value:.2f}"
            )
            if maximum_value > 0
            else None
        )

        category = (
            self.category_filter
            .currentText()
            .strip()
        )

        brand = (
            self.brand_filter
            .currentText()
            .strip()
        )

        return ListingBrowserFilters(
            search_text=(
                self.search_input.text()
            ),
            status=(
                self.status_filter.currentData()
            ),
            age_filter=(
                self.age_filter.currentData()
            ),
            priority=(
                self.priority_filter.currentData()
            ),
            category=(
                category
                if category
                else None
            ),
            brand=(
                brand
                if brand
                else None
            ),
            minimum_price=(
                minimum_price
            ),
            maximum_price=(
                maximum_price
            ),
            sort_by=(
                self.sort_filter.currentData()
            ),
        )

    def _update_dynamic_filters(
        self,
        categories: list[str],
        brands: list[str],
    ) -> None:
        """
        Refresh category and brand suggestions without
        losing the user's current typed value.
        """
        current_category = (
            self.category_filter.currentText()
        )

        current_brand = (
            self.brand_filter.currentText()
        )

        self._updating_filter_options = True

        try:
            self.category_filter.blockSignals(
                True
            )

            self.brand_filter.blockSignals(
                True
            )

            self.category_filter.clear()

            self.category_filter.addItem(
                ""
            )

            self.category_filter.addItems(
                categories
            )

            self.category_filter.setCurrentText(
                current_category
            )

            self.brand_filter.clear()

            self.brand_filter.addItem(
                ""
            )

            self.brand_filter.addItems(
                brands
            )

            self.brand_filter.setCurrentText(
                current_brand
            )

        finally:
            self.category_filter.blockSignals(
                False
            )

            self.brand_filter.blockSignals(
                False
            )

            self._updating_filter_options = False

    def _reset_filters(self) -> None:
        """
        Reset every search/filter/sort option.
        """
        self._updating_filter_options = True

        try:
            self.search_input.clear()

            self.status_filter.setCurrentIndex(
                0
            )

            self.age_filter.setCurrentIndex(
                0
            )

            self.priority_filter.setCurrentIndex(
                0
            )

            self.category_filter.setCurrentText(
                ""
            )

            self.brand_filter.setCurrentText(
                ""
            )

            self.minimum_price_filter.setValue(
                0
            )

            self.maximum_price_filter.setValue(
                0
            )

            self.sort_filter.setCurrentIndex(
                0
            )

        finally:
            self._updating_filter_options = False

        self.refresh()

    def _show_message(
        self,
        text: str,
        object_name: str,
    ) -> None:
        label = QLabel(
            text
        )

        label.setObjectName(
            object_name
        )

        label.setWordWrap(
            True
        )

        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
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

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #searchFrame,
            #filterFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 9px;
            }

            #filterHeading {
                color: #111827;
                font-size: 13px;
                font-weight: 700;
            }

            #filterLabel {
                color: #6b7280;
                font-size: 12px;
                font-weight: 600;
            }

            QLineEdit,
            QComboBox,
            QDoubleSpinBox {
                background-color: white;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 7px;
                min-height: 22px;
            }

            QComboBox QAbstractItemView {
                background-color: white;
                color: #111827;
                selection-background-color: #e5e7eb;
                selection-color: #111827;
            }

            #listingCount {
                color: #6b7280;
                font-size: 14px;
                font-weight: 600;
            }

            #refreshButton,
            #resetButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }

            #refreshButton:hover,
            #resetButton:hover {
                background-color: #f3f4f6;
            }

            #emptyState {
                background-color: white;
                color: #6b7280;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 35px;
                font-size: 15px;
            }

            #errorState {
                background-color: #fef2f2;
                color: #991b1b;
                border: 1px solid #fecaca;
                border-radius: 10px;
                padding: 35px;
                font-size: 14px;
            }
            """
        )