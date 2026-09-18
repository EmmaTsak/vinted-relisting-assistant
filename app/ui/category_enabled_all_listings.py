from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from app.ui.all_listings import (
    AllListingsPage,
)
from app.ui.category_manager import (
    CategoryManagerDialog,
)


class CategoryEnabledAllListingsPage(
    AllListingsPage
):
    """
    All Listings page with bulk category management.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self._add_category_toolbar()

    def _add_category_toolbar(
        self,
    ) -> None:
        toolbar = QFrame()

        toolbar.setObjectName(
            "categoryToolbar"
        )

        layout = QHBoxLayout(
            toolbar
        )

        layout.setContentsMargins(
            12,
            8,
            12,
            8,
        )

        label = QLabel(
            (
                "Organise imported listings "
                "into your own categories."
            )
        )

        label.setObjectName(
            "categoryHelpText"
        )

        layout.addWidget(
            label
        )

        layout.addStretch()

        category_button = QPushButton(
            "BULK CATEGORIES"
        )

        category_button.setObjectName(
            "categoryButton"
        )

        category_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        category_button.clicked.connect(
            self._open_category_manager
        )

        layout.addWidget(
            category_button
        )

        page_layout = self.layout()

        if page_layout is not None:
            page_layout.insertWidget(
                1,
                toolbar,
            )

        self.setStyleSheet(
            self.styleSheet()
            + """
            #categoryToolbar {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }

            #categoryHelpText {
                color: #6b7280;
                font-size: 12px;
            }

            #categoryButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }

            #categoryButton:hover {
                background-color: #f3f4f6;
            }
            """
        )

    def _open_category_manager(
        self,
    ) -> None:
        dialog = CategoryManagerDialog(
            parent=self
        )

        dialog.categories_changed.connect(
            self._categories_changed
        )

        dialog.exec()

    def _categories_changed(
        self,
    ) -> None:
        self.current_page = 1

        self.refresh()