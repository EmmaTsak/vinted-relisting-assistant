from __future__ import annotations

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app import (
    APP_VERSION,
)
from app.ui.main_window import (
    MainWindow,
)


class PolishedMainWindow(MainWindow):
    """
    Polished application shell.

    MainWindow continues to handle:
    - lazy page loading
    - dirty-page refresh
    - dialogs
    - settings
    - listing lifecycle changes

    This class handles the visual shell only.
    """

    PAGE_SUBTITLES = {
        "Dashboard": (
            "Overview of your inventory, relisting activity "
            "and items that may need attention."
        ),
        "Today's Queue": (
            "Listings selected for today's manual "
            "relisting workflow."
        ),
        "All Listings": (
            "Search, filter and manage your complete "
            "local listing inventory."
        ),
        "Add Listing": (
            "Create a listing manually or import "
            "existing listing data."
        ),
        "History": (
            "Review your manual relisting activity "
            "grouped by day."
        ),
        "Sold": (
            "Listings you have marked as sold."
        ),
        "Archived": (
            "Listings currently stored in your archive."
        ),
        "Settings": (
            "Configure relisting rules, storage "
            "and application preferences."
        ),
    }

    def _create_sidebar(
        self,
    ) -> QWidget:
        sidebar = QFrame()

        sidebar.setObjectName(
            "sidebar"
        )

        sidebar.setFixedWidth(
            238
        )

        layout = QVBoxLayout(
            sidebar
        )

        layout.setContentsMargins(
            16,
            24,
            16,
            18,
        )

        layout.setSpacing(
            6
        )

        app_name = QLabel(
            "Vinted"
        )

        app_name.setObjectName(
            "sidebarAppName"
        )

        subtitle = QLabel(
            "Relisting Assistant"
        )

        subtitle.setObjectName(
            "sidebarSubtitle"
        )

        workspace_label = QLabel(
            "LOCAL WORKSPACE"
        )

        workspace_label.setObjectName(
            "versionLabel"
        )

        layout.addWidget(
            app_name
        )

        layout.addWidget(
            subtitle
        )

        layout.addSpacing(
            4
        )

        layout.addWidget(
            workspace_label
        )

        layout.addSpacing(
            20
        )

        self._add_navigation_group(
            layout=layout,
            title="OVERVIEW",
            pages=[
                "Dashboard",
                "Today's Queue",
            ],
        )

        layout.addSpacing(
            10
        )

        self._add_navigation_group(
            layout=layout,
            title="INVENTORY",
            pages=[
                "All Listings",
                "Add Listing",
            ],
        )

        layout.addSpacing(
            10
        )

        self._add_navigation_group(
            layout=layout,
            title="ACTIVITY",
            pages=[
                "History",
                "Sold",
                "Archived",
            ],
        )

        layout.addSpacing(
            10
        )

        self._add_navigation_group(
            layout=layout,
            title="APP",
            pages=[
                "Settings",
            ],
        )

        layout.addStretch()

        quick_add_button = QPushButton(
            "NEW LISTING"
        )

        quick_add_button.setObjectName(
            "primaryButton"
        )

        quick_add_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        quick_add_button.setMinimumHeight(
            40
        )

        quick_add_button.setToolTip(
            "Create a new listing"
        )

        quick_add_button.clicked.connect(
            self.open_add_listing_dialog
        )

        layout.addWidget(
            quick_add_button
        )

        layout.addSpacing(
            12
        )

        workflow_label = QLabel(
            "LOCAL • MANUAL WORKFLOW"
        )

        workflow_label.setObjectName(
            "versionLabel"
        )

        version = QLabel(
            f"Version {APP_VERSION}"
        )

        version.setObjectName(
            "versionLabel"
        )

        layout.addWidget(
            workflow_label
        )

        layout.addWidget(
            version
        )

        self.navigation_buttons[
            "Dashboard"
        ].setChecked(
            True
        )

        return sidebar

    def _add_navigation_group(
        self,
        layout: QVBoxLayout,
        title: str,
        pages: list[str],
    ) -> None:
        section_label = QLabel(
            title
        )

        section_label.setObjectName(
            "versionLabel"
        )

        layout.addWidget(
            section_label
        )

        layout.addSpacing(
            2
        )

        for page_name in pages:
            index = (
                self.PAGE_INDEXES[
                    page_name
                ]
            )

            button = QPushButton(
                page_name
            )

            button.setObjectName(
                "navigationButton"
            )

            button.setCheckable(
                True
            )

            button.setMinimumHeight(
                40
            )

            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            button.clicked.connect(
                lambda checked=False,
                target_index=index,
                target_name=page_name:
                self._change_page(
                    target_index,
                    target_name,
                )
            )

            self.navigation_buttons[
                page_name
            ] = button

            layout.addWidget(
                button
            )

    def _create_content_area(
        self,
    ) -> QWidget:
        """
        Page header now contains only title + description.

        Page-specific actions remain inside the page where
        they actually belong.
        """
        content = QFrame()

        content.setObjectName(
            "contentArea"
        )

        layout = QVBoxLayout(
            content
        )

        layout.setContentsMargins(
            32,
            26,
            32,
            28,
        )

        layout.setSpacing(
            16
        )

        self.page_title = QLabel(
            "Dashboard"
        )

        self.page_title.setObjectName(
            "pageTitle"
        )

        self.page_subtitle = QLabel(
            self.PAGE_SUBTITLES[
                "Dashboard"
            ]
        )

        self.page_subtitle.setObjectName(
            "placeholderText"
        )

        self.page_subtitle.setWordWrap(
            True
        )

        layout.addWidget(
            self.page_title
        )

        layout.addWidget(
            self.page_subtitle
        )

        layout.addSpacing(
            2
        )

        self.page_stack = (
            QStackedWidget()
        )

        self.page_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        for _ in range(
            len(
                self.PAGE_INDEXES
            )
        ):
            self.page_stack.addWidget(
                self._create_lazy_placeholder()
            )

        layout.addWidget(
            self.page_stack,
            1,
        )

        self._ensure_page_loaded(
            "Dashboard"
        )

        self._ensure_page_loaded(
            "Add Listing"
        )

        self.page_stack.setCurrentIndex(
            self.PAGE_INDEXES[
                "Dashboard"
            ]
        )

        self._update_header(
            "Dashboard"
        )

        return content

    def _change_page(
        self,
        index: int,
        page_name: str,
    ) -> None:
        super()._change_page(
            index,
            page_name,
        )

        self._update_header(
            page_name
        )

    def _update_header(
        self,
        page_name: str,
    ) -> None:
        self.page_title.setText(
            page_name
        )

        self.page_subtitle.setText(
            self.PAGE_SUBTITLES.get(
                page_name,
                "",
            )
        )

    def _apply_styles(
        self,
    ) -> None:
        """
        ThemeManager owns all colours and styling.
        """
        return