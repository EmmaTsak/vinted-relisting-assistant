from __future__ import annotations

from datetime import date

from PySide6.QtCore import (
    Qt,
    QUrl,
    Signal,
)
from PySide6.QtGui import (
    QDesktopServices,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models import (
    Listing,
    ListingPhoto,
)
from app.services.photo_service import (
    get_listing_photos,
    get_thumbnail_path,
)
from app.utils.paths import (
    get_listing_photos_directory,
)


class ListingCard(QFrame):
    """
    Visual summary card for one listing.

    Photos can be supplied by the parent page so a large page
    does not make one database query per card.
    """

    edit_requested = Signal(int)
    manage_requested = Signal(int)

    def __init__(
        self,
        listing: Listing,
        photos: list[ListingPhoto] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.listing = listing

        self._preloaded_photos = (
            photos
        )

        self.setObjectName(
            "listingCard"
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.setMinimumHeight(
            195
        )

        self._build_ui()
        self._apply_styles()

    def _build_ui(
        self,
    ) -> None:
        main_layout = QHBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        main_layout.setSpacing(
            20
        )

        photo = self._create_photo()

        main_layout.addWidget(
            photo
        )

        details_layout = (
            QVBoxLayout()
        )

        details_layout.setSpacing(
            6
        )

        title_row = QHBoxLayout()

        title = QLabel(
            self.listing.title
        )

        title.setObjectName(
            "listingTitle"
        )

        title.setWordWrap(
            True
        )

        price = QLabel(
            (
                f"{self.listing.price:.2f} "
                f"{self.listing.currency}"
            )
        )

        price.setObjectName(
            "listingPrice"
        )

        title_row.addWidget(
            title,
            1,
        )

        title_row.addWidget(
            price
        )

        details_layout.addLayout(
            title_row
        )

        status_row = QHBoxLayout()

        status = QLabel(
            self._status_text()
        )

        status.setObjectName(
            self._status_object_name()
        )

        priority = QLabel(
            (
                "Priority: "
                f"{self.listing.priority.value.capitalize()}"
            )
        )

        priority.setObjectName(
            "priorityBadge"
        )

        status_row.addWidget(
            status
        )

        status_row.addWidget(
            priority
        )

        if self.listing.manually_excluded:
            excluded = QLabel(
                "Queue Excluded"
            )

            excluded.setObjectName(
                "excludedBadge"
            )

            status_row.addWidget(
                excluded
            )

        status_row.addStretch()

        details_layout.addLayout(
            status_row
        )

        metadata = QLabel(
            self._build_metadata_text()
        )

        metadata.setObjectName(
            "metadataText"
        )

        metadata.setWordWrap(
            True
        )

        details_layout.addWidget(
            metadata
        )

        dates = QLabel(
            self._build_date_text()
        )

        dates.setObjectName(
            "dateText"
        )

        dates.setWordWrap(
            True
        )

        details_layout.addWidget(
            dates
        )

        details_layout.addStretch()

        main_layout.addLayout(
            details_layout,
            1,
        )

        button_layout = (
            QVBoxLayout()
        )

        button_layout.setSpacing(
            8
        )

        edit_button = QPushButton(
            "EDIT"
        )

        edit_button.setObjectName(
            "primaryCardButton"
        )

        edit_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        edit_button.clicked.connect(
            lambda: (
                self.edit_requested.emit(
                    self.listing.id
                )
            )
        )

        manage_button = QPushButton(
            "MANAGE"
        )

        manage_button.setObjectName(
            "secondaryCardButton"
        )

        manage_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        manage_button.clicked.connect(
            lambda: (
                self.manage_requested.emit(
                    self.listing.id
                )
            )
        )

        folder_button = QPushButton(
            "PHOTO FOLDER"
        )

        folder_button.setObjectName(
            "secondaryCardButton"
        )

        folder_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        folder_button.clicked.connect(
            self._open_photo_folder
        )

        button_layout.addWidget(
            edit_button
        )

        button_layout.addWidget(
            manage_button
        )

        button_layout.addWidget(
            folder_button
        )

        button_layout.addStretch()

        main_layout.addLayout(
            button_layout
        )

    def _status_text(
        self,
    ) -> str:
        if self.listing.paused_indefinitely:
            return (
                "Paused indefinitely"
            )

        if (
            self.listing.paused_until
            is not None
        ):
            return (
                "Paused until "
                f"{self.listing.paused_until:%d %b %Y}"
            )

        return (
            self.listing
            .status
            .value
            .capitalize()
        )

    def _status_object_name(
        self,
    ) -> str:
        status = (
            self.listing.status.value
        )

        mapping = {
            "active": "activeBadge",
            "paused": "pausedBadge",
            "sold": "soldBadge",
            "archived": "archivedBadge",
        }

        return mapping.get(
            status,
            "statusBadge",
        )

    def _create_photo(
        self,
    ) -> QWidget:
        container = QFrame()

        container.setObjectName(
            "photoContainer"
        )

        container.setFixedSize(
            145,
            145,
        )

        layout = QVBoxLayout(
            container
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        label = QLabel()

        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        label.setFixedSize(
            145,
            145,
        )

        try:
            if (
                self._preloaded_photos
                is None
            ):
                photos = (
                    get_listing_photos(
                        self.listing.id
                    )
                )

            else:
                photos = (
                    self._preloaded_photos
                )

            cover = next(
                (
                    photo
                    for photo in photos
                    if photo.is_cover
                ),
                (
                    photos[0]
                    if photos
                    else None
                ),
            )

            if cover is None:
                label.setText(
                    "No Photo"
                )

                label.setObjectName(
                    "noPhoto"
                )

            else:
                thumbnail = (
                    get_thumbnail_path(
                        cover
                    )
                )

                pixmap = QPixmap(
                    str(
                        thumbnail
                    )
                )

                if pixmap.isNull():
                    label.setText(
                        "No Preview"
                    )

                    label.setObjectName(
                        "noPhoto"
                    )

                else:
                    label.setPixmap(
                        pixmap.scaled(
                            135,
                            135,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )

        except Exception:
            label.setText(
                "Photo Error"
            )

            label.setObjectName(
                "noPhoto"
            )

        layout.addWidget(
            label
        )

        return container

    def _build_metadata_text(
        self,
    ) -> str:
        values: list[str] = []

        if self.listing.category:
            values.append(
                self.listing.category
            )

        if self.listing.brand:
            values.append(
                (
                    "Brand: "
                    f"{self.listing.brand}"
                )
            )

        if self.listing.size:
            values.append(
                (
                    "Size: "
                    f"{self.listing.size}"
                )
            )

        if self.listing.condition:
            values.append(
                (
                    "Condition: "
                    f"{self.listing.condition}"
                )
            )

        if self.listing.colour:
            values.append(
                (
                    "Colour: "
                    f"{self.listing.colour}"
                )
            )

        if not values:
            return (
                "No additional listing details."
            )

        return "  •  ".join(
            values
        )

    def _build_date_text(
        self,
    ) -> str:
        original = (
            self.listing.original_created_date
        )

        original_text = (
            original.strftime(
                "%d %b %Y"
            )
        )

        if (
            self.listing.last_relisted_date
            is None
        ):
            last_relisted = "Never"

            days = (
                date.today()
                - original
            ).days

            age_text = (
                f"{days} days since original listing"
            )

        else:
            last_date = (
                self.listing.last_relisted_date
            )

            last_relisted = (
                last_date.strftime(
                    "%d %b %Y"
                )
            )

            days = (
                date.today()
                - last_date
            ).days

            age_text = (
                f"{days} days since last relist"
            )

        return (
            f"Original: {original_text}"
            "   |   "
            f"Last relisted: {last_relisted}"
            "   |   "
            f"{age_text}"
            "   |   "
            "Relisted "
            f"{self.listing.number_of_times_relisted} times"
        )

    def _open_photo_folder(
        self,
    ) -> None:
        folder = (
            get_listing_photos_directory(
                self.listing.id
            )
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

    def _apply_styles(
        self,
    ) -> None:
        self.setStyleSheet(
            """
            #listingCard {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }

            #listingCard:hover {
                border: 1px solid #9ca3af;
            }

            #photoContainer {
                background-color: #f3f4f6;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }

            #noPhoto {
                color: #9ca3af;
                font-size: 13px;
            }

            #listingTitle,
            #listingPrice {
                color: #111827;
                font-size: 18px;
                font-weight: 700;
            }

            #activeBadge {
                background-color: #dcfce7;
                color: #166534;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: 600;
            }

            #pausedBadge {
                background-color: #fef3c7;
                color: #92400e;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: 600;
            }

            #soldBadge {
                background-color: #dbeafe;
                color: #1e40af;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: 600;
            }

            #archivedBadge {
                background-color: #e5e7eb;
                color: #4b5563;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: 600;
            }

            #priorityBadge {
                background-color: #f3f4f6;
                color: #4b5563;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 12px;
            }

            #excludedBadge {
                background-color: #fee2e2;
                color: #991b1b;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: 600;
            }

            #metadataText {
                color: #4b5563;
                font-size: 13px;
            }

            #dateText {
                color: #6b7280;
                font-size: 12px;
            }

            #primaryCardButton {
                background-color: #1f2937;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 13px;
                min-width: 110px;
                font-weight: 600;
            }

            #primaryCardButton:hover {
                background-color: #374151;
            }

            #secondaryCardButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 13px;
                min-width: 110px;
                font-weight: 600;
            }

            #secondaryCardButton:hover {
                background-color: #f3f4f6;
            }
            """
        )