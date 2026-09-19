from __future__ import annotations

from datetime import date

from PySide6.QtCore import (
    Qt,
    Signal,
)
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
from app.ui.components.states.empty_state import (
    FriendlyEmptyState,
)


class HistoryRecordRow(QFrame):
    """
    Compact relisting entry displayed inside one date group.
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
            "activityRow"
        )

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            14,
            11,
            14,
            11,
        )

        layout.setSpacing(
            14
        )

        information = QVBoxLayout()

        information.setSpacing(
            4
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

        details = QLabel(
            self._build_details_text()
        )

        details.setObjectName(
            "historySecondaryText"
        )

        details.setWordWrap(
            True
        )

        information.addWidget(
            details
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

        edit_button.setMinimumWidth(
            100
        )

        edit_button.clicked.connect(
            lambda: (
                self.edit_requested.emit(
                    self.record.listing_id
                )
            )
        )

        layout.addWidget(
            edit_button
        )

    def _build_details_text(
        self,
    ) -> str:
        values: list[str] = []

        values.append(
            (
                "Recorded "
                f"{self.record.recorded_at:%H:%M}"
            )
        )

        if (
            self.record.previous_relisted_date
            is None
        ):
            values.append(
                "First recorded relist"
            )

        else:
            previous_text = (
                "Previous: "
                f"{self.record.previous_relisted_date:%d %b %Y}"
            )

            if (
                self.record.days_since_previous
                is not None
            ):
                previous_text += (
                    " · "
                    f"{self.record.days_since_previous} "
                    "days apart"
                )

            values.append(
                previous_text
            )

        values.append(
            (
                "Current total: "
                f"{self.record.current_relist_count}"
            )
        )

        return "   •   ".join(
            values
        )


class HistoryDayGroup(QFrame):
    """
    Collapsible collection of relisting records for one day.
    """

    edit_requested = Signal(int)

    def __init__(
        self,
        relisted_date: date,
        records: list[HistoryRecord],
        expanded: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.relisted_date = (
            relisted_date
        )

        self.records = records

        self.setObjectName(
            "historyCard"
        )

        self._build_ui(
            expanded=expanded
        )

    def _build_ui(
        self,
        expanded: bool,
    ) -> None:
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
            0
        )

        header = QFrame()

        header.setObjectName(
            "historyDateBox"
        )

        header_layout = QHBoxLayout(
            header
        )

        header_layout.setContentsMargins(
            16,
            11,
            12,
            11,
        )

        header_layout.setSpacing(
            10
        )

        date_label = QLabel(
            self.relisted_date.strftime(
                "%A, %d %B %Y"
            )
        )

        date_label.setObjectName(
            "historyPrimaryText"
        )

        header_layout.addWidget(
            date_label
        )

        count = len(
            self.records
        )

        if count == 1:
            count_text = (
                "1 relist"
            )

        else:
            count_text = (
                f"{count} relists"
            )

        count_label = QLabel(
            count_text
        )

        count_label.setObjectName(
            "historySecondaryText"
        )

        header_layout.addWidget(
            count_label
        )

        header_layout.addStretch()

        self.toggle_button = QPushButton()

        self.toggle_button.setObjectName(
            "smallButton"
        )

        self.toggle_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.toggle_button.setCheckable(
            True
        )

        self.toggle_button.setChecked(
            expanded
        )

        self.toggle_button.setMinimumWidth(
            94
        )

        self.toggle_button.toggled.connect(
            self._set_expanded
        )

        header_layout.addWidget(
            self.toggle_button
        )

        layout.addWidget(
            header
        )

        self.records_container = QWidget()

        records_layout = QVBoxLayout(
            self.records_container
        )

        records_layout.setContentsMargins(
            12,
            10,
            12,
            12,
        )

        records_layout.setSpacing(
            8
        )

        for record in self.records:
            row = HistoryRecordRow(
                record
            )

            row.edit_requested.connect(
                self.edit_requested.emit
            )

            records_layout.addWidget(
                row
            )

        layout.addWidget(
            self.records_container
        )

        self._set_expanded(
            expanded
        )

    def _set_expanded(
        self,
        expanded: bool,
    ) -> None:
        self.records_container.setVisible(
            expanded
        )

        self.toggle_button.setChecked(
            expanded
        )

        if expanded:
            self.toggle_button.setText(
                "COLLAPSE"
            )

        else:
            self.toggle_button.setText(
                "EXPAND"
            )


class HistoryPage(QWidget):
    """
    Recorded relisting history grouped into collapsible days.

    Every date group starts collapsed.
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

    def _build_ui(
        self,
    ) -> None:
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

        layout.addWidget(
            self.summary_frame
        )

        explanation = QLabel(
            (
                "Relisting activity is grouped by day. "
                "Expand a date to see the individual listings "
                "relisted on that day."
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

        self.scroll_area = (
            QScrollArea()
        )

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

        self.groups_layout = QVBoxLayout(
            self.container
        )

        self.groups_layout.setContentsMargins(
            0,
            0,
            6,
            0,
        )

        self.groups_layout.setSpacing(
            10
        )

        self.groups_layout.addStretch()

        self.scroll_area.setWidget(
            self.container
        )

        layout.addWidget(
            self.scroll_area,
            1,
        )

        self.refresh()

    def refresh(
        self,
    ) -> None:
        self._clear_groups()

        try:
            records = (
                get_relist_history()
            )

            summary = (
                get_history_summary()
            )

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

            self.groups_layout.insertWidget(
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

        # -------------------------------------------------
        # Friendly first-history state
        # -------------------------------------------------

        if not records:
            empty = FriendlyEmptyState(
                title=(
                    "No Relisting History Yet"
                ),
                message=(
                    "Once you manually relist an item and confirm "
                    "MARK RELISTED, its relisting history will "
                    "appear here."
                ),
                parent=self.container,
            )

            # History is rendered inside a scroll area, so keep
            # enough vertical room for the empty-state content.
            empty.setMinimumHeight(
                300
            )

            self.groups_layout.insertWidget(
                0,
                empty,
            )

            return

        grouped: dict[
            date,
            list[HistoryRecord],
        ] = {}

        for record in records:
            grouped.setdefault(
                record.relisted_date,
                [],
            ).append(
                record
            )

        for index, (
            relisted_date,
            day_records,
        ) in enumerate(
            grouped.items()
        ):
            group = HistoryDayGroup(
                relisted_date=(
                    relisted_date
                ),
                records=day_records,

                # Every date starts closed.
                expanded=False,
            )

            group.edit_requested.connect(
                self.edit_requested.emit
            )

            self.groups_layout.insertWidget(
                index,
                group,
            )

    def _clear_groups(
        self,
    ) -> None:
        while (
            self.groups_layout.count()
            > 1
        ):
            item = (
                self.groups_layout.takeAt(
                    0
                )
            )

            widget = (
                item.widget()
            )

            if widget is not None:
                widget.deleteLater()
