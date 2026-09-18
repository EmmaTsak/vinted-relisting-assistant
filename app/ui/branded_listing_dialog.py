from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QFileDialog, QWidget

from app.services.listing_service import (
    InvalidISBNError,
    ListingNotFoundError,
    create_listing,
    get_listing,
    normalize_isbn,
    update_listing,
)
from app.services.photo_service import (
    import_photos,
    move_photo,
    remove_photo,
    replace_photo,
    resolve_photo_path,
    rotate_photo,
    set_cover_photo,
    validate_image_file,
)
from app.ui.components.dialogs.message_dialog import BrandedMessageDialog
from app.ui.components.dialogs.error_feedback import show_logged_error
from app.ui.isbn_listing_dialog import ISBNListingDialog
from app.ui.listing_dialog import PhotoPreviewDialog


class BrandedListingDialog(ISBNListingDialog):
    """
    Existing Add/Edit Listing editor with compact branded feedback.

    The form layout and listing logic remain in the existing
    dialog classes. This layer only improves user feedback.
    """

    # =====================================================
    # Validation
    # =====================================================

    def _validate_form(self) -> bool:
        title = self.title_input.text().strip()

        if not title:
            BrandedMessageDialog.warning(
                self,
                title="Missing Title",
                message="Please enter a listing title.",
            )

            self.title_input.setFocus()
            return False

        if self.price_input.value() <= 0:
            BrandedMessageDialog.warning(
                self,
                title="Invalid Price",
                message="Please enter a price greater than â‚¬0.00.",
            )

            self.price_input.setFocus()
            return False

        currency = (
            self.currency_input
            .text()
            .strip()
            .upper()
        )

        if len(currency) != 3:
            BrandedMessageDialog.warning(
                self,
                title="Invalid Currency",
                message="Use a three-letter code such as EUR.",
            )

            self.currency_input.setFocus()
            self.currency_input.selectAll()

            return False

        isbn_text = (
            self.isbn_input
            .text()
            .strip()
        )

        if isbn_text:
            try:
                normalize_isbn(
                    isbn_text
                )

            except InvalidISBNError:
                BrandedMessageDialog.warning(
                    self,
                    title="Invalid ISBN",
                    message="Enter a valid ISBN-10 or ISBN-13.",
                )

                if hasattr(
                    self,
                    "item_details_toggle",
                ):
                    self.item_details_toggle.setChecked(
                        True
                    )

                self.isbn_input.setFocus()
                self.isbn_input.selectAll()

                return False

        return True

    # =====================================================
    # Load listing
    # =====================================================

    def _load_listing(self) -> None:
        if self.listing_id is None:
            return

        try:
            listing = get_listing(
                self.listing_id
            )

        except ListingNotFoundError:
            BrandedMessageDialog.error(
                self,
                title="Listing Not Found",
                message="This listing could not be found.",
            )

            self.reject()
            return

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Load Listing",
                message="The listing could not be loaded.",
                context=(
                    "Unable to load listing "
                    f"#{self.listing_id} in editor"
                ),
                exception=exc,
            )

            self.reject()
            return

        self.title_input.setText(
            listing.title
        )

        self.description_input.setPlainText(
            listing.description
        )

        stored_price = Decimal(
            str(
                listing.price
            )
        )

        self.price_input.setValue(
            float(
                stored_price
            )
        )

        self.currency_input.setText(
            listing.currency
        )

        self.category_input.setText(
            listing.category or ""
        )

        self.subcategory_input.setText(
            listing.subcategory or ""
        )

        self.brand_input.setText(
            listing.brand or ""
        )

        self.size_input.setText(
            listing.size or ""
        )

        self.condition_input.setCurrentText(
            listing.condition or ""
        )

        self.colour_input.setText(
            listing.colour or ""
        )

        self.material_input.setText(
            listing.material or ""
        )

        self.parcel_size_input.setText(
            listing.parcel_size or ""
        )

        priority_index = (
            self.priority_input.findData(
                listing.priority
            )
        )

        if priority_index >= 0:
            self.priority_input.setCurrentIndex(
                priority_index
            )

        original_date = (
            listing.original_created_date
        )

        self.original_date_input.setDate(
            QDate(
                original_date.year,
                original_date.month,
                original_date.day,
            )
        )

        self.notes_input.setPlainText(
            listing.notes or ""
        )

        self.isbn_input.setText(
            listing.isbn or ""
        )

    # =====================================================
    # Save
    # =====================================================

    def _save_listing(self) -> None:
        if not self._validate_form():
            return

        self.save_button.setEnabled(
            False
        )

        try:
            data = (
                self._build_listing_input()
            )

            newly_created = (
                self.listing_id
                is None
            )

            if newly_created:
                self.listing_id = (
                    create_listing(
                        data
                    )
                )

            else:
                update_listing(
                    self.listing_id,
                    data,
                )

            if (
                newly_created
                and self.pending_photos
            ):
                import_photos(
                    self.listing_id,
                    self.pending_photos,
                )

                self.pending_photos.clear()

            saved_listing_id = (
                self.listing_id
            )

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Save",
                message="The listing could not be saved.",
                context=(
                    "Unable to save listing from Add/Edit editor"
                ),
                exception=exc,
            )

            self.save_button.setEnabled(
                True
            )

            return

        self.listing_saved.emit(
            saved_listing_id
        )

        self.accept()

    # =====================================================
    # Adding photos
    # =====================================================

    def _add_photo_paths(
        self,
        paths: list[str],
    ) -> None:
        if not paths:
            return

        valid_paths: list[Path] = []
        skipped_count = 0

        for value in paths:
            try:
                path = validate_image_file(
                    value
                )

                if (
                    path
                    not in self.pending_photos
                ):
                    valid_paths.append(
                        path
                    )

            except Exception:
                skipped_count += 1

        if self.listing_id is None:
            self.pending_photos.extend(
                valid_paths
            )

            self._refresh_photos()

        elif valid_paths:
            try:
                import_photos(
                    self.listing_id,
                    valid_paths,
                )

                self._refresh_photos()

            except Exception as exc:
                show_logged_error(
                    self,
                    title="Unable to Import Photos",
                    message="The photos could not be imported.",
                    context=(
                        "Photo import failed for listing "
                        f"#{self.listing_id}"
                    ),
                    exception=exc,
                )

        if skipped_count:
            word = (
                "photo was"
                if skipped_count == 1
                else "photos were"
            )

            BrandedMessageDialog.notice(
                self,
                title="Some Photos Were Skipped",
                message=(
                    f"{skipped_count} {word} not a supported image."
                ),
            )

    # =====================================================
    # Photo selection / preview
    # =====================================================

    def _selected_photo_data(
        self,
    ) -> dict | None:
        item = (
            self.photo_list.currentItem()
        )

        if item is None:
            BrandedMessageDialog.notice(
                self,
                title="Select a Photo",
                message="Choose a photo first.",
            )

            return None

        return item.data(
            self.photo_list.itemData
            if False
            else 256
        )

    def _preview_selected_photo(
        self,
    ) -> None:
        data = (
            self._selected_photo_data()
        )

        if data is None:
            return

        if data["kind"] == "pending":
            path = Path(
                data["path"]
            )

        else:
            photo = self._get_photo_by_id(
                data["photo_id"]
            )

            if photo is None:
                return

            path = resolve_photo_path(
                photo
            )

        if not path.exists():
            BrandedMessageDialog.warning(
                self,
                title="Photo Missing",
                message="This photo file could not be found.",
            )

            return

        dialog = PhotoPreviewDialog(
            path,
            self,
        )

        dialog.exec()

    # =====================================================
    # Set cover
    # =====================================================

    def _set_selected_cover(
        self,
    ) -> None:
        data = (
            self._selected_photo_data()
        )

        if data is None:
            return

        if data["kind"] == "pending":
            index = data["index"]

            if index != 0:
                photo = self.pending_photos.pop(
                    index
                )

                self.pending_photos.insert(
                    0,
                    photo,
                )

            self._refresh_photos()
            return

        try:
            set_cover_photo(
                data["photo_id"]
            )

            self._refresh_photos()

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Set Cover",
                message="The cover photo could not be changed.",
                context=(
                    "Unable to set cover photo for listing "
                    f"#{self.listing_id}"
                ),
                exception=exc,
            )

    # =====================================================
    # Move photo
    # =====================================================

    def _move_selected_photo(
        self,
        direction: int,
    ) -> None:
        data = (
            self._selected_photo_data()
        )

        if data is None:
            return

        if data["kind"] == "pending":
            index = data["index"]

            target = (
                index
                + direction
            )

            if not (
                0
                <= target
                < len(
                    self.pending_photos
                )
            ):
                return

            self.pending_photos[
                index
            ], self.pending_photos[
                target
            ] = (
                self.pending_photos[
                    target
                ],
                self.pending_photos[
                    index
                ],
            )

            self._refresh_photos()

            self.photo_list.setCurrentRow(
                target
            )

            return

        try:
            move_photo(
                data["photo_id"],
                direction,
            )

            self._refresh_photos()

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Move Photo",
                message="The photo order could not be changed.",
                context=(
                    "Unable to move photo for listing "
                    f"#{self.listing_id}"
                ),
                exception=exc,
            )

    # =====================================================
    # Remove photo
    # =====================================================

    def _remove_selected_photo(
        self,
    ) -> None:
        data = (
            self._selected_photo_data()
        )

        if data is None:
            return

        confirmed = (
            BrandedMessageDialog.ask(
                self,
                title="Remove Photo?",
                message=(
                    "Remove this photo from the assistant?"
                ),
                confirm_text="REMOVE",
                cancel_text="KEEP IT",
            )
        )

        if not confirmed:
            return

        if data["kind"] == "pending":
            self.pending_photos.pop(
                data["index"]
            )

            self._refresh_photos()
            return

        try:
            remove_photo(
                data["photo_id"]
            )

            self._refresh_photos()

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Remove Photo",
                message="The photo could not be removed.",
                context=(
                    "Unable to remove photo for listing "
                    f"#{self.listing_id}"
                ),
                exception=exc,
            )

    # =====================================================
    # Rotate photo
    # =====================================================

    def _rotate_selected_photo(
        self,
        degrees: int,
    ) -> None:
        data = (
            self._selected_photo_data()
        )

        if data is None:
            return

        if data["kind"] == "pending":
            BrandedMessageDialog.notice(
                self,
                title="Save Listing First",
                message=(
                    "Save the listing before rotating its photos."
                ),
            )

            return

        try:
            rotate_photo(
                data["photo_id"],
                degrees,
            )

            self._refresh_photos()

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Rotate Photo",
                message="The photo could not be rotated.",
                context=(
                    "Unable to rotate photo for listing "
                    f"#{self.listing_id}"
                ),
                exception=exc,
            )

    # =====================================================
    # Replace photo
    # =====================================================

    def _replace_selected_photo(
        self,
    ) -> None:
        data = (
            self._selected_photo_data()
        )

        if data is None:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Replacement Photo",
            "",
            "Images (*.jpg *.jpeg *.png *.webp *.bmp)",
        )

        if not file_path:
            return

        if data["kind"] == "pending":
            try:
                replacement = (
                    validate_image_file(
                        file_path
                    )
                )

            except Exception:
                BrandedMessageDialog.warning(
                    self,
                    title="Invalid Photo",
                    message="Choose a supported image file.",
                )

                return

            self.pending_photos[
                data["index"]
            ] = replacement

            self._refresh_photos()
            return

        try:
            replace_photo(
                data["photo_id"],
                file_path,
            )

            self._refresh_photos()

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Replace Photo",
                message="The photo could not be replaced.",
                context=(
                    "Unable to replace photo for listing "
                    f"#{self.listing_id}"
                ),
                exception=exc,
            )

