from __future__ import annotations

from datetime import date

from PySide6.QtCore import (
    QTimer,
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
    HistoryUndoError,
    get_history_summary,
    get_relist_history,
    undo_relist,
)
from app.ui.components.states.empty_state import (
    FriendlyEmptyState,
)
from app.ui.components.states.loading_state import (
    FriendlyLoadingState,
)
from app.ui.components.dialogs.message_dialog import (
    BrandedMessageDialog,
)


class HistoryRecordRow(QFrame):
    """
    Compact relisting entry displayed inside one date group.
    """

    edit_requested = Signal(int)
    undo_requested = Signal(int)

    def __init__(
        self,
        record: HistoryRecord,
        undo_enabled: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.record = record
        self.undo_enabled = undo_enabled

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

        undo_button = QPushButton(
            "UNDO RELIST"
        )

        undo_button.setObjectName(
            "secondaryButton"
        )

        undo_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        undo_button.setMinimumWidth(
            108
        )

        undo_button.setEnabled(
            self.undo_enabled
        )

        if not self.undo_enabled:
            undo_button.setToolTip(
                "Only the most recent relist for this listing can be undone."
            )

        undo_button.clicked.connect(
            lambda: (
                self.undo_requested.emit(
                    self.record.id
                )
            )
        )

        layout.addWidget(
            undo_button
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
    undo_requested = Signal(int)

    def __init__(
        self,
        relisted_date: date,
        records: list[HistoryRecord],
        undoable_history_ids: set[int] | None = None,
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
        self.undoable_history_ids = (
            undoable_history_ids
            or set()
        )

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
                record,
                undo_enabled=(
                    record.id
                    in self.undoable_history_ids
                ),
            )

            row.edit_requested.connect(
                self.edit_requested.emit
            )

            row.undo_requested.connect(
                self.undo_requested.emit
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
        """
        Refresh relisting history while keeping the current content
        visible until the new history data is ready.
        """
        if getattr(
            self,
            "_refresh_pending",
            False,
        ):
            return

        self._refresh_pending = True

        QTimer.singleShot(
            0,
            self._run_deferred_refresh,
        )

    def _run_deferred_refresh(
        self,
    ) -> None:
        self._refresh_pending = False

        self._perform_refresh()

    def _perform_refresh(
        self,
    ) -> None:
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

            # Loading has failed. Replace any previously rendered
            # history with the error state rather than stacking the
            # error above stale history.
            self._clear_groups()

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

        # Data is ready. Replace the old rendered groups now,
        # rather than blanking the page during the database query.
        self._clear_groups()

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

        # Only the newest recorded relist for each listing
        # may be undone safely.
        undoable_history_ids: set[int] = set()
        seen_listing_ids: set[int] = set()

        for record in records:
            if (
                record.listing_id
                not in seen_listing_ids
            ):
                seen_listing_ids.add(
                    record.listing_id
                )

                undoable_history_ids.add(
                    record.id
                )

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
                undoable_history_ids=(
                    undoable_history_ids
                ),

                # Every date starts closed.
                expanded=False,
            )

            group.edit_requested.connect(
                self.edit_requested.emit
            )

            group.undo_requested.connect(
                self._undo_relist
            )

            self.groups_layout.insertWidget(
                index,
                group,
            )

    def _undo_relist(
        self,
        history_id: int,
    ) -> None:
        confirmed = BrandedMessageDialog.ask(
            self,
            title="Undo relist?",
            message=(
                "This will remove the latest relist record "
                "and restore the listing's previous relist date "
                "and count."
            ),
            confirm_text="UNDO RELIST",
            cancel_text="CANCEL",
        )

        if not confirmed:
            return

        try:
            undo_relist(
                history_id
            )

        except HistoryUndoError as exc:
            BrandedMessageDialog.warning(
                self,
                title="Unable to Undo",
                message=str(
                    exc
                ),
            )

            self.refresh()
            return

        except Exception:
            BrandedMessageDialog.error(
                self,
                title="Undo Failed",
                message=(
                    "The relist could not be undone. "
                    "Your existing history has been left unchanged."
                ),
            )

            return

        self.refresh()

        BrandedMessageDialog.notice(
            self,
            title="Relist Undone",
            message=(
                "The listing's latest relist record "
                "was successfully restored."
            ),
        )

    def _show_loading_state(
        self,
    ) -> None:
        self._clear_groups()

        loading = FriendlyLoadingState(
            title="Loading history?",
            message=(
                "Refreshing your relisting activity."
            ),
            parent=self.container,
        )

        loading.setMinimumHeight(
            300
        )

        self.groups_layout.insertWidget(
            0,
            loading,
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
