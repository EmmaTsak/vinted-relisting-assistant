from __future__ import annotations

import math
from decimal import Decimal

from PySide6.QtCore import (
    QTimer,
    Qt,
    Signal,
)
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
    AGE_14_PLUS,
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
from app.services.listing_service import (
    get_listing_photos_for_listings,
)
from app.ui.listing_card import (
    ListingCard,
)


class AllListingsPage(QWidget):
    """
    Searchable, filterable and paginated listing browser.
    """

    edit_requested = Signal(int)
    manage_requested = Signal(int)

    FILTER_DELAY_MS = 250

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self._updating_filter_options = False

        self.current_page = 1

        self._refresh_timer = QTimer(
            self
        )

        self._refresh_timer.setSingleShot(
            True
        )

        self._refresh_timer.setInterval(
            self.FILTER_DELAY_MS
        )

        self._refresh_timer.timeout.connect(
            self.refresh
        )

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(
            12
        )

        main_layout.addWidget(
            self._create_search_bar()
        )

        self.filter_panel = (
            self._create_filter_panel()
        )

        # Filters remain closed when the page first opens.
        self.filter_panel.setVisible(
            False
        )

        main_layout.addWidget(
            self.filter_panel
        )

        information_row = (
            QHBoxLayout()
        )

        self.count_label = QLabel(
            "0 listings"
        )

        self.count_label.setObjectName(
            "listingCount"
        )

        information_row.addWidget(
            self.count_label
        )

        information_row.addStretch()

        show_label = QLabel(
            "Show"
        )

        show_label.setObjectName(
            "listingCount"
        )

        information_row.addWidget(
            show_label
        )

        self.page_size_input = (
            QComboBox()
        )

        for value in (
            25,
            50,
            100,
        ):
            self.page_size_input.addItem(
                str(value),
                value,
            )

        self.page_size_input.currentIndexChanged.connect(
            self._page_size_changed
        )

        information_row.addWidget(
            self.page_size_input
        )

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

        information_row.addWidget(
            refresh_button
        )

        main_layout.addLayout(
            information_row
        )

        self.scroll_area = (
            QScrollArea()
        )

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

        self.cards_layout = (
            QVBoxLayout(
                self.container
            )
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

        main_layout.addWidget(
            self.scroll_area,
            1,
        )

        main_layout.addWidget(
            self._create_pagination_bar()
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
            10,
            14,
            10,
        )

        self.search_input = (
            QLineEdit()
        )

        self.search_input.setPlaceholderText(
            (
                "Search title, ISBN, description, "
                "brand, category, size, colour..."
            )
        )

        self.search_input.setClearButtonEnabled(
            True
        )

        self.search_input.textChanged.connect(
            self._search_changed
        )

        self.filter_toggle_button = (
            QPushButton(
                "FILTERS ▾"
            )
        )

        self.filter_toggle_button.setObjectName(
            "filterToggleButton"
        )

        self.filter_toggle_button.setCheckable(
            True
        )

        self.filter_toggle_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.filter_toggle_button.toggled.connect(
            self._toggle_filters
        )

        layout.addWidget(
            self.search_input,
            1,
        )

        layout.addWidget(
            self.filter_toggle_button
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

        layout.setSpacing(
            12
        )

        heading_row = (
            QHBoxLayout()
        )

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

        grid.setHorizontalSpacing(
            16
        )

        grid.setVerticalSpacing(
            10
        )

        # Row 1 -------------------------------------------------

        self.status_filter = (
            QComboBox()
        )

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
            self._filter_changed
        )

        self.age_filter = (
            QComboBox()
        )

        self.age_filter.addItem(
            "Any Age",
            AGE_ALL,
        )

        self.age_filter.addItem(
            "Never Relisted",
            AGE_NEVER_RELISTED,
        )

        self.age_filter.addItem(
            "14+ Days",
            AGE_14_PLUS,
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
            self._filter_changed
        )

        self.priority_filter = (
            QComboBox()
        )

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
            self._filter_changed
        )

        self.sort_filter = (
            QComboBox()
        )

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
            self._filter_changed
        )

        # Row 2 -------------------------------------------------

        self.category_filter = (
            QComboBox()
        )

        self.category_filter.addItem(
            "All Categories",
            None,
        )

        self.category_filter.currentIndexChanged.connect(
            self._filter_changed
        )

        self.subcategory_filter = (
            QComboBox()
        )

        self.subcategory_filter.addItem(
            "All Subcategories",
            None,
        )

        self.subcategory_filter.currentIndexChanged.connect(
            self._filter_changed
        )

        self.brand_filter = (
            QComboBox()
        )

        self.brand_filter.addItem(
            "All Brands",
            None,
        )

        self.brand_filter.currentIndexChanged.connect(
            self._filter_changed
        )

        self.condition_filter = (
            QComboBox()
        )

        self.condition_filter.addItem(
            "All Conditions",
            None,
        )

        self.condition_filter.currentIndexChanged.connect(
            self._filter_changed
        )

        # Row 3 -------------------------------------------------

        self.size_filter = (
            QComboBox()
        )

        self.size_filter.addItem(
            "All Sizes",
            None,
        )

        self.size_filter.currentIndexChanged.connect(
            self._filter_changed
        )

        self.colour_filter = (
            QComboBox()
        )

        self.colour_filter.addItem(
            "All Colours",
            None,
        )

        self.colour_filter.currentIndexChanged.connect(
            self._filter_changed
        )

        self.minimum_price_filter = (
            QDoubleSpinBox()
        )

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
            self._price_filter_changed
        )

        self.maximum_price_filter = (
            QDoubleSpinBox()
        )

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
            self._price_filter_changed
        )

        # Layout ------------------------------------------------

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
            "Subcategory",
            self.subcategory_filter,
        )

        self._add_filter_control(
            grid,
            1,
            2,
            "Brand",
            self.brand_filter,
        )

        self._add_filter_control(
            grid,
            1,
            3,
            "Condition",
            self.condition_filter,
        )

        self._add_filter_control(
            grid,
            2,
            0,
            "Size",
            self.size_filter,
        )

        self._add_filter_control(
            grid,
            2,
            1,
            "Colour",
            self.colour_filter,
        )

        self._add_filter_control(
            grid,
            2,
            2,
            "Minimum Price",
            self.minimum_price_filter,
        )

        self._add_filter_control(
            grid,
            2,
            3,
            "Maximum Price",
            self.maximum_price_filter,
        )

        for column in range(
            4
        ):
            grid.setColumnStretch(
                column,
                1,
            )

        layout.addLayout(
            grid
        )

        return frame

    def _create_pagination_bar(
        self,
    ) -> QWidget:
        frame = QFrame()

        frame.setObjectName(
            "paginationFrame"
        )

        layout = QHBoxLayout(
            frame
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        self.previous_button = (
            QPushButton(
                "← PREVIOUS"
            )
        )

        self.previous_button.setObjectName(
            "paginationButton"
        )

        self.previous_button.clicked.connect(
            self._previous_page
        )

        self.page_label = QLabel(
            "Page 1 of 1"
        )

        self.page_label.setObjectName(
            "pageNumberLabel"
        )

        self.page_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.next_button = (
            QPushButton(
                "NEXT →"
            )
        )

        self.next_button.setObjectName(
            "paginationButton"
        )

        self.next_button.clicked.connect(
            self._next_page
        )

        layout.addWidget(
            self.previous_button
        )

        layout.addStretch()

        layout.addWidget(
            self.page_label
        )

        layout.addStretch()

        layout.addWidget(
            self.next_button
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

        container_layout = (
            QVBoxLayout(
                container
            )
        )

        container_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        container_layout.setSpacing(
            4
        )

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

    def _toggle_filters(
        self,
        visible: bool,
    ) -> None:
        self.filter_panel.setVisible(
            visible
        )

        self._update_filter_button_text()

    def _update_filter_button_text(
        self,
    ) -> None:
        active_count = (
            self._active_filter_count()
        )

        if active_count:
            base_text = (
                f"FILTERS ({active_count})"
            )

        else:
            base_text = (
                "FILTERS"
            )

        if (
            self.filter_toggle_button
            .isChecked()
        ):
            self.filter_toggle_button.setText(
                f"{base_text} ▴"
            )

        else:
            self.filter_toggle_button.setText(
                f"{base_text} ▾"
            )

    def _active_filter_count(
        self,
    ) -> int:
        count = 0

        if (
            self.status_filter.currentData()
            is not None
        ):
            count += 1

        if (
            self.age_filter.currentData()
            != AGE_ALL
        ):
            count += 1

        if (
            self.priority_filter.currentData()
            is not None
        ):
            count += 1

        for combo in (
            self.category_filter,
            self.subcategory_filter,
            self.brand_filter,
            self.condition_filter,
            self.size_filter,
            self.colour_filter,
        ):
            if (
                combo.currentData()
                is not None
            ):
                count += 1

        if (
            self.minimum_price_filter.value()
            > 0
        ):
            count += 1

        if (
            self.maximum_price_filter.value()
            > 0
        ):
            count += 1

        if (
            self.sort_filter.currentData()
            != SORT_NEWEST
        ):
            count += 1

        return count

    def _search_changed(
        self,
        *_args,
    ) -> None:
        self.current_page = 1

        self._schedule_refresh()

    def _filter_changed(
        self,
        *_args,
    ) -> None:
        if self._updating_filter_options:
            return

        self.current_page = 1

        self._update_filter_button_text()

        self.refresh()

    def _price_filter_changed(
        self,
        *_args,
    ) -> None:
        if self._updating_filter_options:
            return

        self.current_page = 1

        self._update_filter_button_text()

        self._schedule_refresh()

    def _schedule_refresh(
        self,
    ) -> None:
        if self._updating_filter_options:
            return

        self._refresh_timer.start()

    def _page_size_changed(
        self,
        *_args,
    ) -> None:
        self.current_page = 1

        self.refresh()

    def _previous_page(
        self,
    ) -> None:
        if self.current_page <= 1:
            return

        self.current_page -= 1

        self.refresh()

        self.scroll_area.verticalScrollBar().setValue(
            0
        )

    def _next_page(
        self,
    ) -> None:
        self.current_page += 1

        self.refresh()

        self.scroll_area.verticalScrollBar().setValue(
            0
        )

    def refresh(
        self,
        *_args,
    ) -> None:
        """
        Reload listings and render only the current page.
        """
        if self._updating_filter_options:
            return

        self._refresh_timer.stop()

        try:
            filters = (
                self._build_filters()
            )

            result = (
                get_listing_browser_result(
                    filters
                )
            )

        except Exception as exc:
            self._clear_cards()

            self.count_label.setText(
                "Unable to load listings"
            )

            self._show_message(
                (
                    "There was an error loading "
                    "the listing database:\n\n"
                    f"{exc}"
                ),
                object_name="errorState",
            )

            return

        self._update_dynamic_filters(
            categories=result.categories,
            subcategories=(
                result.subcategories
            ),
            brands=result.brands,
            conditions=result.conditions,
            sizes=result.sizes,
            colours=result.colours,
        )

        page_size = int(
            self.page_size_input.currentData()
            or 25
        )

        total_results = (
            result.filtered_count
        )

        total_pages = max(
            1,
            math.ceil(
                total_results
                / page_size
            ),
        )

        self.current_page = min(
            max(
                1,
                self.current_page,
            ),
            total_pages,
        )

        start_index = (
            (self.current_page - 1)
            * page_size
        )

        end_index = min(
            start_index
            + page_size,
            total_results,
        )

        visible_listings = (
            result.listings[
                start_index:end_index
            ]
        )

        if total_results == 0:
            count_text = (
                "0 listings"
            )

        elif (
            result.filtered_count
            == result.total_count
        ):
            count_text = (
                f"{result.total_count} listings"
                f"  •  Showing "
                f"{start_index + 1}–{end_index}"
            )

        else:
            count_text = (
                f"{result.filtered_count} of "
                f"{result.total_count} listings"
                f"  •  Showing "
                f"{start_index + 1}–{end_index}"
            )

        self.count_label.setText(
            count_text
        )

        self.page_label.setText(
            (
                f"Page {self.current_page} "
                f"of {total_pages}"
            )
        )

        self.previous_button.setEnabled(
            self.current_page > 1
        )

        self.next_button.setEnabled(
            (
                self.current_page
                < total_pages
            )
        )

        self.container.setUpdatesEnabled(
            False
        )

        try:
            self._clear_cards()

            if not visible_listings:
                if (
                    result.total_count
                    == 0
                ):
                    message = (
                        "No listings have been stored yet.\n\n"
                        "Use Add Listing or Import CSV / JSON "
                        "to add your inventory."
                    )

                else:
                    message = (
                        "No listings match the current "
                        "search and filters.\n\n"
                        "Try changing or resetting "
                        "the filters."
                    )

                self._show_message(
                    message,
                    object_name="emptyState",
                )

                return

            listing_ids = [
                listing.id
                for listing
                in visible_listings
            ]

            photos_by_listing = (
                get_listing_photos_for_listings(
                    listing_ids
                )
            )

            for (
                index,
                listing,
            ) in enumerate(
                visible_listings
            ):
                card = ListingCard(
                    listing=listing,
                    photos=(
                        photos_by_listing.get(
                            listing.id,
                            [],
                        )
                    ),
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
                self.category_filter.currentData()
            ),
            subcategory=(
                self.subcategory_filter.currentData()
            ),
            brand=(
                self.brand_filter.currentData()
            ),
            condition=(
                self.condition_filter.currentData()
            ),
            size=(
                self.size_filter.currentData()
            ),
            colour=(
                self.colour_filter.currentData()
            ),
            minimum_price=minimum_price,
            maximum_price=maximum_price,
            sort_by=(
                self.sort_filter.currentData()
            ),
        )

    def _update_dynamic_filters(
        self,
        *,
        categories: list[str],
        subcategories: list[str],
        brands: list[str],
        conditions: list[str],
        sizes: list[str],
        colours: list[str],
    ) -> None:
        """
        Refresh dropdown options while preserving current selections.
        """
        filter_definitions = [
            (
                self.category_filter,
                "All Categories",
                categories,
            ),
            (
                self.subcategory_filter,
                "All Subcategories",
                subcategories,
            ),
            (
                self.brand_filter,
                "All Brands",
                brands,
            ),
            (
                self.condition_filter,
                "All Conditions",
                conditions,
            ),
            (
                self.size_filter,
                "All Sizes",
                sizes,
            ),
            (
                self.colour_filter,
                "All Colours",
                colours,
            ),
        ]

        current_values = {
            id(combo): combo.currentData()
            for (
                combo,
                _placeholder,
                _values,
            ) in filter_definitions
        }

        self._updating_filter_options = True

        try:
            for (
                combo,
                placeholder,
                values,
            ) in filter_definitions:
                combo.blockSignals(
                    True
                )

                combo.clear()

                combo.addItem(
                    placeholder,
                    None,
                )

                for value in values:
                    combo.addItem(
                        value,
                        value,
                    )

                selected_value = (
                    current_values[
                        id(combo)
                    ]
                )

                if selected_value is not None:
                    index = combo.findData(
                        selected_value
                    )

                    if index >= 0:
                        combo.setCurrentIndex(
                            index
                        )

        finally:
            for (
                combo,
                _placeholder,
                _values,
            ) in filter_definitions:
                combo.blockSignals(
                    False
                )

            self._updating_filter_options = False

        self._update_filter_button_text()

    def _reset_filters(
        self,
        *_args,
    ) -> None:
        self._refresh_timer.stop()

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

            self.sort_filter.setCurrentIndex(
                0
            )

            self.category_filter.setCurrentIndex(
                0
            )

            self.subcategory_filter.setCurrentIndex(
                0
            )

            self.brand_filter.setCurrentIndex(
                0
            )

            self.condition_filter.setCurrentIndex(
                0
            )

            self.size_filter.setCurrentIndex(
                0
            )

            self.colour_filter.setCurrentIndex(
                0
            )

            self.minimum_price_filter.setValue(
                0
            )

            self.maximum_price_filter.setValue(
                0
            )

        finally:
            self._updating_filter_options = False

        self.current_page = 1

        self._update_filter_button_text()

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

    def _clear_cards(
        self,
    ) -> None:
        while (
            self.cards_layout.count()
            > 1
        ):
            item = (
                self.cards_layout.takeAt(
                    0
                )
            )

            widget = (
                item.widget()
            )

            if widget is not None:
                widget.deleteLater()

    def _apply_styles(
        self,
    ) -> None:
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

            #filterToggleButton {
                background-color: #f9fafb;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
                min-width: 105px;
            }

            #filterToggleButton:hover {
                background-color: #f3f4f6;
            }

            #filterToggleButton:checked {
                background-color: #e5e7eb;
                color: #111827;
            }

            #listingCount {
                color: #6b7280;
                font-size: 13px;
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

            #paginationFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }

            #paginationButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 7px 14px;
                font-weight: 600;
            }

            #paginationButton:hover:enabled {
                background-color: #f3f4f6;
            }

            #paginationButton:disabled {
                color: #9ca3af;
                background-color: #f9fafb;
            }

            #pageNumberLabel {
                color: #4b5563;
                font-size: 13px;
                font-weight: 600;
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