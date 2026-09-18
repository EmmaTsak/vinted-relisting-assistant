from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services.listing_service import (
    ListingNotFoundError,
    get_listing,
)
from app.services.photo_service import (
    get_listing_photos,
    get_thumbnail_path,
    resolve_photo_path,
)
from app.services.queue_service import (
    DAILY_RELIST_LIMIT,
    DEFAULT_MINIMUM_RELIST_AGE_DAYS,
    DailyLimitReachedError,
    QueueEntryNotFoundError,
    mark_as_relisted,
)
from app.utils.clipboard import copy_text
from app.utils.paths import get_listing_photos_directory


DEFAULT_VINTED_URL = "https://www.vinted.gr/"


class RelistingPreparationDialog(QDialog):
    """
    Dedicated preparation workspace for manually recreating
    a listing on Vinted.

    This dialog never controls or automates the Vinted website.
    """

    relisted = Signal(int)

    def __init__(
        self,
        listing_id: int,
        parent: QWidget | None = None,
        configured_limit: int = DAILY_RELIST_LIMIT,
        minimum_age_days: int = DEFAULT_MINIMUM_RELIST_AGE_DAYS,
        vinted_url: str = DEFAULT_VINTED_URL,
    ) -> None:
        super().__init__(parent)

        self.listing_id = listing_id
        self.configured_limit = configured_limit
        self.minimum_age_days = minimum_age_days
        self.vinted_url = vinted_url

        self.listing = None
        self.photos = []

        self.setWindowTitle(
            "Prepare Listing for Relisting"
        )

        self.resize(
            1180,
            800,
        )

        self.setMinimumSize(
            950,
            650,
        )

        try:
            self.listing = get_listing(
                self.listing_id
            )

            self.photos = get_listing_photos(
                self.listing_id
            )

        except ListingNotFoundError as exc:
            QMessageBox.critical(
                self,
                "Listing Not Found",
                str(exc),
            )

            return

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Load Listing",
                str(exc),
            )

            return

        self._build_ui()
        self._load_photo_gallery()
        self._apply_styles()

    def _build_ui(self) -> None:
        """
        Build the relisting preparation interface.
        """
        if self.listing is None:
            return

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            22,
            22,
            22,
            22,
        )

        main_layout.setSpacing(
            16
        )

        heading_row = QHBoxLayout()

        heading = QLabel(
            "Prepare Listing"
        )

        heading.setObjectName(
            "preparationHeading"
        )

        price = Decimal(
            str(self.listing.price)
        )

        price_label = QLabel(
            f"{price:.2f} {self.listing.currency}"
        )

        price_label.setObjectName(
            "headerPrice"
        )

        heading_row.addWidget(
            heading
        )

        heading_row.addStretch()

        heading_row.addWidget(
            price_label
        )

        main_layout.addLayout(
            heading_row
        )

        subtitle = QLabel(
            (
                "Use this screen to prepare the listing. "
                "You remain responsible for manually uploading "
                "the photos and publishing it on Vinted."
            )
        )

        subtitle.setWordWrap(
            True
        )

        subtitle.setObjectName(
            "subtitle"
        )

        main_layout.addWidget(
            subtitle
        )

        content_layout = QHBoxLayout()

        content_layout.setSpacing(
            22
        )

        content_layout.addWidget(
            self._create_photo_panel()
        )

        content_layout.addWidget(
            self._create_details_panel(),
            1,
        )

        main_layout.addLayout(
            content_layout,
            1,
        )

        bottom_row = QHBoxLayout()

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setObjectName(
            "secondaryButton"
        )

        close_button.clicked.connect(
            self.reject
        )

        copy_full_button = QPushButton(
            "COPY FULL LISTING"
        )

        copy_full_button.setObjectName(
            "secondaryButton"
        )

        copy_full_button.clicked.connect(
            self._copy_full_listing
        )

        open_vinted_button = QPushButton(
            "OPEN VINTED"
        )

        open_vinted_button.setObjectName(
            "secondaryButton"
        )

        open_vinted_button.clicked.connect(
            self._open_vinted
        )

        relisted_button = QPushButton(
            "MARK AS RELISTED"
        )

        relisted_button.setObjectName(
            "primaryButton"
        )

        relisted_button.clicked.connect(
            self._mark_as_relisted
        )

        bottom_row.addWidget(
            close_button
        )

        bottom_row.addStretch()

        bottom_row.addWidget(
            copy_full_button
        )

        bottom_row.addWidget(
            open_vinted_button
        )

        bottom_row.addWidget(
            relisted_button
        )

        main_layout.addLayout(
            bottom_row
        )

    def _create_photo_panel(
        self,
    ) -> QWidget:
        """
        Create the left-side photo gallery.
        """
        panel = QFrame()

        panel.setObjectName(
            "photoPanel"
        )

        panel.setFixedWidth(
            360
        )

        layout = QVBoxLayout(
            panel
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

        title = QLabel(
            "PHOTOS"
        )

        title.setObjectName(
            "sectionTitle"
        )

        layout.addWidget(
            title
        )

        self.large_preview = QLabel(
            "No Photo"
        )

        self.large_preview.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.large_preview.setFixedHeight(
            360
        )

        self.large_preview.setObjectName(
            "largePreview"
        )

        layout.addWidget(
            self.large_preview
        )

        self.photo_list = QListWidget()

        self.photo_list.setViewMode(
            QListWidget.ViewMode.IconMode
        )

        self.photo_list.setIconSize(
            QSize(
                85,
                85,
            )
        )

        self.photo_list.setMovement(
            QListWidget.Movement.Static
        )

        self.photo_list.setResizeMode(
            QListWidget.ResizeMode.Adjust
        )

        self.photo_list.setSpacing(
            7
        )

        self.photo_list.setFixedHeight(
            130
        )

        self.photo_list.currentItemChanged.connect(
            self._photo_selection_changed
        )

        layout.addWidget(
            self.photo_list
        )

        folder_button = QPushButton(
            "OPEN PHOTO FOLDER"
        )

        folder_button.setObjectName(
            "secondaryButton"
        )

        folder_button.clicked.connect(
            self._open_photo_folder
        )

        layout.addWidget(
            folder_button
        )

        return panel

    def _create_details_panel(
        self,
    ) -> QWidget:
        """
        Create the right-side listing information panel.
        """
        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        container = QWidget()

        layout = QVBoxLayout(
            container
        )

        layout.setContentsMargins(
            0,
            0,
            10,
            0,
        )

        layout.setSpacing(
            10
        )

        section_title = QLabel(
            "LISTING DETAILS"
        )

        section_title.setObjectName(
            "sectionTitle"
        )

        layout.addWidget(
            section_title
        )

        listing = self.listing

        if listing is None:
            return scroll

        price = Decimal(
            str(listing.price)
        )

        self._add_detail_field(
            layout,
            "TITLE",
            listing.title,
        )

        self._add_detail_field(
            layout,
            "DESCRIPTION",
            listing.description,
            multiline=True,
        )

        self._add_detail_field(
            layout,
            "PRICE",
            f"{price:.2f} {listing.currency}",
        )

        self._add_optional_field(
            layout,
            "CATEGORY",
            listing.category,
        )

        self._add_optional_field(
            layout,
            "SUBCATEGORY",
            listing.subcategory,
        )

        self._add_optional_field(
            layout,
            "BRAND",
            listing.brand,
        )

        self._add_optional_field(
            layout,
            "SIZE",
            listing.size,
        )

        self._add_optional_field(
            layout,
            "CONDITION",
            listing.condition,
        )

        self._add_optional_field(
            layout,
            "COLOUR",
            listing.colour,
        )

        self._add_optional_field(
            layout,
            "MATERIAL",
            listing.material,
        )

        self._add_optional_field(
            layout,
            "PARCEL SIZE",
            listing.parcel_size,
        )

        if listing.notes:
            self._add_detail_field(
                layout,
                "PRIVATE NOTES",
                listing.notes,
                multiline=True,
            )

        information = QFrame()

        information.setObjectName(
            "informationBox"
        )

        information_layout = QVBoxLayout(
            information
        )

        information_layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        if listing.last_relisted_date:
            last_relisted = (
                listing.last_relisted_date.strftime(
                    "%d %B %Y"
                )
            )
        else:
            last_relisted = "Never"

        information_text = QLabel(
            (
                f"Original listing date: "
                f"{listing.original_created_date:%d %B %Y}\n"
                f"Last relisted: {last_relisted}\n"
                f"Relist count: "
                f"{listing.number_of_times_relisted}\n"
                f"Priority: "
                f"{listing.priority.value.capitalize()}"
            )
        )

        information_text.setObjectName(
            "metadataText"
        )

        information_layout.addWidget(
            information_text
        )

        layout.addWidget(
            information
        )

        layout.addStretch()

        scroll.setWidget(
            container
        )

        return scroll

    def _add_optional_field(
        self,
        layout: QVBoxLayout,
        label: str,
        value: str | None,
    ) -> None:
        """
        Add a field only when the listing has a value.
        """
        if value:
            self._add_detail_field(
                layout,
                label,
                value,
            )

    def _add_detail_field(
        self,
        layout: QVBoxLayout,
        label: str,
        value: str,
        multiline: bool = False,
    ) -> None:
        """
        Create one listing detail with its own Copy button.
        """
        frame = QFrame()

        frame.setObjectName(
            "detailField"
        )

        field_layout = QHBoxLayout(
            frame
        )

        field_layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        text_layout = QVBoxLayout()

        heading = QLabel(
            label
        )

        heading.setObjectName(
            "fieldHeading"
        )

        text_layout.addWidget(
            heading
        )

        if multiline:
            value_widget = QTextEdit()

            value_widget.setPlainText(
                value
            )

            value_widget.setReadOnly(
                True
            )

            value_widget.setMinimumHeight(
                90
            )

            value_widget.setMaximumHeight(
                160
            )

            value_widget.setObjectName(
                "fieldTextEdit"
            )

        else:
            value_widget = QLabel(
                value
            )

            value_widget.setWordWrap(
                True
            )

            value_widget.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

            value_widget.setObjectName(
                "fieldValue"
            )

        text_layout.addWidget(
            value_widget
        )

        field_layout.addLayout(
            text_layout,
            1,
        )

        copy_button = QPushButton(
            "COPY"
        )

        copy_button.setObjectName(
            "copyButton"
        )

        copy_button.setFixedWidth(
            75
        )

        copy_button.clicked.connect(
            lambda checked=False, text=value: (
                self._copy_value(
                    text
                )
            )
        )

        field_layout.addWidget(
            copy_button,
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        layout.addWidget(
            frame
        )

    def _load_photo_gallery(
        self,
    ) -> None:
        """
        Populate the thumbnail strip.
        """
        if not hasattr(
            self,
            "photo_list",
        ):
            return

        self.photo_list.clear()

        if not self.photos:
            self.large_preview.setText(
                "No photos stored"
            )

            return

        cover_index = 0

        for index, photo in enumerate(
            self.photos
        ):
            thumbnail = get_thumbnail_path(
                photo
            )

            item = QListWidgetItem()

            item.setData(
                Qt.ItemDataRole.UserRole,
                photo.id,
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

            if photo.is_cover:
                item.setText(
                    "Cover"
                )

                cover_index = index

            self.photo_list.addItem(
                item
            )

        self.photo_list.setCurrentRow(
            cover_index
        )

        self._show_photo(
            self.photos[
                cover_index
            ]
        )

    def _photo_selection_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        """
        Update the large image when a thumbnail is selected.
        """
        del previous

        if current is None:
            return

        photo_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        for photo in self.photos:
            if photo.id == photo_id:
                self._show_photo(
                    photo
                )

                return

    def _show_photo(
        self,
        photo,
    ) -> None:
        """
        Show one stored image in the large preview.
        """
        path = resolve_photo_path(
            photo
        )

        if not path.exists():
            self.large_preview.clear()

            self.large_preview.setText(
                "Photo file is missing"
            )

            return

        pixmap = QPixmap(
            str(path)
        )

        if pixmap.isNull():
            self.large_preview.clear()

            self.large_preview.setText(
                "Unable to preview image"
            )

            return

        self.large_preview.setPixmap(
            pixmap.scaled(
                330,
                340,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _copy_value(
        self,
        value: str,
    ) -> None:
        """
        Copy a single listing value to the clipboard.
        """
        try:
            copy_text(
                value
            )

        except Exception as exc:
            QMessageBox.warning(
                self,
                "Clipboard Error",
                str(exc),
            )

            return

        self.setWindowTitle(
            "Prepare Listing for Relisting — Copied"
        )

    def _copy_full_listing(
        self,
    ) -> None:
        """
        Copy a human-readable summary of the listing.
        """
        if self.listing is None:
            return

        listing = self.listing

        price = Decimal(
            str(listing.price)
        )

        lines = [
            "TITLE",
            listing.title,
            "",
            "DESCRIPTION",
            listing.description,
            "",
            "PRICE",
            f"{price:.2f} {listing.currency}",
        ]

        optional_values = [
            (
                "CATEGORY",
                listing.category,
            ),
            (
                "SUBCATEGORY",
                listing.subcategory,
            ),
            (
                "BRAND",
                listing.brand,
            ),
            (
                "SIZE",
                listing.size,
            ),
            (
                "CONDITION",
                listing.condition,
            ),
            (
                "COLOUR",
                listing.colour,
            ),
            (
                "MATERIAL",
                listing.material,
            ),
            (
                "PARCEL SIZE",
                listing.parcel_size,
            ),
        ]

        for heading, value in optional_values:
            if value:
                lines.extend(
                    [
                        "",
                        heading,
                        value,
                    ]
                )

        full_text = "\n".join(
            lines
        )

        self._copy_value(
            full_text
        )

    def _open_photo_folder(
        self,
    ) -> None:
        """
        Open this listing's managed photo directory in Windows Explorer.
        """
        folder = get_listing_photos_directory(
            self.listing_id
        )

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(
                str(
                    folder.resolve()
                )
            )
        )

    def _open_vinted(
        self,
    ) -> None:
        """
        Open Vinted in the user's normal browser.

        No website automation is performed.
        """
        QDesktopServices.openUrl(
            QUrl(
                self.vinted_url
            )
        )

    def _mark_as_relisted(
        self,
    ) -> None:
        """
        Record a successful manual republication after confirmation.
        """
        answer = QMessageBox.question(
            self,
            "Mark as Relisted",
            (
                "Have you successfully published this "
                "listing on Vinted?\n\n"
                "Only choose Yes after the listing has "
                "been manually published."
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.Cancel
            ),
            QMessageBox.StandardButton.Cancel,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            mark_as_relisted(
                listing_id=self.listing_id,
                configured_limit=(
                    self.configured_limit
                ),
                minimum_age_days=(
                    self.minimum_age_days
                ),
            )

        except DailyLimitReachedError as exc:
            QMessageBox.warning(
                self,
                "Daily Limit Reached",
                str(exc),
            )

            return

        except QueueEntryNotFoundError as exc:
            QMessageBox.warning(
                self,
                "Queue Entry Not Found",
                str(exc),
            )

            return

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Record Relisting",
                str(exc),
            )

            return

        QMessageBox.information(
            self,
            "Relisting Recorded",
            (
                "The listing was successfully recorded "
                "as relisted."
            ),
        )

        self.relisted.emit(
            self.listing_id
        )

        self.accept()

    def _apply_styles(
        self,
    ) -> None:
        """
        Apply preparation-window styling with explicit text colours
        so Windows dark mode does not make fields unreadable.
        """
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

            #preparationHeading {
                font-size: 26px;
                font-weight: 700;
            }

            #headerPrice {
                font-size: 22px;
                font-weight: 700;
            }

            #subtitle {
                color: #6b7280;
            }

            #sectionTitle {
                font-size: 14px;
                font-weight: 700;
                color: #4b5563;
            }

            #photoPanel {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }

            #largePreview {
                background-color: #f3f4f6;
                color: #9ca3af;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }

            QListWidget {
                background-color: #f9fafb;
                color: #111827;
                border: 1px solid #e5e7eb;
                border-radius: 7px;
            }

            QListWidget::item:selected {
                background-color: #dbeafe;
                color: #111827;
            }

            #detailField {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }

            #fieldHeading {
                color: #6b7280;
                font-size: 11px;
                font-weight: 700;
            }

            #fieldValue {
                color: #111827;
                font-size: 14px;
            }

            #fieldTextEdit {
                background-color: transparent;
                color: #111827;
                border: none;
            }

            #informationBox {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }

            #metadataText {
                color: #4b5563;
            }

            #copyButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 9px;
                font-size: 11px;
                font-weight: 700;
            }

            #copyButton:hover {
                background-color: #f3f4f6;
            }

            #primaryButton {
                background-color: #1f2937;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 16px;
                font-weight: 700;
            }

            #primaryButton:hover {
                background-color: #374151;
            }

            #secondaryButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 7px;
                padding: 10px 16px;
                font-weight: 600;
            }

            #secondaryButton:hover {
                background-color: #f3f4f6;
            }
            """
        )