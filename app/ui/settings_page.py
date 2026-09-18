from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QIntValidator,
    QWheelEvent,
)
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
    QScrollArea,
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
from app.ui.theme import (
    apply_theme,
)


class NoWheelComboBox(QComboBox):
    """
    Combo box that does not change selection when the
    mouse wheel is used over it.

    Ignoring the event allows the surrounding scroll area
    to continue scrolling.
    """

    def wheelEvent(
        self,
        event: QWheelEvent,
    ) -> None:
        event.ignore()


class SettingsPage(QWidget):
    """
    Persistent application settings and backup controls.
    """

    settings_saved = Signal(object)

    FIELD_HEIGHT = 42
    BUTTON_HEIGHT = 40

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

    def _build_ui(
        self,
    ) -> None:
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
            0
        )

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
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
            10,
        )

        content_layout.setSpacing(
            16
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

        content_layout.addWidget(
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
            18
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
            18
        )

        form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        # -------------------------------------------------
        # Daily limit
        #
        # Plain text field rather than QSpinBox:
        # - no arrows
        # - no wheel changes
        # - only valid integers 1-50
        # -------------------------------------------------

        self.daily_limit_input = (
            QLineEdit()
        )

        self.daily_limit_input.setValidator(
            QIntValidator(
                1,
                50,
                self.daily_limit_input,
            )
        )

        self.daily_limit_input.setMinimumHeight(
            self.FIELD_HEIGHT
        )

        self.daily_limit_input.setMaximumWidth(
            160
        )

        self.daily_limit_input.setPlaceholderText(
            "1 - 50"
        )

        self.daily_limit_input.setToolTip(
            "Enter a number from 1 to 50."
        )

        # -------------------------------------------------
        # Minimum relist age
        #
        # Also a plain typed integer field.
        # -------------------------------------------------

        self.minimum_age_input = (
            QLineEdit()
        )

        self.minimum_age_input.setValidator(
            QIntValidator(
                0,
                3650,
                self.minimum_age_input,
            )
        )

        self.minimum_age_input.setMinimumHeight(
            self.FIELD_HEIGHT
        )

        self.minimum_age_input.setMaximumWidth(
            160
        )

        self.minimum_age_input.setPlaceholderText(
            "Days"
        )

        self.minimum_age_input.setToolTip(
            (
                "Enter the minimum number of days "
                "before a listing is eligible again."
            )
        )

        self.vinted_url_input = (
            QLineEdit()
        )

        self.vinted_url_input.setMinimumHeight(
            self.FIELD_HEIGHT
        )

        self.currency_input = (
            QLineEdit()
        )

        self.currency_input.setMaxLength(
            3
        )

        self.currency_input.setMaximumWidth(
            100
        )

        self.currency_input.setMinimumHeight(
            self.FIELD_HEIGHT
        )

        self.photo_directory_input = (
            QLineEdit()
        )

        self.photo_directory_input.setMinimumHeight(
            self.FIELD_HEIGHT
        )

        photo_row = QWidget()

        photo_row.setMinimumHeight(
            self.FIELD_HEIGHT
        )

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

        photo_browse.setMinimumHeight(
            self.BUTTON_HEIGHT
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

        self.backup_directory_input = (
            QLineEdit()
        )

        self.backup_directory_input.setMinimumHeight(
            self.FIELD_HEIGHT
        )

        backup_row = QWidget()

        backup_row.setMinimumHeight(
            self.FIELD_HEIGHT
        )

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

        backup_browse.setMinimumHeight(
            self.BUTTON_HEIGHT
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

        # Theme dropdown also ignores wheel changes.
        self.theme_input = (
            NoWheelComboBox()
        )

        self.theme_input.setMinimumHeight(
            self.FIELD_HEIGHT
        )

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

        settings_buttons = (
            QHBoxLayout()
        )

        reset_button = QPushButton(
            "RESET TO DEFAULTS"
        )

        reset_button.setObjectName(
            "secondaryButton"
        )

        reset_button.setMinimumHeight(
            self.BUTTON_HEIGHT
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

        save_button.setMinimumHeight(
            self.BUTTON_HEIGHT
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

        content_layout.addWidget(
            settings_frame
        )

        # -------------------------------------------------
        # Backup section
        # -------------------------------------------------

        backup_frame = QFrame()

        backup_frame.setObjectName(
            "settingsFrame"
        )

        backup_frame_layout = (
            QVBoxLayout(
                backup_frame
            )
        )

        backup_frame_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        backup_frame_layout.setSpacing(
            14
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

        backup_buttons = (
            QHBoxLayout()
        )

        create_backup_button = (
            QPushButton(
                "CREATE BACKUP"
            )
        )

        create_backup_button.setObjectName(
            "primaryButton"
        )

        create_backup_button.setMinimumHeight(
            self.BUTTON_HEIGHT
        )

        create_backup_button.clicked.connect(
            self._create_backup
        )

        manage_backups_button = (
            QPushButton(
                "MANAGE / RESTORE BACKUPS"
            )
        )

        manage_backups_button.setObjectName(
            "secondaryButton"
        )

        manage_backups_button.setMinimumHeight(
            self.BUTTON_HEIGHT
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

        content_layout.addWidget(
            backup_frame
        )

        content_layout.addStretch()

        self.scroll_area.setWidget(
            content
        )

        root_layout.addWidget(
            self.scroll_area,
            1,
        )

    def reload(
        self,
    ) -> None:
        try:
            settings = (
                load_settings()
            )

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

            settings = (
                default_settings()
            )

        self._populate(
            settings
        )

    def _populate(
        self,
        settings: AppSettings,
    ) -> None:
        self.daily_limit_input.setText(
            str(
                settings.daily_relist_limit
            )
        )

        self.minimum_age_input.setText(
            str(
                settings.minimum_relist_age_days
            )
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

    def _validate_number_fields(
        self,
    ) -> tuple[int, int] | None:
        """
        Validate the two manually typed numeric settings.
        """
        daily_text = (
            self.daily_limit_input
            .text()
            .strip()
        )

        age_text = (
            self.minimum_age_input
            .text()
            .strip()
        )

        if not daily_text:
            QMessageBox.warning(
                self,
                "Missing Daily Limit",
                (
                    "Enter a daily relist limit "
                    "between 1 and 50."
                ),
            )

            self.daily_limit_input.setFocus()

            return None

        if not age_text:
            QMessageBox.warning(
                self,
                "Missing Minimum Age",
                (
                    "Enter a minimum relist age "
                    "between 0 and 3650 days."
                ),
            )

            self.minimum_age_input.setFocus()

            return None

        try:
            daily_limit = int(
                daily_text
            )

            minimum_age = int(
                age_text
            )

        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Number",
                "Enter whole numbers only.",
            )

            return None

        if not (
            1
            <= daily_limit
            <= 50
        ):
            QMessageBox.warning(
                self,
                "Invalid Daily Limit",
                (
                    "Daily relist limit must be "
                    "between 1 and 50."
                ),
            )

            self.daily_limit_input.setFocus()

            return None

        if not (
            0
            <= minimum_age
            <= 3650
        ):
            QMessageBox.warning(
                self,
                "Invalid Minimum Age",
                (
                    "Minimum relist age must be "
                    "between 0 and 3650 days."
                ),
            )

            self.minimum_age_input.setFocus()

            return None

        return (
            daily_limit,
            minimum_age,
        )

    def _choose_photo_directory(
        self,
    ) -> None:
        selected = (
            QFileDialog.getExistingDirectory(
                self,
                "Choose Photo Storage Directory",
                (
                    self.photo_directory_input
                    .text()
                    .strip()
                ),
            )
        )

        if selected:
            self.photo_directory_input.setText(
                selected
            )

    def _choose_backup_directory(
        self,
    ) -> None:
        selected = (
            QFileDialog.getExistingDirectory(
                self,
                "Choose Backup Directory",
                (
                    self.backup_directory_input
                    .text()
                    .strip()
                ),
            )
        )

        if selected:
            self.backup_directory_input.setText(
                selected
            )

    def _build_settings(
        self,
    ) -> AppSettings | None:
        number_values = (
            self._validate_number_fields()
        )

        if number_values is None:
            return None

        (
            daily_limit,
            minimum_age,
        ) = number_values

        return AppSettings(
            daily_relist_limit=(
                daily_limit
            ),
            minimum_relist_age_days=(
                minimum_age
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

    def _save(
        self,
    ) -> None:
        new_settings = (
            self._build_settings()
        )

        if new_settings is None:
            return

        try:
            saved = save_settings(
                new_settings
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

    def _create_backup(
        self,
    ) -> None:
        new_settings = (
            self._build_settings()
        )

        if new_settings is None:
            return

        try:
            saved = save_settings(
                new_settings
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

            backup = (
                create_backup()
            )

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
        dialog = (
            BackupRestoreDialog(
                parent=self
            )
        )

        dialog.restore_completed.connect(
            self._backup_restored
        )

        dialog.exec()

    def _backup_restored(
        self,
    ) -> None:
        try:
            settings = (
                load_settings()
            )

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
        self.setStyleSheet(
            ""
        )