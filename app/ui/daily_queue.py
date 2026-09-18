from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.photo_service import (
    get_listing_photos,
    get_thumbnail_path,
)
from app.services.queue_service import (
    DAILY_RELIST_LIMIT,
    DEFAULT_MINIMUM_RELIST_AGE_DAYS,
    DailyLimitReachedError,
    QueueItem,
    get_today_queue,
    mark_as_relisted,
    skip_today,
)


class QueueCard(QFrame):
    prepare_requested = Signal(int)
    edit_requested = Signal(int)
    relisted_requested = Signal(int)
    skip_requested = Signal(int)

    def __init__(
        self,
        item: QueueItem,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.item = item
        self.listing = item.listing

        self.setObjectName(
            "queueCard"
        )

        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        layout.setSpacing(
            20
        )

        photo_label = QLabel()

        photo_label.setFixedSize(
            150,
            150,
        )

        photo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        photo_label.setObjectName(
            "queuePhoto"
        )

        try:
            photos = get_listing_photos(
                self.listing.id
            )

            cover = next(
                (
                    photo
                    for photo in photos
                    if photo.is_cover
                ),
                photos[0]
                if photos
                else None,
            )

            if cover is None:
                photo_label.setText(
                    "No Photo"
                )

            else:
                thumbnail = get_thumbnail_path(
                    cover
                )

                pixmap = QPixmap(
                    str(thumbnail)
                )

                if pixmap.isNull():
                    photo_label.setText(
                        "No Preview"
                    )

                else:
                    photo_label.setPixmap(
                        pixmap.scaled(
                            140,
                            140,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )

        except Exception:
            photo_label.setText(
                "Photo Error"
            )

        layout.addWidget(
            photo_label
        )

        details = QVBoxLayout()

        title_row = QHBoxLayout()

        title = QLabel(
            self.listing.title
        )

        title.setObjectName(
            "queueTitle"
        )

        title.setWordWrap(True)

        price = QLabel(
            (
                f"{self.listing.price:.2f} "
                f"{self.listing.currency}"
            )
        )

        price.setObjectName(
            "queuePrice"
        )

        title_row.addWidget(
            title,
            1,
        )

        title_row.addWidget(
            price
        )

        details.addLayout(
            title_row
        )

        if self.item.never_relisted:
            last_relisted = (
                "Never relisted"
            )
        else:
            last_relisted = (
                "Last relisted: "
                f"{self.listing.last_relisted_date:%d %b %Y}"
            )

        information = QLabel(
            (
                f"{last_relisted}\n"
                f"Days since refresh: "
                f"{self.item.days_since_relisted}\n"
                f"Relist count: "
                f"{self.listing.number_of_times_relisted}\n"
                f"Priority: "
                f"{self.listing.priority.value.capitalize()}"
            )
        )

        information.setObjectName(
            "queueDetails"
        )

        details.addWidget(
            information
        )

        details.addStretch()

        layout.addLayout(
            details,
            1,
        )

        buttons = QVBoxLayout()

        prepare_button = QPushButton(
            "PREPARE LISTING"
        )

        prepare_button.setObjectName(
            "primaryQueueButton"
        )

        prepare_button.clicked.connect(
            lambda: self.prepare_requested.emit(
                self.listing.id
            )
        )

        edit_button = QPushButton(
            "EDIT LISTING"
        )

        edit_button.setObjectName(
            "secondaryQueueButton"
        )

        edit_button.clicked.connect(
            lambda: self.edit_requested.emit(
                self.listing.id
            )
        )

        relisted_button = QPushButton(
            "MARK AS RELISTED"
        )

        relisted_button.setObjectName(
            "secondaryQueueButton"
        )

        relisted_button.clicked.connect(
            lambda: self.relisted_requested.emit(
                self.listing.id
            )
        )

        skip_button = QPushButton(
            "SKIP TODAY"
        )

        skip_button.setObjectName(
            "secondaryQueueButton"
        )

        skip_button.clicked.connect(
            lambda: self.skip_requested.emit(
                self.listing.id
            )
        )

        buttons.addWidget(
            prepare_button
        )

        buttons.addWidget(
            edit_button
        )

        buttons.addWidget(
            relisted_button
        )

        buttons.addWidget(
            skip_button
        )

        buttons.addStretch()

        layout.addLayout(
            buttons
        )

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #queueCard {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }

            #queuePhoto {
                background-color: #f3f4f6;
                color: #9ca3af;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }

            #queueTitle,
            #queuePrice {
                color: #111827;
                font-size: 18px;
                font-weight: 700;
            }

            #queueDetails {
                color: #4b5563;
                font-size: 13px;
            }

            #primaryQueueButton {
                background-color: #1f2937;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 13px;
                min-width: 150px;
                font-weight: 600;
            }

            #primaryQueueButton:hover {
                background-color: #374151;
            }

            #secondaryQueueButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 9px 13px;
                min-width: 150px;
                font-weight: 600;
            }

            #secondaryQueueButton:hover {
                background-color: #f3f4f6;
            }
            """
        )


class DailyQueuePage(QWidget):
    prepare_requested = Signal(int)
    edit_requested = Signal(int)
    queue_changed = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.daily_limit = (
            DAILY_RELIST_LIMIT
        )

        self.minimum_age_days = (
            DEFAULT_MINIMUM_RELIST_AGE_DAYS
        )

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            14
        )

        header = QFrame()

        header.setObjectName(
            "queueHeader"
        )

        header_layout = QHBoxLayout(
            header
        )

        self.progress_label = QLabel()

        self.progress_label.setObjectName(
            "queueProgress"
        )

        self.rule_label = QLabel(
            (
                "Minimum age: "
                f"{self.minimum_age_days} days"
            )
        )

        refresh_button = QPushButton(
            "REFRESH"
        )

        refresh_button.clicked.connect(
            self.refresh
        )

        header_layout.addWidget(
            self.progress_label
        )

        header_layout.addSpacing(
            20
        )

        header_layout.addWidget(
            self.rule_label
        )

        header_layout.addStretch()

        header_layout.addWidget(
            refresh_button
        )

        layout.addWidget(
            header
        )

        self.message_label = QLabel()

        self.message_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.message_label
        )

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.container = QWidget()

        self.cards_layout = QVBoxLayout(
            self.container
        )

        self.cards_layout.setContentsMargins(
            0,
            0,
            6,
            0,
        )

        self.cards_layout.setSpacing(
            12
        )

        self.cards_layout.addStretch()

        self.scroll_area.setWidget(
            self.container
        )

        layout.addWidget(
            self.scroll_area,
            1,
        )

        self.refresh()

    def refresh(self) -> None:
        self._clear_cards()

        try:
            snapshot = get_today_queue(
                configured_limit=(
                    self.daily_limit
                ),
                minimum_age_days=(
                    self.minimum_age_days
                ),
            )

        except Exception as exc:
            self.progress_label.setText(
                "Queue unavailable"
            )

            self.message_label.setText(
                str(exc)
            )

            return

        self.progress_label.setText(
            (
                "Completed today: "
                f"{snapshot.completed_count}/"
                f"{snapshot.configured_limit}"
            )
        )

        if snapshot.is_complete:
            self.message_label.setText(
                (
                    "Today's relisting queue is complete. "
                    "No additional listings will be generated "
                    "until the next calendar day."
                )
            )

            self._show_empty_message(
                "Today's relisting queue is complete."
            )

            return

        if not snapshot.queued_items:
            self.message_label.setText(
                (
                    "There are currently no eligible listings."
                )
            )

            self._show_empty_message(
                "No eligible listings are available today."
            )

            return

        self.message_label.setText(
            (
                f"{len(snapshot.queued_items)} listing(s) "
                "are ready for manual relisting."
            )
        )

        for index, item in enumerate(
            snapshot.queued_items
        ):
            card = QueueCard(
                item
            )

            card.prepare_requested.connect(
                self.prepare_requested.emit
            )

            card.edit_requested.connect(
                self.edit_requested.emit
            )

            card.skip_requested.connect(
                self._skip_listing
            )

            card.relisted_requested.connect(
                self._mark_relisted
            )

            self.cards_layout.insertWidget(
                index,
                card,
            )

    def _skip_listing(
        self,
        listing_id: int,
    ) -> None:
        answer = QMessageBox.question(
            self,
            "Skip Today",
            (
                "Skip this listing for today?\n\n"
                "It will not count toward the daily limit."
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
            skip_today(
                listing_id=listing_id,
                configured_limit=(
                    self.daily_limit
                ),
                minimum_age_days=(
                    self.minimum_age_days
                ),
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Skip",
                str(exc),
            )

            return

        self.refresh()

        self.queue_changed.emit()

    def _mark_relisted(
        self,
        listing_id: int,
    ) -> None:
        answer = QMessageBox.question(
            self,
            "Mark as Relisted",
            (
                "Have you successfully published this "
                "listing on Vinted?"
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
                listing_id=listing_id,
                configured_limit=(
                    self.daily_limit
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

            self.refresh()

            return

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Mark as Relisted",
                str(exc),
            )

            return

        QMessageBox.information(
            self,
            "Relisting Recorded",
            "Relisting recorded successfully.",
        )

        self.refresh()

        self.queue_changed.emit()

    def _show_empty_message(
        self,
        text: str,
    ) -> None:
        label = QLabel(
            text
        )

        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        label.setWordWrap(
            True
        )

        self.cards_layout.insertWidget(
            0,
            label,
        )

    def _clear_cards(self) -> None:
        while (
            self.cards_layout.count()
            > 1
        ):
            item = self.cards_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()