from __future__ import annotations

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.services.statistics_service import (
    DashboardStatistics,
    get_dashboard_statistics,
)


class DashboardMoment(QFrame):
    """
    Small friendly Dashboard moment.

    The Dashboard itself remains a functional working screen.
    This card adds a little personality using real dashboard
    state without changing any business logic.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.setObjectName(
            "informationBox"
        )

        self.setMinimumHeight(
            104
        )

        self._build_ui()

        self.refresh()

    def _build_ui(
        self,
    ) -> None:
        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            18,
            16,
            20,
            16,
        )

        layout.setSpacing(
            16
        )

        # -------------------------------------------------
        # Brand illustration
        # -------------------------------------------------

        self.icon_label = QLabel()

        self.icon_label.setFixedSize(
            66,
            66,
        )

        self.icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        app = QApplication.instance()

        if app is not None:
            icon = app.windowIcon()

            if not icon.isNull():
                self.icon_label.setPixmap(
                    icon.pixmap(
                        60,
                        60,
                    )
                )

        layout.addWidget(
            self.icon_label,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

        # -------------------------------------------------
        # Message
        # -------------------------------------------------

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            4
        )

        eyebrow = QLabel(
            "TODAY"
        )

        eyebrow.setObjectName(
            "sectionHeading"
        )

        self.title_label = QLabel()

        self.title_label.setObjectName(
            "placeholderTitle"
        )

        self.title_label.setWordWrap(
            True
        )

        self.message_label = QLabel()

        self.message_label.setObjectName(
            "informationText"
        )

        self.message_label.setWordWrap(
            True
        )

        text_layout.addWidget(
            eyebrow
        )

        text_layout.addWidget(
            self.title_label
        )

        text_layout.addWidget(
            self.message_label
        )

        layout.addLayout(
            text_layout,
            1,
        )

    # =====================================================
    # State
    # =====================================================

    def refresh(
        self,
    ) -> None:
        """
        Refresh the friendly message from the same statistics
        service already used by the Dashboard.

        If statistics are temporarily unavailable, the card falls
        back to neutral wording rather than showing an error.
        """
        try:
            statistics = (
                get_dashboard_statistics()
            )

        except Exception:
            self._show_fallback()

            return

        self._apply_statistics(
            statistics
        )

    def _apply_statistics(
        self,
        statistics: DashboardStatistics,
    ) -> None:
        active = (
            statistics.active_listings
        )

        queued = (
            statistics.queued_today
        )

        completed = (
            statistics.completed_today
        )

        # -------------------------------------------------
        # No inventory yet
        # -------------------------------------------------

        if active == 0:
            self.title_label.setText(
                "Your closet is ready when you are"
            )

            self.message_label.setText(
                (
                    "Add your first listing whenever you're ready. "
                    "Once your inventory grows, this little workspace "
                    "will help keep everything organised."
                )
            )

            return

        # -------------------------------------------------
        # Worked today + queue cleared
        # -------------------------------------------------

        if (
            completed > 0
            and queued == 0
        ):
            self.title_label.setText(
                "Today's queue is all clear"
            )

            relist_word = (
                "relist"
                if completed == 1
                else "relists"
            )

            self.message_label.setText(
                (
                    f"You've recorded {completed} {relist_word} "
                    "today. Nothing else is waiting in your queue."
                )
            )

            return

        # -------------------------------------------------
        # Worked today + more available
        # -------------------------------------------------

        if (
            completed > 0
            and queued > 0
        ):
            self.title_label.setText(
                "You're making lovely progress today"
            )

            completed_word = (
                "listing"
                if completed == 1
                else "listings"
            )

            queued_word = (
                "listing"
                if queued == 1
                else "listings"
            )

            self.message_label.setText(
                (
                    f"{completed} {completed_word} relisted, "
                    f"with {queued} {queued_word} still ready "
                    "whenever you want to continue."
                )
            )

            return

        # -------------------------------------------------
        # Queue ready, nothing completed yet
        # -------------------------------------------------

        if queued > 0:
            self.title_label.setText(
                "Your relisting list is ready"
            )

            queued_word = (
                "listing is"
                if queued == 1
                else "listings are"
            )

            self.message_label.setText(
                (
                    f"{queued} {queued_word} ready for today's "
                    "manual relisting routine."
                )
            )

            return

        # -------------------------------------------------
        # Nothing currently waiting
        # -------------------------------------------------

        self.title_label.setText(
            "Everything looks calm today"
        )

        self.message_label.setText(
            (
                "There's nothing waiting in today's queue right now. "
                "Your listings are still safely organised here."
            )
        )

    def _show_fallback(
        self,
    ) -> None:
        self.title_label.setText(
            "Your listing workspace is ready"
        )

        self.message_label.setText(
            (
                "Everything you need for your manual relisting "
                "routine is right here."
            )
        )