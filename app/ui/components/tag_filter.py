from __future__ import annotations

from PySide6.QtCore import (
    Signal,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QMenu,
    QPushButton,
    QWidgetAction,
)


class TagFilterButton(QPushButton):
    """
    Compact multi-select filter for listing tags.

    The popup contains checkboxes so several tags may be
    selected without replacing the previous selection.
    """

    selection_changed = Signal()

    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(
            parent
        )

        self._selected: set[str] = (
            set()
        )

        self._options: list[str] = []

        self._tag_menu = QMenu(
            self
        )

        self.setMenu(
            self._tag_menu
        )

        self._update_text()

    def selected_tags(
        self,
    ) -> list[str]:
        return sorted(
            self._selected,
            key=str.casefold,
        )

    def menu_widget(
        self,
    ) -> QMenu:
        return self._tag_menu

    def set_options(
        self,
        values: list[str],
    ) -> None:
        """
        Replace available tag choices while preserving
        currently-selected values.

        Selected tags remain visible even if they currently
        match zero listings, keeping the active filter honest.
        """
        cleaned: dict[
            str,
            str,
        ] = {}

        for value in values:
            display = (
                value.strip()
            )

            if not display:
                continue

            cleaned.setdefault(
                display.casefold(),
                display,
            )

        for value in self._selected:
            cleaned.setdefault(
                value.casefold(),
                value,
            )

        previous_normalized = {
            value.casefold()
            for value
            in self._selected
        }

        self._options = sorted(
            cleaned.values(),
            key=str.casefold,
        )

        self._selected = {
            value
            for value in self._options
            if (
                value.casefold()
                in previous_normalized
            )
        }

        self._rebuild_menu()
        self._update_text()

    def clear_selection(
        self,
    ) -> None:
        if not self._selected:
            self._update_text()
            return

        self._selected.clear()

        self._rebuild_menu()
        self._update_text()

        self.selection_changed.emit()

    def _rebuild_menu(
        self,
    ) -> None:
        self._tag_menu.clear()

        if not self._options:
            empty_action = (
                self._tag_menu.addAction(
                    "No tags yet"
                )
            )

            empty_action.setEnabled(
                False
            )

            return

        for value in self._options:
            checkbox = QCheckBox(
                value
            )

            checkbox.setChecked(
                value in self._selected
            )

            checkbox.setMinimumWidth(
                180
            )

            action = QWidgetAction(
                self._tag_menu
            )

            action.setDefaultWidget(
                checkbox
            )

            self._tag_menu.addAction(
                action
            )

            checkbox.toggled.connect(
                lambda checked, tag=value:
                self._set_checked(
                    tag,
                    checked,
                )
            )

    def _set_checked(
        self,
        tag: str,
        checked: bool,
    ) -> None:
        if checked:
            self._selected.add(
                tag
            )

        else:
            self._selected.discard(
                tag
            )

        self._update_text()

        self.selection_changed.emit()

    def _update_text(
        self,
    ) -> None:
        count = len(
            self._selected
        )

        if count == 0:
            text = "All Tags"

        elif count == 1:
            text = next(
                iter(
                    self._selected
                )
            )

        else:
            text = (
                f"Tags ({count})"
            )

        self.setText(
            text
        )
