from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models import (
    ListingStatus,
)
from app.services.lifecycle_service import (
    archive_listing,
    delete_permanently,
    mark_sold,
    pause_listing,
    restore_to_active,
    set_queue_excluded,
)
from app.services.listing_service import (
    get_listing,
)


class ListingLifecycleDialog(QDialog):
    """
    Manage lifecycle and relisting availability for one listing.
    """

    listing_changed = Signal(int)
    listing_deleted = Signal(int)

    BUTTON_HEIGHT = 40

    def __init__(
        self,
        listing_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.listing_id = listing_id

        self.setWindowTitle(
            "Manage Listing"
        )

        self.setModal(
            True
        )

        self.resize(
            620,
            680,
        )

        self.setMinimumSize(
            540,
            560,
        )

        self._build_ui()
        self._apply_styles()

    def _build_ui(
        self,
    ) -> None:
        listing = get_listing(
            self.listing_id
        )

        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            24,
            24,
            24,
            20,
        )

        root_layout.setSpacing(
            14
        )

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        header = QFrame()

        header.setObjectName(
            "informationBox"
        )

        header_layout = QVBoxLayout(
            header
        )

        header_layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        header_layout.setSpacing(
            8
        )

        title_row = QHBoxLayout()

        title_row.setSpacing(
            12
        )

        title = QLabel(
            listing.title
        )

        title.setObjectName(
            "listingTitle"
        )

        title.setWordWrap(
            True
        )

        status = QLabel(
            listing.status.value.upper()
        )

        status.setObjectName(
            self._status_badge_name(
                listing.status
            )
        )

        status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title_row.addWidget(
            title,
            1,
        )

        title_row.addWidget(
            status,
        )

        header_layout.addLayout(
            title_row
        )

        state_information = QLabel(
            self._build_state_information(
                listing
            )
        )

        state_information.setObjectName(
            "informationText"
        )

        state_information.setWordWrap(
            True
        )

        header_layout.addWidget(
            state_information
        )

        if listing.manually_excluded:
            excluded_label = QLabel(
                (
                    "This listing is currently excluded "
                    "from automatic relisting selection."
                )
            )

            excluded_label.setObjectName(
                "warningText"
            )

            excluded_label.setWordWrap(
                True
            )

            header_layout.addWidget(
                excluded_label
            )

        root_layout.addWidget(
            header
        )

        # -------------------------------------------------
        # Scrollable action area
        # -------------------------------------------------

        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(
            True
        )

        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            0,
            0,
            6,
            0,
        )

        content_layout.setSpacing(
            14
        )

        if (
            listing.status
            == ListingStatus.ACTIVE
        ):
            self._build_active_sections(
                content_layout,
                listing,
            )

        elif (
            listing.status
            == ListingStatus.PAUSED
        ):
            self._build_paused_sections(
                content_layout,
                listing,
            )

        elif (
            listing.status
            == ListingStatus.SOLD
        ):
            self._build_sold_sections(
                content_layout,
            )

        elif (
            listing.status
            == ListingStatus.ARCHIVED
        ):
            self._build_archived_sections(
                content_layout,
            )

        content_layout.addStretch()

        scroll_area.setWidget(
            content
        )

        root_layout.addWidget(
            scroll_area,
            1,
        )

        # -------------------------------------------------
        # Close
        # -------------------------------------------------

        footer = QHBoxLayout()

        footer.addStretch()

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setObjectName(
            "secondaryButton"
        )

        close_button.setMinimumHeight(
            self.BUTTON_HEIGHT
        )

        close_button.setMinimumWidth(
            110
        )

        close_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        close_button.clicked.connect(
            self.reject
        )

        footer.addWidget(
            close_button
        )

        root_layout.addLayout(
            footer
        )

    # =====================================================
    # Active
    # =====================================================

    def _build_active_sections(
        self,
        root: QVBoxLayout,
        listing,
    ) -> None:
        availability = self._create_section(
            title="AVAILABILITY",
            description=(
                "Temporarily remove this listing from "
                "the active relisting rotation."
            ),
        )

        availability_layout = (
            availability.layout()
        )

        pause_row = QHBoxLayout()

        pause_row.setSpacing(
            8
        )

        pause_7 = self._create_action_button(
            "PAUSE 7 DAYS",
            lambda: self._pause(7),
        )

        pause_30 = self._create_action_button(
            "PAUSE 30 DAYS",
            lambda: self._pause(30),
        )

        pause_forever = self._create_action_button(
            "PAUSE INDEFINITELY",
            lambda: self._pause(None),
        )

        pause_row.addWidget(
            pause_7
        )

        pause_row.addWidget(
            pause_30
        )

        pause_row.addWidget(
            pause_forever
        )

        availability_layout.addLayout(
            pause_row
        )

        root.addWidget(
            availability
        )

        root.addWidget(
            self._build_queue_section(
                listing.manually_excluded
            )
        )

        status_section = self._create_section(
            title="LISTING STATUS",
            description=(
                "Use these actions when the item's "
                "overall inventory status changes."
            ),
        )

        status_layout = (
            status_section.layout()
        )

        actions = QHBoxLayout()

        actions.setSpacing(
            8
        )

        sold_button = (
            self._create_action_button(
                "MARK AS SOLD",
                self._mark_sold,
            )
        )

        archive_button = (
            self._create_action_button(
                "ARCHIVE LISTING",
                self._archive,
            )
        )

        actions.addWidget(
            sold_button
        )

        actions.addWidget(
            archive_button
        )

        status_layout.addLayout(
            actions
        )

        root.addWidget(
            status_section
        )

    # =====================================================
    # Paused
    # =====================================================

    def _build_paused_sections(
        self,
        root: QVBoxLayout,
        listing,
    ) -> None:
        availability = self._create_section(
            title="AVAILABILITY",
            description=(
                "This listing is paused and will not be "
                "selected until it becomes active again."
            ),
        )

        availability_layout = (
            availability.layout()
        )

        restore_button = (
            self._create_action_button(
                "RESUME / MAKE ACTIVE",
                self._restore,
                primary=True,
            )
        )

        availability_layout.addWidget(
            restore_button
        )

        root.addWidget(
            availability
        )

        root.addWidget(
            self._build_queue_section(
                listing.manually_excluded
            )
        )

        status_section = self._create_section(
            title="LISTING STATUS",
            description=(
                "You can still mark a paused listing "
                "as sold or move it to the archive."
            ),
        )

        status_layout = (
            status_section.layout()
        )

        actions = QHBoxLayout()

        actions.setSpacing(
            8
        )

        actions.addWidget(
            self._create_action_button(
                "MARK AS SOLD",
                self._mark_sold,
            )
        )

        actions.addWidget(
            self._create_action_button(
                "ARCHIVE LISTING",
                self._archive,
            )
        )

        status_layout.addLayout(
            actions
        )

        root.addWidget(
            status_section
        )

    # =====================================================
    # Sold
    # =====================================================

    def _build_sold_sections(
        self,
        root: QVBoxLayout,
    ) -> None:
        status_section = self._create_section(
            title="LISTING STATUS",
            description=(
                "Sold listings stay stored locally and are "
                "excluded from relisting."
            ),
        )

        status_layout = (
            status_section.layout()
        )

        actions = QHBoxLayout()

        actions.setSpacing(
            8
        )

        actions.addWidget(
            self._create_action_button(
                "RESTORE TO ACTIVE",
                self._restore,
                primary=True,
            )
        )

        actions.addWidget(
            self._create_action_button(
                "ARCHIVE LISTING",
                self._archive,
            )
        )

        status_layout.addLayout(
            actions
        )

        root.addWidget(
            status_section
        )

    # =====================================================
    # Archived
    # =====================================================

    def _build_archived_sections(
        self,
        root: QVBoxLayout,
    ) -> None:
        status_section = self._create_section(
            title="LISTING STATUS",
            description=(
                "Archived listings remain stored locally "
                "but do not participate in relisting."
            ),
        )

        status_layout = (
            status_section.layout()
        )

        status_layout.addWidget(
            self._create_action_button(
                "RESTORE TO ACTIVE",
                self._restore,
                primary=True,
            )
        )

        root.addWidget(
            status_section
        )

        danger_section = self._create_section(
            title="DANGER ZONE",
            description=(
                "Permanent deletion removes this listing, "
                "its stored photos and its relisting history. "
                "This cannot be undone."
            ),
        )

        danger_layout = (
            danger_section.layout()
        )

        delete_button = (
            self._create_action_button(
                "DELETE PERMANENTLY",
                self._delete_permanently,
                destructive=True,
            )
        )

        danger_layout.addWidget(
            delete_button
        )

        root.addWidget(
            danger_section
        )

    # =====================================================
    # Queue section
    # =====================================================

    def _build_queue_section(
        self,
        excluded: bool,
    ) -> QFrame:
        section = self._create_section(
            title="RELISTING QUEUE",
            description=(
                "Control whether the assistant is allowed "
                "to select this item for a future daily queue."
            ),
        )

        layout = section.layout()

        if excluded:
            button = (
                self._create_action_button(
                    "INCLUDE IN RELISTING QUEUE",
                    lambda:
                    self._set_excluded(
                        False
                    ),
                    primary=True,
                )
            )

        else:
            button = (
                self._create_action_button(
                    "EXCLUDE FROM RELISTING QUEUE",
                    lambda:
                    self._set_excluded(
                        True
                    ),
                )
            )

        layout.addWidget(
            button
        )

        return section

    # =====================================================
    # UI helpers
    # =====================================================

    def _create_section(
        self,
        title: str,
        description: str,
    ) -> QFrame:
        frame = QFrame()

        frame.setObjectName(
            "informationBox"
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        layout.setSpacing(
            10
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
            "informationText"
        )

        help_text.setWordWrap(
            True
        )

        layout.addWidget(
            heading
        )

        layout.addWidget(
            help_text
        )

        return frame

    def _create_action_button(
        self,
        text: str,
        callback,
        primary: bool = False,
        destructive: bool = False,
    ) -> QPushButton:
        button = QPushButton(
            text
        )

        button.setMinimumHeight(
            self.BUTTON_HEIGHT
        )

        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        if destructive:
            button.setObjectName(
                "destructiveButton"
            )

        elif primary:
            button.setObjectName(
                "primaryButton"
            )

        else:
            button.setObjectName(
                "actionButton"
            )

        button.clicked.connect(
            callback
        )

        return button

    def _status_badge_name(
        self,
        status: ListingStatus,
    ) -> str:
        if status == ListingStatus.ACTIVE:
            return "activeBadge"

        if status == ListingStatus.PAUSED:
            return "pausedBadge"

        if status == ListingStatus.SOLD:
            return "soldBadge"

        if status == ListingStatus.ARCHIVED:
            return "archivedBadge"

        return "statusBadge"

    def _build_state_information(
        self,
        listing,
    ) -> str:
        if listing.status == ListingStatus.ACTIVE:
            if listing.manually_excluded:
                return (
                    "Active listing, but manually excluded "
                    "from relisting selection."
                )

            return (
                "Active and available for relisting "
                "when it meets your queue rules."
            )

        if listing.status == ListingStatus.PAUSED:
            if listing.paused_indefinitely:
                return (
                    "Paused indefinitely. Restore it to Active "
                    "when you want it available again."
                )

            if listing.paused_until is not None:
                return (
                    "Paused until "
                    f"{listing.paused_until:%d %B %Y}."
                )

            return (
                "This listing is currently paused."
            )

        if listing.status == ListingStatus.SOLD:
            return (
                "Marked as sold. Its information and photos "
                "are still stored locally."
            )

        if listing.status == ListingStatus.ARCHIVED:
            return (
                "Archived locally and excluded from relisting."
            )

        return (
            f"Current status: "
            f"{listing.status.value.capitalize()}"
        )

    # =====================================================
    # Lifecycle actions
    # =====================================================

    def _pause(
        self,
        days: int | None,
    ) -> None:
        try:
            pause_listing(
                self.listing_id,
                days,
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Pause Failed",
                str(exc),
            )

            return

        if days is None:
            text = (
                "Listing paused indefinitely."
            )

        else:
            text = (
                f"Listing paused for {days} days."
            )

        QMessageBox.information(
            self,
            "Listing Paused",
            text,
        )

        self.listing_changed.emit(
            self.listing_id
        )

        self.accept()

    def _restore(
        self,
    ) -> None:
        try:
            restore_to_active(
                self.listing_id
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Restore Failed",
                str(exc),
            )

            return

        QMessageBox.information(
            self,
            "Listing Restored",
            "The listing is active again.",
        )

        self.listing_changed.emit(
            self.listing_id
        )

        self.accept()

    def _set_excluded(
        self,
        excluded: bool,
    ) -> None:
        try:
            set_queue_excluded(
                self.listing_id,
                excluded,
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Update Failed",
                str(exc),
            )

            return

        if excluded:
            message = (
                "The listing has been excluded "
                "from automatic relisting selection."
            )

        else:
            message = (
                "The listing can now be selected "
                "for relisting again."
            )

        QMessageBox.information(
            self,
            "Queue Setting Updated",
            message,
        )

        self.listing_changed.emit(
            self.listing_id
        )

        self.accept()

    def _mark_sold(
        self,
    ) -> None:
        answer = QMessageBox.question(
            self,
            "Mark as Sold",
            (
                "Mark this listing as sold?\n\n"
                "It will leave the relisting rotation, "
                "but its information and photos will be kept."
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
            mark_sold(
                self.listing_id
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Mark Sold",
                str(exc),
            )

            return

        self.listing_changed.emit(
            self.listing_id
        )

        self.accept()

    def _archive(
        self,
    ) -> None:
        answer = QMessageBox.question(
            self,
            "Archive Listing",
            (
                "Archive this listing?\n\n"
                "The listing and all stored photos will "
                "remain on your computer."
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
            archive_listing(
                self.listing_id
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Archive Failed",
                str(exc),
            )

            return

        self.listing_changed.emit(
            self.listing_id
        )

        self.accept()

    def _delete_permanently(
        self,
    ) -> None:
        answer = QMessageBox.warning(
            self,
            "Delete this listing permanently?",
            (
                "Delete this listing permanently?\n\n"
                "This will permanently remove the listing "
                "from the assistant, including its stored "
                "photos and relisting history.\n\n"
                "This cannot be undone."
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
            delete_permanently(
                self.listing_id
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Delete Failed",
                str(exc),
            )

            return

        deleted_id = (
            self.listing_id
        )

        QMessageBox.information(
            self,
            "Listing Deleted",
            (
                "The archived listing was "
                "permanently deleted."
            ),
        )

        self.listing_deleted.emit(
            deleted_id
        )

        self.accept()

    def _apply_styles(
        self,
    ) -> None:
        """
        ThemeManager owns the application appearance.
        """
        return