from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class FriendlyLoadingState(QFrame):
    """
    Shared loading state used by data-heavy pages.

    The content is kept in one centered block with enough reserved
    space for wrapped text so labels and the progress bar can never
    visually collide.
    """

    def __init__(
        self,
        *,
        title: str = "Loading...",
        message: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.setObjectName(
            "friendlyLoadingState"
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.setMinimumHeight(
            280
        )

        # --------------------------------------------------
        # Outer centering layout
        # --------------------------------------------------

        outer = QVBoxLayout(
            self
        )

        outer.setContentsMargins(
            28,
            28,
            28,
            28,
        )

        outer.setSpacing(
            0
        )

        outer.addStretch(
            1
        )

        # --------------------------------------------------
        # Center content block
        # --------------------------------------------------

        content = QWidget(
            self
        )

        content.setObjectName(
            "loadingContent"
        )

        content.setMaximumWidth(
            560
        )

        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            12,
            8,
            12,
            8,
        )

        content_layout.setSpacing(
            14
        )

        # --------------------------------------------------
        # Title
        # --------------------------------------------------

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "placeholderTitle"
        )

        title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title_label.setWordWrap(
            False
        )

        title_label.setMinimumHeight(
            38
        )

        title_label.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )

        content_layout.addWidget(
            title_label,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )

        # --------------------------------------------------
        # Progress
        # --------------------------------------------------

        # Keep loading states intentionally minimal.
        # The title already explains what is happening.
        content_layout.addSpacing(
            8
        )

        progress = QProgressBar()

        progress.setObjectName(
            "loadingProgress"
        )

        progress.setRange(
            0,
            0,
        )

        progress.setTextVisible(
            False
        )

        progress.setFixedHeight(
            8
        )

        progress.setMinimumWidth(
            220
        )

        progress.setMaximumWidth(
            260
        )

        content_layout.addWidget(
            progress,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )

        outer.addWidget(
            content,
            0,
            Qt.AlignmentFlag.AlignCenter,
        )

        outer.addStretch(
            1
        )
