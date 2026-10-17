from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QObject,
    QThread,
    QTimer,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.states.empty_state import (
    FriendlyEmptyState,
)

from app.services.backup_service import (
    BackupInfo,
    create_backup,
    delete_backup,
    list_backups,
    restore_backup,
)
from app.ui.components.dialogs.error_feedback import (
    show_logged_error,
)
from app.ui.components.dialogs.message_dialog import (
    BrandedMessageDialog,
)


class _BackupWorker(QObject):
    """
    Run the filesystem-heavy backup outside the GUI thread.
    """

    completed = Signal(object)
    failed = Signal(object)

    @Slot()
    def run(
        self,
    ) -> None:
        try:
            backup = create_backup()

        except Exception as exc:
            self.failed.emit(
                exc
            )

            return

        self.completed.emit(
            backup
        )


class BackupRestoreDialog(QDialog):
    """
    Create, inspect, restore and delete local backups.
    """

    restore_completed = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.setWindowTitle(
            "Backup & Restore"
        )

        self.resize(
            760,
            560,
        )

        self.setMinimumSize(
            650,
            480,
        )

        self.backups: list[
            BackupInfo
        ] = []

        self._backup_thread: (
            QThread | None
        ) = None

        self._backup_worker: (
            _BackupWorker | None
        ) = None

        self._backup_result: (
            BackupInfo | None
        ) = None

        self._backup_error: (
            Exception | None
        ) = None

        self._build_ui()
        self._apply_styles()

        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            22,
            22,
            22,
            22,
        )

        layout.setSpacing(
            14
        )

        heading = QLabel(
            "Backup & Restore"
        )

        heading.setObjectName(
            "backupHeading"
        )

        layout.addWidget(
            heading
        )

        description = QLabel(
            (
                "Backups contain your local database, "
                "settings and managed listing photos. "
                "Restoring automatically creates a "
                "pre-restore safety backup first."
            )
        )

        description.setObjectName(
            "backupDescription"
        )

        description.setWordWrap(
            True
        )

        layout.addWidget(
            description
        )

        top_buttons = QHBoxLayout()

        self.create_button = QPushButton(
            "CREATE BACKUP"
        )

        self.create_button.setObjectName(
            "primaryButton"
        )

        self.create_button.clicked.connect(
            self._create_backup
        )

        self.refresh_button = QPushButton(
            "REFRESH"
        )

        self.refresh_button.setObjectName(
            "secondaryButton"
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        top_buttons.addWidget(
            self.create_button
        )

        top_buttons.addWidget(
            self.refresh_button
        )

        top_buttons.addStretch()

        layout.addLayout(
            top_buttons
        )

        self.backup_status_label = QLabel(
            ""
        )

        self.backup_status_label.setObjectName(
            "backupStatus"
        )

        self.backup_status_label.setWordWrap(
            True
        )

        self.backup_status_label.setVisible(
            False
        )

        layout.addWidget(
            self.backup_status_label
        )

        self.backup_progress = (
            QProgressBar()
        )

        # 0, 0 gives Qt's indeterminate/busy animation.
        self.backup_progress.setRange(
            0,
            0,
        )

        self.backup_progress.setTextVisible(
            False
        )

        self.backup_progress.setMaximumHeight(
            8
        )

        self.backup_progress.setVisible(
            False
        )

        layout.addWidget(
            self.backup_progress
        )

        self.backup_list = QListWidget()

        self.backup_list.setObjectName(
            "backupList"
        )

        self.backup_list.currentItemChanged.connect(
            self._selection_changed
        )

        layout.addWidget(
            self.backup_list,
            1,
        )

        self.backup_empty_state = FriendlyEmptyState(
            title="No Backups Yet",
            message=(
                "Create your first safety backup so your "
                "listings, settings and managed photos can "
                "be restored if you ever need them."
            ),
            action_text="CREATE BACKUP",
            action=self._create_backup,
            show_icon=True,
            parent=self,
        )

        self.backup_empty_state.setVisible(
            False
        )

        layout.addWidget(
            self.backup_empty_state,
            1,
        )

        self.details_label = QLabel(
            "Select a backup to see its details."
        )

        self.details_label.setObjectName(
            "backupDetails"
        )

        self.details_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.details_label
        )

        bottom_buttons = QHBoxLayout()

        self.open_button = QPushButton(
            "OPEN FOLDER"
        )

        self.open_button.setObjectName(
            "secondaryButton"
        )

        self.open_button.clicked.connect(
            self._open_selected
        )

        self.restore_button = QPushButton(
            "RESTORE SELECTED"
        )

        self.restore_button.setObjectName(
            "primaryButton"
        )

        self.restore_button.clicked.connect(
            self._restore_selected
        )

        self.delete_button = QPushButton(
            "DELETE BACKUP"
        )

        self.delete_button.setObjectName(
            "destructiveButton"
        )

        self.delete_button.clicked.connect(
            self._delete_selected
        )

        self.close_button = QPushButton(
            "CLOSE"
        )

        self.close_button.setObjectName(
            "secondaryButton"
        )

        self.close_button.clicked.connect(
            self.reject
        )

        bottom_buttons.addWidget(
            self.open_button
        )

        bottom_buttons.addWidget(
            self.delete_button
        )

        bottom_buttons.addStretch()

        bottom_buttons.addWidget(
            self.close_button
        )

        bottom_buttons.addWidget(
            self.restore_button
        )

        layout.addLayout(
            bottom_buttons
        )

        self._set_selection_buttons(
            False
        )

    def refresh(self) -> None:
        self.backup_list.clear()

        if (
            self._backup_thread
            is None
        ):
            self.backup_progress.setVisible(
                False
            )

        self.backup_list.setVisible(
            True
        )

        self.backup_empty_state.setVisible(
            False
        )

        self.details_label.setVisible(
            True
        )

        self.details_label.setText(
            "Select a backup to see its details."
        )

        self._set_selection_buttons(
            False
        )

        try:
            self.backups = (
                list_backups()
            )

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Load Backups",
                message=(
                    "The backup list could not be loaded."
                ),
                context=(
                    "Unable to load backup list"
                ),
                exception=exc,
            )

            self.backups = []

            return

        if not self.backups:
            self.backup_list.setVisible(
                False
            )

            self.details_label.setVisible(
                False
            )

            self.backup_empty_state.setVisible(
                True
            )

            return

        for backup in self.backups:
            warning_text = (
                (
                    f"  •  "
                    f"{len(backup.warnings)} warning(s)"
                )
                if backup.warnings
                else ""
            )

            text = (
                f"{backup.created_at:%d %b %Y  %H:%M:%S}"
                f"  •  "
                f"{backup.photo_count} photos"
                f"  •  "
                f"{backup.total_size_mb:.2f} MB"
                f"{warning_text}"
            )

            item = QListWidgetItem(
                text
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                str(
                    backup.path
                ),
            )

            self.backup_list.addItem(
                item
            )

    def _selected_backup(
        self,
    ) -> BackupInfo | None:
        item = (
            self.backup_list.currentItem()
        )

        if item is None:
            return None

        path_text = item.data(
            Qt.ItemDataRole.UserRole
        )

        if not path_text:
            return None

        selected_path = Path(
            path_text
        )

        for backup in self.backups:
            if backup.path == selected_path:
                return backup

        return None

    def _selection_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        del current
        del previous

        backup = (
            self._selected_backup()
        )

        if backup is None:
            self._set_selection_buttons(
                False
            )

            return

        self._set_selection_buttons(
            True
        )

        warning_text = (
            "\nWarnings: "
            f"{len(backup.warnings)}"
            if backup.warnings
            else ""
        )

        self.details_label.setText(
            (
                f"Folder: {backup.path}\n"
                f"Created: "
                f"{backup.created_at:%d %B %Y %H:%M:%S}\n"
                f"Photos: {backup.photo_count}\n"
                f"Size: {backup.total_size_mb:.2f} MB"
                f"{warning_text}"
            )
        )

    def _set_selection_buttons(
        self,
        enabled: bool,
    ) -> None:
        self.open_button.setEnabled(
            enabled
        )

        self.restore_button.setEnabled(
            enabled
        )

        self.delete_button.setEnabled(
            enabled
        )

    def _create_backup(
        self,
    ) -> None:
        if (
            self._backup_thread
            is not None
        ):
            return

        self._backup_result = None
        self._backup_error = None

        # FIRST: change the visible UI.
        self._set_backup_busy(
            True
        )

        # Force the busy state onto the screen before any
        # filesystem work has a chance to begin.
        self.create_button.repaint()
        self.backup_status_label.repaint()
        self.backup_progress.repaint()
        self.repaint()

        QApplication.processEvents()

        # Give Qt a complete event-loop turn. The backup worker
        # starts only after the user can already see the feedback.
        QTimer.singleShot(
            100,
            self._start_backup_worker,
        )

    def _start_backup_worker(
        self,
    ) -> None:
        # The dialog may have been destroyed unexpectedly before
        # the deferred start. Never launch twice.
        if (
            self._backup_thread
            is not None
        ):
            return

        thread = QThread(
            self
        )

        worker = _BackupWorker()

        worker.moveToThread(
            thread
        )

        thread.started.connect(
            worker.run
        )

        worker.completed.connect(
            self._backup_completed
        )

        worker.failed.connect(
            self._backup_failed
        )

        worker.completed.connect(
            thread.quit
        )

        worker.failed.connect(
            thread.quit
        )

        worker.completed.connect(
            worker.deleteLater
        )

        worker.failed.connect(
            worker.deleteLater
        )

        thread.finished.connect(
            self._backup_thread_finished
        )

        thread.finished.connect(
            thread.deleteLater
        )

        self._backup_thread = (
            thread
        )

        self._backup_worker = (
            worker
        )

        thread.start()


    def _set_backup_busy(
        self,
        busy: bool,
    ) -> None:
        self.create_button.setEnabled(
            not busy
        )

        self.refresh_button.setEnabled(
            not busy
        )

        self.close_button.setEnabled(
            not busy
        )

        if busy:
            self.open_button.setEnabled(
                False
            )

            self.restore_button.setEnabled(
                False
            )

            self.delete_button.setEnabled(
                False
            )

            self.create_button.setText(
                "CREATING BACKUP..."
            )

            self.backup_status_label.setText(
                (
                    "Creating backup..."
                    "\n"
                    "Copying your database, settings "
                    "and managed listing photos."
                )
            )

            self.backup_status_label.setVisible(
                True
            )

            self.backup_progress.setVisible(
                True
            )

        else:
            self.create_button.setText(
                "CREATE BACKUP"
            )

            self.backup_progress.setVisible(
                False
            )

            selected = (
                self._selected_backup()
                is not None
            )

            self._set_selection_buttons(
                selected
            )

    @Slot(object)
    def _backup_completed(
        self,
        backup: BackupInfo,
    ) -> None:
        self._backup_result = (
            backup
        )

        self.backup_status_label.setText(
            "Backup created. Finishing up..."
        )

    @Slot(object)
    def _backup_failed(
        self,
        exc: Exception,
    ) -> None:
        self._backup_error = exc

        self.backup_status_label.setText(
            "Backup could not be completed."
        )

    @Slot()
    def _backup_thread_finished(
        self,
    ) -> None:
        backup = (
            self._backup_result
        )

        error = (
            self._backup_error
        )

        self._backup_thread = None
        self._backup_worker = None

        self._set_backup_busy(
            False
        )

        if error is not None:
            show_logged_error(
                self,
                title="Backup Failed",
                message=(
                    "The backup could not be created."
                ),
                context=(
                    "Unable to create backup"
                ),
                exception=error,
            )

            self.backup_status_label.setText(
                "Backup failed."
            )

            return

        if backup is None:
            self.backup_status_label.setText(
                "Backup did not complete."
            )

            return

        self.backup_status_label.setText(
            (
                "Backup created successfully. "
                f"{backup.photo_count} photo(s) copied."
            )
        )

        self.refresh()

        message = (
            "Backup created successfully.\n\n"
            f"Folder:\n{backup.path}\n\n"
            f"Photos copied: {backup.photo_count}\n"
            f"Size: {backup.total_size_mb:.2f} MB"
        )

        if backup.warnings:
            message += (
                "\n\nWarnings: "
                f"{len(backup.warnings)}"
            )

        BrandedMessageDialog.notice(
            self,
            title="Backup Created",
            message=message,
            button_text="OK",
        )


    def _restore_selected(self) -> None:
        backup = (
            self._selected_backup()
        )

        if backup is None:
            return

        confirmed = BrandedMessageDialog.ask(
            self,
            title="Restore Backup?",
            message=(
                "This will replace your current database "
                "and settings with the selected backup.\n\n"
                "Your managed photos will also be restored. "
                "A safety backup of your current state will "
                "be created automatically first."
            ),
            confirm_text="RESTORE",
            cancel_text="CANCEL",
        )

        if not confirmed:
            return

        try:
            result = restore_backup(
                backup.path
            )

        except Exception as exc:
            show_logged_error(
                self,
                title="Restore Failed",
                message=(
                    "The selected backup could not be restored."
                ),
                context=(
                    f"Unable to restore backup: {backup.path}"
                ),
                exception=exc,
            )

            return

        message = (
            "Backup restored successfully.\n\n"
            f"Photos restored: "
            f"{result.photos_restored}\n\n"
            "Safety backup of the previous state:\n"
            f"{result.safety_backup.path}"
        )

        if result.warnings:
            message += (
                "\n\nRestore warnings: "
                f"{len(result.warnings)}"
            )

        BrandedMessageDialog.notice(
            self,
            title="Restore Complete",
            message=message,
            button_text="OK",
        )

        self.restore_completed.emit()

        self.accept()

    def _delete_selected(self) -> None:
        backup = (
            self._selected_backup()
        )

        if backup is None:
            return

        confirmation = BrandedMessageDialog(
            parent=self,
            title="Delete Backup?",
            message=(
                "Permanently delete this backup?\n\n"
                f"{backup.path}\n\n"
                "Your current listings and application "
                "database will not be deleted."
            ),
            confirm_text="DELETE",
            cancel_text="CANCEL",
            confirm_object_name="destructiveButton",
            default_to_cancel=True,
        )

        confirmation.exec()

        if not confirmation.confirmed:
            return

        try:
            delete_backup(
                backup.path
            )

        except Exception as exc:
            show_logged_error(
                self,
                title="Delete Failed",
                message=(
                    "The selected backup could not be deleted."
                ),
                context=(
                    f"Unable to delete backup: {backup.path}"
                ),
                exception=exc,
            )

            return

        self.refresh()

    def _open_selected(self) -> None:
        backup = (
            self._selected_backup()
        )

        if backup is None:
            return

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(
                str(
                    backup.path
                )
            )
        )

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

            #backupHeading {
                font-size: 24px;
                font-weight: 700;
            }

            #backupDescription {
                color: #6b7280;
            }

            #backupStatus {
                font-weight: 600;
                padding: 4px 2px;
            }

            #backupList {
                background-color: white;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 6px;
            }

            #backupList::item {
                padding: 10px;
                border-bottom: 1px solid #f3f4f6;
            }

            #backupList::item:selected {
                background-color: #e5e7eb;
                color: #111827;
            }

            #backupDetails {
                background-color: white;
                color: #4b5563;
                border: 1px solid #e5e7eb;
                border-radius: 7px;
                padding: 12px;
            }

            #primaryButton {
                background-color: #1f2937;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 14px;
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
                padding: 9px 14px;
                font-weight: 600;
            }

            #secondaryButton:hover {
                background-color: #f3f4f6;
            }

            #destructiveButton {
                background-color: #b91c1c;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 14px;
                font-weight: 700;
            }

            #destructiveButton:hover {
                background-color: #991b1b;
            }
            """
        )