from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.history_service import (
    HistoryRecord,
    get_history_summary,
    get_relist_history,
)


class HistoryCard(QFrame):
    """
    Visual representation of one successful relisting event.
    """

    edit_requested = Signal(int)

    def __init__(
        self,
        record: HistoryRecord,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.record = record

        self.setObjectName(
            "historyCard"
        )

        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        layout.setSpacing(
            18
        )

        date_box = QFrame()

        date_box.setObjectName(
            "historyDateBox"
        )

        date_box.setFixedSize(
            90,
            82,
        )

        date_layout = QVBoxLayout(
            date_box
        )

        date_layout.setContentsMargins(
            6,
            8,
            6,
            8,
        )

        day = QLabel(
            self.record.relisted_date.strftime(
                "%d"
            )
        )

        day.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        day.setObjectName(
            "historyDay"
        )

        month = QLabel(
            self.record.relisted_date.strftime(
                "%b %Y"
            )
        )

        month.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        month.setObjectName(
            "historyMonth"
        )

        date_layout.addWidget(
            day
        )

        date_layout.addWidget(
            month
        )

        layout.addWidget(
            date_box
        )

        information = QVBoxLayout()

        information.setSpacing(
            5
        )

        title = QLabel(
            self.record.title
        )

        title.setObjectName(
            "historyTitle"
        )

        title.setWordWrap(
            True
        )

        information.addWidget(
            title
        )

        relisted_text = QLabel(
            (
                "Relisted on "
                f"{self.record.relisted_date:%d %B %Y}"
            )
        )

        relisted_text.setObjectName(
            "historyPrimaryText"
        )

        information.addWidget(
            relisted_text
        )

        if (
            self.record.previous_relisted_date
            is None
        ):
            previous_text = (
                "Previous relist: none recorded"
            )

        else:
            previous_text = (
                "Previous relist: "
                f"{self.record.previous_relisted_date:%d %B %Y}"
            )

            if (
                self.record.days_since_previous
                is not None
            ):
                previous_text += (
                    "  •  "
                    f"{self.record.days_since_previous} "
                    "days between relists"
                )

        previous = QLabel(
            previous_text
        )

        previous.setObjectName(
            "historySecondaryText"
        )

        previous.setWordWrap(
            True
        )

        information.addWidget(
            previous
        )

        recorded = QLabel(
            (
                "Recorded in assistant: "
                f"{self.record.recorded_at:%d %b %Y %H:%M}"
                "  •  "
                "Current total relist count: "
                f"{self.record.current_relist_count}"
            )
        )

        recorded.setObjectName(
            "historySecondaryText"
        )

        recorded.setWordWrap(
            True
        )

        information.addWidget(
            recorded
        )

        layout.addLayout(
            information,
            1,
        )

        edit_button = QPushButton(
            "VIEW / EDIT"
        )

        edit_button.setObjectName(
            "historyEditButton"
        )

        edit_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        edit_button.clicked.connect(
            lambda: self.edit_requested.emit(
                self.record.listing_id
            )
        )

        layout.addWidget(
            edit_button,
            0,
            Qt.AlignmentFlag.AlignTop,
        )

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #historyCard {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }

            #historyCard:hover {
                border: 1px solid #cbd5e1;
            }

            #historyDateBox {
                background-color: #f3f4f6;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }

            #historyDay {
                color: #111827;
                font-size: 25px;
                font-weight: 700;
            }

            #historyMonth {
                color: #6b7280;
                font-size: 12px;
                font-weight: 600;
            }

            #historyTitle {
                color: #111827;
                font-size: 17px;
                font-weight: 700;
            }

            #historyPrimaryText {
                color: #374151;
                font-size: 14px;
                font-weight: 600;
            }

            #historySecondaryText {
                color: #6b7280;
                font-size: 12px;
            }

            #historyEditButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 13px;
                min-width: 100px;
                font-weight: 600;
            }

            #historyEditButton:hover {
                background-color: #f3f4f6;
            }
            """
        )


class HistoryPage(QWidget):
    """
    Complete recorded relisting history page.
    """

    edit_requested = Signal(int)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            14
        )

        self.summary_frame = QFrame()

        self.summary_frame.setObjectName(
            "historySummary"
        )

        summary_layout = QHBoxLayout(
            self.summary_frame
        )

        summary_layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        summary_layout.setSpacing(
            30
        )

        self.total_label = QLabel(
            "Recorded relists: 0"
        )

        self.total_label.setObjectName(
            "summaryValue"
        )

        self.listings_label = QLabel(
            "Listings with history: 0"
        )

        self.listings_label.setObjectName(
            "summaryValue"
        )

        self.month_label = QLabel(
            "This month: 0"
        )

        self.month_label.setObjectName(
            "summaryValue"
        )

        refresh_button = QPushButton(
            "REFRESH"
        )

        refresh_button.setObjectName(
            "historyRefreshButton"
        )

        refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        refresh_button.clicked.connect(
            self.refresh
        )

        summary_layout.addWidget(
            self.total_label
        )

        summary_layout.addWidget(
            self.listings_label
        )

        summary_layout.addWidget(
            self.month_label
        )

        summary_layout.addStretch()

        summary_layout.addWidget(
            refresh_button
        )

        layout.addWidget(
            self.summary_frame
        )

        explanation = QLabel(
            (
                "History contains relists confirmed through "
                "Vinted Relisting Assistant. Existing relist counts "
                "imported without dates are not converted into "
                "made-up history records."
            )
        )

        explanation.setWordWrap(
            True
        )

        explanation.setObjectName(
            "historyExplanation"
        )

        layout.addWidget(
            explanation
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

        self.container = QWidget()

        self.cards_layout = QVBoxLayout(
            self.container
        )

        self.cards_layout.setContentsMargins(
            0,
            0,
            6,
            0,
        )

        self.cards_layout.setSpacing(
            12
        )

        self.cards_layout.addStretch()

        self.scroll_area.setWidget(
            self.container
        )

        layout.addWidget(
            self.scroll_area,
            1,
        )

        self.setStyleSheet(
            """
            #historySummary {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 9px;
            }

            #summaryValue {
                color: #111827;
                font-size: 14px;
                font-weight: 700;
            }

            #historyExplanation {
                color: #6b7280;
                font-size: 13px;
            }

            #historyRefreshButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }

            #historyRefreshButton:hover {
                background-color: #f3f4f6;
            }

            #historyEmpty {
                background-color: white;
                color: #6b7280;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 40px;
                font-size: 15px;
            }

            #historyError {
                background-color: #fef2f2;
                color: #991b1b;
                border: 1px solid #fecaca;
                border-radius: 10px;
                padding: 25px;
            }
            """
        )

        self.refresh()

    def refresh(self) -> None:
        """
        Reload history from SQLite.
        """
        self._clear_cards()

        try:
            records = get_relist_history()

            summary = get_history_summary()

        except Exception as exc:
            self.total_label.setText(
                "History unavailable"
            )

            self.listings_label.setText(
                ""
            )

            self.month_label.setText(
                ""
            )

            error = QLabel(
                (
                    "Unable to load relisting history.\n\n"
                    f"{exc}"
                )
            )

            error.setObjectName(
                "historyError"
            )

            error.setWordWrap(
                True
            )

            self.cards_layout.insertWidget(
                0,
                error,
            )

            return

        self.total_label.setText(
            (
                "Recorded relists: "
                f"{summary.total_recorded_relists}"
            )
        )

        self.listings_label.setText(
            (
                "Listings with history: "
                f"{summary.unique_listings}"
            )
        )

        self.month_label.setText(
            (
                "This month: "
                f"{summary.recorded_this_month}"
            )
        )

        if not records:
            empty = QLabel(
                (
                    "No relisting history has been recorded yet.\n\n"
                    "When you manually publish an item on Vinted "
                    "and confirm MARK AS RELISTED, its history "
                    "will appear here."
                )
            )

            empty.setObjectName(
                "historyEmpty"
            )

            empty.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            empty.setWordWrap(
                True
            )

            self.cards_layout.insertWidget(
                0,
                empty,
            )

            return

        for index, record in enumerate(
            records
        ):
            card = HistoryCard(
                record
            )

            card.edit_requested.connect(
                self.edit_requested.emit
            )

            self.cards_layout.insertWidget(
                index,
                card,
            )

    def _clear_cards(self) -> None:
        """
        Remove existing history cards while retaining the
        final stretch item.
        """
        while (
            self.cards_layout.count()
            > 1
        ):
            item = self.cards_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()