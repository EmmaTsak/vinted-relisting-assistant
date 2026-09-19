from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.dialog_geometry import (
    fit_dialog_to_screen,
)
from app.services.import_service import (
    ImportFileError,
    import_listings_file,
)
from app.ui.components.dialogs.error_feedback import (
    show_logged_error,
)
from app.ui.components.dialogs.message_dialog import (
    BrandedMessageDialog,
)


class ImportListingsDialog(QDialog):
    """
    Generic CSV / JSON listing importer.

    Important:
    This importer does not have the Vinted item-ID duplicate
    protection used by the dedicated Vinted data importer.
    """

    import_completed = Signal(int)

    CONTROL_HEIGHT = 40

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.selected_file: Path | None = None

        self.setWindowTitle(
            "Import CSV / JSON"
        )

        self.setModal(
            True
        )

        self.resize(
            740,
            650,
        )

        self.setMinimumSize(
            660,
            560,
        )

        self._build_ui()

        fit_dialog_to_screen(
            self,
            preferred_width=740,
            preferred_height=620,
            minimum_width=600,
            minimum_height=460,
            width_ratio=0.88,
            height_ratio=0.82,
        )

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

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        heading = QLabel(
            "Import CSV / JSON"
        )

        heading.setObjectName(
            "preparationHeading"
        )

        description = QLabel(
            (
                "Import listings from your own structured "
                "CSV or JSON file."
            )
        )

        description.setObjectName(
            "informationText"
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

        # -------------------------------------------------
        # File selection
        # -------------------------------------------------

        file_section = QFrame()

        file_section.setObjectName(
            "informationBox"
        )

        file_layout = QVBoxLayout(
            file_section
        )

        file_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        file_layout.setSpacing(
            9
        )

        file_title = QLabel(
            "IMPORT FILE"
        )

        file_title.setObjectName(
            "sectionHeading"
        )

        file_layout.addWidget(
            file_title
        )

        file_row = QHBoxLayout()

        file_row.setSpacing(
            8
        )

        self.file_input = QLineEdit()

        self.file_input.setReadOnly(
            True
        )

        self.file_input.setPlaceholderText(
            "Choose a .csv or .json file"
        )

        self.file_input.setMinimumHeight(
            self.CONTROL_HEIGHT
        )

        browse_button = QPushButton(
            "CHOOSE FILE"
        )

        browse_button.setObjectName(
            "secondaryButton"
        )

        browse_button.setMinimumHeight(
            self.CONTROL_HEIGHT
        )

        browse_button.setCursor(
            Qt.CursorShape.PointingHandCursor
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

        file_layout.addLayout(
            file_row
        )

        self.status_label = QLabel(
            "No import file selected."
        )

        self.status_label.setObjectName(
            "informationText"
        )

        self.status_label.setWordWrap(
            True
        )

        file_layout.addWidget(
            self.status_label
        )

        layout.addWidget(
            file_section
        )

        # -------------------------------------------------
        # Format information
        # -------------------------------------------------

        format_section = QFrame()

        format_section.setObjectName(
            "informationBox"
        )

        format_layout = QVBoxLayout(
            format_section
        )

        format_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        format_layout.setSpacing(
            7
        )

        format_title = QLabel(
            "FORMAT INFORMATION"
        )

        format_title.setObjectName(
            "sectionHeading"
        )

        information = QLabel(
            (
                "Required fields:\n"
                "• title\n"
                "• price\n\n"
                "JSON files can also contain a photos array:\n"
                '\"photos\": [\"photo1.jpg\", \"photo2.jpg\"]\n\n'
                "Relative photo paths are resolved from the "
                "location of the JSON file. Imported photos are "
                "copied into the assistant's own local storage."
            )
        )

        information.setObjectName(
            "informationText"
        )

        information.setWordWrap(
            True
        )

        information.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        format_layout.addWidget(
            format_title
        )

        format_layout.addWidget(
            information
        )

        layout.addWidget(
            format_section
        )

        # -------------------------------------------------
        # Duplicate warning
        # -------------------------------------------------

        warning = QLabel(
            (
                "Generic CSV / JSON imports do not use Vinted "
                "item-ID duplicate detection.\n\n"
                "Importing the same file more than once may create "
                "duplicate listings. For Vinted personal-data exports, "
                "use IMPORT VINTED DATA EXPORT instead."
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

        # -------------------------------------------------
        # Results
        # -------------------------------------------------

        results_title = QLabel(
            "IMPORT RESULTS"
        )

        results_title.setObjectName(
            "sectionHeading"
        )

        layout.addWidget(
            results_title
        )

        self.result_output = QTextEdit()

        self.result_output.setReadOnly(
            True
        )

        self.result_output.setPlaceholderText(
            "Import results will appear here."
        )

        self.result_output.setMinimumHeight(
            150
        )

        layout.addWidget(
            self.result_output,
            1,
        )

        # -------------------------------------------------
        # Footer
        # -------------------------------------------------

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
            self.CONTROL_HEIGHT
        )

        close_button.setMinimumWidth(
            100
        )

        close_button.setCursor(
            Qt.CursorShape.PointingHandCursor
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

        self.import_button.setMinimumHeight(
            self.CONTROL_HEIGHT
        )

        self.import_button.setMinimumWidth(
            150
        )

        self.import_button.setCursor(
            Qt.CursorShape.PointingHandCursor
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

    # =====================================================
    # File selection
    # =====================================================

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

        self.selected_file = path

        self.file_input.setText(
            str(
                path
            )
        )

        self.status_label.setText(
            (
                "Ready to import: "
                f"{path.name}"
            )
        )

        self.result_output.setPlainText(
            (
                "File selected successfully.\n\n"
                f"{path}\n\n"
                "Review the duplicate warning above, "
                "then choose IMPORT LISTINGS."
            )
        )

        self.import_button.setEnabled(
            True
        )

    # =====================================================
    # Import
    # =====================================================

    def _run_import(
        self,
    ) -> None:
        if self.selected_file is None:
            return

        confirmed = BrandedMessageDialog.ask(
            self,
            title="Confirm Import",
            message=(
                f"Import listings from {self.selected_file.name}?\n\n"
                "Existing listings will not be deleted. "
                "Generic CSV / JSON imports do not have "
                "Vinted item-ID duplicate protection."
            ),
            confirm_text="IMPORT",
            cancel_text="CANCEL",
        )

        if not confirmed:
            return

        self.import_button.setEnabled(
            False
        )

        self.status_label.setText(
            "Importing listings..."
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
            message = str(exc)

            BrandedMessageDialog.error(
                self,
                title="Import Failed",
                message=message,
            )

            self.status_label.setText(
                "Import failed."
            )

            self.result_output.setPlainText(
                message
            )

            self.import_button.setEnabled(
                True
            )

            return

        except Exception as exc:
            show_logged_error(
                self,
                title="Import Failed",
                message=(
                    "The listings could not be imported."
                ),
                context=(
                    "Unexpected CSV / JSON import failure"
                ),
                exception=exc,
            )

            self.status_label.setText(
                "Import failed."
            )

            self.result_output.setPlainText(
                (
                    "The import could not be completed.\n\n"
                    "Technical details were saved to the app log."
                )
            )

            self.import_button.setEnabled(
                True
            )

            return

        lines = [
            "IMPORT COMPLETE",
            "",
            (
                "Rows found:          "
                f"{result.total_rows}"
            ),
            (
                "Listings imported:   "
                f"{result.imported_count}"
            ),
            (
                "Listings skipped:    "
                f"{result.skipped_count}"
            ),
            (
                "Photos imported:     "
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
                "Finished — "
                f"{result.imported_count} listing(s) imported, "
                f"{result.skipped_count} skipped."
            )
        )

        if (
            result.imported_count
            > 0
        ):
            self.import_completed.emit(
                result.imported_count
            )

        BrandedMessageDialog.notice(
            self,
            title="Import Complete",
            message=(
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
        """
        ThemeManager owns application styling.
        """
        return