from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services.import_service import (
    ImportFileError,
    import_listings_file,
)


class ImportListingsDialog(QDialog):
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
            "Import Listings"
        )

        self.resize(
            720,
            620,
        )

        self.setMinimumSize(
            640,
            540,
        )

        self._build_ui()
        self._apply_styles()

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
            "Import Existing Listings"
        )

        heading.setObjectName(
            "dialogHeading"
        )

        description = QLabel(
            (
                "Choose a local CSV or JSON file "
                "containing your existing listing "
                "information and optional photo paths."
            )
        )

        description.setWordWrap(
            True
        )

        description.setObjectName(
            "dialogSubtitle"
        )

        layout.addWidget(
            heading
        )

        layout.addWidget(
            description
        )

        file_title = QLabel(
            "Selected file"
        )

        file_title.setObjectName(
            "sectionLabel"
        )

        layout.addWidget(
            file_title
        )

        file_row = QHBoxLayout()

        self.file_input = QLineEdit()

        self.file_input.setReadOnly(
            True
        )

        self.file_input.setPlaceholderText(
            "No file selected"
        )

        browse_button = QPushButton(
            "CHOOSE FILE"
        )

        browse_button.setObjectName(
            "secondaryButton"
        )

        browse_button.clicked.connect(
            self._choose_file
        )

        file_row.addWidget(
            self.file_input,
            1,
        )

        file_row.addWidget(
            browse_button
        )

        layout.addLayout(
            file_row
        )

        self.status_label = QLabel(
            "No import file selected."
        )

        self.status_label.setObjectName(
            "statusText"
        )

        layout.addWidget(
            self.status_label
        )

        information = QLabel(
            (
                "Required fields: title, price\n\n"
                "JSON can also contain:\n"
                "\"photos\": [\"photo1.jpg\", \"photo2.jpg\"]\n\n"
                "Relative photo paths are resolved relative "
                "to the JSON file. The photos are copied into "
                "the application's own storage."
            )
        )

        information.setWordWrap(
            True
        )

        information.setObjectName(
            "infoBox"
        )

        layout.addWidget(
            information
        )

        warning = QLabel(
            (
                "Importing the same file more than once "
                "can create duplicate listings."
            )
        )

        warning.setWordWrap(
            True
        )

        warning.setObjectName(
            "warningText"
        )

        layout.addWidget(
            warning
        )

        self.result_output = QTextEdit()

        self.result_output.setReadOnly(
            True
        )

        self.result_output.setPlaceholderText(
            "Import results will appear here."
        )

        layout.addWidget(
            self.result_output,
            1,
        )

        buttons = QHBoxLayout()

        buttons.addStretch()

        close_button = QPushButton(
            "Close"
        )

        close_button.setObjectName(
            "secondaryButton"
        )

        close_button.clicked.connect(
            self.reject
        )

        self.import_button = QPushButton(
            "IMPORT LISTINGS"
        )

        self.import_button.setObjectName(
            "primaryButton"
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

    def _choose_file(
        self,
    ) -> None:
        dialog = QFileDialog(
            self
        )

        dialog.setWindowTitle(
            "Choose Listings Import File"
        )

        dialog.setFileMode(
            QFileDialog.FileMode.ExistingFile
        )

        dialog.setNameFilters(
            [
                "Listing Files (*.json *.csv)",
                "JSON Files (*.json)",
                "CSV Files (*.csv)",
            ]
        )

        if not dialog.exec():
            return

        files = (
            dialog.selectedFiles()
        )

        if not files:
            return

        path = Path(
            files[0]
        )

        self.selected_file = (
            path
        )

        self.file_input.setText(
            str(
                path
            )
        )

        self.status_label.setText(
            f"Ready to import: {path.name}"
        )

        self.result_output.setPlainText(
            (
                "File selected successfully.\n\n"
                f"{path}\n\n"
                "Press IMPORT LISTINGS."
            )
        )

        self.import_button.setEnabled(
            True
        )

    def _run_import(
        self,
    ) -> None:
        if self.selected_file is None:
            return

        confirmation = (
            QMessageBox.question(
                self,
                "Confirm Import",
                (
                    "Import listings from:\n\n"
                    f"{self.selected_file.name}\n\n"
                    "Existing listings will not be deleted."
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.Cancel
                ),
                QMessageBox.StandardButton.Cancel,
            )
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
            "Importing..."
        )

        try:
            result = (
                import_listings_file(
                    self.selected_file
                )
            )

        except ImportFileError as exc:
            QMessageBox.critical(
                self,
                "Import Failed",
                str(
                    exc
                ),
            )

            self.result_output.setPlainText(
                str(
                    exc
                )
            )

            self.import_button.setEnabled(
                True
            )

            return

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Import Failed",
                (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

            self.import_button.setEnabled(
                True
            )

            return

        lines = [
            "IMPORT COMPLETE",
            "",
            (
                "Rows found: "
                f"{result.total_rows}"
            ),
            (
                "Listings imported: "
                f"{result.imported_count}"
            ),
            (
                "Listings skipped: "
                f"{result.skipped_count}"
            ),
            (
                "Photos imported: "
                f"{result.photos_imported}"
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
                    (
                        f"Row {warning.row_number}: "
                        f"{warning.message}"
                    )
                )

        if result.errors:
            lines.extend(
                [
                    "",
                    "ERRORS",
                    "------",
                ]
            )

            for error in result.errors:
                lines.append(
                    (
                        f"Row {error.row_number}: "
                        f"{error.message}"
                    )
                )

        self.result_output.setPlainText(
            "\n".join(
                lines
            )
        )

        self.status_label.setText(
            (
                f"Finished — "
                f"{result.imported_count} listings, "
                f"{result.photos_imported} photos."
            )
        )

        if (
            result.imported_count
            > 0
        ):
            self.import_completed.emit(
                result.imported_count
            )

        QMessageBox.information(
            self,
            "Import Complete",
            (
                "Listings imported: "
                f"{result.imported_count}\n"
                "Photos imported: "
                f"{result.photos_imported}\n"
                "Listings skipped: "
                f"{result.skipped_count}"
            ),
        )

        self.import_button.setEnabled(
            True
        )

    def _apply_styles(
        self,
    ) -> None:
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

            #dialogHeading {
                font-size: 24px;
                font-weight: 700;
            }

            #dialogSubtitle {
                color: #6b7280;
            }

            #sectionLabel,
            #statusText {
                font-weight: 600;
            }

            #infoBox {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
            }

            #warningText {
                background-color: #fffbeb;
                color: #92400e;
                border: 1px solid #fde68a;
                border-radius: 7px;
                padding: 10px;
            }

            QLineEdit,
            QTextEdit {
                background-color: white;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px;
            }

            #primaryButton {
                background-color: #1f2937;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 18px;
                font-weight: 600;
            }

            #primaryButton:hover {
                background-color: #374151;
            }

            #primaryButton:disabled {
                background-color: #9ca3af;
            }

            #secondaryButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 7px;
                padding: 10px 16px;
            }
            """
        )