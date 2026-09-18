from __future__ import annotations

from typing import Final

from PySide6.QtCore import (
    QEvent,
    QObject,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QPalette,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
)


THEME_SYSTEM: Final[str] = "system"
THEME_LIGHT: Final[str] = "light"
THEME_DARK: Final[str] = "dark"


class ThemeManager(QObject):
    """
    Central appearance manager.

    The application still contains a few older widget-local
    stylesheets from earlier development stages. They are cleared
    when widgets appear so the global product theme wins.
    """

    def __init__(
        self,
        application: QApplication,
    ) -> None:
        super().__init__(
            application
        )

        self.application = application

        self.preference = THEME_SYSTEM

        self._native_palette = QPalette(
            application.palette()
        )

        self.application.installEventFilter(
            self
        )

        self._connect_system_theme_signal()

    # =====================================================
    # Public API
    # =====================================================

    def apply(
        self,
        preference: str,
    ) -> None:
        normalized = (
            str(
                preference
            )
            .strip()
            .lower()
        )

        if normalized not in {
            THEME_SYSTEM,
            THEME_LIGHT,
            THEME_DARK,
        }:
            normalized = THEME_SYSTEM

        self.preference = normalized

        effective_theme = (
            self._effective_theme()
        )

        self._clear_existing_local_styles()

        if (
            effective_theme
            == THEME_DARK
        ):
            palette = (
                self._create_dark_palette()
            )

            stylesheet = (
                self._build_stylesheet(
                    dark=True
                )
            )

        else:
            palette = (
                self._create_light_palette()
            )

            stylesheet = (
                self._build_stylesheet(
                    dark=False
                )
            )

        self.application.setPalette(
            palette
        )

        self.application.setStyleSheet(
            stylesheet
        )

    def effective_theme(
        self,
    ) -> str:
        return self._effective_theme()

    # =====================================================
    # System appearance
    # =====================================================

    def eventFilter(
        self,
        watched: QObject,
        event: QEvent,
    ) -> bool:
        if (
            event.type()
            == QEvent.Type.Show
            and isinstance(
                watched,
                QWidget,
            )
        ):
            self._clear_widget_styles(
                watched
            )

        return super().eventFilter(
            watched,
            event,
        )

    def _connect_system_theme_signal(
        self,
    ) -> None:
        try:
            style_hints = (
                self.application
                .styleHints()
            )

            style_hints.colorSchemeChanged.connect(
                self._system_theme_changed
            )

        except (
            AttributeError,
            RuntimeError,
        ):
            pass

    def _system_theme_changed(
        self,
        *args,
    ) -> None:
        del args

        if (
            self.preference
            == THEME_SYSTEM
        ):
            self.apply(
                THEME_SYSTEM
            )

    def _effective_theme(
        self,
    ) -> str:
        if (
            self.preference
            == THEME_LIGHT
        ):
            return THEME_LIGHT

        if (
            self.preference
            == THEME_DARK
        ):
            return THEME_DARK

        return (
            THEME_DARK
            if self._system_is_dark()
            else THEME_LIGHT
        )

    def _system_is_dark(
        self,
    ) -> bool:
        try:
            scheme = (
                self.application
                .styleHints()
                .colorScheme()
            )

            if (
                scheme
                == Qt.ColorScheme.Dark
            ):
                return True

            if (
                scheme
                == Qt.ColorScheme.Light
            ):
                return False

        except (
            AttributeError,
            RuntimeError,
        ):
            pass

        native_window = (
            self._native_palette.color(
                QPalette.ColorRole.Window
            )
        )

        return (
            native_window.lightness()
            < 128
        )

    # =====================================================
    # Legacy style cleanup
    # =====================================================

    def _clear_existing_local_styles(
        self,
    ) -> None:
        for widget in (
            self.application.allWidgets()
        ):
            if widget.styleSheet():
                widget.setStyleSheet(
                    ""
                )

    def _clear_widget_styles(
        self,
        widget: QWidget,
    ) -> None:
        if widget.styleSheet():
            widget.setStyleSheet(
                ""
            )

        for child in widget.findChildren(
            QWidget
        ):
            if child.styleSheet():
                child.setStyleSheet(
                    ""
                )

    # =====================================================
    # Qt palettes
    # =====================================================

    def _create_light_palette(
        self,
    ) -> QPalette:
        palette = QPalette()

        palette.setColor(
            QPalette.ColorRole.Window,
            QColor(
                "#F9ECEF"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.WindowText,
            QColor(
                "#2D2427"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Base,
            QColor(
                "#FFF3F5"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.AlternateBase,
            QColor(
                "#F7E5EA"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Text,
            QColor(
                "#2D2427"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Button,
            QColor(
                "#FFF3F5"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.ButtonText,
            QColor(
                "#2D2427"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Highlight,
            QColor(
                "#B83268"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.HighlightedText,
            QColor(
                "#FFFFFF"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.ToolTipBase,
            QColor(
                "#2D2427"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.ToolTipText,
            QColor(
                "#F9ECEF"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.PlaceholderText,
            QColor(
                "#9A858D"
            ),
        )

        return palette

    def _create_dark_palette(
        self,
    ) -> QPalette:
        palette = QPalette()

        palette.setColor(
            QPalette.ColorRole.Window,
            QColor(
                "#1E191B"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.WindowText,
            QColor(
                "#F8F2F4"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Base,
            QColor(
                "#2A2226"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.AlternateBase,
            QColor(
                "#352A2F"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Text,
            QColor(
                "#F8F2F4"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Button,
            QColor(
                "#2A2226"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.ButtonText,
            QColor(
                "#F8F2F4"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Highlight,
            QColor(
                "#F08DB1"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.HighlightedText,
            QColor(
                "#291820"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.ToolTipBase,
            QColor(
                "#F8F2F4"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.ToolTipText,
            QColor(
                "#2A2226"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.PlaceholderText,
            QColor(
                "#A9959D"
            ),
        )

        return palette

    # =====================================================
    # Global stylesheet
    # =====================================================

    def _build_stylesheet(
        self,
        dark: bool,
    ) -> str:
        if dark:
            # ---------------------------------------------
            # Warm dark mode
            # ---------------------------------------------

            background = "#1E191B"

            surface = "#2A2226"

            surface_alt = "#352A2F"

            surface_hover = "#403238"

            text = "#F8F2F4"

            secondary_text = "#E1D3D8"

            muted_text = "#BBAAB0"

            border = "#4A3A41"

            border_hover = "#765A66"

            primary = "#F08DB1"

            primary_hover = "#FA9FC0"

            primary_text = "#291820"

            sidebar = "#261E22"

            sidebar_hover = "#35272E"

            sidebar_selected = "#F08DB1"

            sidebar_text = "#F8F2F4"

            sidebar_muted = "#C7B5BC"

            sidebar_selected_text = "#291820"

            success_background = "#173E2B"

            success_text = "#BDE8CD"

            warning_background = "#49351C"

            warning_text = "#F5D59C"

            danger_background = "#4A2228"

            danger = "#B94B5A"

            danger_hover = "#A33B49"

            danger_text = "#F5C8CE"

            info_background = "#24364D"

            info_text = "#C9DCF5"

            accent_soft = "#422B35"

            accent_soft_text = "#F5CBDC"

            scrollbar = "#765A66"

        else:
            # ---------------------------------------------
            # Warm light mode
            # ---------------------------------------------

            background = "#F9ECEF"

            surface = "#FFF3F5"

            surface_alt = "#F7E5EA"

            surface_hover = "#F1D8E0"

            text = "#2D2427"

            secondary_text = "#59474E"

            muted_text = "#78666D"

            border = "#DFC5CF"

            border_hover = "#CA93A6"

            primary = "#B83268"

            primary_hover = "#9E2858"

            primary_text = "#FFFFFF"

            sidebar = "#F3D5DF"

            sidebar_hover = "#EBC3D1"

            sidebar_selected = "#B83268"

            sidebar_text = "#49353D"

            sidebar_muted = "#806B73"

            sidebar_selected_text = "#FFFFFF"

            success_background = "#E7F6ED"

            success_text = "#24623A"

            warning_background = "#FFF2D9"

            warning_text = "#7A5314"

            danger_background = "#FCE6E8"

            danger = "#B63848"

            danger_hover = "#982D3B"

            danger_text = "#872633"

            info_background = "#E8EFFA"

            info_text = "#34547C"

            accent_soft = "#FBE7EE"

            accent_soft_text = "#853251"

            scrollbar = "#CFA8B7"

        return f"""
        /*
        ====================================================
        BASE
        ====================================================
        */

        * {{
            font-family: "Segoe UI";
            font-size: 13px;
        }}

        QMainWindow,
        QDialog {{
            background-color: {background};
            color: {text};
        }}

        QWidget {{
            color: {text};
        }}

        QScrollArea,
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
            border: none;
        }}

        QLabel {{
            background-color: transparent;
            color: {text};
        }}

        QFrame#contentArea {{
            background-color: {background};
        }}

        /*
        ====================================================
        SIDEBAR / BRAND
        ====================================================
        */

        #sidebar {{
            background-color: {sidebar};
            border: none;
        }}

        #brandIdentity {{
            background-color: transparent;
            border: none;
        }}

        #sidebarAppName {{
            color: {sidebar_text};
            font-size: 22px;
            font-weight: 700;
        }}

        #sidebarSubtitle {{
            color: {sidebar_muted};
            font-size: 12px;
        }}

        #navigationButton {{
            background-color: transparent;
            color: {sidebar_text};
            border: none;
            border-radius: 10px;
            text-align: left;
            padding: 10px 12px;
        }}

        #navigationButton:hover {{
            background-color: {sidebar_hover};
            color: {sidebar_text};
        }}

        #navigationButton:checked {{
            background-color: {sidebar_selected};
            color: {sidebar_selected_text};
            font-weight: 600;
        }}

        #versionLabel {{
            color: {sidebar_muted};
            font-size: 11px;
        }}

        /*
        ====================================================
        TYPOGRAPHY
        ====================================================
        */

        #pageTitle {{
            color: {text};
            font-size: 27px;
            font-weight: 700;
        }}

        #preparationHeading,
        #backupHeading {{
            color: {text};
            font-size: 23px;
            font-weight: 700;
        }}

        #placeholderTitle {{
            color: {text};
            font-size: 16px;
            font-weight: 700;
        }}

        #headerPrice {{
            color: {text};
            font-size: 21px;
            font-weight: 700;
        }}

        #listingTitle,
        #queueTitle,
        #historyTitle,
        #attentionTitle,
        #activityTitle {{
            color: {text};
            font-weight: 700;
        }}

        #listingPrice,
        #queuePrice {{
            color: {text};
            font-size: 17px;
            font-weight: 700;
        }}

        #subtitle,
        #placeholderText,
        #settingsExplanation,
        #backupDescription,
        #dashboardIntroduction,
        #historyExplanation,
        #metadataText,
        #dateText,
        #queueDetails,
        #queueMessage,
        #historySecondaryText,
        #attentionText,
        #activityDate,
        #panelMessage,
        #informationText,
        #settingsNoteText,
        #categoryHelpText,
        #helpText {{
            color: {muted_text};
        }}

        #sectionTitle,
        #sectionHeading,
        #filterHeading,
        #panelHeading,
        #attentionHeading,
        #fieldHeading {{
            color: {secondary_text};
            font-weight: 700;
        }}

        /*
        ====================================================
        CARDS / PANELS
        ====================================================
        */

        #pagePlaceholder,
        #settingsFrame,
        #searchFrame,
        #filterFrame,
        #queueHeader,
        #queueCard,
        #listingCard,
        #historySummary,
        #historyCard,
        #statisticCard,
        #dashboardPanel,
        #photoPanel,
        #detailField,
        #informationBox,
        #categoryToolbar {{
            background-color: {surface};
            border: 1px solid {border};
            border-radius: 14px;
        }}

        #listingCard:hover,
        #historyCard:hover,
        #queueCard:hover {{
            border: 1px solid {border_hover};
        }}

        #photoContainer,
        #queuePhoto,
        #largePreview,
        #historyDateBox,
        #attentionItem,
        #activityRow,
        #settingsNote {{
            background-color: {surface_alt};
            border: 1px solid {border};
            border-radius: 12px;
        }}

        #noPhoto,
        #statisticSubtitle {{
            color: {muted_text};
        }}

        #statisticTitle,
        #filterLabel {{
            color: {muted_text};
            font-size: 11px;
            font-weight: 600;
        }}

        #statisticValue,
        #historyDay {{
            color: {text};
            font-size: 27px;
            font-weight: 700;
        }}

        #historyMonth {{
            color: {muted_text};
            font-size: 11px;
            font-weight: 600;
        }}

        #summaryValue,
        #queueProgress,
        #historyPrimaryText,
        #currentStatus {{
            color: {text};
            font-weight: 600;
        }}

        /*
        ====================================================
        FORM CONTROLS
        ====================================================
        */

        QLineEdit,
        QTextEdit,
        QPlainTextEdit,
        QComboBox,
        QSpinBox,
        QDoubleSpinBox,
        QDateEdit,
        QListWidget,
        QTreeWidget,
        QTableWidget,
        QTableView {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 7px 9px;
            selection-background-color: {primary};
            selection-color: {primary_text};
        }}

        QTextEdit:read-only,
        QPlainTextEdit:read-only {{
            background-color: {surface_alt};
        }}

        QLineEdit:hover,
        QTextEdit:hover,
        QPlainTextEdit:hover,
        QComboBox:hover,
        QSpinBox:hover,
        QDoubleSpinBox:hover,
        QDateEdit:hover,
        QListWidget:hover {{
            border-color: {border_hover};
        }}

        QLineEdit:focus,
        QTextEdit:focus,
        QPlainTextEdit:focus,
        QComboBox:focus,
        QSpinBox:focus,
        QDoubleSpinBox:focus,
        QDateEdit:focus,
        QListWidget:focus {{
            border: 1px solid {primary};
        }}

        QComboBox QAbstractItemView,
        QAbstractItemView {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            selection-background-color: {primary};
            selection-color: {primary_text};
            outline: none;
        }}

        QComboBox::drop-down {{
            border: none;
            width: 26px;
        }}

        QCheckBox {{
            color: {text};
            spacing: 8px;
        }}

        /*
        ====================================================
        BUTTONS
        ====================================================
        */

        QPushButton {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 8px 13px;
            font-weight: 600;
        }}

        QPushButton:hover {{
            background-color: {surface_hover};
            border-color: {border_hover};
        }}

        QPushButton:pressed {{
            background-color: {surface_alt};
        }}

        QPushButton:disabled {{
            color: {muted_text};
            background-color: {surface_alt};
            border-color: {border};
        }}

        #primaryButton,
        #primaryCardButton,
        #primaryQueueButton,
        #saveButton {{
            background-color: {primary};
            color: {primary_text};
            border: 1px solid {primary};
            border-radius: 12px;
            font-weight: 700;
        }}

        #primaryButton:hover,
        #primaryCardButton:hover,
        #primaryQueueButton:hover,
        #saveButton:hover {{
            background-color: {primary_hover};
            border-color: {primary_hover};
        }}

        #secondaryButton,
        #secondaryCardButton,
        #secondaryQueueButton,
        #browseButton,
        #refreshButton,
        #resetButton,
        #historyRefreshButton,
        #dashboardRefreshButton,
        #copyButton,
        #smallButton,
        #panelActionButton,
        #historyEditButton,
        #actionButton,
        #cancelButton,
        #photoButton,
        #filterToggleButton,
        #paginationButton {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 10px;
        }}

        #secondaryButton:hover,
        #secondaryCardButton:hover,
        #secondaryQueueButton:hover,
        #browseButton:hover,
        #refreshButton:hover,
        #resetButton:hover,
        #historyRefreshButton:hover,
        #dashboardRefreshButton:hover,
        #copyButton:hover,
        #smallButton:hover,
        #panelActionButton:hover,
        #historyEditButton:hover,
        #actionButton:hover,
        #cancelButton:hover,
        #photoButton:hover,
        #filterToggleButton:hover,
        #paginationButton:hover {{
            background-color: {surface_hover};
            border-color: {border_hover};
        }}

        #filterToggleButton:checked {{
            background-color: {accent_soft};
            color: {accent_soft_text};
            border-color: {border_hover};
        }}

        /*
        ====================================================
        DESTRUCTIVE ACTIONS
        ====================================================
        */

        #destructiveButton {{
            background-color: {danger};
            color: white;
            border: 1px solid {danger};
            border-radius: 10px;
            font-weight: 700;
        }}

        #destructiveButton:hover {{
            background-color: {danger_hover};
            border-color: {danger_hover};
        }}

        /*
        ====================================================
        BADGES
        ====================================================
        */

        #activeBadge {{
            background-color: {success_background};
            color: {success_text};
            border-radius: 7px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 600;
        }}

        #pausedBadge,
        #warningBadge {{
            background-color: {warning_background};
            color: {warning_text};
            border-radius: 7px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 600;
        }}

        #soldBadge {{
            background-color: {info_background};
            color: {info_text};
            border-radius: 7px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 600;
        }}

        #archivedBadge,
        #priorityBadge {{
            background-color: {surface_alt};
            color: {secondary_text};
            border: 1px solid {border};
            border-radius: 7px;
            padding: 4px 8px;
            font-size: 11px;
        }}

        #excludedBadge {{
            background-color: {danger_background};
            color: {danger_text};
            border-radius: 7px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 600;
        }}

        /*
        ====================================================
        MESSAGES
        ====================================================
        */

        #warningText {{
            background-color: {warning_background};
            color: {warning_text};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 10px;
        }}

        #successText {{
            color: {success_text};
            font-weight: 700;
        }}

        #emptyState,
        #queueEmpty,
        #historyEmpty,
        #statusEmpty {{
            background-color: {surface};
            color: {muted_text};
            border: 1px solid {border};
            border-radius: 14px;
            padding: 35px;
        }}

        #errorState,
        #historyError,
        #dashboardError {{
            background-color: {danger_background};
            color: {danger_text};
            border: 1px solid {danger};
            border-radius: 14px;
            padding: 25px;
        }}

        /*
        ====================================================
        PROGRESS
        ====================================================
        */

        QProgressBar {{
            background-color: {surface_alt};
            border: 1px solid {border};
            border-radius: 6px;
            color: {text};
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {primary};
            border-radius: 5px;
        }}

        /*
        ====================================================
        BACKUPS
        ====================================================
        */

        #backupList {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 6px;
        }}

        #backupList::item {{
            padding: 10px;
            border-bottom: 1px solid {border};
        }}

        #backupList::item:selected {{
            background-color: {primary};
            color: {primary_text};
        }}

        #backupDetails {{
            background-color: {surface_alt};
            color: {secondary_text};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 12px;
        }}

        /*
        ====================================================
        TOOLTIP / MESSAGE BOX
        ====================================================
        */

        QToolTip {{
            background-color: {text};
            color: {surface};
            border: 1px solid {border_hover};
            border-radius: 6px;
            padding: 6px;
        }}

        QMessageBox {{
            background-color: {background};
        }}

        QMessageBox QLabel {{
            color: {text};
            background-color: transparent;
        }}

        QMessageBox QPushButton {{
            min-width: 88px;
            min-height: 32px;
        }}

        /*
        ====================================================
        SCROLLBARS
        ====================================================
        */

        QScrollBar:vertical {{
            background: transparent;
            width: 11px;
            margin: 2px;
        }}

        QScrollBar::handle:vertical {{
            background: {scrollbar};
            border-radius: 5px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {primary};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: transparent;
        }}

        QScrollBar:horizontal {{
            background: transparent;
            height: 11px;
            margin: 2px;
        }}

        QScrollBar::handle:horizontal {{
            background: {scrollbar};
            border-radius: 5px;
            min-width: 30px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {primary};
        }}

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {{
            background: transparent;
        }}

        /*
        ====================================================
        MENUS
        ====================================================
        */

        QMenu {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 4px;
        }}

        QMenu::item {{
            padding: 7px 24px;
            border-radius: 6px;
        }}

        QMenu::item:selected {{
            background-color: {primary};
            color: {primary_text};
        }}
        """


_theme_manager: ThemeManager | None = None


def initialize_theme_manager(
    application: QApplication,
) -> ThemeManager:
    """
    Create and retain the application's single ThemeManager.
    """
    global _theme_manager

    if _theme_manager is None:
        _theme_manager = ThemeManager(
            application
        )

    return _theme_manager


def get_theme_manager() -> ThemeManager | None:
    return _theme_manager


def apply_theme(
    preference: str,
) -> None:
    """
    Apply a theme from anywhere in the UI.
    """
    if _theme_manager is not None:
        _theme_manager.apply(
            preference
        )