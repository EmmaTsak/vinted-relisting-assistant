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
    Compact high-level dashboard statistic.
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

        self.setMinimumHeight(
            112
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            18,
            15,
            18,
            15,
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


class HealthMetric(QFrame):
    """
    Smaller inventory-health statistic.
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
            "attentionItem"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        layout.setSpacing(
            3
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
            "summaryValue"
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
    Main command-centre dashboard.

    Shows:
    - high-level inventory statistics
    - inventory health
    - listings needing attention
    - recent relisting activity
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

        self.content = QWidget()

        self.content_layout = QVBoxLayout(
            self.content
        )

        self.content_layout.setContentsMargins(
            0,
            0,
            8,
            10,
        )

        self.content_layout.setSpacing(
            18
        )

        self._build_primary_statistics()

        self._build_health_section()

        self._build_lower_section()

        self.content_layout.addStretch()

        self.scroll_area.setWidget(
            self.content
        )

        root_layout.addWidget(
            self.scroll_area,
            1,
        )

        self.refresh()

    def _build_primary_statistics(
        self,
    ) -> None:
        self.primary_cards_container = (
            QWidget()
        )

        self.primary_cards_layout = (
            QGridLayout(
                self.primary_cards_container
            )
        )

        self.primary_cards_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.primary_cards_layout.setHorizontalSpacing(
            12
        )

        self.primary_cards_layout.setVerticalSpacing(
            12
        )

        for column in range(
            4
        ):
            self.primary_cards_layout.setColumnStretch(
                column,
                1,
            )

        self.content_layout.addWidget(
            self.primary_cards_container
        )

    def _build_health_section(
        self,
    ) -> None:
        self.health_panel = QFrame()

        self.health_panel.setObjectName(
            "dashboardPanel"
        )

        layout = QVBoxLayout(
            self.health_panel
        )

        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        layout.setSpacing(
            12
        )

        heading_row = QHBoxLayout()

        heading = QLabel(
            "INVENTORY HEALTH"
        )

        heading.setObjectName(
            "panelHeading"
        )

        explanation = QLabel(
            (
                "Age is measured from the last relist, "
                "or the original listing date if never relisted."
            )
        )

        explanation.setObjectName(
            "panelMessage"
        )

        explanation.setWordWrap(
            True
        )

        heading_row.addWidget(
            heading
        )

        heading_row.addSpacing(
            12
        )

        heading_row.addWidget(
            explanation,
            1,
        )

        layout.addLayout(
            heading_row
        )

        self.health_metrics_container = (
            QWidget()
        )

        self.health_metrics_layout = (
            QGridLayout(
                self.health_metrics_container
            )
        )

        self.health_metrics_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.health_metrics_layout.setHorizontalSpacing(
            10
        )

        self.health_metrics_layout.setVerticalSpacing(
            10
        )

        for column in range(
            4
        ):
            self.health_metrics_layout.setColumnStretch(
                column,
                1,
            )

        layout.addWidget(
            self.health_metrics_container
        )

        self.average_interval_label = QLabel()

        self.average_interval_label.setObjectName(
            "informationText"
        )

        self.average_interval_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.average_interval_label
        )

        self.content_layout.addWidget(
            self.health_panel
        )

    def _build_lower_section(
        self,
    ) -> None:
        lower_layout = QHBoxLayout()

        lower_layout.setSpacing(
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

        lower_layout.addWidget(
            self.attention_panel,
            1,
        )

        lower_layout.addWidget(
            self.activity_panel,
            1,
        )

        self.content_layout.addLayout(
            lower_layout
        )

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
            9
        )

        content_layout.addStretch()

        layout.addWidget(
            content,
            1,
        )

        panel.content_layout = (
            content_layout
        )

        return panel

    def refresh(
        self,
    ) -> None:
        """
        Reload all dashboard information from SQLite.
        """
        self._clear_layout(
            self.primary_cards_layout
        )

        self._clear_layout(
            self.health_metrics_layout
        )

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
                "historyError"
            )

            error.setWordWrap(
                True
            )

            self.primary_cards_layout.addWidget(
                error,
                0,
                0,
                1,
                4,
            )

            return

        self._populate_primary_statistics(
            statistics
        )

        self._populate_health_section(
            statistics
        )

        self._populate_attention_panel(
            statistics
        )

        self._populate_activity_panel(
            statistics
        )

    def _populate_primary_statistics(
        self,
        statistics: DashboardStatistics,
    ) -> None:
        queue_subtitle = (
            f"{statistics.completed_today} completed today"
        )

        cards = [
            (
                "ACTIVE LISTINGS",
                str(
                    statistics.active_listings
                ),
                "Current active inventory",
            ),
            (
                "TODAY'S QUEUE",
                str(
                    statistics.queued_today
                ),
                queue_subtitle,
            ),
            (
                "RELISTED THIS WEEK",
                str(
                    statistics.relisted_this_week
                ),
                "Confirmed through this app",
            ),
            (
                "SOLD",
                str(
                    statistics.sold_items
                ),
                "Retained in local inventory",
            ),
        ]

        for column, (
            title,
            value,
            subtitle,
        ) in enumerate(
            cards
        ):
            card = StatisticCard(
                title=title,
                value=value,
                subtitle=subtitle,
            )

            self.primary_cards_layout.addWidget(
                card,
                0,
                column,
            )

    def _populate_health_section(
        self,
        statistics: DashboardStatistics,
    ) -> None:
        metrics = [
            (
                "NEVER RELISTED",
                str(
                    statistics.never_relisted
                ),
                "Active listings",
            ),
            (
                "30+ DAYS",
                str(
                    statistics.older_than_30_days
                ),
                "Since last refresh",
            ),
            (
                "60+ DAYS",
                str(
                    statistics.older_than_60_days
                ),
                "Since last refresh",
            ),
            (
                "90+ DAYS",
                str(
                    statistics.older_than_90_days
                ),
                "Since last refresh",
            ),
        ]

        for column, (
            title,
            value,
            subtitle,
        ) in enumerate(
            metrics
        ):
            metric = HealthMetric(
                title=title,
                value=value,
                subtitle=subtitle,
            )

            self.health_metrics_layout.addWidget(
                metric,
                0,
                column,
            )

        if (
            statistics.average_days_between_relists
            is None
        ):
            average_text = (
                "Average between known relists: "
                "not enough recorded history yet."
            )

        else:
            average_text = (
                "Average between known relists: "
                f"{statistics.average_days_between_relists:.1f} days."
            )

        self.average_interval_label.setText(
            average_text
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
                14,
                12,
                14,
                12,
            )

            oldest_layout.setSpacing(
                5
            )

            heading = QLabel(
                "OLDEST LISTING"
            )

            heading.setObjectName(
                "attentionHeading"
            )

            title = QLabel(
                (
                    statistics.oldest_listing_title
                    or "Unknown listing"
                )
            )

            title.setObjectName(
                "attentionTitle"
            )

            title.setWordWrap(
                True
            )

            days = QLabel(
                (
                    f"{statistics.oldest_listing_days} "
                    "days since last refresh"
                )
            )

            days.setObjectName(
                "attentionText"
            )

            view_button = QPushButton(
                "VIEW / EDIT LISTING"
            )

            view_button.setObjectName(
                "smallButton"
            )

            view_button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            listing_id = (
                statistics.oldest_listing_id
            )

            view_button.clicked.connect(
                lambda checked=False,
                target_id=listing_id:
                self.edit_requested.emit(
                    target_id
                )
            )

            oldest_layout.addWidget(
                heading
            )

            oldest_layout.addWidget(
                title
            )

            oldest_layout.addWidget(
                days
            )

            oldest_layout.addWidget(
                view_button
            )

            layout.insertWidget(
                max(
                    0,
                    layout.count() - 1,
                ),
                oldest,
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
                14,
                12,
                14,
                12,
            )

            most_layout.setSpacing(
                5
            )

            heading = QLabel(
                "MOST FREQUENTLY RELISTED"
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
                "VIEW / EDIT LISTING"
            )

            view_button.setObjectName(
                "smallButton"
            )

            view_button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            listing_id = (
                statistics.most_relisted_listing_id
            )

            view_button.clicked.connect(
                lambda checked=False,
                target_id=listing_id:
                self.edit_requested.emit(
                    target_id
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

            layout.insertWidget(
                max(
                    0,
                    layout.count() - 1,
                ),
                most_relisted,
            )

        queue_button = QPushButton(
            "OPEN TODAY'S QUEUE"
        )

        queue_button.setObjectName(
            "panelActionButton"
        )

        queue_button.setCursor(
            Qt.CursorShape.PointingHandCursor
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
                    12,
                    9,
                    12,
                    9,
                )

                row_layout.setSpacing(
                    10
                )

                details = QVBoxLayout()

                details.setSpacing(
                    3
                )

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

                view_button = QPushButton(
                    "VIEW"
                )

                view_button.setObjectName(
                    "smallButton"
                )

                view_button.setCursor(
                    Qt.CursorShape.PointingHandCursor
                )

                listing_id = (
                    record.listing_id
                )

                view_button.clicked.connect(
                    lambda checked=False,
                    target_id=listing_id:
                    self.edit_requested.emit(
                        target_id
                    )
                )

                row_layout.addWidget(
                    view_button
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

        history_button.setCursor(
            Qt.CursorShape.PointingHandCursor
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
        message = QLabel(
            text
        )

        message.setObjectName(
            "panelMessage"
        )

        message.setWordWrap(
            True
        )

        layout.insertWidget(
            max(
                0,
                layout.count() - 1,
            ),
            message,
        )

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

    def _clear_layout(
        self,
        layout: QGridLayout,
    ) -> None:
        while (
            layout.count()
            > 0
        ):
            item = layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()