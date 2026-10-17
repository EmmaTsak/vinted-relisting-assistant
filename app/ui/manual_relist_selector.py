from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models import (
    ListingPriority,
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
)
from app.services.manual_relist_service import (
    get_manual_relist_result,
)
from app.services.queue_service import (
    add_listings_to_today_queue,
)
from app.ui.components.dialogs.error_feedback import (
    show_logged_error,
)
from app.ui.components.tag_filter import (
    TagFilterButton,
)
from app.ui.dialog_geometry import (
    fit_dialog_to_screen,
)


class ManualRelistSelectorDialog(QDialog):
    """
    Choose specific listings to place in today's manual queue.

    Intentionally does NOT expose Status, Condition or Colour.
    Lifecycle eligibility is handled automatically.
    """

    def __init__(
        self,
        *,
        configured_limit: int,
        minimum_age_days: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.configured_limit = (
            configured_limit
        )

        self.minimum_age_days = (
            minimum_age_days
        )

        self._selected_ids: set[int] = (
            set()
        )

        self.setWindowTitle(
            "Choose Listings to Relist"
        )

        self.setModal(
            True
        )

        self._build_ui()

        fit_dialog_to_screen(
            self,
            preferred_width=960,
            preferred_height=720,
            minimum_width=760,
            minimum_height=540,
            width_ratio=0.86,
            height_ratio=0.82,
        )

        self._refresh_results()

    # =====================================================
    # UI
    # =====================================================

    def _build_ui(
        self,
    ) -> None:
        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        root.setSpacing(
            14
        )

        heading = QLabel(
            "Choose Listings to Relist"
        )

        heading.setObjectName(
            "preparationHeading"
        )

        help_text = QLabel(
            (
                "Pick what you want to work on today. "
                "Sold, archived, paused, excluded and too-new "
                "listings are left out automatically."
            )
        )

        help_text.setObjectName(
            "informationText"
        )

        help_text.setWordWrap(
            True
        )

        root.addWidget(
            heading
        )

        root.addWidget(
            help_text
        )

        self.search_input = (
            QLineEdit()
        )

        self.search_input.setPlaceholderText(
            (
                "Search title, brand, category, "
                "tag, size..."
            )
        )

        self.search_input.setClearButtonEnabled(
            True
        )

        self.search_input.setMinimumHeight(
            40
        )

        self.search_input.textChanged.connect(
            self._refresh_results
        )

        root.addWidget(
            self.search_input
        )

        root.addWidget(
            self._build_filters()
        )

        selection_row = QHBoxLayout()

        select_all = QPushButton(
            "SELECT ALL RESULTS"
        )

        select_all.setObjectName(
            "secondaryButton"
        )

        select_all.setMinimumHeight(
            40
        )

        select_all.clicked.connect(
            self._select_all_results
        )

        clear = QPushButton(
            "CLEAR SELECTION"
        )

        clear.setObjectName(
            "secondaryButton"
        )

        clear.setMinimumHeight(
            40
        )

        clear.clicked.connect(
            self._clear_selection
        )

        self.selection_label = QLabel(
            "0 selected"
        )

        self.selection_label.setObjectName(
            "informationText"
        )

        selection_row.addWidget(
            select_all
        )

        selection_row.addWidget(
            clear
        )

        selection_row.addStretch()

        selection_row.addWidget(
            self.selection_label
        )

        root.addLayout(
            selection_row
        )

        self.list_widget = QListWidget()

        self.list_widget.itemChanged.connect(
            self._item_changed
        )

        root.addWidget(
            self.list_widget,
            1,
        )

        self.result_label = QLabel(
            ""
        )

        self.result_label.setObjectName(
            "informationText"
        )

        self.result_label.setWordWrap(
            True
        )

        root.addWidget(
            self.result_label
        )

        bottom = QHBoxLayout()

        bottom.addStretch()

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setObjectName(
            "secondaryButton"
        )

        close_button.setMinimumHeight(
            40
        )

        close_button.clicked.connect(
            self.reject
        )

        self.add_button = QPushButton(
            "ADD SELECTED TO TODAY'S QUEUE"
        )

        self.add_button.setObjectName(
            "primaryButton"
        )

        self.add_button.setMinimumHeight(
            40
        )

        self.add_button.clicked.connect(
            self._add_selected
        )

        bottom.addWidget(
            close_button
        )

        bottom.addWidget(
            self.add_button
        )

        root.addLayout(
            bottom
        )

    def _build_filters(
        self,
    ) -> QWidget:
        frame = QFrame()

        frame.setObjectName(
            "informationBox"
        )

        grid = QGridLayout(
            frame
        )

        grid.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        grid.setHorizontalSpacing(
            12
        )

        grid.setVerticalSpacing(
            10
        )

        self.category_filter = (
            QComboBox()
        )

        self.category_filter.addItem(
            "All Categories",
            None,
        )

        self.subcategory_filter = (
            QComboBox()
        )

        self.subcategory_filter.addItem(
            "All Subcategories",
            None,
        )

        self.tag_filter = TagFilterButton()

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

        self.priority_filter = (
            QComboBox()
        )

        self.priority_filter.addItem(
            "Any Priority",
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

        self.brand_filter = (
            QComboBox()
        )

        self.brand_filter.addItem(
            "All Brands",
            None,
        )

        self.size_filter = QComboBox()

        self.size_filter.addItem(
            "All Sizes",
            None,
        )

        self.sort_filter = QComboBox()

        self.sort_filter.addItem(
            "Oldest",
            SORT_OLDEST,
        )

        self.sort_filter.addItem(
            "Newest",
            SORT_NEWEST,
        )

        self.sort_filter.addItem(
            "Last Relisted",
            SORT_LAST_RELISTED,
        )

        self.sort_filter.addItem(
            "Least Relisted",
            SORT_LEAST_RELISTED,
        )

        self.sort_filter.addItem(
            "Most Relisted",
            SORT_MOST_RELISTED,
        )

        self.sort_filter.addItem(
            "Price: Low to High",
            SORT_PRICE_LOW_HIGH,
        )

        self.sort_filter.addItem(
            "Price: High to Low",
            SORT_PRICE_HIGH_LOW,
        )

        self.minimum_price = (
            QDoubleSpinBox()
        )

        self.minimum_price.setDecimals(
            2
        )

        self.minimum_price.setRange(
            0,
            9_999_999.99,
        )

        self.minimum_price.setPrefix(
            "\u20ac "
        )

        self.maximum_price = (
            QDoubleSpinBox()
        )

        self.maximum_price.setDecimals(
            2
        )

        self.maximum_price.setRange(
            0,
            9_999_999.99,
        )

        self.maximum_price.setPrefix(
            "\u20ac "
        )

        price_widget = QWidget()

        price_layout = QHBoxLayout(
            price_widget
        )

        price_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        price_layout.setSpacing(
            6
        )

        price_layout.addWidget(
            self.minimum_price,
            1,
        )

        separator = QLabel(
            "to"
        )

        separator.setObjectName(
            "informationText"
        )

        price_layout.addWidget(
            separator
        )

        price_layout.addWidget(
            self.maximum_price,
            1,
        )

        controls = (
            self.category_filter,
            self.subcategory_filter,
            self.age_filter,
            self.priority_filter,
            self.brand_filter,
            self.size_filter,
            self.sort_filter,
        )

        for control in controls:
            control.setMinimumHeight(
                40
            )

            control.currentIndexChanged.connect(
                self._refresh_results
            )

        self.tag_filter.setMinimumHeight(
            40
        )

        self.tag_filter.selection_changed.connect(
            self._refresh_results
        )

        self.minimum_price.setMinimumHeight(
            40
        )

        self.maximum_price.setMinimumHeight(
            40
        )

        self.minimum_price.valueChanged.connect(
            self._refresh_results
        )

        self.maximum_price.valueChanged.connect(
            self._refresh_results
        )

        self._add_filter(
            grid,
            0,
            0,
            "Category",
            self.category_filter,
        )

        self._add_filter(
            grid,
            0,
            1,
            "Subcategory",
            self.subcategory_filter,
        )

        self._add_filter(
            grid,
            0,
            2,
            "Tags",
            self.tag_filter,
        )

        self._add_filter(
            grid,
            1,
            0,
            "Relist Age",
            self.age_filter,
        )

        self._add_filter(
            grid,
            1,
            1,
            "Priority",
            self.priority_filter,
        )

        self._add_filter(
            grid,
            1,
            2,
            "Brand",
            self.brand_filter,
        )

        self._add_filter(
            grid,
            2,
            0,
            "Size",
            self.size_filter,
        )

        self._add_filter(
            grid,
            2,
            1,
            "Price Range",
            price_widget,
        )

        self._add_filter(
            grid,
            2,
            2,
            "Sort",
            self.sort_filter,
        )

        for column in range(
            3
        ):
            grid.setColumnStretch(
                column,
                1,
            )

        return frame

    def _add_filter(
        self,
        grid: QGridLayout,
        row: int,
        column: int,
        title: str,
        widget: QWidget,
    ) -> None:
        container = QWidget()

        layout = QVBoxLayout(
            container
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            4
        )

        label = QLabel(
            title
        )

        label.setObjectName(
            "filterLabel"
        )

        layout.addWidget(
            label
        )

        layout.addWidget(
            widget
        )

        grid.addWidget(
            container,
            row,
            column,
        )

    # =====================================================
    # Data
    # =====================================================

    def _filters(
        self,
    ) -> ListingBrowserFilters:
        minimum = (
            self.minimum_price.value()
        )

        maximum = (
            self.maximum_price.value()
        )

        return ListingBrowserFilters(
            search_text=(
                self.search_input.text()
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
            tags=tuple(
                self.tag_filter.selected_tags()
            ),
            brand=(
                self.brand_filter.currentData()
            ),
            size=(
                self.size_filter.currentData()
            ),
            minimum_price=(
                Decimal(
                    f"{minimum:.2f}"
                )
                if minimum > 0
                else None
            ),
            maximum_price=(
                Decimal(
                    f"{maximum:.2f}"
                )
                if maximum > 0
                else None
            ),
            sort_by=(
                self.sort_filter.currentData()
            ),
        )

    def _refresh_results(
        self,
        *_args,
    ) -> None:
        try:
            result = get_manual_relist_result(
                self._filters(),
                minimum_age_days=(
                    self.minimum_age_days
                ),
            )

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Load Listings",
                message=(
                    "The available relisting choices "
                    "could not be loaded."
                ),
                context=(
                    "Unable to load manual relist candidates"
                ),
                exception=exc,
            )

            return

        self._update_combo(
            self.category_filter,
            "All Categories",
            result.categories,
        )

        self._update_combo(
            self.subcategory_filter,
            "All Subcategories",
            result.subcategories,
        )

        self._update_combo(
            self.brand_filter,
            "All Brands",
            result.brands,
        )

        self._update_combo(
            self.size_filter,
            "All Sizes",
            result.sizes,
        )

        self.tag_filter.set_options(
            result.tags
        )

        self.list_widget.blockSignals(
            True
        )

        try:
            self.list_widget.clear()

            for listing in (
                result.listings
            ):
                item = QListWidgetItem(
                    self._listing_text(
                        listing
                    )
                )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    listing.id,
                )

                item.setFlags(
                    item.flags()
                    | Qt.ItemFlag.ItemIsUserCheckable
                )

                item.setCheckState(
                    (
                        Qt.CheckState.Checked
                        if listing.id
                        in self._selected_ids
                        else Qt.CheckState.Unchecked
                    )
                )

                self.list_widget.addItem(
                    item
                )

        finally:
            self.list_widget.blockSignals(
                False
            )

        self.result_label.setText(
            (
                f"{len(result.listings)} "
                "eligible listing(s) shown."
            )
        )

        self._update_selection_label()

    def _update_combo(
        self,
        combo: QComboBox,
        placeholder: str,
        values: list[str],
    ) -> None:
        current = (
            combo.currentData()
        )

        combo.blockSignals(
            True
        )

        try:
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

            if current is not None:
                index = combo.findData(
                    current
                )

                if index >= 0:
                    combo.setCurrentIndex(
                        index
                    )

        finally:
            combo.blockSignals(
                False
            )

    def _listing_text(
        self,
        listing,
    ) -> str:
        metadata: list[str] = []

        if listing.category:
            category = (
                listing.category
            )

            if listing.subcategory:
                category += (
                    " > "
                    + listing.subcategory
                )

            metadata.append(
                category
            )

        if listing.brand:
            metadata.append(
                listing.brand
            )

        if listing.size:
            metadata.append(
                f"Size {listing.size}"
            )

        metadata.append(
            (
                f"{listing.price:.2f} "
                f"{listing.currency}"
            )
        )

        if listing.last_relisted_date:
            history = (
                "Last relisted "
                + listing.last_relisted_date.strftime(
                    "%d %b %Y"
                )
            )

        else:
            history = "Never relisted"

        tags = (
            ", ".join(
                tag.name
                for tag
                in listing.tags
            )
        )

        lines = [
            listing.title,
            " | ".join(
                metadata
            ),
            history,
        ]

        if tags:
            lines.append(
                "Tags: "
                + tags
            )

        return "\n".join(
            lines
        )

    # =====================================================
    # Selection
    # =====================================================

    def _item_changed(
        self,
        item: QListWidgetItem,
    ) -> None:
        listing_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        if (
            item.checkState()
            == Qt.CheckState.Checked
        ):
            self._selected_ids.add(
                listing_id
            )

        else:
            self._selected_ids.discard(
                listing_id
            )

        self._update_selection_label()

    def _select_all_results(
        self,
    ) -> None:
        self.list_widget.blockSignals(
            True
        )

        try:
            for index in range(
                self.list_widget.count()
            ):
                item = (
                    self.list_widget.item(
                        index
                    )
                )

                listing_id = item.data(
                    Qt.ItemDataRole.UserRole
                )

                self._selected_ids.add(
                    listing_id
                )

                item.setCheckState(
                    Qt.CheckState.Checked
                )

        finally:
            self.list_widget.blockSignals(
                False
            )

        self._update_selection_label()

    def _clear_selection(
        self,
    ) -> None:
        self._selected_ids.clear()

        self.list_widget.blockSignals(
            True
        )

        try:
            for index in range(
                self.list_widget.count()
            ):
                self.list_widget.item(
                    index
                ).setCheckState(
                    Qt.CheckState.Unchecked
                )

        finally:
            self.list_widget.blockSignals(
                False
            )

        self._update_selection_label()

    def _update_selection_label(
        self,
    ) -> None:
        count = len(
            self._selected_ids
        )

        self.selection_label.setText(
            (
                "1 selected"
                if count == 1
                else f"{count} selected"
            )
        )

        self.add_button.setText(
            (
                "ADD 1 TO TODAY'S QUEUE"
                if count == 1
                else (
                    f"ADD {count} TO TODAY'S QUEUE"
                    if count
                    else "ADD SELECTED TO TODAY'S QUEUE"
                )
            )
        )

    def _add_selected(
        self,
    ) -> None:
        if not self._selected_ids:
            self.result_label.setText(
                "Select at least one listing first."
            )

            return

        try:
            result = (
                add_listings_to_today_queue(
                    sorted(
                        self._selected_ids
                    ),
                    configured_limit=(
                        self.configured_limit
                    ),
                    minimum_age_days=(
                        self.minimum_age_days
                    ),
                )
            )

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Update Queue",
                message=(
                    "The selected listings could not "
                    "be added to today's queue."
                ),
                context=(
                    "Unable to add manual relist selections"
                ),
                exception=exc,
            )

            return

        if result.added <= 0:
            details = []

            if result.skipped_existing:
                details.append(
                    (
                        f"{result.skipped_existing} "
                        "already used today"
                    )
                )

            if result.skipped_ineligible:
                details.append(
                    (
                        f"{result.skipped_ineligible} "
                        "no longer eligible"
                    )
                )

            if result.skipped_limit:
                details.append(
                    (
                        f"{result.skipped_limit} "
                        "over today's limit"
                    )
                )

            self.result_label.setText(
                (
                    "No listings were added."
                    + (
                        " "
                        + "; ".join(
                            details
                        )
                        if details
                        else ""
                    )
                )
            )

            self._refresh_results()

            return

        self.accept()
