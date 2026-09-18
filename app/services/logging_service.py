from __future__ import annotations

import logging
import sys
import threading

from collections.abc import Callable
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app import (
    APP_NAME,
    APP_VERSION,
)
from app.utils.paths import (
    LOG_DIR,
    ensure_app_directories,
)


LOGGER_NAME = (
    "vinted_relisting_assistant"
)

LOG_FILE_PATH = (
    LOG_DIR
    / "application.log"
)

MAX_LOG_BYTES = (
    1_500_000
)

BACKUP_LOG_COUNT = (
    3
)


_logging_initialized = False
_exception_hooks_installed = False


def initialize_logging(
    *,
    record_startup: bool = True,
) -> logging.Logger:
    """
    Configure the application's persistent rotating log.

    Logs are stored under the persistent LocalAppData directory,
    completely independently from:
    - source code
    - build/
    - dist/
    - the location of the executable
    """
    global _logging_initialized

    logger = logging.getLogger(
        LOGGER_NAME
    )

    if _logging_initialized:
        return logger

    ensure_app_directories()

    logger.setLevel(
        logging.INFO
    )

    logger.propagate = False

    handler = RotatingFileHandler(
        filename=LOG_FILE_PATH,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_LOG_COUNT,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        (
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt=(
            "%Y-%m-%d %H:%M:%S"
        ),
    )

    handler.setFormatter(
        formatter
    )

    logger.addHandler(
        handler
    )

    _logging_initialized = True

    if record_startup:
        logger.info(
            "--------------------------------------------------"
        )

        logger.info(
            "%s %s starting",
            APP_NAME,
            APP_VERSION,
        )

        logger.info(
            "Python %s.%s.%s",
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        )

        logger.info(
            "Packaged executable: %s",
            bool(
                getattr(
                    sys,
                    "frozen",
                    False,
                )
            ),
        )

        logger.info(
            "Log file: %s",
            LOG_FILE_PATH,
        )

    return logger


def get_logger(
    name: str | None = None,
) -> logging.Logger:
    """
    Return an application logger.

    Child loggers inherit the configured application handler.
    """
    initialize_logging(
        record_startup=False
    )

    if not name:
        return logging.getLogger(
            LOGGER_NAME
        )

    return logging.getLogger(
        (
            f"{LOGGER_NAME}."
            f"{name}"
        )
    )


def get_log_file_path() -> Path:
    return LOG_FILE_PATH


def log_exception(
    context: str,
    exception: BaseException,
) -> None:
    """
    Record a caught exception with its traceback.

    Screens can gradually move from exposing raw exception
    messages to friendly user-facing errors while still keeping
    technical details available locally.
    """
    logger = get_logger(
        "errors"
    )

    logger.error(
        "%s: %s",
        context,
        exception,
        exc_info=(
            type(
                exception
            ),
            exception,
            exception.__traceback__,
        ),
    )


def install_exception_hooks(
    show_error: (
        Callable[
            [Path],
            None,
        ]
        | None
    ) = None,
) -> None:
    """
    Install global unexpected-exception handlers.

    UI-thread failures:
    - full traceback goes to application.log
    - optional friendly error UI is shown

    Background-thread failures:
    - full traceback goes to application.log
    - no GUI is created from that background thread
    """
    global _exception_hooks_installed

    if _exception_hooks_installed:
        return

    logger = initialize_logging()

    original_sys_hook = (
        sys.excepthook
    )

    original_thread_hook = (
        threading.excepthook
    )

    def handle_main_exception(
        exception_type,
        exception,
        traceback,
    ) -> None:
        if issubclass(
            exception_type,
            KeyboardInterrupt,
        ):
            original_sys_hook(
                exception_type,
                exception,
                traceback,
            )

            return

        logger.critical(
            "Unhandled application exception",
            exc_info=(
                exception_type,
                exception,
                traceback,
            ),
        )

        if show_error is None:
            return

        try:
            show_error(
                LOG_FILE_PATH
            )

        except Exception:
            logger.exception(
                (
                    "Unable to display the friendly "
                    "unexpected-error dialog"
                )
            )

    def handle_thread_exception(
        args: threading.ExceptHookArgs,
    ) -> None:
        if (
            args.exc_type
            is SystemExit
        ):
            return

        logger.critical(
            (
                "Unhandled background-thread exception "
                "in thread %s"
            ),
            (
                args.thread.name
                if args.thread
                is not None
                else "unknown"
            ),
            exc_info=(
                args.exc_type,
                args.exc_value,
                args.exc_traceback,
            ),
        )

        # Never create Qt widgets from a worker thread.
        #
        # The error remains available in application.log.

    sys.excepthook = (
        handle_main_exception
    )

    threading.excepthook = (
        handle_thread_exception
    )

    _exception_hooks_installed = True

    logger.info(
        "Global exception handlers installed"
    )

    # Keep references alive conceptually and make the intent clear.
    _ = (
        original_sys_hook,
        original_thread_hook,
    )