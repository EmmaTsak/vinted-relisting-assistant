from __future__ import annotations

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.listing_service import (
    InvalidISBNError,
    ListingInput,
    ListingNotFoundError,
    get_listing,
    normalize_isbn,
)
from app.ui.listing_dialog import (
    ListingDialog,
)


class ISBNListingDialog(ListingDialog):
    """
    Listing editor with optional ISBN support and
    collapsible secondary sections.

    Default state:
    - Photos: collapsed
    - Item Details: collapsed

    Always visible:
    - Basic Information
    - Relisting
    - Private Notes
    """

    FIELD_HEIGHT = 40

    def __init__(
        self,
        parent: QWidget | None = None,
        listing_id: int | None = None,
    ) -> None:
        super().__init__(
            parent=parent,
            listing_id=listing_id,
        )

    def _build_ui(
        self,
    ) -> None:
        """
        Build the normal listing editor first, then apply
        ISBN support and the cleaner collapsible layout.
        """
        super()._build_ui()

        # -------------------------------------------------
        # ISBN
        # -------------------------------------------------

        self.isbn_input = QLineEdit()

        self.isbn_input.setMaxLength(
            20
        )

        self.isbn_input.setPlaceholderText(
            "ISBN-10 or ISBN-13, e.g. 9780141187761"
        )

        self.isbn_input.setClearButtonEnabled(
            True
        )

        self.isbn_input.setMinimumHeight(
            self.FIELD_HEIGHT
        )

        form_layout = (
            self._find_listing_form()
        )

        notes_row = (
            self._find_widget_row(
                form_layout,
                self.notes_input,
            )
        )

        if notes_row is None:
            form_layout.addRow(
                "ISBN (Books)",
                self.isbn_input,
            )

        else:
            form_layout.insertRow(
                notes_row,
                "ISBN (Books)",
                self.isbn_input,
            )

        # -------------------------------------------------
        # Consistent field sizing
        # -------------------------------------------------

        self._polish_fields()

        # -------------------------------------------------
        # Standard section headings
        # -------------------------------------------------

        self._insert_section_before(
            form_layout=form_layout,
            target_widget=self.notes_input,
            title="PRIVATE NOTES",
            description=(
                "Notes are stored locally and are not part "
                "of the public Vinted listing."
            ),
        )

        self._insert_section_before(
            form_layout=form_layout,
            target_widget=self.priority_input,
            title="RELISTING",
            description=(
                "Controls used by the local relisting queue."
            ),
        )

        self._insert_section_before(
            form_layout=form_layout,
            target_widget=self.title_input,
            title="BASIC INFORMATION",
            description=(
                "Core information for this listing."
            ),
        )

        # -------------------------------------------------
        # Collapsible Item Details
        # -------------------------------------------------

        self._create_item_details_section(
            form_layout
        )

        # -------------------------------------------------
        # Collapsible Photos
        # -------------------------------------------------

        self._create_photos_section()

    def _polish_fields(
        self,
    ) -> None:
        """
        Standardize ordinary input heights.

        Description and notes remain larger because they
        contain multi-line text.
        """
        single_line_fields = (
            self.title_input,
            self.price_input,
            self.currency_input,
            self.category_input,
            self.subcategory_input,
            self.brand_input,
            self.size_input,
            self.condition_input,
            self.colour_input,
            self.material_input,
            self.parcel_size_input,
            self.priority_input,
            self.original_date_input,
            self.isbn_input,
        )

        for widget in single_line_fields:
            widget.setMinimumHeight(
                self.FIELD_HEIGHT
            )

        self.description_input.setMinimumHeight(
            130
        )

        self.notes_input.setMinimumHeight(
            100
        )

        self.save_button.setMinimumHeight(
            42
        )

    # =====================================================
    # Photos
    # =====================================================

    def _create_photos_section(
        self,
    ) -> None:
        """
        Place a collapsible heading directly above the
        existing photo manager.

        The photo manager itself remains unchanged.
        """
        photo_frame = self.findChild(
            QFrame,
            "photoSection",
        )

        if photo_frame is None:
            return

        parent = photo_frame.parentWidget()

        if parent is None:
            return

        parent_layout = parent.layout()

        if not isinstance(
            parent_layout,
            QVBoxLayout,
        ):
            return

        photo_index = (
            parent_layout.indexOf(
                photo_frame
            )
        )

        if photo_index < 0:
            return

        # The toggle itself becomes the visible Photos heading.
        # Hide the old heading inside the photo frame to avoid
        # showing "Photos" twice when expanded.
        for label in photo_frame.findChildren(
            QLabel
        ):
            if (
                label.text()
                .strip()
                .lower()
                == "photos"
            ):
                label.hide()
                break

        self.photos_toggle = QPushButton(
            "PHOTOS ▾"
        )

        self.photos_toggle.setObjectName(
            "secondaryButton"
        )

        self.photos_toggle.setCheckable(
            True
        )

        self.photos_toggle.setChecked(
            False
        )

        self.photos_toggle.setMinimumHeight(
            42
        )

        self.photos_toggle.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.photos_toggle.setToolTip(
            "Show or hide listing photos"
        )

        self.photos_toggle.toggled.connect(
            self._toggle_photos
        )

        parent_layout.insertWidget(
            photo_index,
            self.photos_toggle,
        )

        # Start closed.
        photo_frame.setVisible(
            False
        )

    def _toggle_photos(
        self,
        expanded: bool,
    ) -> None:
        photo_frame = self.findChild(
            QFrame,
            "photoSection",
        )

        if photo_frame is None:
            return

        photo_frame.setVisible(
            expanded
        )

        if expanded:
            self.photos_toggle.setText(
                "PHOTOS ▴"
            )
        else:
            self.photos_toggle.setText(
                "PHOTOS ▾"
            )

    # =====================================================
    # Item details
    # =====================================================

    def _create_item_details_section(
        self,
        form_layout: QFormLayout,
    ) -> None:
        """
        Create a collapsible Item Details group.

        Fields:
        - Category
        - Subcategory
        - Brand
        - Size
        - Condition
        - Colour
        - Material
        - Parcel Size
        - ISBN
        """
        category_row = (
            self._find_widget_row(
                form_layout,
                self.category_input,
            )
        )

        if category_row is None:
            return

        self.item_details_toggle = (
            QPushButton(
                "ITEM DETAILS ▾"
            )
        )

        self.item_details_toggle.setObjectName(
            "secondaryButton"
        )

        self.item_details_toggle.setCheckable(
            True
        )

        self.item_details_toggle.setChecked(
            False
        )

        self.item_details_toggle.setMinimumHeight(
            42
        )

        self.item_details_toggle.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.item_details_toggle.setToolTip(
            (
                "Show or hide category, brand, size, "
                "condition and other optional details"
            )
        )

        self.item_details_toggle.toggled.connect(
            lambda expanded:
            self._toggle_item_details(
                form_layout,
                expanded,
            )
        )

        form_layout.insertRow(
            category_row,
            self.item_details_toggle,
        )

        # Start collapsed.
        self._set_item_detail_rows_visible(
            form_layout,
            False,
        )

    def _toggle_item_details(
        self,
        form_layout: QFormLayout,
        expanded: bool,
    ) -> None:
        self._set_item_detail_rows_visible(
            form_layout,
            expanded,
        )

        if expanded:
            self.item_details_toggle.setText(
                "ITEM DETAILS ▴"
            )
        else:
            self.item_details_toggle.setText(
                "ITEM DETAILS ▾"
            )

    def _set_item_detail_rows_visible(
        self,
        form_layout: QFormLayout,
        visible: bool,
    ) -> None:
        item_detail_widgets = (
            self.category_input,
            self.subcategory_input,
            self.brand_input,
            self.size_input,
            self.condition_input,
            self.colour_input,
            self.material_input,
            self.parcel_size_input,
            self.isbn_input,
        )

        for widget in item_detail_widgets:
            self._set_form_row_visible(
                form_layout,
                widget,
                visible,
            )

    def _set_form_row_visible(
        self,
        form_layout: QFormLayout,
        target_widget: QWidget,
        visible: bool,
    ) -> None:
        """
        Hide/show both the field and its matching label.
        """
        row = self._find_widget_row(
            form_layout,
            target_widget,
        )

        if row is None:
            return

        label_item = form_layout.itemAt(
            row,
            QFormLayout.ItemRole.LabelRole,
        )

        field_item = form_layout.itemAt(
            row,
            QFormLayout.ItemRole.FieldRole,
        )

        if label_item is not None:
            label_widget = (
                label_item.widget()
            )

            if label_widget is not None:
                label_widget.setVisible(
                    visible
                )

        if field_item is not None:
            field_widget = (
                field_item.widget()
            )

            if field_widget is not None:
                field_widget.setVisible(
                    visible
                )

    # =====================================================
    # Ordinary section headings
    # =====================================================

    def _insert_section_before(
        self,
        form_layout: QFormLayout,
        target_widget: QWidget,
        title: str,
        description: str,
    ) -> None:
        row = self._find_widget_row(
            form_layout,
            target_widget,
        )

        if row is None:
            return

        section = QFrame()

        section.setObjectName(
            "listingFormSection"
        )

        section_layout = QVBoxLayout(
            section
        )

        section_layout.setContentsMargins(
            0,
            16,
            0,
            6,
        )

        section_layout.setSpacing(
            3
        )

        heading = QLabel(
            title
        )

        heading.setObjectName(
            "sectionHeading"
        )

        help_text = QLabel(
            description
        )

        help_text.setObjectName(
            "helpText"
        )

        help_text.setWordWrap(
            True
        )

        section_layout.addWidget(
            heading
        )

        section_layout.addWidget(
            help_text
        )

        form_layout.insertRow(
            row,
            section,
        )

    # =====================================================
    # Form helpers
    # =====================================================

    def _find_widget_row(
        self,
        form_layout: QFormLayout,
        target_widget: QWidget,
    ) -> int | None:
        for row in range(
            form_layout.rowCount()
        ):
            field_item = form_layout.itemAt(
                row,
                QFormLayout.ItemRole.FieldRole,
            )

            if (
                field_item is not None
                and field_item.widget()
                is target_widget
            ):
                return row

        return None

    def _find_listing_form(
        self,
    ) -> QFormLayout:
        for layout in self.findChildren(
            QFormLayout
        ):
            return layout

        raise RuntimeError(
            "Could not find the listing form layout."
        )

    # =====================================================
    # Existing ISBN functionality
    # =====================================================

    def _load_listing(
        self,
    ) -> None:
        """
        Load normal listing fields and then the ISBN.

        Collapsed fields still contain their values; hiding
        them does not remove or reset any listing data.
        """
        super()._load_listing()

        if self.listing_id is None:
            return

        try:
            listing = get_listing(
                self.listing_id
            )

        except ListingNotFoundError:
            return

        self.isbn_input.setText(
            listing.isbn
            or ""
        )

    def _validate_form(
        self,
    ) -> bool:
        if not super()._validate_form():
            return False

        isbn_text = (
            self.isbn_input
            .text()
            .strip()
        )

        if not isbn_text:
            return True

        try:
            normalize_isbn(
                isbn_text
            )

        except InvalidISBNError as exc:
            QMessageBox.warning(
                self,
                "Invalid ISBN",
                (
                    f"{exc}\n\n"
                    "You can enter either:\n"
                    "• ISBN-10\n"
                    "• ISBN-13\n\n"
                    "Spaces and hyphens are allowed."
                ),
            )

            # Open Item Details automatically so the user
            # can immediately see and correct the ISBN.
            self.item_details_toggle.setChecked(
                True
            )

            self.isbn_input.setFocus()

            self.isbn_input.selectAll()

            return False

        return True

    def _build_listing_input(
        self,
    ) -> ListingInput:
        data = (
            super()._build_listing_input()
        )

        data.isbn = (
            self.isbn_input.text()
        )

        return data