from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.category_service import (
    CategoryListingSummary,
    bulk_assign_category,
    get_category_listing_summaries,
    get_existing_categories,
    get_existing_subcategories,
)


class CategoryManagerDialog(QDialog):
    """
    Bulk category and subcategory editor.
    """

    categories_changed = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self._summaries: dict[
            int,
            CategoryListingSummary,
        ] = {}

        self.setWindowTitle(
            "Bulk Category Manager"
        )

        self.resize(
            900,
            720,
        )

        self.setMinimumSize(
            720,
            600,
        )

        self._build_ui()
        self._apply_styles()

        self._load_category_options()
        self._load_listings()

    def _build_ui(
        self,
    ) -> None:
        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        main_layout.setSpacing(
            14
        )

        heading = QLabel(
            "Bulk Category Manager"
        )

        heading.setObjectName(
            "dialogHeading"
        )

        explanation = QLabel(
            (
                "Search for listings, select several items, "
                "then assign the same category and optional "
                "subcategory to them."
            )
        )

        explanation.setObjectName(
            "helpText"
        )

        explanation.setWordWrap(
            True
        )

        main_layout.addWidget(
            heading
        )

        main_layout.addWidget(
            explanation
        )

        search_frame = QFrame()

        search_frame.setObjectName(
            "sectionFrame"
        )

        search_layout = QVBoxLayout(
            search_frame
        )

        search_layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        search_row = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            (
                "Search title, brand, category "
                "or subcategory..."
            )
        )

        self.search_input.setClearButtonEnabled(
            True
        )

        self.search_input.textChanged.connect(
            self._apply_visibility_filters
        )

        search_row.addWidget(
            self.search_input,
            1,
        )

        self.uncategorized_only = QCheckBox(
            "Only without category"
        )

        self.uncategorized_only.setChecked(
            True
        )

        self.uncategorized_only.toggled.connect(
            self._uncategorized_filter_changed
        )

        search_row.addWidget(
            self.uncategorized_only
        )

        search_layout.addLayout(
            search_row
        )

        selection_row = QHBoxLayout()

        select_visible_button = QPushButton(
            "SELECT ALL VISIBLE"
        )

        select_visible_button.setObjectName(
            "secondaryButton"
        )

        select_visible_button.clicked.connect(
            self._select_all_visible
        )

        clear_selection_button = QPushButton(
            "CLEAR SELECTION"
        )

        clear_selection_button.setObjectName(
            "secondaryButton"
        )

        clear_selection_button.clicked.connect(
            self._clear_selection
        )

        selection_row.addWidget(
            select_visible_button
        )

        selection_row.addWidget(
            clear_selection_button
        )

        selection_row.addStretch()

        self.selection_label = QLabel(
            "0 selected"
        )

        self.selection_label.setObjectName(
            "countText"
        )

        selection_row.addWidget(
            self.selection_label
        )

        search_layout.addLayout(
            selection_row
        )

        main_layout.addWidget(
            search_frame
        )

        self.list_widget = QListWidget()

        self.list_widget.setObjectName(
            "listingList"
        )

        self.list_widget.itemChanged.connect(
            self._update_selection_count
        )

        main_layout.addWidget(
            self.list_widget,
            1,
        )

        assignment_frame = QFrame()

        assignment_frame.setObjectName(
            "sectionFrame"
        )

        assignment_layout = QVBoxLayout(
            assignment_frame
        )

        assignment_layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        assignment_title = QLabel(
            "ASSIGN CATEGORY"
        )

        assignment_title.setObjectName(
            "sectionHeading"
        )

        assignment_layout.addWidget(
            assignment_title
        )

        fields_row = QHBoxLayout()

        category_group = QVBoxLayout()

        category_label = QLabel(
            "Category"
        )

        category_label.setObjectName(
            "fieldLabel"
        )

        self.category_input = QComboBox()

        self.category_input.setEditable(
            True
        )

        self.category_input.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert
        )

        self.category_input.setPlaceholderText(
            "e.g. Books"
        )

        category_group.addWidget(
            category_label
        )

        category_group.addWidget(
            self.category_input
        )

        fields_row.addLayout(
            category_group,
            1,
        )

        subcategory_group = (
            QVBoxLayout()
        )

        subcategory_label = QLabel(
            "Subcategory"
        )

        subcategory_label.setObjectName(
            "fieldLabel"
        )

        self.subcategory_input = (
            QComboBox()
        )

        self.subcategory_input.setEditable(
            True
        )

        self.subcategory_input.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert
        )

        self.subcategory_input.setPlaceholderText(
            (
                "Optional, e.g. "
                "Language Learning"
            )
        )

        subcategory_group.addWidget(
            subcategory_label
        )

        subcategory_group.addWidget(
            self.subcategory_input
        )

        fields_row.addLayout(
            subcategory_group,
            1,
        )

        assignment_layout.addLayout(
            fields_row
        )

        options_row = QHBoxLayout()

        self.update_subcategory_checkbox = (
            QCheckBox(
                "Update subcategory"
            )
        )

        self.update_subcategory_checkbox.setChecked(
            True
        )

        options_row.addWidget(
            self.update_subcategory_checkbox
        )

        self.overwrite_checkbox = (
            QCheckBox(
                (
                    "Allow replacing existing "
                    "categories"
                )
            )
        )

        self.overwrite_checkbox.setChecked(
            False
        )

        self.overwrite_checkbox.setEnabled(
            False
        )

        options_row.addWidget(
            self.overwrite_checkbox
        )

        options_row.addStretch()

        assignment_layout.addLayout(
            options_row
        )

        main_layout.addWidget(
            assignment_frame
        )

        bottom_row = QHBoxLayout()

        bottom_row.addStretch()

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setObjectName(
            "secondaryButton"
        )

        close_button.clicked.connect(
            self.accept
        )

        self.apply_button = QPushButton(
            "APPLY TO SELECTED"
        )

        self.apply_button.setObjectName(
            "primaryButton"
        )

        self.apply_button.clicked.connect(
            self._apply_category
        )

        bottom_row.addWidget(
            close_button
        )

        bottom_row.addWidget(
            self.apply_button
        )

        main_layout.addLayout(
            bottom_row
        )

    def _load_category_options(
        self,
    ) -> None:
        categories = (
            get_existing_categories()
        )

        subcategories = (
            get_existing_subcategories()
        )

        current_category = (
            self.category_input
            .currentText()
        )

        current_subcategory = (
            self.subcategory_input
            .currentText()
        )

        self.category_input.clear()

        self.category_input.addItems(
            categories
        )

        self.category_input.setCurrentText(
            current_category
        )

        self.subcategory_input.clear()

        self.subcategory_input.addItems(
            subcategories
        )

        self.subcategory_input.setCurrentText(
            current_subcategory
        )

    def _load_listings(
        self,
    ) -> None:
        self.list_widget.blockSignals(
            True
        )

        try:
            self.list_widget.clear()

            summaries = (
                get_category_listing_summaries()
            )

            self._summaries = {
                summary.listing_id: summary
                for summary in summaries
            }

            for summary in summaries:
                item = QListWidgetItem(
                    self._build_item_text(
                        summary
                    )
                )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    summary.listing_id,
                )

                item.setFlags(
                    item.flags()
                    | Qt.ItemFlag.ItemIsUserCheckable
                )

                item.setCheckState(
                    Qt.CheckState.Unchecked
                )

                self.list_widget.addItem(
                    item
                )

        finally:
            self.list_widget.blockSignals(
                False
            )

        self._apply_visibility_filters()
        self._update_selection_count()

    def _build_item_text(
        self,
        summary: CategoryListingSummary,
    ) -> str:
        category = (
            summary.category
            or "No category"
        )

        if summary.subcategory:
            category = (
                f"{category} → "
                f"{summary.subcategory}"
            )

        brand_text = ""

        if summary.brand:
            brand_text = (
                f"  •  {summary.brand}"
            )

        return (
            f"{summary.title}"
            f"\n{category}"
            f"{brand_text}"
            f"  •  {summary.status.capitalize()}"
        )

    def _apply_visibility_filters(
        self,
        *_args,
    ) -> None:
        search = (
            self.search_input
            .text()
            .strip()
            .casefold()
        )

        uncategorized_only = (
            self.uncategorized_only
            .isChecked()
        )

        visible_count = 0

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

            summary = (
                self._summaries.get(
                    listing_id
                )
            )

            if summary is None:
                item.setHidden(
                    True
                )
                continue

            searchable = " ".join(
                value
                for value in (
                    summary.title,
                    summary.category,
                    summary.subcategory,
                    summary.brand,
                )
                if value
            ).casefold()

            search_matches = (
                not search
                or search
                in searchable
            )

            has_category = bool(
                summary.category
                and summary.category.strip()
            )

            category_matches = (
                not uncategorized_only
                or not has_category
            )

            visible = (
                search_matches
                and category_matches
            )

            item.setHidden(
                not visible
            )

            if visible:
                visible_count += 1

        self.selection_label.setToolTip(
            (
                f"{visible_count} listings "
                "currently visible"
            )
        )

    def _uncategorized_filter_changed(
        self,
        checked: bool,
    ) -> None:
        self.overwrite_checkbox.setEnabled(
            not checked
        )

        if checked:
            self.overwrite_checkbox.setChecked(
                False
            )

        self._apply_visibility_filters()

    def _select_all_visible(
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

                if not item.isHidden():
                    item.setCheckState(
                        Qt.CheckState.Checked
                    )

        finally:
            self.list_widget.blockSignals(
                False
            )

        self._update_selection_count()

    def _clear_selection(
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

                item.setCheckState(
                    Qt.CheckState.Unchecked
                )

        finally:
            self.list_widget.blockSignals(
                False
            )

        self._update_selection_count()

    def _selected_listing_ids(
        self,
    ) -> list[int]:
        selected: list[int] = []

        for index in range(
            self.list_widget.count()
        ):
            item = (
                self.list_widget.item(
                    index
                )
            )

            if (
                item.checkState()
                == Qt.CheckState.Checked
            ):
                selected.append(
                    item.data(
                        Qt.ItemDataRole.UserRole
                    )
                )

        return selected

    def _update_selection_count(
        self,
        *_args,
    ) -> None:
        count = len(
            self._selected_listing_ids()
        )

        if count == 1:
            text = "1 selected"

        else:
            text = (
                f"{count} selected"
            )

        self.selection_label.setText(
            text
        )

    def _apply_category(
        self,
    ) -> None:
        listing_ids = (
            self._selected_listing_ids()
        )

        if not listing_ids:
            QMessageBox.information(
                self,
                "Nothing Selected",
                (
                    "Select at least one "
                    "listing first."
                ),
            )

            return

        category = (
            self.category_input
            .currentText()
            .strip()
        )

        if not category:
            QMessageBox.warning(
                self,
                "Missing Category",
                (
                    "Enter the category "
                    "you want to assign."
                ),
            )

            self.category_input.setFocus()

            return

        subcategory = (
            self.subcategory_input
            .currentText()
            .strip()
        )

        overwrite = (
            self.overwrite_checkbox
            .isChecked()
        )

        if overwrite:
            confirmation = (
                QMessageBox.question(
                    self,
                    "Replace Existing Categories?",
                    (
                        "Some selected listings may "
                        "already have a category.\n\n"
                        "Do you want to replace "
                        "existing category values?"
                    ),
                    (
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.Cancel
                    ),
                    QMessageBox.StandardButton.Cancel,
                )
            )

            if (
                confirmation
                != QMessageBox.StandardButton.Yes
            ):
                return

        try:
            result = bulk_assign_category(
                listing_ids=listing_ids,
                category=category,
                subcategory=subcategory,
                overwrite_existing=overwrite,
                update_subcategory=(
                    self.update_subcategory_checkbox
                    .isChecked()
                ),
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Category Update Failed",
                str(exc),
            )

            return

        message_parts = [
            (
                f"Updated: "
                f"{result.updated}"
            )
        ]

        if result.skipped_existing:
            message_parts.append(
                (
                    "Skipped because a category "
                    "already existed: "
                    f"{result.skipped_existing}"
                )
            )

        if result.missing:
            message_parts.append(
                (
                    "Listings no longer found: "
                    f"{result.missing}"
                )
            )

        QMessageBox.information(
            self,
            "Categories Updated",
            "\n".join(
                message_parts
            ),
        )

        self.categories_changed.emit()

        self._load_category_options()
        self._load_listings()

    def _apply_styles(
        self,
    ) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background-color: #f5f6f8;
            }

            QWidget {
                font-family: "Segoe UI";
                font-size: 14px;
            }

            #dialogHeading {
                font-size: 24px;
                font-weight: 700;
                color: #111827;
            }

            #helpText,
            #countText {
                color: #6b7280;
            }

            #sectionFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 9px;
            }

            #sectionHeading {
                color: #111827;
                font-size: 13px;
                font-weight: 700;
            }

            #fieldLabel {
                color: #6b7280;
                font-size: 12px;
                font-weight: 600;
            }

            QLineEdit,
            QComboBox,
            QListWidget {
                background-color: white;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 7px;
            }

            QListWidget::item {
                padding: 8px;
                margin: 2px;
            }

            QListWidget::item:hover {
                background-color: #f3f4f6;
            }

            QListWidget::item:selected {
                background-color: #e5e7eb;
                color: #111827;
            }

            #primaryButton {
                background-color: #1f2937;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 16px;
                font-weight: 600;
            }

            #primaryButton:hover {
                background-color: #374151;
            }

            #secondaryButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 7px;
                padding: 9px 14px;
                font-weight: 600;
            }

            #secondaryButton:hover {
                background-color: #f3f4f6;
            }
            """
        )