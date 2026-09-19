from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QSettings,
    QTimer,
    Qt,
)
from PySide6.QtGui import (
    QCloseEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
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
from app.services.logging_service import (
    get_logger,
    initialize_logging,
    install_exception_hooks,
)
from app.services.settings_service import (
    AppSettings,
    default_settings,
    load_settings,
)
from app.ui.add_import_hub import (
    AddImportHub,
)
from app.ui.all_listings import (
    AllListingsPage,
)
from app.ui.components.cards.dashboard_moment import (
    DashboardMoment,
)
from app.ui.components.dialogs.about_dialog import (
    AboutDialog,
)
from app.ui.components.dialogs.error_feedback import (
    show_logged_error,
)
from app.ui.components.dialogs.message_dialog import (
    BrandedMessageDialog,
)
from app.ui.components.dialogs.welcome_dialog import (
    WelcomeDialog,
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
from app.ui.lifecycle_dialog import (
    ListingLifecycleDialog,
)
from app.ui.listing_dialog import (
    ListingDialog,
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
from app.ui.vinted_export_import_dialog import (
    VintedExportImportDialog,
)


WELCOME_COMPLETE_KEY = (
    "onboarding/welcome_complete"
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

    def _initialize_core_window(
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

    def _core_ensure_page_loaded(
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

        # The modal import dialog has fully closed.
        # Rebuild the visible page from the database now.
        # Let Qt fully return control to the main window
        # before rebuilding the visible inventory page.
        page_name = self._current_page_name

        QTimer.singleShot(
            100,
            lambda name=page_name: self._refresh_page_if_needed(
                name,
                force=True,
            ),
        )

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
            show_logged_error(
                self,
                title="Unable to Manage Listing",
                message=(
                    "The listing management window could not be opened."
                ),
                context=(
                    "Unable to open lifecycle dialog for "
                    f"listing {listing_id}"
                ),
                exception=exc,
            )

            return

        dialog.listing_changed.connect(
            self._lifecycle_changed
        )

        dialog.listing_deleted.connect(
            self._lifecycle_deleted
        )

        dialog.exec()

        if (
            self._current_page_name
            == "All Listings"
            and self.all_listings_page
            is not None
        ):
            self.all_listings_page.refresh_silent()

            self._dirty_pages.discard(
                "All Listings"
            )

        elif (
            self._current_page_name
            == "Sold"
            and self.sold_page
            is not None
        ):
            self.sold_page.refresh_silent()

            self._dirty_pages.discard(
                "Sold"
            )

        elif (
            self._current_page_name
            == "Archived"
            and self.archived_page
            is not None
        ):
            self.archived_page.refresh_silent()

            self._dirty_pages.discard(
                "Archived"
            )

        else:
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

        BrandedMessageDialog.notice(
            self,
            title="Listing Saved",
            message=(
                "The listing was saved locally.\n\n"
                f"Listing ID: {listing_id}"
            ),
        )

    def _listing_updated(
        self,
        listing_id: int,
    ) -> None:
        self._mark_listing_views_dirty()

        BrandedMessageDialog.notice(
            self,
            title="Listing Updated",
            message=(
                f"Listing #{listing_id} was updated successfully."
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

        # Refresh the page the user is currently viewing
        # immediately after a successful import.

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

    def _core_change_page(
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

    """
    Final branded application shell.

    Owns:
    - polished sidebar and page headers
    - persistent application logging
    - unexpected-error handling
    - one-time welcome
    - Add / Import hub
    - Dashboard moment
    - branded relisting workflow
    - Settings About card
    - persistent window geometry
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

    def __init__(
        self,
    ) -> None:
        initialize_logging()

        self.logger = get_logger(
            "main_window"
        )

        install_exception_hooks(
            self._show_unhandled_error
        )

        self.logger.info(
            "Creating main application window"
        )

        self._settings_about_installed = False

        self._dashboard_moment_installed = False

        self._dashboard_moment: (
            DashboardMoment | None
        ) = None

        self._window_settings = (
            QSettings()
        )

        self._initialize_core_window()

        self._install_sidebar_branding()

        self._restore_window_geometry()

        QTimer.singleShot(
            250,
            self._show_first_run_welcome_if_needed,
        )

        self.logger.info(
            "Main application window ready"
        )

    # =====================================================
    # Polished shell
    # =====================================================

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
            "LOCAL â€¢ MANUAL WORKFLOW"
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

    # =====================================================
    # Unexpected errors
    # =====================================================

    def _show_unhandled_error(
        self,
        log_path: Path,
    ) -> None:
        app = QApplication.instance()

        parent = None

        if app is not None:
            parent = (
                app.activeWindow()
            )

        BrandedMessageDialog.error(
            parent,
            title="Something Went Wrong",
            message=(
                "The app ran into an unexpected problem.\n\n"
                "Technical details were saved to the local "
                "application log. You can continue if the app "
                "is still responding, or restart it if the "
                "problem happens again."
            ),
            detail=(
                "Log file:\n"
                f"{log_path}\n\n"
                "The log can contain technical information such "
                "as local file paths. Review it before sharing it."
            ),
        )

    # =====================================================
    # Add / Import hub
    # =====================================================

    def _create_add_listing_page(
        self,
    ) -> QWidget:
        page = AddImportHub(
            add_manual=(
                self.open_add_listing_dialog
            ),
            import_vinted=(
                self._open_vinted_export_import
            ),
            import_generic=(
                self.open_import_dialog
            ),
        )

        self.last_saved_label = (
            page.status_label
        )

        return page

    def _open_vinted_export_import(
        self,
    ) -> None:
        """
        Open the dedicated Vinted data-export importer.

        Imported listings are added locally only. Existing
        locally edited listings are never overwritten.
        """
        try:
            dialog = VintedExportImportDialog(
                parent=self
            )

            dialog.import_completed.connect(
                self._vinted_import_completed
            )

            dialog.exec()

            # The modal import dialog has fully closed.
            # Rebuild the visible page from the database now.
            # Let Qt fully return control to the main window
            # before rebuilding the visible inventory page.
            page_name = self._current_page_name

            QTimer.singleShot(
                100,
                lambda name=page_name: self._refresh_page_if_needed(
                    name,
                    force=True,
                ),
            )

        except Exception:
            self.logger.exception(
                "Unable to open Vinted Export importer"
            )

            BrandedMessageDialog.error(
                self,
                title="Unable to Open Import",
                message=(
                    "The Vinted Export importer "
                    "could not be opened."
                ),
            )

    def _vinted_import_completed(
        self,
        imported_count: int,
    ) -> None:
        """
        Refresh listing views after a successful Vinted import.
        """
        self._mark_listing_views_dirty()

        # Refresh the page the user is currently viewing
        # immediately after a successful import.

        if self.last_saved_label is None:
            return

        if imported_count == 1:
            message = (
                "1 new Vinted listing imported."
            )

        else:
            message = (
                f"{imported_count} new Vinted listings imported."
            )

        self.last_saved_label.setText(
            message
        )
    # =====================================================
    # First-run welcome
    # =====================================================

    def _show_first_run_welcome_if_needed(
        self,
    ) -> None:
        completed = (
            self._window_settings.value(
                WELCOME_COMPLETE_KEY,
                False,
                type=bool,
            )
        )

        if completed:
            return

        app = QApplication.instance()

        app_icon = (
            app.windowIcon()
            if app is not None
            else None
        )

        dialog = WelcomeDialog(
            parent=self,
            app_icon=app_icon,
        )

        dialog.exec()

        self._window_settings.setValue(
            WELCOME_COMPLETE_KEY,
            True,
        )

        self._window_settings.sync()

        self.logger.info(
            "First-run welcome completed"
        )

    # =====================================================
    # Sidebar branding
    # =====================================================

    def _install_sidebar_branding(
        self,
    ) -> None:
        sidebar = self.findChild(
            QFrame,
            "sidebar",
        )

        if sidebar is None:
            return

        sidebar_layout = (
            sidebar.layout()
        )

        if not isinstance(
            sidebar_layout,
            QVBoxLayout,
        ):
            return

        old_name = sidebar.findChild(
            QLabel,
            "sidebarAppName",
        )

        old_subtitle = (
            sidebar.findChild(
                QLabel,
                "sidebarSubtitle",
            )
        )

        if old_name is not None:
            old_name.hide()

        if old_subtitle is not None:
            old_subtitle.hide()

        brand_frame = QFrame()

        brand_frame.setObjectName(
            "brandIdentity"
        )

        brand_layout = QHBoxLayout(
            brand_frame
        )

        brand_layout.setContentsMargins(
            0,
            0,
            0,
            4,
        )

        brand_layout.setSpacing(
            10
        )

        icon_label = QLabel()

        icon_label.setFixedSize(
            48,
            48,
        )

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        app = QApplication.instance()

        if app is not None:
            icon = app.windowIcon()

            if not icon.isNull():
                icon_label.setPixmap(
                    icon.pixmap(
                        46,
                        46,
                    )
                )

        brand_layout.addWidget(
            icon_label,
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        text_layout = QVBoxLayout()

        text_layout.setContentsMargins(
            0,
            2,
            0,
            0,
        )

        text_layout.setSpacing(
            1
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

        subtitle.setWordWrap(
            True
        )

        text_layout.addWidget(
            name
        )

        text_layout.addWidget(
            subtitle
        )

        brand_layout.addLayout(
            text_layout,
            1,
        )

        sidebar_layout.insertWidget(
            0,
            brand_frame,
        )

    # =====================================================
    # Page enhancements
    # =====================================================

    def _ensure_page_loaded(
        self,
        page_name: str,
    ) -> QWidget:
        page = self._core_ensure_page_loaded(
            page_name
        )

        if (
            page_name == "Dashboard"
            and not self._dashboard_moment_installed
        ):
            self._install_dashboard_moment(
                page
            )

        if (
            page_name == "Settings"
            and not self._settings_about_installed
        ):
            self._install_settings_about_card(
                page
            )

        return page

    def _change_page(
        self,
        index: int,
        page_name: str,
    ) -> None:
        self._core_change_page(
            index,
            page_name,
        )

        self._update_header(
            page_name
        )

        if (
            page_name == "Dashboard"
            and self._dashboard_moment
            is not None
        ):
            self._dashboard_moment.refresh()

    # =====================================================
    # Relisting Preparation
    # =====================================================

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

    # =====================================================
    # Dashboard personality
    # =====================================================

    def _install_dashboard_moment(
        self,
        page: QWidget,
    ) -> None:
        content_layout = getattr(
            page,
            "content_layout",
            None,
        )

        if not isinstance(
            content_layout,
            QVBoxLayout,
        ):
            return

        moment = DashboardMoment(
            parent=page
        )

        content_layout.insertWidget(
            0,
            moment,
        )

        self._dashboard_moment = (
            moment
        )

        self._dashboard_moment_installed = (
            True
        )

    # =====================================================
    # Settings enhancement
    # =====================================================

    def _install_settings_about_card(
        self,
        page: QWidget,
    ) -> None:
        scroll_area = getattr(
            page,
            "scroll_area",
            None,
        )

        if scroll_area is None:
            return

        content = (
            scroll_area.widget()
        )

        if content is None:
            return

        content_layout = (
            content.layout()
        )

        if not isinstance(
            content_layout,
            QVBoxLayout,
        ):
            return

        card = QFrame()

        card.setObjectName(
            "settingsFrame"
        )

        card_layout = QHBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            24,
            20,
            24,
            20,
        )

        card_layout.setSpacing(
            16
        )

        icon_label = QLabel()

        icon_label.setFixedSize(
            64,
            64,
        )

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        app = QApplication.instance()

        if app is not None:
            icon = app.windowIcon()

            if not icon.isNull():
                icon_label.setPixmap(
                    icon.pixmap(
                        60,
                        60,
                    )
                )

        card_layout.addWidget(
            icon_label,
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        information = QVBoxLayout()

        information.setSpacing(
            5
        )

        heading = QLabel(
            "ABOUT THE APP"
        )

        heading.setObjectName(
            "sectionHeading"
        )

        app_name = QLabel(
            "Vinted Relisting Assistant"
        )

        app_name.setObjectName(
            "placeholderTitle"
        )

        version = QLabel(
            f"Version {APP_VERSION}"
        )

        version.setObjectName(
            "informationText"
        )

        message = QLabel(
            (
                "A little helper for keeping your listings "
                "organised and making manual relisting easier."
            )
        )

        message.setObjectName(
            "informationText"
        )

        message.setWordWrap(
            True
        )

        information.addWidget(
            heading
        )

        information.addWidget(
            app_name
        )

        information.addWidget(
            version
        )

        information.addWidget(
            message
        )

        card_layout.addLayout(
            information,
            1,
        )

        about_button = QPushButton(
            "ABOUT & APP INFO"
        )

        about_button.setObjectName(
            "secondaryButton"
        )

        about_button.setMinimumHeight(
            40
        )

        about_button.setMinimumWidth(
            150
        )

        about_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        about_button.clicked.connect(
            self._open_about_dialog
        )

        card_layout.addWidget(
            about_button,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

        insertion_index = max(
            0,
            content_layout.count() - 1,
        )

        content_layout.insertWidget(
            insertion_index,
            card,
        )

        self._settings_about_installed = (
            True
        )

    def _open_about_dialog(
        self,
    ) -> None:
        app = QApplication.instance()

        app_icon = (
            app.windowIcon()
            if app is not None
            else None
        )

        dialog = AboutDialog(
            parent=self,
            app_icon=app_icon,
        )

        dialog.exec()

    # =====================================================
    # Window persistence
    # =====================================================

    def _restore_window_geometry(
        self,
    ) -> None:
        geometry = (
            self._window_settings.value(
                "window/geometry"
            )
        )

        if geometry is None:
            return

        restored = self.restoreGeometry(
            geometry
        )

        if not restored:
            return

        app = QApplication.instance()

        if app is None:
            return

        window_center = (
            self.frameGeometry().center()
        )

        if (
            app.screenAt(
                window_center
            )
            is not None
        ):
            return

        primary_screen = (
            app.primaryScreen()
        )

        if primary_screen is None:
            return

        available = (
            primary_screen.availableGeometry()
        )

        self.resize(
            min(
                1200,
                available.width(),
            ),
            min(
                760,
                available.height(),
            ),
        )

        frame = (
            self.frameGeometry()
        )

        frame.moveCenter(
            available.center()
        )

        self.move(
            frame.topLeft()
        )

    def _save_window_geometry(
        self,
    ) -> None:
        self._window_settings.setValue(
            "window/geometry",
            self.saveGeometry(),
        )

        self._window_settings.sync()

        self.logger.info(
            "Window geometry saved"
        )

    def closeEvent(
        self,
        event: QCloseEvent,
    ) -> None:
        self.logger.info(
            "Application window closing"
        )

        self._save_window_geometry()

        super().closeEvent(
            event
        )

