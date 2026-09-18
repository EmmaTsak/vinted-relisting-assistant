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
    Central theme manager for the entire application.

    Individual screens in earlier development stages used their own
    stylesheets. This manager clears those local styles whenever a
    widget appears and lets one application-wide stylesheet control
    the appearance consistently.
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

    def apply(
        self,
        preference: str,
    ) -> None:
        """
        Apply System, Light or Dark appearance.

        System follows the current operating-system colour scheme.
        """
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

        if effective_theme == THEME_DARK:
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
        """
        Return the currently rendered theme.
        """
        return self._effective_theme()

    def eventFilter(
        self,
        watched: QObject,
        event: QEvent,
    ) -> bool:
        """
        Remove old widget-specific styles whenever widgets are shown.

        This also handles cards/dialogs created after the application
        has already started.
        """
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
        """
        Follow Windows theme changes while System mode is selected.
        """
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
        """
        Ask Qt for the operating-system colour scheme.

        Falls back to the original application palette when the
        installed Qt version cannot expose the OS colour scheme.
        """
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

    def _clear_existing_local_styles(
        self,
    ) -> None:
        """
        Remove all older widget-level stylesheets.

        The application-wide theme stylesheet then becomes the single
        source of truth for colours.
        """
        for widget in (
            self.application
            .allWidgets()
        ):
            if widget.styleSheet():
                widget.setStyleSheet(
                    ""
                )

    def _clear_widget_styles(
        self,
        widget: QWidget,
    ) -> None:
        """
        Clear styles from one newly displayed widget and its children.
        """
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

    def _create_light_palette(
        self,
    ) -> QPalette:
        palette = QPalette()

        palette.setColor(
            QPalette.ColorRole.Window,
            QColor(
                "#f5f6f8"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.WindowText,
            QColor(
                "#111827"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Base,
            QColor(
                "#ffffff"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.AlternateBase,
            QColor(
                "#f9fafb"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Text,
            QColor(
                "#111827"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Button,
            QColor(
                "#ffffff"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.ButtonText,
            QColor(
                "#111827"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Highlight,
            QColor(
                "#dbeafe"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.HighlightedText,
            QColor(
                "#111827"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.ToolTipBase,
            QColor(
                "#111827"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.ToolTipText,
            QColor(
                "#ffffff"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.PlaceholderText,
            QColor(
                "#9ca3af"
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
                "#111827"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.WindowText,
            QColor(
                "#f3f4f6"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Base,
            QColor(
                "#1f2937"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.AlternateBase,
            QColor(
                "#273449"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Text,
            QColor(
                "#f3f4f6"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Button,
            QColor(
                "#273449"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.ButtonText,
            QColor(
                "#f3f4f6"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.Highlight,
            QColor(
                "#2563eb"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.HighlightedText,
            QColor(
                "#ffffff"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.ToolTipBase,
            QColor(
                "#f9fafb"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.ToolTipText,
            QColor(
                "#111827"
            ),
        )

        palette.setColor(
            QPalette.ColorRole.PlaceholderText,
            QColor(
                "#9ca3af"
            ),
        )

        return palette

    def _build_stylesheet(
        self,
        dark: bool,
    ) -> str:
        if dark:
            background = "#111827"
            surface = "#1f2937"
            surface_alt = "#273449"
            surface_hover = "#334155"

            text = "#f3f4f6"
            secondary_text = "#cbd5e1"
            muted_text = "#94a3b8"

            border = "#374151"
            border_hover = "#64748b"

            primary = "#2563eb"
            primary_hover = "#1d4ed8"

            sidebar = "#0f172a"
            sidebar_hover = "#1e293b"
            sidebar_selected = "#334155"

            success_background = "#14532d"
            success_text = "#dcfce7"

            warning_background = "#78350f"
            warning_text = "#fef3c7"

            danger_background = "#7f1d1d"
            danger = "#dc2626"
            danger_hover = "#b91c1c"
            danger_text = "#fee2e2"

            info_background = "#1e3a8a"
            info_text = "#dbeafe"

        else:
            background = "#f5f6f8"
            surface = "#ffffff"
            surface_alt = "#f9fafb"
            surface_hover = "#f3f4f6"

            text = "#111827"
            secondary_text = "#4b5563"
            muted_text = "#6b7280"

            border = "#e5e7eb"
            border_hover = "#9ca3af"

            primary = "#1f2937"
            primary_hover = "#374151"

            sidebar = "#1f2937"
            sidebar_hover = "#374151"
            sidebar_selected = "#4b5563"

            success_background = "#dcfce7"
            success_text = "#166534"

            warning_background = "#fef3c7"
            warning_text = "#92400e"

            danger_background = "#fee2e2"
            danger = "#b91c1c"
            danger_hover = "#991b1b"
            danger_text = "#991b1b"

            info_background = "#dbeafe"
            info_text = "#1e40af"

        return f"""
        * {{
            font-family: "Segoe UI";
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

        #sidebar {{
            background-color: {sidebar};
            border: none;
        }}

        #sidebarAppName {{
            color: white;
            font-size: 24px;
            font-weight: 700;
        }}

        #sidebarSubtitle {{
            color: #cbd5e1;
        }}

        #navigationButton {{
            background-color: transparent;
            color: #d1d5db;
            border: none;
            border-radius: 7px;
            text-align: left;
            padding: 11px 12px;
        }}

        #navigationButton:hover {{
            background-color: {sidebar_hover};
            color: white;
        }}

        #navigationButton:checked {{
            background-color: {sidebar_selected};
            color: white;
            font-weight: 600;
        }}

        #versionLabel {{
            color: #94a3b8;
            font-size: 12px;
        }}

        #pageTitle {{
            color: {text};
            font-size: 28px;
            font-weight: 700;
        }}

        #preparationHeading,
        #backupHeading {{
            color: {text};
            font-size: 24px;
            font-weight: 700;
        }}

        #headerPrice {{
            color: {text};
            font-size: 22px;
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
            font-size: 18px;
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
        #settingsNoteText {{
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
        #informationBox {{
            background-color: {surface};
            border: 1px solid {border};
            border-radius: 10px;
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
            border-radius: 8px;
        }}

        #noPhoto,
        #statisticSubtitle {{
            color: {muted_text};
        }}

        #statisticTitle,
        #filterLabel {{
            color: {muted_text};
            font-size: 12px;
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
            font-size: 12px;
            font-weight: 600;
        }}

        #summaryValue,
        #queueProgress,
        #historyPrimaryText,
        #currentStatus {{
            color: {text};
            font-weight: 600;
        }}

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
            border-radius: 6px;
            padding: 7px;
            selection-background-color: {primary};
            selection-color: white;
        }}

        QTextEdit:read-only,
        QPlainTextEdit:read-only {{
            background-color: {surface_alt};
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
            selection-color: white;
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}

        QPushButton {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 7px;
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
        #primaryQueueButton {{
            background-color: {primary};
            color: white;
            border: 1px solid {primary};
            font-weight: 700;
        }}

        #primaryButton:hover,
        #primaryCardButton:hover,
        #primaryQueueButton:hover {{
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
        #actionButton {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
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
        #actionButton:hover {{
            background-color: {surface_hover};
        }}

        #destructiveButton {{
            background-color: {danger};
            color: white;
            border: 1px solid {danger};
            font-weight: 700;
        }}

        #destructiveButton:hover {{
            background-color: {danger_hover};
            border-color: {danger_hover};
        }}

        #activeBadge {{
            background-color: {success_background};
            color: {success_text};
            border-radius: 5px;
            padding: 4px 8px;
            font-size: 12px;
            font-weight: 600;
        }}

        #pausedBadge {{
            background-color: {warning_background};
            color: {warning_text};
            border-radius: 5px;
            padding: 4px 8px;
            font-size: 12px;
            font-weight: 600;
        }}

        #soldBadge {{
            background-color: {info_background};
            color: {info_text};
            border-radius: 5px;
            padding: 4px 8px;
            font-size: 12px;
            font-weight: 600;
        }}

        #archivedBadge,
        #priorityBadge {{
            background-color: {surface_alt};
            color: {secondary_text};
            border: 1px solid {border};
            border-radius: 5px;
            padding: 4px 8px;
            font-size: 12px;
        }}

        #excludedBadge {{
            background-color: {danger_background};
            color: {danger_text};
            border-radius: 5px;
            padding: 4px 8px;
            font-size: 12px;
            font-weight: 600;
        }}

        #warningText {{
            background-color: {warning_background};
            color: {warning_text};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 8px;
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
            border-radius: 10px;
            padding: 35px;
        }}

        #errorState,
        #historyError,
        #dashboardError {{
            background-color: {danger_background};
            color: {danger_text};
            border: 1px solid {danger};
            border-radius: 10px;
            padding: 25px;
        }}

        #backupList {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 6px;
        }}

        #backupList::item {{
            padding: 10px;
            border-bottom: 1px solid {border};
        }}

        #backupList::item:selected {{
            background-color: {primary};
            color: white;
        }}

        #backupDetails {{
            background-color: {surface_alt};
            color: {secondary_text};
            border: 1px solid {border};
            border-radius: 7px;
            padding: 12px;
        }}

        QToolTip {{
            background-color: {text};
            color: {surface};
            border: 1px solid {border_hover};
            padding: 5px;
        }}

        QMessageBox {{
            background-color: {background};
        }}

        QMessageBox QLabel {{
            color: {text};
            background-color: transparent;
        }}

        QMessageBox QPushButton {{
            min-width: 80px;
            min-height: 28px;
        }}

        QScrollBar:vertical {{
            background: transparent;
            width: 11px;
            margin: 2px;
        }}

        QScrollBar::handle:vertical {{
            background: {border_hover};
            border-radius: 4px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {muted_text};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background: transparent;
            height: 11px;
            margin: 2px;
        }}

        QScrollBar::handle:horizontal {{
            background: {border_hover};
            border-radius: 4px;
            min-width: 30px;
        }}

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        QMenu {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
        }}

        QMenu::item {{
            padding: 7px 24px;
        }}

        QMenu::item:selected {{
            background-color: {primary};
            color: white;
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