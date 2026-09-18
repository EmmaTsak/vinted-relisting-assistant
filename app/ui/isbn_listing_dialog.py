from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QMessageBox,
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
    Listing editor with optional ISBN support for books.

    ISBN is optional. When supplied, the value must be a valid
    ISBN-10 or ISBN-13.
    """

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
        Build the ordinary listing editor, then add the optional
        ISBN field immediately before Notes.
        """
        super()._build_ui()

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

        form_layout = self._find_listing_form()

        notes_row = None

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
                is self.notes_input
            ):
                notes_row = row
                break

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

    def _find_listing_form(
        self,
    ) -> QFormLayout:
        """
        Find the main listing-information QFormLayout.
        """
        for layout in self.findChildren(
            QFormLayout
        ):
            return layout

        raise RuntimeError(
            "Could not find the listing form layout."
        )

    def _load_listing(
        self,
    ) -> None:
        """
        Load the normal listing fields and then its ISBN.
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
        """
        Validate the normal form plus optional ISBN.
        """
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

            self.isbn_input.setFocus()

            self.isbn_input.selectAll()

            return False

        return True

    def _build_listing_input(
        self,
    ) -> ListingInput:
        """
        Build the ordinary ListingInput and include ISBN.
        """
        data = (
            super()._build_listing_input()
        )

        data.isbn = (
            self.isbn_input.text()
        )

        return data