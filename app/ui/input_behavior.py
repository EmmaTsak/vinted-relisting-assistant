from __future__ import annotations

from PySide6.QtCore import (
    QEvent,
    QObject,
    Qt,
)
from PySide6.QtGui import (
    QKeyEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QWidget,
)


class InputBehaviorManager(QObject):
    """
    Application-wide protection against accidental value changes.

    Behaviour:
    - numeric spin boxes have no +/- arrow buttons
    - mouse wheel does not change numeric values
    - mouse wheel does not change combo-box selections
    - mouse wheel does not change date/time spin controls
    - Up/Down/PageUp/PageDown do not increment numeric spin boxes
    - mouse wheel continues scrolling the surrounding page where
      a scroll area exists

    This is installed once on QApplication and automatically
    applies to widgets created later.
    """

    def __init__(
        self,
        application: QApplication,
    ) -> None:
        super().__init__(
            application
        )

        self.application = application

        self.application.installEventFilter(
            self
        )

    def eventFilter(
        self,
        watched: QObject,
        event: QEvent,
    ) -> bool:
        # ---------------------------------------------
        # Numeric boxes should look like normal
        # writing fields rather than spinner controls.
        # ---------------------------------------------
        if (
            event.type()
            == QEvent.Type.Show
            and isinstance(
                watched,
                (
                    QSpinBox,
                    QDoubleSpinBox,
                ),
            )
        ):
            watched.setButtonSymbols(
                QAbstractSpinBox.ButtonSymbols.NoButtons
            )

        # ---------------------------------------------
        # Disable wheel-based value changes.
        #
        # QAbstractSpinBox also includes QDateEdit /
        # QTimeEdit, so dates cannot accidentally move
        # while the user is scrolling.
        # ---------------------------------------------
        if (
            event.type()
            == QEvent.Type.Wheel
            and isinstance(
                watched,
                (
                    QComboBox,
                    QAbstractSpinBox,
                ),
            )
        ):
            if isinstance(
                event,
                QWheelEvent,
            ):
                self._forward_wheel_to_scroll_area(
                    watched,
                    event,
                )

            return True

        # ---------------------------------------------
        # Numeric boxes should be typed into.
        #
        # Prevent keyboard Up/Down/PageUp/PageDown
        # from acting like hidden spinner buttons.
        # ---------------------------------------------
        if (
            event.type()
            == QEvent.Type.KeyPress
            and isinstance(
                watched,
                (
                    QSpinBox,
                    QDoubleSpinBox,
                ),
            )
            and isinstance(
                event,
                QKeyEvent,
            )
        ):
            blocked_keys = {
                Qt.Key.Key_Up,
                Qt.Key.Key_Down,
                Qt.Key.Key_PageUp,
                Qt.Key.Key_PageDown,
            }

            if (
                event.key()
                in blocked_keys
            ):
                return True

        return super().eventFilter(
            watched,
            event,
        )

    def _forward_wheel_to_scroll_area(
        self,
        widget: QObject,
        event: QWheelEvent,
    ) -> None:
        """
        When a protected field is inside a scrollable page,
        use the wheel movement to scroll the page instead of
        modifying the field.

        When there is no surrounding scroll area, simply
        prevent the field value from changing.
        """
        if not isinstance(
            widget,
            QWidget,
        ):
            event.ignore()
            return

        ancestor = (
            widget.parentWidget()
        )

        while ancestor is not None:
            if isinstance(
                ancestor,
                QAbstractScrollArea,
            ):
                scrollbar = (
                    ancestor
                    .verticalScrollBar()
                )

                delta = (
                    event.angleDelta().y()
                )

                if delta:
                    steps = (
                        delta
                        / 120
                    )

                    distance = max(
                        20,
                        scrollbar.singleStep()
                        * 3,
                    )

                    new_value = int(
                        scrollbar.value()
                        - (
                            steps
                            * distance
                        )
                    )

                    scrollbar.setValue(
                        new_value
                    )

                    event.accept()
                    return

            ancestor = (
                ancestor.parentWidget()
            )

        event.ignore()


def initialize_input_behavior(
    application: QApplication,
) -> InputBehaviorManager:
    """
    Install the global input behaviour manager.
    """
    return InputBehaviorManager(
        application
    )