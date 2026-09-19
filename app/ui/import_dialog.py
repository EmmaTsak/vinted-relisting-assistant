from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QObject,
    QThread,
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


class ImportListingsWorker(QObject):
    """
    Run the generic CSV / JSON importer outside the Qt UI thread.
    """

    completed = Signal(object)
    failed = Signal(object)

    def __init__(
        self,
        file_path: Path,
    ) -> None:
        super().__init__()

        self.file_path = file_path

    def run(
        self,
    ) -> None:
        try:
            result = import_listings_file(
                self.file_path
            )

        except Exception as exc:
            self.failed.emit(
                exc
            )

            return

        self.completed.emit(
            result
        )


class ImportListingsDialog(QDialog):
    """
    Generic CSV / JSON listing importer.

    Existing matching listings are skipped automatically.
    Vinted exports should still use the dedicated Vinted importer
    for Vinted item-ID and relist matching.
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

        self._import_thread: QThread | None = None
        self._import_worker: ImportListingsWorker | None = None

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
            preferred_width=780,
            preferred_height=780,
            minimum_width=660,
            minimum_height=650,
            width_ratio=0.92,
            height_ratio=0.90,
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

        self.status_label.setMinimumHeight(
            26
        )

        self.status_label.setContentsMargins(
            2,
            4,
            0,
            0,
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
                "Required: title and price. "
                "Other listing fields are imported when present.\n"
                "JSON imports can also include a local photos array."
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
                "Existing matching listings are skipped automatically. "
                "For Vinted personal-data exports, use IMPORT VINTED "
                "DATA EXPORT for Vinted ID and relist matching."
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
            120
        )

        self.result_output.setMaximumHeight(
            190
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

        buttons.setContentsMargins(
            0,
            8,
            0,
            0,
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
                "Review the import details above, "
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

        if (
            self._import_thread is not None
            and self._import_thread.isRunning()
        ):
            return

        confirmed = BrandedMessageDialog.ask(
            self,
            title="Confirm Import",
            message=(
                f"Import listings from {self.selected_file.name}?\n\n"
                "Existing listings will not be deleted. "
                "Listings that already exist in your local inventory "
                "will be skipped automatically."
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
            (
                "Importing listings and photos...\n\n"
                "You can continue to see the app responding "
                "while the import runs."
            )
        )

        thread = QThread(
            self
        )

        worker = ImportListingsWorker(
            self.selected_file
        )

        worker.moveToThread(
            thread
        )

        thread.started.connect(
            worker.run
        )

        worker.completed.connect(
            self._import_succeeded
        )

        worker.failed.connect(
            self._import_failed
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
            self._import_thread_finished
        )

        self._import_thread = thread
        self._import_worker = worker

        thread.start()

    def _import_succeeded(
        self,
        result,
    ) -> None:
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
            (
                "Warnings:            "
                f"{len(result.warnings)}"
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
                "Finished ? "
                f"{result.imported_count} listing(s) imported, "
                f"{result.skipped_count} skipped."
            )
        )

        if result.imported_count > 0:
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
                f"{result.skipped_count}\n"
                "Warnings: "
                f"{len(result.warnings)}"
            ),
        )

        # Return to the main application after the user
        # acknowledges the successful import summary.
        self._close_after_import = True

        if (
            self._import_thread is None
            or not self._import_thread.isRunning()
        ):
            self._close_after_import = False
            self.accept()

    def _import_failed(
        self,
        exc: object,
    ) -> None:
        if isinstance(
            exc,
            ImportFileError,
        ):
            message = str(
                exc
            )

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

            return

        if isinstance(
            exc,
            Exception,
        ):
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

        else:
            BrandedMessageDialog.error(
                self,
                title="Import Failed",
                message=(
                    "The listings could not be imported."
                ),
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

    def _import_thread_finished(
        self,
    ) -> None:
        thread = self._import_thread

        self._import_thread = None
        self._import_worker = None

        self.import_button.setEnabled(
            self.selected_file is not None
        )

        if thread is not None:
            thread.deleteLater()

        if getattr(
            self,
            "_close_after_import",
            False,
        ):
            self._close_after_import = False
            self.accept()

    def reject(
        self,
    ) -> None:
        if (
            self._import_thread is not None
            and self._import_thread.isRunning()
        ):
            BrandedMessageDialog.notice(
                self,
                title="Import in Progress",
                message=(
                    "The import is still running. "
                    "Keep this window open until it finishes."
                ),
            )

            return

        super().reject()

    def closeEvent(
        self,
        event,
    ) -> None:
        if (
            self._import_thread is not None
            and self._import_thread.isRunning()
        ):
            event.ignore()

            return

        super().closeEvent(
            event
        )


    def _apply_styles(
        self,
    ) -> None:
        """
        ThemeManager owns application styling.
        """
        return