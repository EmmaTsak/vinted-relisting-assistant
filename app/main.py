from __future__ import annotations

import sys

from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
)

from app import APP_NAME
from app.database import (
    database_health_check,
    initialize_database,
)
from app.services.settings_service import (
    default_settings,
    load_settings,
)
from app.ui.input_behavior import (
    initialize_input_behavior,
)
from app.ui.polished_main_window import (
    PolishedMainWindow,
)
from app.ui.theme import (
    initialize_theme_manager,
)


MINIMUM_PYTHON_VERSION = (
    3,
    12,
)


def check_python_version() -> None:
    if (
        sys.version_info
        < MINIMUM_PYTHON_VERSION
    ):
        required_version = ".".join(
            map(
                str,
                MINIMUM_PYTHON_VERSION,
            )
        )

        current_version = (
            f"{sys.version_info.major}."
            f"{sys.version_info.minor}."
            f"{sys.version_info.micro}"
        )

        raise RuntimeError(
            (
                f"{APP_NAME} requires Python "
                f"{required_version} or newer. "
                f"Current version: {current_version}"
            )
        )


def initialize_application() -> None:
    initialize_database()

    if not database_health_check():
        raise RuntimeError(
            (
                "The application could not connect "
                "to the local SQLite database."
            )
        )


def load_startup_theme() -> str:
    """
    Load the saved appearance preference without preventing
    startup if settings.json is damaged.
    """
    try:
        settings = load_settings()

    except Exception:
        settings = default_settings()

    return settings.theme


def main() -> int:
    check_python_version()

    qt_app = QApplication(
        sys.argv
    )

    qt_app.setApplicationName(
        APP_NAME
    )

    qt_app.setOrganizationName(
        "VintedRelistingAssistant"
    )

    # -------------------------------------------------
    # Global input safety.
    #
    # This must be installed before windows/dialogs are
    # created so both existing and lazily-created widgets
    # receive the same behaviour.
    # -------------------------------------------------

    input_behavior = (
        initialize_input_behavior(
            qt_app
        )
    )

    # Keep a strong reference for the lifetime of main().
    # QObject is also parented to QApplication.
    _ = input_behavior

    theme_manager = (
        initialize_theme_manager(
            qt_app
        )
    )

    theme_manager.apply(
        load_startup_theme()
    )

    try:
        initialize_application()

    except Exception as exc:
        QMessageBox.critical(
            None,
            "Application Error",
            (
                "Vinted Relisting Assistant "
                "could not start.\n\n"
                f"{exc}"
            ),
        )

        return 1

    window = (
        PolishedMainWindow()
    )

    window.show()

    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(
        main()
    )