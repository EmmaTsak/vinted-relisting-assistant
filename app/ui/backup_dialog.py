from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QUrl,
    Signal,
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
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

        create_button = QPushButton(
            "CREATE BACKUP"
        )

        create_button.setObjectName(
            "primaryButton"
        )

        create_button.clicked.connect(
            self._create_backup
        )

        refresh_button = QPushButton(
            "REFRESH"
        )

        refresh_button.setObjectName(
            "secondaryButton"
        )

        refresh_button.clicked.connect(
            self.refresh
        )

        top_buttons.addWidget(
            create_button
        )

        top_buttons.addWidget(
            refresh_button
        )

        top_buttons.addStretch()

        layout.addLayout(
            top_buttons
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

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setObjectName(
            "secondaryButton"
        )

        close_button.clicked.connect(
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
            close_button
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

    def _create_backup(self) -> None:
        try:
            backup = create_backup()

        except Exception as exc:
            show_logged_error(
                self,
                title="Backup Failed",
                message=(
                    "The backup could not be created."
                ),
                context=(
                    "Unable to create backup"
                ),
                exception=exc,
            )

            return

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

        self.refresh()

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