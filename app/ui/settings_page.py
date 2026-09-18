from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.services.backup_service import (
    create_backup,
)
from app.services.settings_service import (
    AppSettings,
    default_settings,
    load_settings,
    save_settings,
)
from app.ui.backup_dialog import (
    BackupRestoreDialog,
)
from app.ui.theme import apply_theme


class SettingsPage(QWidget):
    """
    Persistent application settings and backup controls.
    """

    settings_saved = Signal(object)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self._build_ui()
        self._apply_styles()
        self.reload()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(
            self
        )

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.setSpacing(
            14
        )

        explanation = QLabel(
            (
                "Settings and backups remain local "
                "to this computer."
            )
        )

        explanation.setObjectName(
            "settingsExplanation"
        )

        explanation.setWordWrap(
            True
        )

        root_layout.addWidget(
            explanation
        )

        settings_frame = QFrame()

        settings_frame.setObjectName(
            "settingsFrame"
        )

        settings_layout = QVBoxLayout(
            settings_frame
        )

        settings_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        settings_layout.setSpacing(
            16
        )

        settings_heading = QLabel(
            "APPLICATION SETTINGS"
        )

        settings_heading.setObjectName(
            "sectionHeading"
        )

        settings_layout.addWidget(
            settings_heading
        )

        form = QFormLayout()

        form.setHorizontalSpacing(
            24
        )

        form.setVerticalSpacing(
            15
        )

        self.daily_limit_input = QSpinBox()

        self.daily_limit_input.setRange(
            1,
            50,
        )

        self.minimum_age_input = QSpinBox()

        self.minimum_age_input.setRange(
            0,
            3650,
        )

        self.minimum_age_input.setSuffix(
            " days"
        )

        self.vinted_url_input = QLineEdit()

        self.currency_input = QLineEdit()

        self.currency_input.setMaxLength(
            3
        )

        self.currency_input.setMaximumWidth(
            100
        )

        self.photo_directory_input = QLineEdit()

        photo_row = QWidget()

        photo_layout = QHBoxLayout(
            photo_row
        )

        photo_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        photo_layout.setSpacing(
            8
        )

        photo_browse = QPushButton(
            "BROWSE"
        )

        photo_browse.setObjectName(
            "browseButton"
        )

        photo_browse.clicked.connect(
            self._choose_photo_directory
        )

        photo_layout.addWidget(
            self.photo_directory_input,
            1,
        )

        photo_layout.addWidget(
            photo_browse
        )

        self.backup_directory_input = QLineEdit()

        backup_row = QWidget()

        backup_layout = QHBoxLayout(
            backup_row
        )

        backup_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        backup_layout.setSpacing(
            8
        )

        backup_browse = QPushButton(
            "BROWSE"
        )

        backup_browse.setObjectName(
            "browseButton"
        )

        backup_browse.clicked.connect(
            self._choose_backup_directory
        )

        backup_layout.addWidget(
            self.backup_directory_input,
            1,
        )

        backup_layout.addWidget(
            backup_browse
        )

        self.theme_input = QComboBox()

        self.theme_input.addItem(
            "System",
            "system",
        )

        self.theme_input.addItem(
            "Light",
            "light",
        )

        self.theme_input.addItem(
            "Dark",
            "dark",
        )

        form.addRow(
            "Daily relist limit",
            self.daily_limit_input,
        )

        form.addRow(
            "Minimum relist age",
            self.minimum_age_input,
        )

        form.addRow(
            "Vinted website",
            self.vinted_url_input,
        )

        form.addRow(
            "Default currency",
            self.currency_input,
        )

        form.addRow(
            "Photo storage",
            photo_row,
        )

        form.addRow(
            "Backup directory",
            backup_row,
        )

        form.addRow(
            "Theme",
            self.theme_input,
        )

        settings_layout.addLayout(
            form
        )

        note = QLabel(
            (
                "Theme changes apply immediately after saving. "
                "System follows the Windows colour scheme. "
                "Changing Photo storage affects new managed photos "
                "only; existing photos are not silently moved."
            )
        )

        note.setObjectName(
            "settingsNote"
        )

        note.setWordWrap(
            True
        )

        settings_layout.addWidget(
            note
        )

        settings_buttons = QHBoxLayout()

        reset_button = QPushButton(
            "RESET TO DEFAULTS"
        )

        reset_button.setObjectName(
            "secondaryButton"
        )

        reset_button.clicked.connect(
            self._reset_defaults
        )

        save_button = QPushButton(
            "SAVE SETTINGS"
        )

        save_button.setObjectName(
            "primaryButton"
        )

        save_button.clicked.connect(
            self._save
        )

        settings_buttons.addWidget(
            reset_button
        )

        settings_buttons.addStretch()

        settings_buttons.addWidget(
            save_button
        )

        settings_layout.addLayout(
            settings_buttons
        )

        root_layout.addWidget(
            settings_frame
        )

        backup_frame = QFrame()

        backup_frame.setObjectName(
            "settingsFrame"
        )

        backup_frame_layout = QVBoxLayout(
            backup_frame
        )

        backup_frame_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        backup_frame_layout.setSpacing(
            12
        )

        backup_heading = QLabel(
            "BACKUP & RESTORE"
        )

        backup_heading.setObjectName(
            "sectionHeading"
        )

        backup_description = QLabel(
            (
                "Create a local snapshot of the database, "
                "settings and managed listing photos. "
                "Restores always create a safety backup first."
            )
        )

        backup_description.setObjectName(
            "settingsNoteText"
        )

        backup_description.setWordWrap(
            True
        )

        backup_frame_layout.addWidget(
            backup_heading
        )

        backup_frame_layout.addWidget(
            backup_description
        )

        backup_buttons = QHBoxLayout()

        create_backup_button = QPushButton(
            "CREATE BACKUP"
        )

        create_backup_button.setObjectName(
            "primaryButton"
        )

        create_backup_button.clicked.connect(
            self._create_backup
        )

        manage_backups_button = QPushButton(
            "MANAGE / RESTORE BACKUPS"
        )

        manage_backups_button.setObjectName(
            "secondaryButton"
        )

        manage_backups_button.clicked.connect(
            self._open_backup_manager
        )

        backup_buttons.addWidget(
            create_backup_button
        )

        backup_buttons.addWidget(
            manage_backups_button
        )

        backup_buttons.addStretch()

        backup_frame_layout.addLayout(
            backup_buttons
        )

        root_layout.addWidget(
            backup_frame
        )

        root_layout.addStretch()

    def reload(self) -> None:
        try:
            settings = load_settings()

        except Exception as exc:
            QMessageBox.warning(
                self,
                "Settings Error",
                (
                    "The saved settings could not "
                    "be loaded. Defaults will be shown.\n\n"
                    f"{exc}"
                ),
            )

            settings = default_settings()

        self._populate(
            settings
        )

    def _populate(
        self,
        settings: AppSettings,
    ) -> None:
        self.daily_limit_input.setValue(
            settings.daily_relist_limit
        )

        self.minimum_age_input.setValue(
            settings.minimum_relist_age_days
        )

        self.vinted_url_input.setText(
            settings.vinted_url
        )

        self.currency_input.setText(
            settings.currency
        )

        self.photo_directory_input.setText(
            settings.photo_storage_directory
        )

        self.backup_directory_input.setText(
            settings.backup_directory
        )

        theme_index = (
            self.theme_input.findData(
                settings.theme
            )
        )

        if theme_index >= 0:
            self.theme_input.setCurrentIndex(
                theme_index
            )

    def _choose_photo_directory(
        self,
    ) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose Photo Storage Directory",
            (
                self.photo_directory_input
                .text()
                .strip()
            ),
        )

        if selected:
            self.photo_directory_input.setText(
                selected
            )

    def _choose_backup_directory(
        self,
    ) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose Backup Directory",
            (
                self.backup_directory_input
                .text()
                .strip()
            ),
        )

        if selected:
            self.backup_directory_input.setText(
                selected
            )

    def _build_settings(
        self,
    ) -> AppSettings:
        return AppSettings(
            daily_relist_limit=(
                self.daily_limit_input.value()
            ),
            minimum_relist_age_days=(
                self.minimum_age_input.value()
            ),
            vinted_url=(
                self.vinted_url_input.text()
            ),
            currency=(
                self.currency_input.text()
            ),
            photo_storage_directory=(
                self.photo_directory_input.text()
            ),
            backup_directory=(
                self.backup_directory_input.text()
            ),
            theme=(
                self.theme_input.currentData()
            ),
        )

    def _save(self) -> None:
        try:
            saved = save_settings(
                self._build_settings()
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Save Settings",
                str(exc),
            )

            return

        self._populate(
            saved
        )

        apply_theme(
            saved.theme
        )

        self.settings_saved.emit(
            saved
        )

        QMessageBox.information(
            self,
            "Settings Saved",
            (
                "Your settings were saved successfully.\n\n"
                "The selected theme has been applied."
            ),
        )

    def _create_backup(self) -> None:
        try:
            saved = save_settings(
                self._build_settings()
            )

            self._populate(
                saved
            )

            apply_theme(
                saved.theme
            )

            self.settings_saved.emit(
                saved
            )

            backup = create_backup()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Backup Failed",
                str(exc),
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

        QMessageBox.information(
            self,
            "Backup Created",
            message,
        )

    def _open_backup_manager(
        self,
    ) -> None:
        dialog = BackupRestoreDialog(
            parent=self
        )

        dialog.restore_completed.connect(
            self._backup_restored
        )

        dialog.exec()

    def _backup_restored(
        self,
    ) -> None:
        try:
            settings = load_settings()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Restore Error",
                (
                    "The backup was restored, but the "
                    "restored settings could not be loaded.\n\n"
                    f"{exc}"
                ),
            )

            return

        self._populate(
            settings
        )

        apply_theme(
            settings.theme
        )

        self.settings_saved.emit(
            settings
        )

    def _reset_defaults(
        self,
    ) -> None:
        answer = QMessageBox.question(
            self,
            "Reset Settings",
            (
                "Reset the fields to default values?\n\n"
                "Press SAVE SETTINGS afterwards "
                "to persist and apply them."
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

        self._populate(
            default_settings()
        )

    def _apply_styles(
        self,
    ) -> None:
        """
        Older page-level styling is intentionally minimal.

        The central ThemeManager applies the real colours.
        """
        self.setStyleSheet(
            ""
        )