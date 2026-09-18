from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.statistics_service import (
    DashboardStatistics,
    get_dashboard_statistics,
)


class StatisticCard(QFrame):
    """
    Small dashboard statistic card.
    """

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.setObjectName(
            "statisticCard"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        layout.setSpacing(
            4
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "statisticTitle"
        )

        value_label = QLabel(
            value
        )

        value_label.setObjectName(
            "statisticValue"
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        if subtitle:
            subtitle_label = QLabel(
                subtitle
            )

            subtitle_label.setObjectName(
                "statisticSubtitle"
            )

            subtitle_label.setWordWrap(
                True
            )

            layout.addWidget(
                subtitle_label
            )

        layout.addStretch()


class DashboardPage(QWidget):
    """
    Main statistics dashboard.
    """

    edit_requested = Signal(int)
    open_queue_requested = Signal()
    open_history_requested = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self._build_ui()

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

        top_row = QHBoxLayout()

        introduction = QLabel(
            (
                "Overview of your local inventory "
                "and relisting activity."
            )
        )

        introduction.setObjectName(
            "dashboardIntroduction"
        )

        refresh_button = QPushButton(
            "REFRESH"
        )

        refresh_button.setObjectName(
            "dashboardRefreshButton"
        )

        refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        refresh_button.clicked.connect(
            self.refresh
        )

        top_row.addWidget(
            introduction
        )

        top_row.addStretch()

        top_row.addWidget(
            refresh_button
        )

        root_layout.addLayout(
            top_row
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

        self.content = QWidget()

        self.content_layout = QVBoxLayout(
            self.content
        )

        self.content_layout.setContentsMargins(
            0,
            0,
            8,
            0,
        )

        self.content_layout.setSpacing(
            16
        )

        self.cards_container = QWidget()

        self.cards_layout = QGridLayout(
            self.cards_container
        )

        self.cards_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.cards_layout.setHorizontalSpacing(
            12
        )

        self.cards_layout.setVerticalSpacing(
            12
        )

        for column in range(
            4
        ):
            self.cards_layout.setColumnStretch(
                column,
                1,
            )

        self.content_layout.addWidget(
            self.cards_container
        )

        lower_row = QHBoxLayout()

        lower_row.setSpacing(
            14
        )

        self.attention_panel = (
            self._create_panel(
                "NEEDS ATTENTION"
            )
        )

        self.activity_panel = (
            self._create_panel(
                "RECENT RELISTING ACTIVITY"
            )
        )

        lower_row.addWidget(
            self.attention_panel,
            1,
        )

        lower_row.addWidget(
            self.activity_panel,
            1,
        )

        self.content_layout.addLayout(
            lower_row
        )

        self.content_layout.addStretch()

        self.scroll_area.setWidget(
            self.content
        )

        root_layout.addWidget(
            self.scroll_area,
            1,
        )

        self._apply_styles()

        self.refresh()

    def _create_panel(
        self,
        title: str,
    ) -> QFrame:
        panel = QFrame()

        panel.setObjectName(
            "dashboardPanel"
        )

        layout = QVBoxLayout(
            panel
        )

        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        layout.setSpacing(
            10
        )

        heading = QLabel(
            title
        )

        heading.setObjectName(
            "panelHeading"
        )

        layout.addWidget(
            heading
        )

        content = QWidget()

        content.setObjectName(
            "panelContent"
        )

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(
            10
        )

        content_layout.addStretch()

        layout.addWidget(
            content,
            1,
        )

        panel.content_layout = content_layout

        return panel

    def refresh(self) -> None:
        """
        Reload all dashboard statistics.
        """
        self._clear_stat_cards()

        self._clear_panel(
            self.attention_panel
        )

        self._clear_panel(
            self.activity_panel
        )

        try:
            statistics = (
                get_dashboard_statistics()
            )

        except Exception as exc:
            error = QLabel(
                (
                    "Unable to load dashboard statistics.\n\n"
                    f"{exc}"
                )
            )

            error.setObjectName(
                "dashboardError"
            )

            error.setWordWrap(
                True
            )

            self.cards_layout.addWidget(
                error,
                0,
                0,
                1,
                4,
            )

            return

        self._populate_stat_cards(
            statistics
        )

        self._populate_attention_panel(
            statistics
        )

        self._populate_activity_panel(
            statistics
        )

    def _populate_stat_cards(
        self,
        statistics: DashboardStatistics,
    ) -> None:
        average_text = (
            (
                f"{statistics.average_days_between_relists:.1f}"
            )
            if (
                statistics.average_days_between_relists
                is not None
            )
            else "—"
        )

        values = [
            (
                "Active Listings",
                str(
                    statistics.active_listings
                ),
                "Currently active inventory",
            ),
            (
                "Today's Queue",
                str(
                    statistics.queued_today
                ),
                (
                    f"{statistics.completed_today} "
                    "completed today"
                ),
            ),
            (
                "Relisted This Week",
                str(
                    statistics.relisted_this_week
                ),
                "Confirmed through this app",
            ),
            (
                "Relisted This Month",
                str(
                    statistics.relisted_this_month
                ),
                "Confirmed through this app",
            ),
            (
                "Sold Items",
                str(
                    statistics.sold_items
                ),
                "Retained in local inventory",
            ),
            (
                "Never Relisted",
                str(
                    statistics.never_relisted
                ),
                "Active listings",
            ),
            (
                "30+ Days",
                str(
                    statistics.older_than_30_days
                ),
                (
                    "Active listings since "
                    "last refresh"
                ),
            ),
            (
                "60+ Days",
                str(
                    statistics.older_than_60_days
                ),
                (
                    "Active listings since "
                    "last refresh"
                ),
            ),
            (
                "90+ Days",
                str(
                    statistics.older_than_90_days
                ),
                (
                    "Active listings since "
                    "last refresh"
                ),
            ),
            (
                "Avg. Days Between Relists",
                average_text,
                (
                    "Uses only known recorded "
                    "date intervals"
                ),
            ),
        ]

        for index, (
            title,
            value,
            subtitle,
        ) in enumerate(
            values
        ):
            row = (
                index
                // 4
            )

            column = (
                index
                % 4
            )

            card = StatisticCard(
                title=title,
                value=value,
                subtitle=subtitle,
            )

            self.cards_layout.addWidget(
                card,
                row,
                column,
            )

    def _populate_attention_panel(
        self,
        statistics: DashboardStatistics,
    ) -> None:
        layout = (
            self.attention_panel
            .content_layout
        )

        if (
            statistics.oldest_listing_id
            is not None
        ):
            oldest = QFrame()

            oldest.setObjectName(
                "attentionItem"
            )

            oldest_layout = QVBoxLayout(
                oldest
            )

            oldest_layout.setContentsMargins(
                12,
                10,
                12,
                10,
            )

            oldest_heading = QLabel(
                "Oldest listing needing refresh"
            )

            oldest_heading.setObjectName(
                "attentionHeading"
            )

            oldest_title = QLabel(
                (
                    statistics.oldest_listing_title
                    or "Unknown listing"
                )
            )

            oldest_title.setObjectName(
                "attentionTitle"
            )

            oldest_title.setWordWrap(
                True
            )

            oldest_days = QLabel(
                (
                    f"{statistics.oldest_listing_days} "
                    "days since last refresh"
                )
            )

            oldest_days.setObjectName(
                "attentionText"
            )

            oldest_button = QPushButton(
                "VIEW / EDIT"
            )

            oldest_button.setObjectName(
                "smallButton"
            )

            listing_id = (
                statistics.oldest_listing_id
            )

            oldest_button.clicked.connect(
                lambda checked=False,
                target_id=listing_id: (
                    self.edit_requested.emit(
                        target_id
                    )
                )
            )

            oldest_layout.addWidget(
                oldest_heading
            )

            oldest_layout.addWidget(
                oldest_title
            )

            oldest_layout.addWidget(
                oldest_days
            )

            oldest_layout.addWidget(
                oldest_button
            )

            layout.insertWidget(
                0,
                oldest
            )

        else:
            self._insert_panel_message(
                layout,
                "No active listings yet.",
            )

        if (
            statistics.most_relisted_listing_id
            is not None
        ):
            most_relisted = QFrame()

            most_relisted.setObjectName(
                "attentionItem"
            )

            most_layout = QVBoxLayout(
                most_relisted
            )

            most_layout.setContentsMargins(
                12,
                10,
                12,
                10,
            )

            heading = QLabel(
                "Most frequently relisted"
            )

            heading.setObjectName(
                "attentionHeading"
            )

            title = QLabel(
                (
                    statistics
                    .most_relisted_listing_title
                    or "Unknown listing"
                )
            )

            title.setObjectName(
                "attentionTitle"
            )

            title.setWordWrap(
                True
            )

            count = QLabel(
                (
                    f"{statistics.most_relisted_count} "
                    "total relists"
                )
            )

            count.setObjectName(
                "attentionText"
            )

            view_button = QPushButton(
                "VIEW / EDIT"
            )

            view_button.setObjectName(
                "smallButton"
            )

            listing_id = (
                statistics
                .most_relisted_listing_id
            )

            view_button.clicked.connect(
                lambda checked=False,
                target_id=listing_id: (
                    self.edit_requested.emit(
                        target_id
                    )
                )
            )

            most_layout.addWidget(
                heading
            )

            most_layout.addWidget(
                title
            )

            most_layout.addWidget(
                count
            )

            most_layout.addWidget(
                view_button
            )

            insert_position = max(
                0,
                layout.count() - 1,
            )

            layout.insertWidget(
                insert_position,
                most_relisted,
            )

        queue_button = QPushButton(
            "OPEN TODAY'S QUEUE"
        )

        queue_button.setObjectName(
            "panelActionButton"
        )

        queue_button.clicked.connect(
            self.open_queue_requested.emit
        )

        layout.insertWidget(
            max(
                0,
                layout.count() - 1,
            ),
            queue_button,
        )

    def _populate_activity_panel(
        self,
        statistics: DashboardStatistics,
    ) -> None:
        layout = (
            self.activity_panel
            .content_layout
        )

        if not statistics.recent_relists:
            self._insert_panel_message(
                layout,
                (
                    "No relisting activity has "
                    "been recorded yet."
                ),
            )

        else:
            for record in (
                statistics.recent_relists
            ):
                row = QFrame()

                row.setObjectName(
                    "activityRow"
                )

                row_layout = QHBoxLayout(
                    row
                )

                row_layout.setContentsMargins(
                    10,
                    8,
                    10,
                    8,
                )

                details = QVBoxLayout()

                title = QLabel(
                    record.title
                )

                title.setObjectName(
                    "activityTitle"
                )

                title.setWordWrap(
                    True
                )

                date_label = QLabel(
                    record.relisted_date.strftime(
                        "%d %B %Y"
                    )
                )

                date_label.setObjectName(
                    "activityDate"
                )

                details.addWidget(
                    title
                )

                details.addWidget(
                    date_label
                )

                row_layout.addLayout(
                    details,
                    1,
                )

                edit_button = QPushButton(
                    "VIEW"
                )

                edit_button.setObjectName(
                    "smallButton"
                )

                listing_id = (
                    record.listing_id
                )

                edit_button.clicked.connect(
                    lambda checked=False,
                    target_id=listing_id: (
                        self.edit_requested.emit(
                            target_id
                        )
                    )
                )

                row_layout.addWidget(
                    edit_button
                )

                layout.insertWidget(
                    max(
                        0,
                        layout.count() - 1,
                    ),
                    row,
                )

        history_button = QPushButton(
            "OPEN FULL HISTORY"
        )

        history_button.setObjectName(
            "panelActionButton"
        )

        history_button.clicked.connect(
            self.open_history_requested.emit
        )

        layout.insertWidget(
            max(
                0,
                layout.count() - 1,
            ),
            history_button,
        )

    def _insert_panel_message(
        self,
        layout: QVBoxLayout,
        text: str,
    ) -> None:
        label = QLabel(
            text
        )

        label.setObjectName(
            "panelMessage"
        )

        label.setWordWrap(
            True
        )

        layout.insertWidget(
            0,
            label,
        )

    def _clear_stat_cards(
        self,
    ) -> None:
        while (
            self.cards_layout.count()
            > 0
        ):
            item = (
                self.cards_layout.takeAt(
                    0
                )
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _clear_panel(
        self,
        panel: QFrame,
    ) -> None:
        layout = (
            panel.content_layout
        )

        while (
            layout.count()
            > 1
        ):
            item = layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #dashboardIntroduction {
                color: #6b7280;
                font-size: 14px;
            }

            #dashboardRefreshButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }

            #dashboardRefreshButton:hover {
                background-color: #f3f4f6;
            }

            #statisticCard {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                min-height: 105px;
            }

            #statisticTitle {
                color: #6b7280;
                font-size: 12px;
                font-weight: 600;
            }

            #statisticValue {
                color: #111827;
                font-size: 28px;
                font-weight: 700;
            }

            #statisticSubtitle {
                color: #9ca3af;
                font-size: 11px;
            }

            #dashboardPanel {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                min-height: 280px;
            }

            #panelHeading {
                color: #4b5563;
                font-size: 13px;
                font-weight: 700;
            }

            #attentionItem,
            #activityRow {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 7px;
            }

            #attentionHeading {
                color: #6b7280;
                font-size: 11px;
                font-weight: 700;
            }

            #attentionTitle,
            #activityTitle {
                color: #111827;
                font-size: 14px;
                font-weight: 600;
            }

            #attentionText,
            #activityDate,
            #panelMessage {
                color: #6b7280;
                font-size: 12px;
            }

            #smallButton,
            #panelActionButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 7px 11px;
                font-weight: 600;
            }

            #smallButton:hover,
            #panelActionButton:hover {
                background-color: #f3f4f6;
            }

            #dashboardError {
                background-color: #fef2f2;
                color: #991b1b;
                border: 1px solid #fecaca;
                border-radius: 10px;
                padding: 30px;
            }
            """
        )