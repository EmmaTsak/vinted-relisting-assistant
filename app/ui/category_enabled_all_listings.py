from __future__ import annotations

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtGui import (
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from app.ui.all_listings import (
    AllListingsPage,
)
from app.ui.category_manager import (
    CategoryManagerDialog,
)


class CategoryEnabledAllListingsPage(
    AllListingsPage
):
    """
    Polished All Listings page with bulk category management.

    The base AllListingsPage continues to own:
    - searching
    - filtering
    - sorting
    - pagination
    - listing-card creation
    - photo batching
    - filter state

    This subclass only improves the presentation.
    """

    CONTROL_HEIGHT = 40

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self._add_category_toolbar()
        self._polish_existing_controls()
        self._install_shortcuts()

    def _add_category_toolbar(
        self,
    ) -> None:
        toolbar = QFrame()

        toolbar.setObjectName(
            "categoryToolbar"
        )

        toolbar.setMinimumHeight(
            48
        )

        layout = QHBoxLayout(
            toolbar
        )

        layout.setContentsMargins(
            14,
            8,
            10,
            8,
        )

        layout.setSpacing(
            12
        )

        label_container = QWidget()

        label_layout = QHBoxLayout(
            label_container
        )

        label_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        label_layout.setSpacing(
            8
        )

        heading = QLabel(
            "CATEGORIES"
        )

        heading.setObjectName(
            "sectionHeading"
        )

        help_text = QLabel(
            (
                "Organise imported listings "
                "without editing them one by one."
            )
        )

        help_text.setObjectName(
            "categoryHelpText"
        )

        help_text.setWordWrap(
            True
        )

        label_layout.addWidget(
            heading
        )

        label_layout.addWidget(
            help_text
        )

        label_layout.addStretch()

        layout.addWidget(
            label_container,
            1,
        )

        category_button = QPushButton(
            "BULK CATEGORIES"
        )

        category_button.setObjectName(
            "secondaryButton"
        )

        category_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        category_button.setMinimumHeight(
            36
        )

        category_button.setMinimumWidth(
            150
        )

        category_button.clicked.connect(
            self._open_category_manager
        )

        layout.addWidget(
            category_button
        )

        page_layout = self.layout()

        if page_layout is not None:
            # Search stays first.
            # Category tools come directly underneath it.
            page_layout.insertWidget(
                1,
                toolbar,
            )

    def _polish_existing_controls(
        self,
    ) -> None:
        """
        Improve the existing AllListingsPage controls without
        changing any filtering or pagination logic.
        """

        # -------------------------------------------------
        # Search
        # -------------------------------------------------

        self.search_input.setMinimumHeight(
            42
        )

        self.search_input.setPlaceholderText(
            (
                "Search listings by title, ISBN, brand, "
                "category, size, colour..."
            )
        )

        self.filter_toggle_button.setMinimumHeight(
            42
        )

        self.filter_toggle_button.setMinimumWidth(
            125
        )

        # -------------------------------------------------
        # Remove redundant manual Refresh button.
        #
        # Searches and filters already refresh automatically,
        # and page changes/load events refresh when required.
        # -------------------------------------------------

        refresh_button = self.findChild(
            QPushButton,
            "refreshButton",
        )

        if refresh_button is not None:
            refresh_button.hide()

        # -------------------------------------------------
        # Standardize filter control sizes.
        # -------------------------------------------------

        combo_filters = (
            self.status_filter,
            self.age_filter,
            self.priority_filter,
            self.sort_filter,
            self.category_filter,
            self.subcategory_filter,
            self.brand_filter,
            self.condition_filter,
            self.size_filter,
            self.colour_filter,
        )

        for combo in combo_filters:
            combo.setMinimumHeight(
                self.CONTROL_HEIGHT
            )

        self.minimum_price_filter.setMinimumHeight(
            self.CONTROL_HEIGHT
        )

        self.maximum_price_filter.setMinimumHeight(
            self.CONTROL_HEIGHT
        )

        # The global InputBehaviorManager removes the
        # spin-box arrows and blocks accidental wheel changes.

        # -------------------------------------------------
        # Page-size control
        # -------------------------------------------------

        current_page_size = (
            self.page_size_input.currentData()
        )

        self.page_size_input.blockSignals(
            True
        )

        self.page_size_input.clear()

        for value in (
            25,
            50,
            100,
        ):
            self.page_size_input.addItem(
                f"{value} per page",
                value,
            )

        current_index = (
            self.page_size_input.findData(
                current_page_size
            )
        )

        if current_index < 0:
            current_index = 0

        self.page_size_input.setCurrentIndex(
            current_index
        )

        self.page_size_input.blockSignals(
            False
        )

        self.page_size_input.setMinimumHeight(
            36
        )

        self.page_size_input.setMinimumWidth(
            125
        )

        # -------------------------------------------------
        # Pagination
        # -------------------------------------------------

        self.previous_button.setMinimumHeight(
            38
        )

        self.next_button.setMinimumHeight(
            38
        )

        self.previous_button.setMinimumWidth(
            120
        )

        self.next_button.setMinimumWidth(
            120
        )

        # -------------------------------------------------
        # Count label
        # -------------------------------------------------

        self.count_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        # Keep filters collapsed on initial page load.
        self.filter_toggle_button.setChecked(
            False
        )

        self.filter_panel.setVisible(
            False
        )

        self._update_filter_button_text()

    def _install_shortcuts(
        self,
    ) -> None:
        """
        Ctrl+F jumps directly to listing search.
        """
        self.search_shortcut = QShortcut(
            QKeySequence.StandardKey.Find,
            self,
        )

        self.search_shortcut.activated.connect(
            self._focus_search
        )

    def _focus_search(
        self,
    ) -> None:
        self.search_input.setFocus()

        self.search_input.selectAll()

    def _open_category_manager(
        self,
    ) -> None:
        dialog = CategoryManagerDialog(
            parent=self
        )

        dialog.categories_changed.connect(
            self._categories_changed
        )

        dialog.exec()

    def _categories_changed(
        self,
    ) -> None:
        self.current_page = 1

        self.refresh()