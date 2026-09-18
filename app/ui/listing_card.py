from __future__ import annotations

from datetime import date

from PySide6.QtCore import (
    Qt,
    QUrl,
    Signal,
)
from PySide6.QtGui import (
    QDesktopServices,
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
from app.ui.image_cache import (
    get_scaled_pixmap,
)
from app.utils.paths import (
    get_listing_photos_directory,
)


class ListingCard(QFrame):
    """
    Compact visual summary for one listing.

    Supports preloaded photo metadata so list pages can avoid
    one database query per card.
    """

    edit_requested = Signal(int)
    manage_requested = Signal(int)

    def __init__(
        self,
        listing: Listing,
        parent: QWidget | None = None,
        photos: list[ListingPhoto] | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.listing = listing
        self._preloaded_photos = photos

        self.setObjectName(
            "listingCard"
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.setMinimumHeight(
            150
        )

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        main_layout = QHBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        main_layout.setSpacing(
            16
        )

        main_layout.addWidget(
            self._create_photo()
        )

        details_layout = QVBoxLayout()

        details_layout.setSpacing(
            5
        )

        details_layout.addLayout(
            self._create_title_row()
        )

        details_layout.addLayout(
            self._create_badge_row()
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

        secondary_information = QLabel(
            self._build_secondary_text()
        )

        secondary_information.setObjectName(
            "dateText"
        )

        secondary_information.setWordWrap(
            True
        )

        secondary_information.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        details_layout.addWidget(
            secondary_information
        )

        details_layout.addStretch()

        main_layout.addLayout(
            details_layout,
            1,
        )

        main_layout.addLayout(
            self._create_actions()
        )

    def _create_title_row(
        self,
    ) -> QHBoxLayout:
        layout = QHBoxLayout()

        layout.setSpacing(
            12
        )

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

        price.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTop
        )

        layout.addWidget(
            title,
            1,
        )

        layout.addWidget(
            price
        )

        return layout

    def _create_badge_row(
        self,
    ) -> QHBoxLayout:
        layout = QHBoxLayout()

        layout.setSpacing(
            6
        )

        status = QLabel(
            self._status_text()
        )

        status.setObjectName(
            self._status_object_name()
        )

        layout.addWidget(
            status
        )

        priority = QLabel(
            self.listing.priority.value.capitalize()
        )

        priority.setObjectName(
            "priorityBadge"
        )

        priority.setToolTip(
            "Relisting priority"
        )

        layout.addWidget(
            priority
        )

        if self.listing.manually_excluded:
            excluded = QLabel(
                "Queue excluded"
            )

            excluded.setObjectName(
                "excludedBadge"
            )

            layout.addWidget(
                excluded
            )

        layout.addStretch()

        return layout

    def _create_photo(
        self,
    ) -> QWidget:
        container = QFrame()

        container.setObjectName(
            "photoContainer"
        )

        container.setFixedSize(
            112,
            112,
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
            112,
            112,
        )

        try:
            if self._preloaded_photos is None:
                photos = get_listing_photos(
                    self.listing.id
                )
            else:
                photos = self._preloaded_photos

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
                thumbnail = get_thumbnail_path(
                    cover
                )

                pixmap = get_scaled_pixmap(
                    thumbnail,
                    104,
                    104,
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
                        pixmap
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

    def _create_actions(
        self,
    ) -> QVBoxLayout:
        layout = QVBoxLayout()

        layout.setSpacing(
            6
        )

        edit_button = QPushButton(
            "EDIT LISTING"
        )

        edit_button.setObjectName(
            "primaryCardButton"
        )

        edit_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        edit_button.setMinimumWidth(
            125
        )

        edit_button.setToolTip(
            "Edit listing information and photos"
        )

        edit_button.clicked.connect(
            lambda: self.edit_requested.emit(
                self.listing.id
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

        manage_button.setMinimumWidth(
            125
        )

        manage_button.setToolTip(
            (
                "Pause, sell, archive, exclude "
                "or manage listing status"
            )
        )

        manage_button.clicked.connect(
            lambda: self.manage_requested.emit(
                self.listing.id
            )
        )

        folder_button = QPushButton(
            "PHOTOS"
        )

        folder_button.setObjectName(
            "secondaryCardButton"
        )

        folder_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        folder_button.setMinimumWidth(
            125
        )

        folder_button.setToolTip(
            "Open this listing's local photo folder"
        )

        folder_button.clicked.connect(
            self._open_photo_folder
        )

        layout.addWidget(
            edit_button
        )

        layout.addWidget(
            manage_button
        )

        layout.addWidget(
            folder_button
        )

        layout.addStretch()

        return layout

    def _status_text(
        self,
    ) -> str:
        if self.listing.paused_indefinitely:
            return "Paused"

        if self.listing.paused_until is not None:
            return (
                "Paused until "
                f"{self.listing.paused_until:%d %b}"
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
        mapping = {
            "active": "activeBadge",
            "paused": "pausedBadge",
            "sold": "soldBadge",
            "archived": "archivedBadge",
        }

        return mapping.get(
            self.listing.status.value,
            "statusBadge",
        )

    def _build_metadata_text(
        self,
    ) -> str:
        values: list[str] = []

        if self.listing.category:
            category = self.listing.category

            if self.listing.subcategory:
                category += (
                    " › "
                    f"{self.listing.subcategory}"
                )

            values.append(
                category
            )

        if self.listing.brand:
            values.append(
                f"Brand: {self.listing.brand}"
            )

        if self.listing.size:
            values.append(
                f"Size: {self.listing.size}"
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
                "No additional listing details"
            )

        return "   •   ".join(
            values
        )

    def _build_secondary_text(
        self,
    ) -> str:
        values: list[str] = []

        if self.listing.isbn:
            values.append(
                f"ISBN: {self.listing.isbn}"
            )

        if self.listing.last_relisted_date is None:
            reference_date = (
                self.listing.original_created_date
            )

            days = max(
                0,
                (
                    date.today()
                    - reference_date
                ).days,
            )

            values.append(
                f"Never relisted · {days} days old"
            )

        else:
            reference_date = (
                self.listing.last_relisted_date
            )

            days = max(
                0,
                (
                    date.today()
                    - reference_date
                ).days,
            )

            values.append(
                (
                    "Last relisted "
                    f"{reference_date:%d %b %Y}"
                    f" · {days} days ago"
                )
            )

        relist_count = (
            self.listing.number_of_times_relisted
        )

        if relist_count == 1:
            values.append(
                "Relisted once"
            )
        else:
            values.append(
                (
                    f"Relisted "
                    f"{relist_count} times"
                )
            )

        return "   •   ".join(
            values
        )

    def _open_photo_folder(
        self,
    ) -> None:
        folder = get_listing_photos_directory(
            self.listing.id
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