from __future__ import annotations

from importlib import import_module
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
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import (
    APP_VERSION,
)
from app.services.logging_service import (
    get_logger,
    initialize_logging,
    install_exception_hooks,
)
from app.ui.about_dialog import (
    AboutDialog,
)
from app.ui.add_import_hub import (
    AddImportHub,
)
from app.ui.branded_relisting_preparation import (
    BrandedRelistingPreparationDialog,
)
from app.ui.dashboard_moment import (
    DashboardMoment,
)
from app.ui.polished_main_window import (
    PolishedMainWindow,
)
from app.ui.welcome_dialog import (
    WelcomeDialog,
)


WELCOME_COMPLETE_KEY = (
    "onboarding/welcome_complete"
)


class BrandedMainWindow(
    PolishedMainWindow
):
    """
    Final branded product shell.

    Adds:
    - persistent application logging
    - friendly unexpected-error handling
    - one-time welcome
    - branded sidebar
    - polished Add / Import hub
    - friendly Dashboard moment
    - branded relisting success
    - Settings About card
    - persistent window geometry
    """

    def __init__(
        self,
    ) -> None:
        # -------------------------------------------------
        # Production diagnostics
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Branded-shell state
        # -------------------------------------------------

        self._settings_about_installed = False

        self._dashboard_moment_installed = False

        self._dashboard_moment: (
            DashboardMoment | None
        ) = None

        self._window_settings = (
            QSettings()
        )

        super().__init__()

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
    # Unexpected errors
    # =====================================================

    def _show_unhandled_error(
        self,
        log_path: Path,
    ) -> None:
        """
        Friendly fallback for an unexpected uncaught exception.

        Technical details stay in the local log rather than
        being dumped into the UI.
        """
        app = QApplication.instance()

        parent = None

        if app is not None:
            parent = (
                app.activeWindow()
            )

        message_box = QMessageBox(
            parent
        )

        message_box.setIcon(
            QMessageBox.Icon.Critical
        )

        message_box.setWindowTitle(
            "Something Went Wrong"
        )

        message_box.setText(
            (
                "The app ran into an unexpected problem."
            )
        )

        message_box.setInformativeText(
            (
                "Technical details were saved to the local "
                "application log.\n\n"
                "You can close this message and continue if the "
                "app is still responding. If the problem happens "
                "again, restart the app."
            )
        )

        message_box.setDetailedText(
            (
                "Log file:\n"
                f"{log_path}\n\n"
                "The log can contain technical information such "
                "as local file paths. Review it before sharing it "
                "with anyone."
            )
        )

        message_box.setStandardButtons(
            QMessageBox.StandardButton.Ok
        )

        message_box.exec()

    # =====================================================
    # Add / Import hub
    # =====================================================

    def _create_add_listing_page(
        self,
    ) -> QWidget:
        """
        Three-option inventory entry point.

        Existing dialogs and services still perform all actual
        listing creation/import work.
        """
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
        Open the existing Vinted Export importer.

        This wrapper never implements import logic itself.
        """
        inherited_method_names = (
            "open_vinted_export_import_dialog",
            "open_vinted_export_dialog",
            "open_vinted_import_dialog",
        )

        for method_name in (
            inherited_method_names
        ):
            method = (
                self._find_inherited_method(
                    method_name
                )
            )

            if method is None:
                continue

            try:
                method(
                    self
                )

            except Exception as exc:
                self.logger.exception(
                    (
                        "Unable to open inherited "
                        "Vinted Export importer"
                    )
                )

                QMessageBox.critical(
                    self,
                    "Unable to Open Vinted Import",
                    (
                        "The Vinted Export importer "
                        "could not be opened.\n\n"
                        "Technical details were saved "
                        "to the application log."
                    ),
                )

                return

            self._mark_listing_views_dirty()

            return

        try:
            module = import_module(
                "app.ui.vinted_export_import_dialog"
            )

            dialog_class = (
                self._find_vinted_import_dialog_class(
                    module
                )
            )

            if dialog_class is None:
                raise RuntimeError(
                    (
                        "The Vinted Export importer module "
                        "was found, but its import dialog "
                        "could not be identified."
                    )
                )

            try:
                dialog = dialog_class(
                    parent=self
                )

            except TypeError:
                dialog = dialog_class(
                    self
                )

            result = dialog.exec()

        except Exception:
            self.logger.exception(
                (
                    "Unable to open dedicated "
                    "Vinted Export importer"
                )
            )

            QMessageBox.critical(
                self,
                "Unable to Open Vinted Import",
                (
                    "The Vinted Export importer "
                    "could not be opened.\n\n"
                    "Technical details were saved "
                    "to the application log."
                ),
            )

            return

        self._mark_listing_views_dirty()

        if (
            result
            == QDialog.DialogCode.Accepted
            and self.last_saved_label
            is not None
        ):
            self.last_saved_label.setText(
                (
                    "Vinted Export import completed. "
                    "Your local inventory has been refreshed."
                )
            )

    def _find_inherited_method(
        self,
        method_name: str,
    ):
        for base_class in (
            type(self).mro()[1:]
        ):
            method = (
                base_class.__dict__.get(
                    method_name
                )
            )

            if method is not None:
                return method

        return None

    def _find_vinted_import_dialog_class(
        self,
        module,
    ):
        preferred_names = (
            "VintedExportImportDialog",
            "VintedExportDialog",
            "ImportVintedExportDialog",
        )

        for name in preferred_names:
            candidate = getattr(
                module,
                name,
                None,
            )

            if (
                isinstance(
                    candidate,
                    type,
                )
                and issubclass(
                    candidate,
                    QDialog,
                )
            ):
                return candidate

        for name, candidate in vars(
            module
        ).items():
            if not isinstance(
                candidate,
                type,
            ):
                continue

            try:
                is_dialog = issubclass(
                    candidate,
                    QDialog,
                )

            except TypeError:
                continue

            if not is_dialog:
                continue

            if (
                candidate.__module__
                != module.__name__
            ):
                continue

            normalized_name = (
                name.casefold()
            )

            if (
                "vinted"
                in normalized_name
                and "import"
                in normalized_name
            ):
                return candidate

        return None

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
        page = super()._ensure_page_loaded(
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
        super()._change_page(
            index,
            page_name,
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
            BrandedRelistingPreparationDialog(
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