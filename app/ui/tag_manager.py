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
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.tag_service import (
    TagListingSummary,
    bulk_add_tags,
    bulk_remove_tags,
    get_existing_tags,
    get_tag_listing_summaries,
)
from app.ui.components.dialogs.error_feedback import (
    show_logged_error,
)
from app.ui.dialog_geometry import (
    fit_dialog_to_screen,
)


class TagManagerDialog(QDialog):
    """
    Bulk tag editor for listings.

    Tags are intentionally flexible: a listing may have
    several tags such as Winter, Christmas or Quick Sale.
    """

    tags_changed = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self._summaries: dict[
            int,
            TagListingSummary,
        ] = {}

        self.setWindowTitle(
            "Bulk Tags"
        )

        self.setModal(
            True
        )

        self._build_ui()
        self._load_tag_options()
        self._load_listings()

        fit_dialog_to_screen(
            self,
            preferred_width=860,
            preferred_height=650,
            minimum_width=680,
            minimum_height=500,
            width_ratio=0.82,
            height_ratio=0.78,
        )

    def _build_ui(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        layout.setSpacing(
            14
        )

        heading = QLabel(
            "Bulk Tags"
        )

        heading.setObjectName(
            "preparationHeading"
        )

        explanation = QLabel(
            (
                "Select several listings, then add or "
                "remove the same tag from all of them."
            )
        )

        explanation.setObjectName(
            "informationText"
        )

        explanation.setWordWrap(
            True
        )

        layout.addWidget(
            heading
        )

        layout.addWidget(
            explanation
        )

        search_frame = QFrame()

        search_frame.setObjectName(
            "informationBox"
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

        search_layout.setSpacing(
            10
        )

        search_row = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            (
                "Search title, brand, category "
                "or existing tag..."
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

        self.untagged_only = QCheckBox(
            "Only without tags"
        )

        self.untagged_only.toggled.connect(
            self._apply_visibility_filters
        )

        search_row.addWidget(
            self.untagged_only
        )

        search_layout.addLayout(
            search_row
        )

        selection_row = QHBoxLayout()

        select_button = QPushButton(
            "SELECT ALL VISIBLE"
        )

        select_button.setObjectName(
            "secondaryButton"
        )

        select_button.setMinimumHeight(
            40
        )

        select_button.clicked.connect(
            self._select_all_visible
        )

        clear_button = QPushButton(
            "CLEAR SELECTION"
        )

        clear_button.setObjectName(
            "secondaryButton"
        )

        clear_button.setMinimumHeight(
            40
        )

        clear_button.clicked.connect(
            self._clear_selection
        )

        selection_row.addWidget(
            select_button
        )

        selection_row.addWidget(
            clear_button
        )

        selection_row.addStretch()

        self.selection_label = QLabel(
            "0 selected"
        )

        self.selection_label.setObjectName(
            "informationText"
        )

        selection_row.addWidget(
            self.selection_label
        )

        search_layout.addLayout(
            selection_row
        )

        layout.addWidget(
            search_frame
        )

        self.list_widget = QListWidget()

        self.list_widget.itemChanged.connect(
            self._update_selection_count
        )

        layout.addWidget(
            self.list_widget,
            1,
        )

        tag_frame = QFrame()

        tag_frame.setObjectName(
            "informationBox"
        )

        tag_layout = QVBoxLayout(
            tag_frame
        )

        tag_layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        tag_layout.setSpacing(
            8
        )

        title = QLabel(
            "TAG"
        )

        title.setObjectName(
            "sectionHeading"
        )

        tag_layout.addWidget(
            title
        )

        action_row = QHBoxLayout()

        self.tag_input = QComboBox()

        self.tag_input.setEditable(
            True
        )

        self.tag_input.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert
        )

        self.tag_input.setPlaceholderText(
            "Choose or type a tag, e.g. Winter"
        )

        self.tag_input.setMinimumHeight(
            40
        )

        action_row.addWidget(
            self.tag_input,
            1,
        )

        add_button = QPushButton(
            "ADD TAG"
        )

        add_button.setObjectName(
            "primaryButton"
        )

        add_button.setMinimumHeight(
            40
        )

        add_button.clicked.connect(
            self._add_tag
        )

        remove_button = QPushButton(
            "REMOVE TAG"
        )

        remove_button.setObjectName(
            "secondaryButton"
        )

        remove_button.setMinimumHeight(
            40
        )

        remove_button.clicked.connect(
            self._remove_tag
        )

        action_row.addWidget(
            add_button
        )

        action_row.addWidget(
            remove_button
        )

        tag_layout.addLayout(
            action_row
        )

        hint = QLabel(
            (
                "Typing a new tag creates it automatically "
                "when you add it."
            )
        )

        hint.setObjectName(
            "informationText"
        )

        hint.setWordWrap(
            True
        )

        tag_layout.addWidget(
            hint
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

        tag_layout.addWidget(
            self.result_label
        )

        layout.addWidget(
            tag_frame
        )

        bottom_row = QHBoxLayout()

        bottom_row.addStretch()

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
            self.accept
        )

        bottom_row.addWidget(
            close_button
        )

        layout.addLayout(
            bottom_row
        )

    def _load_tag_options(
        self,
    ) -> None:
        current = (
            self.tag_input
            .currentText()
        )

        self.tag_input.blockSignals(
            True
        )

        try:
            self.tag_input.clear()

            self.tag_input.addItems(
                get_existing_tags()
            )

            self.tag_input.setCurrentText(
                current
            )

        finally:
            self.tag_input.blockSignals(
                False
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
                get_tag_listing_summaries()
            )

            self._summaries = {
                summary.listing_id: summary
                for summary
                in summaries
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
        summary: TagListingSummary,
    ) -> str:
        details = []

        if summary.category:
            category = summary.category

            if summary.subcategory:
                category += (
                    " > "
                    + summary.subcategory
                )

            details.append(
                category
            )

        if summary.brand:
            details.append(
                summary.brand
            )

        details.append(
            summary.status.capitalize()
        )

        tag_text = (
            ", ".join(
                summary.tags
            )
            if summary.tags
            else "No tags"
        )

        return (
            summary.title
            + "\n"
            + " | ".join(
                details
            )
            + "\nTags: "
            + tag_text
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

        untagged_only = (
            self.untagged_only
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
                    *summary.tags,
                )
                if value
            ).casefold()

            search_matches = (
                not search
                or search
                in searchable
            )

            tag_matches = (
                not untagged_only
                or not summary.tags
            )

            visible = (
                search_matches
                and tag_matches
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
                self.list_widget.item(
                    index
                ).setCheckState(
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
        return [
            self.list_widget.item(
                index
            ).data(
                Qt.ItemDataRole.UserRole
            )
            for index in range(
                self.list_widget.count()
            )
            if (
                self.list_widget.item(
                    index
                ).checkState()
                == Qt.CheckState.Checked
            )
        ]

    def _update_selection_count(
        self,
        *_args,
    ) -> None:
        count = len(
            self._selected_listing_ids()
        )

        self.selection_label.setText(
            (
                "1 selected"
                if count == 1
                else f"{count} selected"
            )
        )

    def _validate_action(
        self,
    ) -> tuple[
        list[int],
        str,
    ] | None:
        listing_ids = (
            self._selected_listing_ids()
        )

        if not listing_ids:
            self.result_label.setText(
                "Select at least one listing first."
            )

            return None

        tag_name = (
            self.tag_input
            .currentText()
            .strip()
        )

        if not tag_name:
            self.result_label.setText(
                "Choose or type a tag first."
            )

            self.tag_input.setFocus()

            return None

        return (
            listing_ids,
            tag_name,
        )

    def _add_tag(
        self,
    ) -> None:
        action = (
            self._validate_action()
        )

        if action is None:
            return

        listing_ids, tag_name = action

        try:
            result = bulk_add_tags(
                listing_ids,
                [
                    tag_name,
                ],
            )

        except Exception as exc:
            show_logged_error(
                self,
                title="Tag Update Failed",
                message=(
                    "The selected listings could not "
                    "be updated."
                ),
                context=(
                    "Unable to bulk add listing tag"
                ),
                exception=exc,
            )

            return

        if result.associations_changed:
            message = (
                f'Added "{tag_name}" to '
                f"{result.listings_changed} "
                + (
                    "listing."
                    if result.listings_changed == 1
                    else "listings."
                )
            )

        else:
            message = (
                f'No changes - the selected listings '
                f'already have "{tag_name}".'
            )

        if result.missing_listings:
            message += (
                " "
                f"{result.missing_listings} "
                "listing(s) were no longer found."
            )

        self.result_label.setText(
            message
        )

        self.tags_changed.emit()

        self._load_tag_options()
        self._load_listings()

        self.tag_input.setCurrentText(
            tag_name
        )

    def _remove_tag(
        self,
    ) -> None:
        action = (
            self._validate_action()
        )

        if action is None:
            return

        listing_ids, tag_name = action

        try:
            result = bulk_remove_tags(
                listing_ids,
                [
                    tag_name,
                ],
            )

        except Exception as exc:
            show_logged_error(
                self,
                title="Tag Update Failed",
                message=(
                    "The selected listings could not "
                    "be updated."
                ),
                context=(
                    "Unable to bulk remove listing tag"
                ),
                exception=exc,
            )

            return

        if result.associations_changed:
            message = (
                f'Removed "{tag_name}" from '
                f"{result.listings_changed} "
                + (
                    "listing."
                    if result.listings_changed == 1
                    else "listings."
                )
            )

        else:
            message = (
                f'No changes - the selected listings '
                f'do not have "{tag_name}".'
            )

        if result.missing_listings:
            message += (
                " "
                f"{result.missing_listings} "
                "listing(s) were no longer found."
            )

        self.result_label.setText(
            message
        )

        self.tags_changed.emit()

        self._load_tag_options()
        self._load_listings()

        self.tag_input.setCurrentText(
            tag_name
        )
