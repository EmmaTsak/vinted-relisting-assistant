from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services.backup_service import (
    create_backup,
)
from app.services.vinted_export_service import (
    VintedExportError,
    import_vinted_export,
)


class VintedExportImportDialog(QDialog):
    """
    Safe incremental importer for a Vinted personal-data export.

    Existing Vinted item IDs are skipped automatically by the
    Vinted export service.

    This dialog deliberately uses add-new-only behaviour.
    Existing local listings are never overwritten.
    """

    import_completed = Signal(int)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.selected_file: Path | None = None

        self.setWindowTitle(
            "Import Vinted Data Export"
        )

        self.resize(
            760,
            650,
        )

        self.setMinimumSize(
            680,
            560,
        )

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
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
            14
        )

        heading = QLabel(
            "Import Vinted Personal Data"
        )

        heading.setObjectName(
            "dialogHeading"
        )

        description = QLabel(
            (
                "Import listings from a newer Vinted personal-data "
                "export without creating duplicates of listings "
                "you have already imported."
            )
        )

        description.setObjectName(
            "dialogSubtitle"
        )

        description.setWordWrap(
            True
        )

        layout.addWidget(
            heading
        )

        layout.addWidget(
            description
        )

        safety_box = QFrame()

        safety_box.setObjectName(
            "informationBox"
        )

        safety_layout = QVBoxLayout(
            safety_box
        )

        safety_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        safety_layout.setSpacing(
            7
        )

        safety_title = QLabel(
            "SAFE INCREMENTAL IMPORT"
        )

        safety_title.setObjectName(
            "sectionHeading"
        )

        safety_text = QLabel(
            (
                "• Existing Vinted item IDs are skipped automatically.\n"
                "• Only Vinted items that are not already stored are added.\n"
                "• Existing categories, ISBNs, notes, priorities and edits "
                "are not overwritten.\n"
                "• A safety backup is created before importing."
            )
        )

        safety_text.setObjectName(
            "informationText"
        )

        safety_text.setWordWrap(
            True
        )

        safety_layout.addWidget(
            safety_title
        )

        safety_layout.addWidget(
            safety_text
        )

        layout.addWidget(
            safety_box
        )

        source_title = QLabel(
            "VINTED EXPORT"
        )

        source_title.setObjectName(
            "sectionHeading"
        )

        layout.addWidget(
            source_title
        )

        source_row = QHBoxLayout()

        source_row.setSpacing(
            8
        )

        self.file_input = QLineEdit()

        self.file_input.setReadOnly(
            True
        )

        self.file_input.setPlaceholderText(
            "Select listings ZIP or index.html"
        )

        self.file_input.setMinimumHeight(
            40
        )

        browse_button = QPushButton(
            "CHOOSE EXPORT"
        )

        browse_button.setObjectName(
            "secondaryButton"
        )

        browse_button.setMinimumHeight(
            40
        )

        browse_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        browse_button.clicked.connect(
            self._choose_export
        )

        source_row.addWidget(
            self.file_input,
            1,
        )

        source_row.addWidget(
            browse_button
        )

        layout.addLayout(
            source_row
        )

        self.status_label = QLabel(
            "No Vinted export selected."
        )

        self.status_label.setObjectName(
            "statusText"
        )

        self.status_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.status_label
        )

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(
            0
        )

        self.progress_bar.setTextVisible(
            True
        )

        layout.addWidget(
            self.progress_bar
        )

        self.current_item_label = QLabel(
            ""
        )

        self.current_item_label.setObjectName(
            "placeholderText"
        )

        self.current_item_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.current_item_label
        )

        self.result_output = QTextEdit()

        self.result_output.setReadOnly(
            True
        )

        self.result_output.setPlaceholderText(
            (
                "After the import, the number of new and skipped "
                "listings will appear here."
            )
        )

        layout.addWidget(
            self.result_output,
            1,
        )

        buttons = QHBoxLayout()

        buttons.setSpacing(
            8
        )

        buttons.addStretch()

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setObjectName(
            "secondaryButton"
        )

        close_button.setMinimumHeight(
            40
        )

        close_button.clicked.connect(
            self.reject
        )

        self.import_button = QPushButton(
            "IMPORT NEW LISTINGS"
        )

        self.import_button.setObjectName(
            "primaryButton"
        )

        self.import_button.setMinimumHeight(
            40
        )

        self.import_button.setEnabled(
            False
        )

        self.import_button.clicked.connect(
            self._run_import
        )

        buttons.addWidget(
            close_button
        )

        buttons.addWidget(
            self.import_button
        )

        layout.addLayout(
            buttons
        )

    def _choose_export(
        self,
    ) -> None:
        selected_file, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Choose Vinted Personal Data Export",
                "",
                (
                    "Vinted Export "
                    "(*.zip *.html *.htm);;"
                    "ZIP Archives (*.zip);;"
                    "HTML Files (*.html *.htm);;"
                    "All Files (*.*)"
                ),
            )
        )

        if not selected_file:
            return

        path = Path(
            selected_file
        )

        self.selected_file = path

        self.file_input.setText(
            str(
                path
            )
        )

        self.status_label.setText(
            (
                "Ready to import new listings from "
                f"{path.name}"
            )
        )

        self.result_output.setPlainText(
            (
                "Export selected.\n\n"
                "Existing Vinted item IDs will be skipped.\n"
                "Only previously unseen Vinted listings "
                "will be added."
            )
        )

        self.progress_bar.setValue(
            0
        )

        self.current_item_label.setText(
            ""
        )

        self.import_button.setEnabled(
            True
        )

    def _run_import(
        self,
    ) -> None:
        if self.selected_file is None:
            return

        confirmation = QMessageBox.question(
            self,
            "Confirm Vinted Import",
            (
                "Import new listings from:\n\n"
                f"{self.selected_file.name}\n\n"
                "Existing Vinted listings will be skipped.\n"
                "Existing local edits will not be overwritten.\n\n"
                "A safety backup will be created first."
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.Cancel
            ),
            QMessageBox.StandardButton.Cancel,
        )

        if (
            confirmation
            != QMessageBox.StandardButton.Yes
        ):
            return

        self.import_button.setEnabled(
            False
        )

        self.result_output.setPlainText(
            "Creating safety backup..."
        )

        self.status_label.setText(
            "Creating safety backup..."
        )

        QApplication.processEvents()

        try:
            backup = create_backup(
                prefix="pre-vinted-import"
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Backup Failed",
                (
                    "The safety backup could not be created.\n\n"
                    "The import has been cancelled and nothing "
                    "has been imported.\n\n"
                    f"{exc}"
                ),
            )

            self.result_output.setPlainText(
                (
                    "IMPORT CANCELLED\n\n"
                    "Safety backup failed.\n\n"
                    f"{exc}"
                )
            )

            self.status_label.setText(
                "Import cancelled."
            )

            self.import_button.setEnabled(
                True
            )

            return

        self.result_output.setPlainText(
            (
                "Safety backup created.\n\n"
                f"{backup.path}\n\n"
                "Scanning Vinted export..."
            )
        )

        self.status_label.setText(
            "Importing new Vinted listings..."
        )

        QApplication.processEvents()

        try:
            result = import_vinted_export(
                self.selected_file,
                progress_callback=(
                    self._update_progress
                ),
            )

        except VintedExportError as exc:
            QMessageBox.critical(
                self,
                "Vinted Import Failed",
                str(
                    exc
                ),
            )

            self.result_output.setPlainText(
                (
                    "IMPORT FAILED\n\n"
                    f"{exc}"
                )
            )

            self.status_label.setText(
                "Import failed."
            )

            self.import_button.setEnabled(
                True
            )

            return

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Vinted Import Failed",
                (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

            self.result_output.setPlainText(
                (
                    "IMPORT FAILED\n\n"
                    f"{type(exc).__name__}: {exc}"
                )
            )

            self.status_label.setText(
                "Import failed."
            )

            self.import_button.setEnabled(
                True
            )

            return

        self.progress_bar.setValue(
            100
        )

        self.current_item_label.setText(
            "Finished"
        )

        lines = [
            "IMPORT COMPLETE",
            "",
            (
                "Listings found:        "
                f"{result.total_found}"
            ),
            (
                "New listings imported: "
                f"{result.imported}"
            ),
            (
                "Existing skipped:      "
                f"{result.skipped_existing}"
            ),
            (
                "Photos imported:       "
                f"{result.photos_imported}"
            ),
            (
                "Sold imported:         "
                f"{result.sold_imported}"
            ),
            (
                "Hidden / excluded:     "
                f"{result.hidden_imported}"
            ),
            (
                "Warnings:              "
                f"{len(result.warnings)}"
            ),
            "",
            "Safety backup:",
            str(
                backup.path
            ),
        ]

        if result.warnings:
            lines.extend(
                [
                    "",
                    "WARNINGS",
                    "--------",
                ]
            )

            for warning in result.warnings:
                lines.append(
                    f"- {warning}"
                )

        self.result_output.setPlainText(
            "\n".join(
                lines
            )
        )

        if result.imported == 0:
            self.status_label.setText(
                (
                    "Finished — no new listings were found. "
                    f"{result.skipped_existing} existing "
                    "listing(s) were skipped."
                )
            )

        else:
            self.status_label.setText(
                (
                    "Finished — "
                    f"{result.imported} new listing(s) imported, "
                    f"{result.skipped_existing} existing skipped."
                )
            )

        self.import_completed.emit(
            result.imported
        )

        QMessageBox.information(
            self,
            "Vinted Import Complete",
            (
                f"New listings imported: {result.imported}\n"
                f"Existing skipped: {result.skipped_existing}\n"
                f"Photos imported: {result.photos_imported}\n"
                f"Warnings: {len(result.warnings)}"
            ),
        )

        self.import_button.setEnabled(
            True
        )

    def _update_progress(
        self,
        current: int,
        total: int,
        title: str,
    ) -> None:
        if total <= 0:
            percentage = 0

        else:
            percentage = int(
                (
                    current
                    / total
                )
                * 100
            )

        percentage = max(
            0,
            min(
                100,
                percentage,
            ),
        )

        self.progress_bar.setValue(
            percentage
        )

        self.status_label.setText(
            (
                f"Checking listing "
                f"{current} of {total}..."
            )
        )

        self.current_item_label.setText(
            title
        )

        QApplication.processEvents()