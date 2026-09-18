from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import (
    QDate,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QIcon,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models import (
    ListingPhoto,
    ListingPriority,
)
from app.services.listing_service import (
    ListingInput,
    ListingNotFoundError,
    create_listing,
    get_listing,
    update_listing,
)
from app.services.photo_service import (
    SUPPORTED_IMAGE_EXTENSIONS,
    get_listing_photos,
    get_thumbnail_path,
    import_photos,
    move_photo,
    remove_photo,
    replace_photo,
    resolve_photo_path,
    rotate_photo,
    set_cover_photo,
    validate_image_file,
)


from app.services.listing_service import (
    InvalidISBNError,
    normalize_isbn,
)

from app.ui.components.dialogs.error_feedback import (
    show_logged_error,
)
from app.ui.components.dialogs.message_dialog import (
    BrandedMessageDialog,
)

from app.ui.dialog_geometry import (
    fit_dialog_to_screen,
)

class PhotoListWidget(QListWidget):
    """
    Thumbnail list supporting files dragged in from Windows Explorer.
    """

    files_dropped = Signal(list)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setAcceptDrops(True)

        self.setDragDropMode(
            QAbstractItemView.DragDropMode.DropOnly
        )

        self.setViewMode(
            QListWidget.ViewMode.IconMode
        )

        self.setResizeMode(
            QListWidget.ResizeMode.Adjust
        )

        self.setMovement(
            QListWidget.Movement.Static
        )

        self.setIconSize(
            QSize(
                120,
                120,
            )
        )

        self.setSpacing(10)

        self.setMinimumHeight(
            185
        )

    def dragEnterEvent(
        self,
        event,
    ) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(
                event
            )

    def dragMoveEvent(
        self,
        event,
    ) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(
                event
            )

    def dropEvent(
        self,
        event,
    ) -> None:
        if not event.mimeData().hasUrls():
            super().dropEvent(
                event
            )
            return

        paths: list[str] = []

        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue

            path = Path(
                url.toLocalFile()
            )

            if (
                path.suffix.lower()
                in SUPPORTED_IMAGE_EXTENSIONS
            ):
                paths.append(
                    str(path)
                )

        if paths:
            self.files_dropped.emit(
                paths
            )

        event.acceptProposedAction()


class PhotoPreviewDialog(QDialog):
    """
    Simple full-size local image preview.
    """

    def __init__(
        self,
        photo_path: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(
            photo_path.name
        )

        self.resize(
            900,
            700,
        )

        layout = QVBoxLayout(
            self
        )

        label = QLabel()

        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        pixmap = QPixmap(
            str(photo_path)
        )

        if pixmap.isNull():
            label.setText(
                "Unable to preview this image."
            )

        else:
            label.setPixmap(
                pixmap.scaled(
                    850,
                    640,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        layout.addWidget(
            label,
            1,
        )


class ListingDialog(QDialog):
    """
    Add/Edit listing dialog with local photo management.
    """

    listing_saved = Signal(int)

    def __init__(
        self,
        parent: QWidget | None = None,
        listing_id: int | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.listing_id = (
            listing_id
        )

        self.pending_photos: list[
            Path
        ] = []

        self.setModal(True)

        self.resize(
            850,
            900,
        )

        self.setMinimumSize(
            700,
            700,
        )

        if self.listing_id is None:
            self.setWindowTitle(
                "Add Listing"
            )
        else:
            self.setWindowTitle(
                "Edit Listing"
            )

        self._build_ui()
        self._apply_styles()

        if (
            self.listing_id
            is not None
        ):
            self._load_listing()
            self._refresh_photos()

        fit_dialog_to_screen(
            self,
            preferred_width=1000,
            preferred_height=720,
            minimum_width=680,
            minimum_height=500,
            width_ratio=0.90,
            height_ratio=0.84,
        )

    def _listing_base_build_ui(
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
            (
                "Add Listing"
                if self.listing_id is None
                else "Edit Listing"
            )
        )

        heading.setObjectName(
            "dialogHeading"
        )

        subtitle = QLabel(
            (
                "Enter listing information and keep "
                "a local copy of its photos."
            )
        )

        subtitle.setObjectName(
            "dialogSubtitle"
        )

        main_layout.addWidget(
            heading
        )

        main_layout.addWidget(
            subtitle
        )

        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(
            True
        )

        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        form_container = QWidget()

        content_layout = QVBoxLayout(
            form_container
        )

        content_layout.setContentsMargins(
            4,
            12,
            12,
            12,
        )

        photo_frame = QFrame()

        photo_frame.setObjectName(
            "photoSection"
        )

        photo_layout = QVBoxLayout(
            photo_frame
        )

        photo_title = QLabel(
            "Photos"
        )

        photo_title.setObjectName(
            "sectionHeading"
        )

        photo_help = QLabel(
            (
                "Add several photos at once or drag them "
                "from Windows Explorer into the box below. "
                "The application stores its own local copy."
            )
        )

        photo_help.setWordWrap(
            True
        )

        photo_help.setObjectName(
            "helpText"
        )

        self.photo_list = (
            PhotoListWidget()
        )

        self.photo_list.files_dropped.connect(
            self._add_photo_paths
        )

        self.photo_list.itemDoubleClicked.connect(
            lambda _: self._preview_selected_photo()
        )

        photo_buttons_1 = QHBoxLayout()
        photo_buttons_2 = QHBoxLayout()

        add_photos_button = QPushButton(
            "Add Photos"
        )

        add_photos_button.clicked.connect(
            self._choose_photos
        )

        self.preview_button = QPushButton(
            "Preview"
        )

        self.preview_button.clicked.connect(
            self._preview_selected_photo
        )

        self.cover_button = QPushButton(
            "Set Cover"
        )

        self.cover_button.clicked.connect(
            self._set_selected_cover
        )

        self.remove_photo_button = QPushButton(
            "Remove"
        )

        self.remove_photo_button.clicked.connect(
            self._remove_selected_photo
        )

        self.move_left_button = QPushButton(
            "Move Left"
        )

        self.move_left_button.clicked.connect(
            lambda: self._move_selected_photo(
                -1
            )
        )

        self.move_right_button = QPushButton(
            "Move Right"
        )

        self.move_right_button.clicked.connect(
            lambda: self._move_selected_photo(
                1
            )
        )

        self.rotate_left_button = QPushButton(
            "Rotate Left"
        )

        self.rotate_left_button.clicked.connect(
            lambda: self._rotate_selected_photo(
                -90
            )
        )

        self.rotate_right_button = QPushButton(
            "Rotate Right"
        )

        self.rotate_right_button.clicked.connect(
            lambda: self._rotate_selected_photo(
                90
            )
        )

        self.replace_button = QPushButton(
            "Replace"
        )

        self.replace_button.clicked.connect(
            self._replace_selected_photo
        )

        for button in (
            add_photos_button,
            self.preview_button,
            self.cover_button,
            self.remove_photo_button,
        ):
            button.setObjectName(
                "photoButton"
            )

            photo_buttons_1.addWidget(
                button
            )

        for button in (
            self.move_left_button,
            self.move_right_button,
            self.rotate_left_button,
            self.rotate_right_button,
            self.replace_button,
        ):
            button.setObjectName(
                "photoButton"
            )

            photo_buttons_2.addWidget(
                button
            )

        photo_layout.addWidget(
            photo_title
        )

        photo_layout.addWidget(
            photo_help
        )

        photo_layout.addWidget(
            self.photo_list
        )

        photo_layout.addLayout(
            photo_buttons_1
        )

        photo_layout.addLayout(
            photo_buttons_2
        )

        content_layout.addWidget(
            photo_frame
        )

        content_layout.addSpacing(
            15
        )

        form_layout = QFormLayout()

        form_layout.setHorizontalSpacing(
            18
        )

        form_layout.setVerticalSpacing(
            14
        )

        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.title_input = QLineEdit()

        self.title_input.setMaxLength(
            255
        )

        self.title_input.setPlaceholderText(
            "e.g. Vintage black handbag"
        )

        self.description_input = QTextEdit()

        self.description_input.setPlaceholderText(
            "Listing description..."
        )

        self.description_input.setMinimumHeight(
            120
        )

        self.price_input = QDoubleSpinBox()

        self.price_input.setDecimals(
            2
        )

        self.price_input.setMinimum(
            0.00
        )

        self.price_input.setMaximum(
            9_999_999.99
        )

        self.price_input.setPrefix(
            "€ "
        )

        self.currency_input = QLineEdit(
            "EUR"
        )

        self.currency_input.setMaxLength(
            3
        )

        self.currency_input.setMaximumWidth(
            90
        )

        self.category_input = QLineEdit()
        self.subcategory_input = QLineEdit()
        self.brand_input = QLineEdit()
        self.size_input = QLineEdit()

        self.condition_input = QComboBox()

        self.condition_input.setEditable(
            True
        )

        self.condition_input.addItems(
            [
                "",
                "New with tags",
                "New without tags",
                "Very good",
                "Good",
                "Satisfactory",
            ]
        )

        self.colour_input = QLineEdit()
        self.material_input = QLineEdit()
        self.parcel_size_input = QLineEdit()

        self.priority_input = QComboBox()

        self.priority_input.addItem(
            "High",
            ListingPriority.HIGH,
        )

        self.priority_input.addItem(
            "Normal",
            ListingPriority.NORMAL,
        )

        self.priority_input.addItem(
            "Low",
            ListingPriority.LOW,
        )

        self.priority_input.setCurrentIndex(
            1
        )

        self.original_date_input = QDateEdit()

        self.original_date_input.setCalendarPopup(
            True
        )

        self.original_date_input.setDisplayFormat(
            "dd MMMM yyyy"
        )

        today = date.today()

        self.original_date_input.setDate(
            QDate(
                today.year,
                today.month,
                today.day,
            )
        )

        self.notes_input = QTextEdit()

        self.notes_input.setMinimumHeight(
            90
        )

        self.notes_input.setPlaceholderText(
            "Private notes..."
        )

        form_layout.addRow(
            "Title *",
            self.title_input,
        )

        form_layout.addRow(
            "Description",
            self.description_input,
        )

        form_layout.addRow(
            "Price *",
            self.price_input,
        )

        form_layout.addRow(
            "Currency",
            self.currency_input,
        )

        form_layout.addRow(
            "Category",
            self.category_input,
        )

        form_layout.addRow(
            "Subcategory",
            self.subcategory_input,
        )

        form_layout.addRow(
            "Brand",
            self.brand_input,
        )

        form_layout.addRow(
            "Size",
            self.size_input,
        )

        form_layout.addRow(
            "Condition",
            self.condition_input,
        )

        form_layout.addRow(
            "Colour",
            self.colour_input,
        )

        form_layout.addRow(
            "Material",
            self.material_input,
        )

        form_layout.addRow(
            "Parcel Size",
            self.parcel_size_input,
        )

        form_layout.addRow(
            "Priority",
            self.priority_input,
        )

        form_layout.addRow(
            "Original Listing Date",
            self.original_date_input,
        )

        form_layout.addRow(
            "Notes",
            self.notes_input,
        )

        content_layout.addLayout(
            form_layout
        )

        scroll_area.setWidget(
            form_container
        )

        main_layout.addWidget(
            scroll_area,
            1,
        )

        button_layout = QHBoxLayout()

        button_layout.addStretch()

        cancel_button = QPushButton(
            "Cancel"
        )

        cancel_button.setObjectName(
            "cancelButton"
        )

        cancel_button.clicked.connect(
            self.reject
        )

        self.save_button = QPushButton(
            (
                "Save Listing"
                if self.listing_id is None
                else "Save Changes"
            )
        )

        self.save_button.setObjectName(
            "saveButton"
        )

        self.save_button.clicked.connect(
            self._save_listing
        )

        button_layout.addWidget(
            cancel_button
        )

        button_layout.addWidget(
            self.save_button
        )

        main_layout.addLayout(
            button_layout
        )

    def _choose_photos(
        self,
    ) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose Listing Photos",
            "",
            (
                "Images "
                "(*.jpg *.jpeg *.png *.webp *.bmp)"
            ),
        )

        self._add_photo_paths(
            paths
        )

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
            if skipped_count == 1:
                message = (
                    "1 photo was not a supported image."
                )

            else:
                message = (
                    f"{skipped_count} photos were not supported images."
                )

            BrandedMessageDialog.notice(
                self,
                title="Some Photos Were Skipped",
                message=message,
            )

    def _refresh_photos(
        self,
    ) -> None:
        self.photo_list.clear()

        if self.listing_id is None:
            for index, path in enumerate(
                self.pending_photos
            ):
                item = QListWidgetItem(
                    path.name
                )

                pixmap = QPixmap(
                    str(path)
                )

                if not pixmap.isNull():
                    item.setIcon(
                        QIcon(
                            pixmap.scaled(
                                120,
                                120,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                        )
                    )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    {
                        "kind": "pending",
                        "index": index,
                        "path": str(path),
                    },
                )

                if index == 0:
                    item.setText(
                        f"★ {path.name}"
                    )

                self.photo_list.addItem(
                    item
                )

            return

        photos = get_listing_photos(
            self.listing_id
        )

        for photo in photos:
            thumbnail = (
                get_thumbnail_path(
                    photo
                )
            )

            title = thumbnail.name

            if photo.is_cover:
                title = (
                    f"★ {title}"
                )

            item = QListWidgetItem(
                title
            )

            pixmap = QPixmap(
                str(thumbnail)
            )

            if not pixmap.isNull():
                item.setIcon(
                    QIcon(
                        pixmap
                    )
                )

            item.setData(
                Qt.ItemDataRole.UserRole,
                {
                    "kind": "stored",
                    "photo_id": photo.id,
                },
            )

            self.photo_list.addItem(
                item
            )

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
            Qt.ItemDataRole.UserRole
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
                message="Remove this photo from the assistant?",
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
                message="Save the listing before rotating its photos.",
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

    def _replace_selected_photo(
        self,
    ) -> None:
        data = (
            self._selected_photo_data()
        )

        if data is None:
            return

        file_path, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Choose Replacement Photo",
                "",
                "Images (*.jpg *.jpeg *.png *.webp *.bmp)",
            )
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

    def _get_photo_by_id(
        self,
        photo_id: int,
    ) -> ListingPhoto | None:
        if self.listing_id is None:
            return None

        photos = get_listing_photos(
            self.listing_id
        )

        for photo in photos:
            if photo.id == photo_id:
                return photo

        return None

    def _listing_base_load_listing(
        self,
    ) -> None:
        """
        Load an existing listing into the edit form.

        Existing price values are explicitly converted through Decimal
        so opening Edit never resets a valid stored price to zero.
        """
        if self.listing_id is None:
            return

        try:
            listing = get_listing(
                self.listing_id
            )

        except ListingNotFoundError as exc:
            QMessageBox.critical(
                self,
                "Listing Not Found",
                str(exc),
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
            str(listing.price)
        )

        self.price_input.setValue(
            float(stored_price)
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

    def _listing_base_validate_form(
        self,
    ) -> bool:
        if not (
            self.title_input
            .text()
            .strip()
        ):
            QMessageBox.warning(
                self,
                "Missing Title",
                "Please enter a listing title.",
            )

            return False

        if (
            self.price_input.value()
            <= 0
        ):
            QMessageBox.warning(
                self,
                "Invalid Price",
                (
                    "Please enter a price "
                    "greater than €0.00."
                ),
            )

            return False

        currency = (
            self.currency_input
            .text()
            .strip()
            .upper()
        )

        if len(
            currency
        ) != 3:
            QMessageBox.warning(
                self,
                "Invalid Currency",
                (
                    "Currency must use a "
                    "three-letter code such as EUR."
                ),
            )

            return False

        return True

    def _listing_base_build_listing_input(
        self,
    ) -> ListingInput:
        return ListingInput(
            title=self.title_input.text(),
            description=(
                self.description_input
                .toPlainText()
            ),
            price=Decimal(
                f"{self.price_input.value():.2f}"
            ),
            currency=(
                self.currency_input.text()
            ),
            category=(
                self.category_input.text()
            ),
            subcategory=(
                self.subcategory_input.text()
            ),
            brand=(
                self.brand_input.text()
            ),
            size=(
                self.size_input.text()
            ),
            condition=(
                self.condition_input
                .currentText()
            ),
            colour=(
                self.colour_input.text()
            ),
            material=(
                self.material_input.text()
            ),
            parcel_size=(
                self.parcel_size_input.text()
            ),
            notes=(
                self.notes_input
                .toPlainText()
            ),
            original_created_date=(
                self.original_date_input
                .date()
                .toPython()
            ),
            priority=(
                self.priority_input
                .currentData()
            ),
        )

    def _save_listing(
        self,
    ) -> None:
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

    def _apply_styles(
        self,
    ) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background-color: #f5f6f8;
                color: #111827;
            }

            QWidget {
                font-family: "Segoe UI";
                font-size: 14px;
                color: #111827;
            }

            #dialogHeading {
                font-size: 24px;
                font-weight: 700;
            }

            #dialogSubtitle,
            #helpText {
                color: #6b7280;
            }

            #sectionHeading {
                font-size: 18px;
                font-weight: 600;
            }

            #photoSection {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 9px;
                padding: 10px;
            }

            QListWidget {
                background-color: #f9fafb;
                border: 1px dashed #9ca3af;
                border-radius: 8px;
                padding: 8px;
            }

            QListWidget::item:selected {
                background-color: #dbeafe;
                color: #111827;
                border-radius: 6px;
            }

            QLineEdit,
            QTextEdit,
            QComboBox,
            QDateEdit,
            QDoubleSpinBox {
                background-color: white;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 7px;
            }

            #photoButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 7px 10px;
            }

            #photoButton:hover {
                background-color: #f3f4f6;
            }

            #saveButton {
                background-color: #1f2937;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 18px;
                font-weight: 600;
            }

            #saveButton:hover {
                background-color: #374151;
            }

            #saveButton:disabled {
                background-color: #9ca3af;
            }

            #cancelButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 7px;
                padding: 10px 18px;
            }
            """
        )

    FIELD_HEIGHT = 40

    def _build_ui(
        self,
    ) -> None:
        """
        Build the normal listing editor first, then apply
        ISBN support and the cleaner collapsible layout.
        """
        self._listing_base_build_ui()

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

    def _load_listing(
        self,
    ) -> None:
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

    def _validate_form(
        self,
    ) -> bool:
        title = (
            self.title_input
            .text()
            .strip()
        )

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
                message="Please enter a price greater than €0.00.",
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

    def _build_listing_input(
        self,
    ) -> ListingInput:
        data = (
            self._listing_base_build_listing_input()
        )

        data.isbn = (
            self.isbn_input.text()
        )

        return data
