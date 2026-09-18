from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models import (
    ListingPhoto,
)
from app.services.listing_service import (
    get_listing_photos_for_listings,
)
from app.services.photo_service import (
    get_listing_photos,
    get_thumbnail_path,
)
from app.services.queue_service import (
    DAILY_RELIST_LIMIT,
    DEFAULT_MINIMUM_RELIST_AGE_DAYS,
    DailyLimitReachedError,
    QueueEntryNotFoundError,
    QueueItem,
    get_today_queue,
    mark_as_relisted,
    skip_today,
)
from app.ui.components.dialogs.message_dialog import (
    BrandedMessageDialog,
)
from app.ui.components.dialogs.error_feedback import (
    log_background_error,
    show_logged_error,
)
from app.ui.components.states.empty_state import (
    FriendlyEmptyState,
)
from app.ui.image_cache import (
    get_scaled_pixmap,
)
from app.ui.components.dialogs.success_dialog import (
    BrandedSuccessDialog,
)


class QueueCard(QFrame):
    """
    Compact card for one listing in Today's Queue.

    Photo metadata can be supplied by the page so the UI
    does not perform one database photo query per card.
    """

    prepare_requested = Signal(int)
    edit_requested = Signal(int)
    relisted_requested = Signal(int)
    skip_requested = Signal(int)

    def __init__(
        self,
        item: QueueItem,
        parent: QWidget | None = None,
        photos: list[ListingPhoto] | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.item = item
        self.listing = item.listing
        self._preloaded_photos = photos

        self.setObjectName(
            "queueCard"
        )

        self.setMinimumHeight(
            142
        )

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        layout.setSpacing(
            16
        )

        layout.addWidget(
            self._create_photo_label()
        )

        details = QVBoxLayout()

        details.setSpacing(
            5
        )

        details.addLayout(
            self._create_title_row()
        )

        details.addLayout(
            self._create_badge_row()
        )

        metadata_text = (
            self._build_metadata_text()
        )

        if metadata_text:
            metadata = QLabel(
                metadata_text
            )

            metadata.setObjectName(
                "metadataText"
            )

            metadata.setWordWrap(
                True
            )

            details.addWidget(
                metadata
            )

        history = QLabel(
            self._build_history_text()
        )

        history.setObjectName(
            "queueDetails"
        )

        history.setWordWrap(
            True
        )

        details.addWidget(
            history
        )

        if self.listing.isbn:
            isbn = QLabel(
                f"ISBN: {self.listing.isbn}"
            )

            isbn.setObjectName(
                "dateText"
            )

            isbn.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

            details.addWidget(
                isbn
            )

        details.addStretch()

        layout.addLayout(
            details,
            1,
        )

        layout.addLayout(
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
            "queueTitle"
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
            "queuePrice"
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

        priority = QLabel(
            (
                self.listing.priority.value.capitalize()
                + " priority"
            )
        )

        priority.setObjectName(
            "priorityBadge"
        )

        layout.addWidget(
            priority
        )

        if self.item.never_relisted:
            never_relisted = QLabel(
                "Never relisted"
            )

            never_relisted.setObjectName(
                "warningBadge"
            )

            layout.addWidget(
                never_relisted
            )

        layout.addStretch()

        return layout

    def _build_metadata_text(
        self,
    ) -> str:
        values: list[str] = []

        if self.listing.category:
            category = (
                self.listing.category
            )

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

        return "   •   ".join(
            values
        )

    def _build_history_text(
        self,
    ) -> str:
        if self.item.never_relisted:
            age_text = (
                f"{self.item.days_since_relisted} "
                "days since original listing"
            )

        else:
            if (
                self.listing.last_relisted_date
                is not None
            ):
                date_text = (
                    self.listing
                    .last_relisted_date
                    .strftime(
                        "%d %b %Y"
                    )
                )

                age_text = (
                    f"Last relisted {date_text}"
                    " · "
                    f"{self.item.days_since_relisted} "
                    "days ago"
                )

            else:
                age_text = (
                    f"{self.item.days_since_relisted} "
                    "days since last refresh"
                )

        count = (
            self.listing
            .number_of_times_relisted
        )

        if count == 1:
            count_text = (
                "Relisted once"
            )

        else:
            count_text = (
                f"Relisted {count} times"
            )

        return (
            f"{age_text}"
            "   •   "
            f"{count_text}"
        )

    def _create_photo_label(
        self,
    ) -> QLabel:
        photo_label = QLabel()

        photo_label.setFixedSize(
            112,
            112,
        )

        photo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        photo_label.setObjectName(
            "queuePhoto"
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
                photo_label.setText(
                    "No Photo"
                )

                return photo_label

            thumbnail = (
                get_thumbnail_path(
                    cover
                )
            )

            pixmap = (
                get_scaled_pixmap(
                    thumbnail,
                    104,
                    104,
                )
            )

            if pixmap.isNull():
                photo_label.setText(
                    "No Preview"
                )

                return photo_label

            photo_label.setPixmap(
                pixmap
            )

        except Exception as exc:
            log_background_error(
                context=(
                    "Unable to load queue listing photo "
                    f"for listing #{self.listing.id}"
                ),
                exception=exc,
            )

            photo_label.setText(
                "Photo unavailable"
            )

        return photo_label

    def _create_actions(
        self,
    ) -> QVBoxLayout:
        layout = QVBoxLayout()

        layout.setSpacing(
            6
        )

        prepare_button = QPushButton(
            "PREPARE LISTING"
        )

        prepare_button.setObjectName(
            "primaryQueueButton"
        )

        prepare_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        prepare_button.setMinimumWidth(
            145
        )

        prepare_button.clicked.connect(
            lambda:
            self.prepare_requested.emit(
                self.listing.id
            )
        )

        edit_button = QPushButton(
            "EDIT LISTING"
        )

        edit_button.setObjectName(
            "secondaryQueueButton"
        )

        edit_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        edit_button.setMinimumWidth(
            145
        )

        edit_button.clicked.connect(
            lambda:
            self.edit_requested.emit(
                self.listing.id
            )
        )

        relisted_button = QPushButton(
            "MARK RELISTED"
        )

        relisted_button.setObjectName(
            "secondaryQueueButton"
        )

        relisted_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        relisted_button.setMinimumWidth(
            145
        )

        relisted_button.clicked.connect(
            lambda:
            self.relisted_requested.emit(
                self.listing.id
            )
        )

        skip_button = QPushButton(
            "SKIP TODAY"
        )

        skip_button.setObjectName(
            "secondaryQueueButton"
        )

        skip_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        skip_button.setMinimumWidth(
            145
        )

        skip_button.clicked.connect(
            lambda:
            self.skip_requested.emit(
                self.listing.id
            )
        )

        layout.addWidget(
            prepare_button
        )

        layout.addWidget(
            edit_button
        )

        layout.addWidget(
            relisted_button
        )

        layout.addWidget(
            skip_button
        )

        layout.addStretch()

        return layout


class DailyQueuePage(QWidget):
    """
    Today's automatically generated manual relisting queue.
    """

    prepare_requested = Signal(int)
    edit_requested = Signal(int)
    queue_changed = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.daily_limit = (
            DAILY_RELIST_LIMIT
        )

        self.minimum_age_days = (
            DEFAULT_MINIMUM_RELIST_AGE_DAYS
        )

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            14
        )

        self._build_summary(
            layout
        )

        self.message_label = QLabel(
            "Loading today's queue..."
        )

        self.message_label.setWordWrap(
            True
        )

        self.message_label.setObjectName(
            "queueMessage"
        )

        layout.addWidget(
            self.message_label
        )

        self.scroll_area = (
            QScrollArea()
        )

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
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
            10
        )

        self.cards_layout.addStretch()

        self.scroll_area.setWidget(
            self.container
        )

        layout.addWidget(
            self.scroll_area,
            1,
        )

    def _build_summary(
        self,
        root_layout: QVBoxLayout,
    ) -> None:
        summary = QFrame()

        summary.setObjectName(
            "queueHeader"
        )

        summary_layout = QVBoxLayout(
            summary
        )

        summary_layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        summary_layout.setSpacing(
            9
        )

        top_row = QHBoxLayout()

        heading = QLabel(
            "TODAY'S PROGRESS"
        )

        heading.setObjectName(
            "panelHeading"
        )

        self.progress_label = QLabel(
            "Completed: —"
        )

        self.progress_label.setObjectName(
            "queueProgress"
        )

        self.ready_label = QLabel(
            "Ready: —"
        )

        self.ready_label.setObjectName(
            "queueProgress"
        )

        self.rule_label = QLabel(
            (
                "Minimum age: "
                f"{self.minimum_age_days} days"
            )
        )

        self.rule_label.setObjectName(
            "queueRule"
        )

        top_row.addWidget(
            heading
        )

        top_row.addSpacing(
            20
        )

        top_row.addWidget(
            self.progress_label
        )

        top_row.addSpacing(
            16
        )

        top_row.addWidget(
            self.ready_label
        )

        top_row.addStretch()

        top_row.addWidget(
            self.rule_label
        )

        summary_layout.addLayout(
            top_row
        )

        self.progress_bar = (
            QProgressBar()
        )

        self.progress_bar.setTextVisible(
            False
        )

        self.progress_bar.setMinimumHeight(
            8
        )

        self.progress_bar.setMaximumHeight(
            8
        )

        self.progress_bar.setRange(
            0,
            max(
                1,
                self.daily_limit,
            ),
        )

        self.progress_bar.setValue(
            0
        )

        summary_layout.addWidget(
            self.progress_bar
        )

        root_layout.addWidget(
            summary
        )

    # =====================================================
    # Queue loading
    # =====================================================

    def refresh(
        self,
    ) -> None:
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
            log_background_error(
                context=(
                    "Unable to load today's relisting queue"
                ),
                exception=exc,
            )

            self.progress_label.setText(
                "Completed: unavailable"
            )

            self.ready_label.setText(
                "Ready: unavailable"
            )

            self.message_label.setText(
                (
                    "Today's queue couldn't be loaded. "
                    "Technical details were saved to the "
                    "application log."
                )
            )

            self.container.setUpdatesEnabled(
                False
            )

            try:
                self._clear_cards()

                self._show_error_state(
                    title=(
                        "Unable to load today's queue"
                    ),
                    message=(
                        "Your listings have not been changed. "
                        "Try opening the page again. If the problem "
                        "continues, restart the app."
                    ),
                )

            finally:
                self.container.setUpdatesEnabled(
                    True
                )

                self.container.update()

            return

        configured_limit = max(
            1,
            snapshot.configured_limit,
        )

        completed = min(
            snapshot.completed_count,
            configured_limit,
        )

        ready_count = len(
            snapshot.queued_items
        )

        self.progress_label.setText(
            (
                "Completed: "
                f"{snapshot.completed_count}"
                "/"
                f"{snapshot.configured_limit}"
            )
        )

        self.ready_label.setText(
            f"Ready: {ready_count}"
        )

        self.rule_label.setText(
            (
                "Minimum age: "
                f"{self.minimum_age_days} days"
            )
        )

        self.progress_bar.setRange(
            0,
            configured_limit,
        )

        self.progress_bar.setValue(
            completed
        )

        if snapshot.is_complete:
            self.message_label.setText(
                "Daily target complete."
            )

            self.container.setUpdatesEnabled(
                False
            )

            try:
                self._clear_cards()

                self._show_friendly_state(
                    title=(
                        "Today's relisting is wrapped up"
                    ),
                    message=(
                        "You reached your daily target. "
                        "Your queue can rest until tomorrow."
                    ),
                )

            finally:
                self.container.setUpdatesEnabled(
                    True
                )

                self.container.update()

            return

        if not snapshot.queued_items:
            self.message_label.setText(
                "No eligible listings right now."
            )

            self.container.setUpdatesEnabled(
                False
            )

            try:
                self._clear_cards()

                self._show_friendly_state(
                    title=(
                        "Nothing needs relisting today"
                    ),
                    message=(
                        "None of your active listings currently "
                        f"meet the {self.minimum_age_days}-day "
                        "relisting rule. Your shop gets a quiet day."
                    ),
                )

            finally:
                self.container.setUpdatesEnabled(
                    True
                )

                self.container.update()

            return

        listing_ids = [
            item.listing.id
            for item in snapshot.queued_items
        ]

        try:
            photos_by_listing = (
                get_listing_photos_for_listings(
                    listing_ids
                )
            )

        except Exception as exc:
            log_background_error(
                context=(
                    "Batch queue photo loading failed; "
                    "falling back to individual photo loading"
                ),
                exception=exc,
            )

            photos_by_listing = None

        remaining = max(
            0,
            (
                snapshot.configured_limit
                - snapshot.completed_count
            ),
        )

        self.message_label.setText(
            (
                f"{ready_count} listing(s) ready. "
                f"{remaining} relist(s) remain "
                "before today's configured limit is reached."
            )
        )

        self.container.setUpdatesEnabled(
            False
        )

        try:
            self._clear_cards()

            for index, item in enumerate(
                snapshot.queued_items
            ):
                if (
                    photos_by_listing
                    is None
                ):
                    photos = None

                else:
                    photos = (
                        photos_by_listing.get(
                            item.listing.id,
                            [],
                        )
                    )

                card = QueueCard(
                    item=item,
                    photos=photos,
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

        finally:
            self.container.setUpdatesEnabled(
                True
            )

            self.container.update()

    # =====================================================
    # Queue actions
    # =====================================================

    def _skip_listing(
        self,
        listing_id: int,
    ) -> None:
        confirmed = (
            BrandedMessageDialog.ask(
                self,
                title="Skip This Listing Today?",
                eyebrow="SKIP FOR TODAY",
                message=(
                    "This listing will be removed from today's "
                    "queue and will not count toward your completed "
                    "daily relist target."
                ),
                detail=(
                    "You can still work with the listing normally "
                    "from All Listings."
                ),
                confirm_text="SKIP TODAY",
                cancel_text="KEEP IT",
            )
        )

        if not confirmed:
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

        except QueueEntryNotFoundError as exc:
            BrandedMessageDialog.notice(
                self,
                title="Listing Is No Longer Queued",
                message=str(
                    exc
                ),
                detail=(
                    "Today's queue will now refresh."
                ),
            )

            self.refresh()

            return

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Skip",
                message=(
                    "The listing could not be skipped right now."
                ),
                context=(
                    "Unable to skip queue listing "
                    f"#{listing_id}"
                ),
                exception=exc,
            )

            return

        self.refresh()

        self.queue_changed.emit()

    def _mark_relisted(
        self,
        listing_id: int,
    ) -> None:
        confirmed = (
            BrandedMessageDialog.ask(
                self,
                title="Mark This Listing as Relisted?",
                eyebrow="CONFIRM RELIST",
                message=(
                    "Only confirm this after you have successfully "
                    "published the listing on Vinted yourself."
                ),
                detail=(
                    "This records the relist locally, updates its "
                    "history, and counts it toward today's target."
                ),
                confirm_text="YES, RELISTED",
                cancel_text="NOT YET",
            )
        )

        if not confirmed:
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
            BrandedMessageDialog.warning(
                self,
                title="Daily Target Already Reached",
                message=str(
                    exc
                ),
                detail=(
                    "Today's queue will refresh using your "
                    "current relisting settings."
                ),
            )

            self.refresh()

            return

        except QueueEntryNotFoundError as exc:
            BrandedMessageDialog.notice(
                self,
                title="Listing Is No Longer Queued",
                message=str(
                    exc
                ),
                detail=(
                    "Today's queue will now refresh."
                ),
            )

            self.refresh()

            return

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Mark as Relisted",
                message=(
                    "The relisting could not be recorded right now."
                ),
                context=(
                    "Unable to mark queue listing "
                    f"#{listing_id} as relisted"
                ),
                exception=exc,
            )

            return

        success_title = (
            "Relisting recorded"
        )

        success_message = (
            "Nice — this listing is now safely recorded "
            "as relisted."
        )

        success_detail = (
            "Your daily progress has been updated."
        )

        try:
            snapshot = get_today_queue(
                configured_limit=(
                    self.daily_limit
                ),
                minimum_age_days=(
                    self.minimum_age_days
                ),
            )

            if snapshot.is_complete:
                success_title = (
                    "Today's target is complete"
                )

                success_message = (
                    "Lovely — that relisting is recorded "
                    "and you've reached today's target."
                )

                success_detail = (
                    "Your queue can rest until tomorrow."
                )

            else:
                remaining = (
                    snapshot.remaining_completions
                )

                if remaining == 1:
                    success_detail = (
                        "1 relist left before today's target."
                    )

                else:
                    success_detail = (
                        f"{remaining} relists left "
                        "before today's target."
                    )

        except Exception as exc:
            log_background_error(
                context=(
                    "Unable to calculate updated queue progress "
                    f"after relisting listing #{listing_id}"
                ),
                exception=exc,
            )

        self.refresh()

        self.queue_changed.emit()

        dialog = BrandedSuccessDialog(
            title=success_title,
            message=success_message,
            detail=success_detail,
            parent=self,
        )

        dialog.exec()

    # =====================================================
    # Friendly / error states
    # =====================================================

    def _show_friendly_state(
        self,
        title: str,
        message: str,
    ) -> None:
        state = FriendlyEmptyState(
            title=title,
            message=message,
        )

        self.cards_layout.insertWidget(
            0,
            state,
        )

    def _show_error_state(
        self,
        title: str,
        message: str,
    ) -> None:
        frame = QFrame()

        frame.setObjectName(
            "errorState"
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        layout.setSpacing(
            7
        )

        heading = QLabel(
            title
        )

        heading.setObjectName(
            "placeholderTitle"
        )

        heading.setWordWrap(
            True
        )

        text = QLabel(
            message
        )

        text.setObjectName(
            "informationText"
        )

        text.setWordWrap(
            True
        )

        log_note = QLabel(
            (
                "Technical details were saved to "
                "the local application log."
            )
        )

        log_note.setObjectName(
            "informationText"
        )

        log_note.setWordWrap(
            True
        )

        layout.addWidget(
            heading
        )

        layout.addWidget(
            text
        )

        layout.addWidget(
            log_note
        )

        self.cards_layout.insertWidget(
            0,
            frame,
        )

    # =====================================================
    # Cleanup
    # =====================================================

    def _clear_cards(
        self,
    ) -> None:
        while (
            self.cards_layout.count()
            > 1
        ):
            item = (
                self.cards_layout.takeAt(
                    0
                )
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

