from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
)


def fit_dialog_to_screen(
    dialog: QWidget,
    *,
    preferred_width: int,
    preferred_height: int,
    minimum_width: int = 700,
    minimum_height: int = 500,
    width_ratio: float = 0.90,
    height_ratio: float = 0.86,
) -> None:
    """
    Size and centre a dialog inside the usable area of its
    current monitor.

    Fixed preferred dimensions are used when there is enough
    room. Smaller screens automatically receive a smaller
    initial window instead of letting the dialog extend past
    the taskbar or screen edges.
    """
    screen = dialog.screen()

    if screen is None:
        screen = QApplication.primaryScreen()

    if screen is None:
        dialog.resize(
            preferred_width,
            preferred_height,
        )

        return

    available = screen.availableGeometry()

    available_width = max(
        640,
        int(
            available.width()
            * width_ratio
        ),
    )

    available_height = max(
        480,
        int(
            available.height()
            * height_ratio
        ),
    )

    width = min(
        preferred_width,
        available_width,
    )

    height = min(
        preferred_height,
        available_height,
    )

    dialog.setMinimumSize(
        min(
            minimum_width,
            width,
        ),
        min(
            minimum_height,
            height,
        ),
    )

    dialog.resize(
        width,
        height,
    )

    frame = dialog.frameGeometry()

    frame.moveCenter(
        available.center()
    )

    dialog.move(
        frame.topLeft()
    )
