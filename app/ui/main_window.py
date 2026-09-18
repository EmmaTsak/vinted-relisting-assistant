from __future__ import annotations

from PySide6.QtCore import (
    QTimer,
    Qt,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app import (
    APP_NAME,
    APP_VERSION,
)
from app.services.settings_service import (
    AppSettings,
    default_settings,
    load_settings,
)
from app.ui.category_enabled_all_listings import (
    CategoryEnabledAllListingsPage as AllListingsPage,
)
from app.ui.daily_queue import (
    DailyQueuePage,
)
from app.ui.dashboard_page import (
    DashboardPage,
)
from app.ui.history_page import (
    HistoryPage,
)
from app.ui.import_dialog import (
    ImportListingsDialog,
)
from app.ui.isbn_listing_dialog import (
    ISBNListingDialog as ListingDialog,
)
from app.ui.lifecycle_dialog import (
    ListingLifecycleDialog,
)
from app.ui.relisting_preparation import (
    RelistingPreparationDialog,
)
from app.ui.settings_page import (
    SettingsPage,
)
from app.ui.status_listings import (
    ArchivedListingsPage,
    SoldListingsPage,
)


class MainWindow(QMainWindow):
    """
    Main Vinted Relisting Assistant window.

    Data-heavy pages are created lazily the first time
    they are opened.

    When listing data changes, hidden pages are marked dirty
    instead of being rebuilt immediately.
    """

    PAGE_INDEXES = {
        "Dashboard": 0,
        "Today's Queue": 1,
        "All Listings": 2,
        "Add Listing": 3,
        "History": 4,
        "Sold": 5,
        "Archived": 6,
        "Settings": 7,
    }

    DATA_PAGES = {
        "Dashboard",
        "Today's Queue",
        "All Listings",
        "History",
        "Sold",
        "Archived",
    }

    def __init__(
        self,
    ) -> None:
        super().__init__()

        self.settings = (
            self._load_settings_safely()
        )

        self.navigation_buttons: dict[
            str,
            QPushButton,
        ] = {}

        self._current_page_name = (
            "Dashboard"
        )

        self._dirty_pages: set[str] = (
            set()
        )

        self.dashboard_page: (
            DashboardPage | None
        ) = None

        self.daily_queue_page: (
            DailyQueuePage | None
        ) = None

        self.all_listings_page: (
            AllListingsPage | None
        ) = None

        self.add_listing_page: (
            QWidget | None
        ) = None

        self.history_page: (
            HistoryPage | None
        ) = None

        self.sold_page: (
            SoldListingsPage | None
        ) = None

        self.archived_page: (
            ArchivedListingsPage | None
        ) = None

        self.settings_page: (
            SettingsPage | None
        ) = None

        self.last_saved_label: (
            QLabel | None
        ) = None

        self.setWindowTitle(
            APP_NAME
        )

        self.resize(
            1200,
            760,
        )

        self.setMinimumSize(
            950,
            650,
        )

        self._build_ui()
        self._apply_styles()

        self._apply_runtime_settings(
            refresh_queue=False
        )

    def _load_settings_safely(
        self,
    ) -> AppSettings:
        try:
            return load_settings()

        except Exception:
            return default_settings()

    def _build_ui(
        self,
    ) -> None:
        central_widget = QWidget()

        self.setCentralWidget(
            central_widget
        )

        main_layout = QHBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(
            0
        )

        main_layout.addWidget(
            self._create_sidebar()
        )

        main_layout.addWidget(
            self._create_content_area(),
            1,
        )

    def _create_sidebar(
        self,
    ) -> QWidget:
        sidebar = QFrame()

        sidebar.setObjectName(
            "sidebar"
        )

        sidebar.setFixedWidth(
            220
        )

        layout = QVBoxLayout(
            sidebar
        )

        layout.setContentsMargins(
            16,
            24,
            16,
            20,
        )

        layout.setSpacing(
            8
        )

        name = QLabel(
            "Vinted"
        )

        name.setObjectName(
            "sidebarAppName"
        )

        subtitle = QLabel(
            "Relisting Assistant"
        )

        subtitle.setObjectName(
            "sidebarSubtitle"
        )

        layout.addWidget(
            name
        )

        layout.addWidget(
            subtitle
        )

        layout.addSpacing(
            25
        )

        navigation_items = [
            ("Dashboard", 0),
            ("Today's Queue", 1),
            ("All Listings", 2),
            ("Add Listing", 3),
            ("History", 4),
            ("Sold", 5),
            ("Archived", 6),
            ("Settings", 7),
        ]

        for (
            page_name,
            index,
        ) in navigation_items:
            button = QPushButton(
                page_name
            )

            button.setObjectName(
                "navigationButton"
            )

            button.setCheckable(
                True
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

        layout.addStretch()

        version = QLabel(
            f"Version {APP_VERSION}"
        )

        version.setObjectName(
            "versionLabel"
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

    def _create_content_area(
        self,
    ) -> QWidget:
        content = QWidget()

        content.setObjectName(
            "contentArea"
        )

        layout = QVBoxLayout(
            content
        )

        layout.setContentsMargins(
            28,
            24,
            28,
            28,
        )

        layout.setSpacing(
            20
        )

        self.page_title = QLabel(
            "Dashboard"
        )

        self.page_title.setObjectName(
            "pageTitle"
        )

        layout.addWidget(
            self.page_title
        )

        self.page_stack = (
            QStackedWidget()
        )

        self.page_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        # Reserve all page positions with tiny placeholders.
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

        # Dashboard is the only data-heavy page
        # loaded during startup.
        self._ensure_page_loaded(
            "Dashboard"
        )

        # Add Listing is lightweight and gives us the
        # persistent save/import confirmation label.
        self._ensure_page_loaded(
            "Add Listing"
        )

        self.page_stack.setCurrentIndex(
            self.PAGE_INDEXES[
                "Dashboard"
            ]
        )

        return content

    def _create_lazy_placeholder(
        self,
    ) -> QWidget:
        placeholder = QWidget()

        placeholder.setObjectName(
            "lazyPagePlaceholder"
        )

        return placeholder

    def _replace_stack_page(
        self,
        index: int,
        page: QWidget,
    ) -> None:
        """
        Replace one placeholder while preserving the page index.
        """
        old_widget = (
            self.page_stack.widget(
                index
            )
        )

        if old_widget is page:
            return

        if old_widget is not None:
            self.page_stack.removeWidget(
                old_widget
            )

            old_widget.deleteLater()

        self.page_stack.insertWidget(
            index,
            page,
        )

    def _ensure_page_loaded(
        self,
        page_name: str,
    ) -> QWidget:
        """
        Create a page only on its first visit.

        Later visits reuse the same QWidget.
        """
        index = (
            self.PAGE_INDEXES[
                page_name
            ]
        )

        if page_name == "Dashboard":
            if (
                self.dashboard_page
                is None
            ):
                page = DashboardPage()

                page.edit_requested.connect(
                    self.open_edit_listing_dialog
                )

                page.open_queue_requested.connect(
                    lambda: self._change_page(
                        self.PAGE_INDEXES[
                            "Today's Queue"
                        ],
                        "Today's Queue",
                    )
                )

                page.open_history_requested.connect(
                    lambda: self._change_page(
                        self.PAGE_INDEXES[
                            "History"
                        ],
                        "History",
                    )
                )

                self.dashboard_page = (
                    page
                )

                self._replace_stack_page(
                    index,
                    page,
                )

                self._dirty_pages.discard(
                    page_name
                )

            return self.dashboard_page

        if (
            page_name
            == "Today's Queue"
        ):
            if (
                self.daily_queue_page
                is None
            ):
                page = DailyQueuePage()

                page.prepare_requested.connect(
                    self.open_relisting_preparation
                )

                page.edit_requested.connect(
                    self.open_edit_listing_dialog
                )

                page.queue_changed.connect(
                    self._queue_changed
                )

                self.daily_queue_page = (
                    page
                )

                self._replace_stack_page(
                    index,
                    page,
                )

                page.daily_limit = (
                    self.settings
                    .daily_relist_limit
                )

                page.minimum_age_days = (
                    self.settings
                    .minimum_relist_age_days
                )

                page.rule_label.setText(
                    (
                        "Minimum age: "
                        f"{self.settings.minimum_relist_age_days} "
                        "days"
                    )
                )

                # DailyQueuePage initially loads with its defaults,
                # so refresh once with the actual saved settings.
                page.refresh()

                self._dirty_pages.discard(
                    page_name
                )

            return self.daily_queue_page

        if (
            page_name
            == "All Listings"
        ):
            if (
                self.all_listings_page
                is None
            ):
                page = (
                    AllListingsPage()
                )

                page.edit_requested.connect(
                    self.open_edit_listing_dialog
                )

                page.manage_requested.connect(
                    self.open_lifecycle_dialog
                )

                self.all_listings_page = (
                    page
                )

                self._replace_stack_page(
                    index,
                    page,
                )

                self._dirty_pages.discard(
                    page_name
                )

            return self.all_listings_page

        if (
            page_name
            == "Add Listing"
        ):
            if (
                self.add_listing_page
                is None
            ):
                page = (
                    self._create_add_listing_page()
                )

                self.add_listing_page = (
                    page
                )

                self._replace_stack_page(
                    index,
                    page,
                )

            return self.add_listing_page

        if page_name == "History":
            if (
                self.history_page
                is None
            ):
                page = HistoryPage()

                page.edit_requested.connect(
                    self.open_edit_listing_dialog
                )

                self.history_page = (
                    page
                )

                self._replace_stack_page(
                    index,
                    page,
                )

                self._dirty_pages.discard(
                    page_name
                )

            return self.history_page

        if page_name == "Sold":
            if (
                self.sold_page
                is None
            ):
                page = SoldListingsPage()

                page.edit_requested.connect(
                    self.open_edit_listing_dialog
                )

                page.manage_requested.connect(
                    self.open_lifecycle_dialog
                )

                self.sold_page = (
                    page
                )

                self._replace_stack_page(
                    index,
                    page,
                )

                self._dirty_pages.discard(
                    page_name
                )

            return self.sold_page

        if page_name == "Archived":
            if (
                self.archived_page
                is None
            ):
                page = (
                    ArchivedListingsPage()
                )

                page.edit_requested.connect(
                    self.open_edit_listing_dialog
                )

                page.manage_requested.connect(
                    self.open_lifecycle_dialog
                )

                self.archived_page = (
                    page
                )

                self._replace_stack_page(
                    index,
                    page,
                )

                self._dirty_pages.discard(
                    page_name
                )

            return self.archived_page

        if page_name == "Settings":
            if (
                self.settings_page
                is None
            ):
                page = SettingsPage()

                page.settings_saved.connect(
                    self._settings_saved
                )

                self.settings_page = (
                    page
                )

                self._replace_stack_page(
                    index,
                    page,
                )

            return self.settings_page

        raise ValueError(
            (
                "Unknown page: "
                f"{page_name}"
            )
        )

    def _create_add_listing_page(
        self,
    ) -> QWidget:
        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        container = QFrame()

        container.setObjectName(
            "pagePlaceholder"
        )

        container_layout = (
            QVBoxLayout(
                container
            )
        )

        container_layout.setContentsMargins(
            30,
            30,
            30,
            30,
        )

        title = QLabel(
            "Add or Import Listings"
        )

        title.setObjectName(
            "placeholderTitle"
        )

        description = QLabel(
            (
                "Add one listing manually or bulk-import "
                "your existing inventory from CSV or JSON."
            )
        )

        description.setObjectName(
            "placeholderText"
        )

        description.setWordWrap(
            True
        )

        add_button = QPushButton(
            "ADD NEW LISTING"
        )

        add_button.setObjectName(
            "primaryButton"
        )

        add_button.setMaximumWidth(
            240
        )

        add_button.clicked.connect(
            self.open_add_listing_dialog
        )

        import_button = QPushButton(
            "IMPORT CSV / JSON"
        )

        import_button.setObjectName(
            "secondaryButton"
        )

        import_button.setMaximumWidth(
            240
        )

        import_button.clicked.connect(
            self.open_import_dialog
        )

        self.last_saved_label = QLabel(
            ""
        )

        self.last_saved_label.setObjectName(
            "successText"
        )

        container_layout.addWidget(
            title
        )

        container_layout.addWidget(
            description
        )

        container_layout.addSpacing(
            24
        )

        container_layout.addWidget(
            add_button
        )

        container_layout.addWidget(
            import_button
        )

        container_layout.addSpacing(
            18
        )

        container_layout.addWidget(
            self.last_saved_label
        )

        container_layout.addStretch()

        layout.addWidget(
            container
        )

        return page

    def open_add_listing_dialog(
        self,
    ) -> None:
        dialog = ListingDialog(
            parent=self
        )

        dialog.currency_input.setText(
            self.settings.currency
        )

        dialog.listing_saved.connect(
            self._listing_saved
        )

        dialog.exec()

    def open_edit_listing_dialog(
        self,
        listing_id: int,
    ) -> None:
        dialog = ListingDialog(
            parent=self,
            listing_id=listing_id,
        )

        dialog.listing_saved.connect(
            self._listing_updated
        )

        dialog.exec()

        self._schedule_current_page_refresh()

    def open_import_dialog(
        self,
    ) -> None:
        dialog = ImportListingsDialog(
            parent=self
        )

        dialog.import_completed.connect(
            self._import_completed
        )

        dialog.exec()

    def open_relisting_preparation(
        self,
        listing_id: int,
    ) -> None:
        dialog = (
            RelistingPreparationDialog(
                listing_id=listing_id,
                parent=self,
                configured_limit=(
                    self.settings
                    .daily_relist_limit
                ),
                minimum_age_days=(
                    self.settings
                    .minimum_relist_age_days
                ),
                vinted_url=(
                    self.settings
                    .vinted_url
                ),
            )
        )

        dialog.relisted.connect(
            self._preparation_relisted
        )

        dialog.exec()

        self._schedule_current_page_refresh()

    def open_lifecycle_dialog(
        self,
        listing_id: int,
    ) -> None:
        try:
            dialog = (
                ListingLifecycleDialog(
                    listing_id=listing_id,
                    parent=self,
                )
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Manage Listing",
                str(exc),
            )

            return

        dialog.listing_changed.connect(
            self._lifecycle_changed
        )

        dialog.listing_deleted.connect(
            self._lifecycle_deleted
        )

        dialog.exec()

        self._schedule_current_page_refresh()

    def _settings_saved(
        self,
        settings: AppSettings,
    ) -> None:
        self.settings = settings

        self._apply_runtime_settings(
            refresh_queue=False
        )

        self._mark_listing_views_dirty()

    def _apply_runtime_settings(
        self,
        refresh_queue: bool = False,
    ) -> None:
        """
        Apply settings only to an already-created queue.

        Loading settings must not cause Today's Queue to be
        constructed during application startup.
        """
        if (
            self.daily_queue_page
            is None
        ):
            return

        self.daily_queue_page.daily_limit = (
            self.settings
            .daily_relist_limit
        )

        self.daily_queue_page.minimum_age_days = (
            self.settings
            .minimum_relist_age_days
        )

        self.daily_queue_page.rule_label.setText(
            (
                "Minimum age: "
                f"{self.settings.minimum_relist_age_days} "
                "days"
            )
        )

        if refresh_queue:
            self.daily_queue_page.refresh()

            self._dirty_pages.discard(
                "Today's Queue"
            )

    def _listing_saved(
        self,
        listing_id: int,
    ) -> None:
        if (
            self.last_saved_label
            is not None
        ):
            self.last_saved_label.setText(
                (
                    f"Listing #{listing_id} "
                    "saved successfully."
                )
            )

        self._mark_listing_views_dirty()

        QMessageBox.information(
            self,
            "Listing Saved",
            (
                "The listing was saved locally.\n\n"
                f"Listing ID: {listing_id}"
            ),
        )

    def _listing_updated(
        self,
        listing_id: int,
    ) -> None:
        self._mark_listing_views_dirty()

        QMessageBox.information(
            self,
            "Listing Updated",
            (
                f"Listing #{listing_id} "
                "was updated successfully."
            ),
        )

    def _import_completed(
        self,
        imported_count: int,
    ) -> None:
        if (
            self.last_saved_label
            is not None
        ):
            self.last_saved_label.setText(
                (
                    f"{imported_count} listings "
                    "imported successfully."
                )
            )

        self._mark_listing_views_dirty()

    def _preparation_relisted(
        self,
        listing_id: int,
    ) -> None:
        del listing_id

        self._mark_listing_views_dirty()

    def _queue_changed(
        self,
    ) -> None:
        """
        Queue refreshes itself before emitting this signal.

        Other listing-based pages become dirty.
        """
        self._mark_listing_views_dirty(
            exclude={
                "Today's Queue",
            }
        )

    def _lifecycle_changed(
        self,
        listing_id: int,
    ) -> None:
        del listing_id

        self._mark_listing_views_dirty()

    def _lifecycle_deleted(
        self,
        listing_id: int,
    ) -> None:
        del listing_id

        self._mark_listing_views_dirty()

    def _mark_listing_views_dirty(
        self,
        exclude: set[str] | None = None,
    ) -> None:
        excluded = (
            exclude
            or set()
        )

        self._dirty_pages.update(
            self.DATA_PAGES
            - excluded
        )

    def _schedule_current_page_refresh(
        self,
    ) -> None:
        page_name = (
            self._current_page_name
        )

        if (
            page_name
            not in self.DATA_PAGES
        ):
            return

        QTimer.singleShot(
            0,
            lambda name=page_name:
            self._refresh_page_if_needed(
                name
            ),
        )

    def _refresh_page_if_needed(
        self,
        page_name: str,
        force: bool = False,
    ) -> None:
        """
        Refresh the visible page only if its data changed.

        If a dirty page has never been created, creating it
        already loads the latest data, so another refresh is
        unnecessary.
        """
        if (
            page_name
            != self._current_page_name
        ):
            return

        if (
            not force
            and page_name
            not in self._dirty_pages
        ):
            return

        if (
            page_name == "Dashboard"
            and self.dashboard_page
            is None
        ):
            self._ensure_page_loaded(
                page_name
            )

            return

        if (
            page_name == "Today's Queue"
            and self.daily_queue_page
            is None
        ):
            self._ensure_page_loaded(
                page_name
            )

            return

        if (
            page_name == "All Listings"
            and self.all_listings_page
            is None
        ):
            self._ensure_page_loaded(
                page_name
            )

            return

        if (
            page_name == "History"
            and self.history_page
            is None
        ):
            self._ensure_page_loaded(
                page_name
            )

            return

        if (
            page_name == "Sold"
            and self.sold_page
            is None
        ):
            self._ensure_page_loaded(
                page_name
            )

            return

        if (
            page_name == "Archived"
            and self.archived_page
            is None
        ):
            self._ensure_page_loaded(
                page_name
            )

            return

        if (
            page_name == "Dashboard"
            and self.dashboard_page
            is not None
        ):
            self.dashboard_page.refresh()

        elif (
            page_name
            == "Today's Queue"
            and self.daily_queue_page
            is not None
        ):
            self.daily_queue_page.refresh()

        elif (
            page_name
            == "All Listings"
            and self.all_listings_page
            is not None
        ):
            self.all_listings_page.refresh()

        elif (
            page_name == "History"
            and self.history_page
            is not None
        ):
            self.history_page.refresh()

        elif (
            page_name == "Sold"
            and self.sold_page
            is not None
        ):
            self.sold_page.refresh()

        elif (
            page_name == "Archived"
            and self.archived_page
            is not None
        ):
            self.archived_page.refresh()

        self._dirty_pages.discard(
            page_name
        )

    def _change_page(
        self,
        index: int,
        page_name: str,
    ) -> None:
        expected_index = (
            self.PAGE_INDEXES.get(
                page_name
            )
        )

        if expected_index is None:
            return

        # Keep the old method signature compatible with
        # existing sidebar/dashboard calls.
        del index

        self._current_page_name = (
            page_name
        )

        self._ensure_page_loaded(
            page_name
        )

        self.page_stack.setCurrentIndex(
            expected_index
        )

        self.page_title.setText(
            page_name
        )

        for (
            name,
            button,
        ) in (
            self.navigation_buttons
            .items()
        ):
            button.setChecked(
                name == page_name
            )

        if page_name == "Settings":
            QTimer.singleShot(
                0,
                lambda:
                self.settings_page.reload()
                if (
                    self._current_page_name
                    == "Settings"
                    and self.settings_page
                    is not None
                )
                else None,
            )

        elif (
            page_name
            in self.DATA_PAGES
        ):
            QTimer.singleShot(
                0,
                lambda name=page_name:
                self._refresh_page_if_needed(
                    name
                ),
            )

    def _apply_styles(
        self,
    ) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f5f6f8;
            }

            QWidget {
                font-family: "Segoe UI";
                font-size: 14px;
                color: #111827;
            }

            #sidebar {
                background-color: #1f2937;
            }

            #sidebarAppName {
                color: white;
                font-size: 24px;
                font-weight: 700;
            }

            #sidebarSubtitle {
                color: #cbd5e1;
            }

            #navigationButton {
                background-color: transparent;
                color: #d1d5db;
                border: none;
                border-radius: 7px;
                text-align: left;
                padding: 11px 12px;
            }

            #navigationButton:hover {
                background-color: #374151;
                color: white;
            }

            #navigationButton:checked {
                background-color: #4b5563;
                color: white;
                font-weight: 600;
            }

            #versionLabel {
                color: #9ca3af;
                font-size: 12px;
            }

            #contentArea {
                background-color: #f5f6f8;
            }

            #pageTitle {
                color: #111827;
                font-size: 28px;
                font-weight: 700;
            }

            #placeholderText {
                color: #6b7280;
            }

            #pagePlaceholder {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }

            #placeholderTitle {
                color: #111827;
                font-size: 18px;
                font-weight: 600;
            }

            #primaryButton {
                background-color: #1f2937;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 12px 18px;
                font-weight: 600;
            }

            #primaryButton:hover {
                background-color: #374151;
            }

            #secondaryButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 7px;
                padding: 12px 18px;
                font-weight: 600;
            }

            #secondaryButton:hover {
                background-color: #f3f4f6;
            }

            #successText {
                color: #15803d;
                font-weight: 600;
            }
            """
        )