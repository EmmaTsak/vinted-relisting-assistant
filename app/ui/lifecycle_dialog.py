from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models import ListingStatus
from app.services.lifecycle_service import (
    archive_listing,
    delete_permanently,
    mark_sold,
    pause_listing,
    restore_to_active,
    set_queue_excluded,
)
from app.services.listing_service import get_listing


class ListingLifecycleDialog(QDialog):
    """
    Manage sold/archive/pause state for one listing.
    """

    listing_changed = Signal(int)
    listing_deleted = Signal(int)

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

        self.resize(
            470,
            560,
        )

        self.setMinimumWidth(
            430
        )

        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        listing = get_listing(
            self.listing_id
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        layout.setSpacing(
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

        layout.addWidget(
            title
        )

        status = QLabel(
            (
                "Current status: "
                f"{listing.status.value.capitalize()}"
            )
        )

        status.setObjectName(
            "currentStatus"
        )

        layout.addWidget(
            status
        )

        if listing.paused_indefinitely:
            pause_information = QLabel(
                "Paused indefinitely"
            )

            pause_information.setObjectName(
                "informationText"
            )

            layout.addWidget(
                pause_information
            )

        elif listing.paused_until is not None:
            pause_information = QLabel(
                (
                    "Paused until: "
                    f"{listing.paused_until:%d %B %Y}"
                )
            )

            pause_information.setObjectName(
                "informationText"
            )

            layout.addWidget(
                pause_information
            )

        if listing.manually_excluded:
            exclusion = QLabel(
                "Excluded from automatic relisting queue"
            )

            exclusion.setObjectName(
                "warningText"
            )

            layout.addWidget(
                exclusion
            )

        separator = QFrame()

        separator.setFrameShape(
            QFrame.Shape.HLine
        )

        layout.addWidget(
            separator
        )

        if listing.status == ListingStatus.ACTIVE:
            self._add_button(
                layout,
                "PAUSE 7 DAYS",
                lambda: self._pause(7),
            )

            self._add_button(
                layout,
                "PAUSE 30 DAYS",
                lambda: self._pause(30),
            )

            self._add_button(
                layout,
                "PAUSE INDEFINITELY",
                lambda: self._pause(None),
            )

            if listing.manually_excluded:
                self._add_button(
                    layout,
                    "INCLUDE IN RELISTING QUEUE",
                    lambda: self._set_excluded(
                        False
                    ),
                )

            else:
                self._add_button(
                    layout,
                    "EXCLUDE FROM RELISTING QUEUE",
                    lambda: self._set_excluded(
                        True
                    ),
                )

            self._add_button(
                layout,
                "MARK AS SOLD",
                self._mark_sold,
            )

            self._add_button(
                layout,
                "ARCHIVE LISTING",
                self._archive,
            )

        elif listing.status == ListingStatus.PAUSED:
            self._add_button(
                layout,
                "RESUME / MAKE ACTIVE",
                self._restore,
                primary=True,
            )

            if listing.manually_excluded:
                self._add_button(
                    layout,
                    "INCLUDE IN RELISTING QUEUE",
                    lambda: self._set_excluded(
                        False
                    ),
                )

            else:
                self._add_button(
                    layout,
                    "EXCLUDE FROM RELISTING QUEUE",
                    lambda: self._set_excluded(
                        True
                    ),
                )

            self._add_button(
                layout,
                "MARK AS SOLD",
                self._mark_sold,
            )

            self._add_button(
                layout,
                "ARCHIVE LISTING",
                self._archive,
            )

        elif listing.status == ListingStatus.SOLD:
            self._add_button(
                layout,
                "RESTORE TO ACTIVE",
                self._restore,
                primary=True,
            )

            self._add_button(
                layout,
                "ARCHIVE LISTING",
                self._archive,
            )

        elif listing.status == ListingStatus.ARCHIVED:
            information = QLabel(
                (
                    "Archived listings remain stored locally. "
                    "Permanent deletion is available only here."
                )
            )

            information.setWordWrap(
                True
            )

            information.setObjectName(
                "informationText"
            )

            layout.addWidget(
                information
            )

            self._add_button(
                layout,
                "RESTORE TO ACTIVE",
                self._restore,
                primary=True,
            )

            self._add_button(
                layout,
                "DELETE PERMANENTLY",
                self._delete_permanently,
                destructive=True,
            )

        layout.addStretch()

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setObjectName(
            "secondaryButton"
        )

        close_button.clicked.connect(
            self.reject
        )

        layout.addWidget(
            close_button
        )

    def _add_button(
        self,
        layout: QVBoxLayout,
        text: str,
        callback,
        primary: bool = False,
        destructive: bool = False,
    ) -> None:
        button = QPushButton(
            text
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

        layout.addWidget(
            button
        )

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

    def _restore(self) -> None:
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

    def _mark_sold(self) -> None:
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

    def _archive(self) -> None:
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

    def _delete_permanently(self) -> None:
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

    def _apply_styles(self) -> None:
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

            #listingTitle {
                font-size: 21px;
                font-weight: 700;
            }

            #currentStatus {
                color: #374151;
                font-size: 15px;
                font-weight: 600;
            }

            #informationText {
                color: #6b7280;
            }

            #warningText {
                color: #92400e;
                background-color: #fffbeb;
                border: 1px solid #fde68a;
                border-radius: 6px;
                padding: 8px;
            }

            #actionButton,
            #secondaryButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 7px;
                padding: 10px 14px;
                font-weight: 600;
            }

            #actionButton:hover,
            #secondaryButton:hover {
                background-color: #f3f4f6;
            }

            #primaryButton {
                background-color: #1f2937;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 14px;
                font-weight: 700;
            }

            #primaryButton:hover {
                background-color: #374151;
            }

            #destructiveButton {
                background-color: #b91c1c;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 14px;
                font-weight: 700;
            }

            #destructiveButton:hover {
                background-color: #991b1b;
            }
            """
        )