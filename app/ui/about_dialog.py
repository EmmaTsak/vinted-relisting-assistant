from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    QUrl,
)
from PySide6.QtGui import (
    QDesktopServices,
    QIcon,
)
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import (
    APP_NAME,
    APP_VERSION,
)


PROJECT_URL = (
    "https://github.com/"
    "EmmaTsak/"
    "vinted-relisting-assistant"
)


class AboutDialog(QDialog):
    """
    Friendly product information.

    About is a non-critical moment, so this screen can have
    slightly warmer copy while keeping important information clear.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        app_icon: QIcon | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.app_icon = app_icon

        self.setWindowTitle(
            f"About {APP_NAME}"
        )

        self.setModal(
            True
        )

        self.resize(
            560,
            500,
        )

        self.setMinimumSize(
            500,
            450,
        )

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        layout.setSpacing(
            16
        )

        # -------------------------------------------------
        # Brand
        # -------------------------------------------------

        brand = QHBoxLayout()

        brand.setSpacing(
            16
        )

        icon_label = QLabel()

        icon_label.setFixedSize(
            80,
            80,
        )

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        if (
            self.app_icon is not None
            and not self.app_icon.isNull()
        ):
            icon_label.setPixmap(
                self.app_icon.pixmap(
                    72,
                    72,
                )
            )

        brand_text = QVBoxLayout()

        brand_text.setSpacing(
            4
        )

        title = QLabel(
            APP_NAME
        )

        title.setObjectName(
            "preparationHeading"
        )

        version = QLabel(
            f"Version {APP_VERSION}"
        )

        version.setObjectName(
            "informationText"
        )

        tagline = QLabel(
            "Your little helper for an easier relisting routine."
        )

        tagline.setObjectName(
            "informationText"
        )

        tagline.setWordWrap(
            True
        )

        brand_text.addWidget(
            title
        )

        brand_text.addWidget(
            version
        )

        brand_text.addWidget(
            tagline
        )

        brand.addWidget(
            icon_label
        )

        brand.addLayout(
            brand_text,
            1,
        )

        layout.addLayout(
            brand
        )

        # -------------------------------------------------
        # About
        # -------------------------------------------------

        about_frame = QFrame()

        about_frame.setObjectName(
            "informationBox"
        )

        about_layout = QVBoxLayout(
            about_frame
        )

        about_layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        about_layout.setSpacing(
            9
        )

        about_heading = QLabel(
            "ABOUT"
        )

        about_heading.setObjectName(
            "sectionHeading"
        )

        description = QLabel(
            (
                "Vinted Relisting Assistant is a local desktop "
                "workspace for organising listings and preparing "
                "manual relisting."
            )
        )

        description.setObjectName(
            "informationText"
        )

        description.setWordWrap(
            True
        )

        privacy = QLabel(
            (
                "Your listings, settings, history and managed "
                "photos stay on your computer."
            )
        )

        privacy.setObjectName(
            "informationText"
        )

        privacy.setWordWrap(
            True
        )

        about_layout.addWidget(
            about_heading
        )

        about_layout.addWidget(
            description
        )

        about_layout.addWidget(
            privacy
        )

        layout.addWidget(
            about_frame
        )

        # -------------------------------------------------
        # Independence notice
        # -------------------------------------------------

        notice_frame = QFrame()

        notice_frame.setObjectName(
            "informationBox"
        )

        notice_layout = QVBoxLayout(
            notice_frame
        )

        notice_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        notice_layout.setSpacing(
            7
        )

        notice_heading = QLabel(
            "INDEPENDENT APP"
        )

        notice_heading.setObjectName(
            "sectionHeading"
        )

        notice = QLabel(
            (
                "This is independent software and is not affiliated "
                "with, endorsed by, sponsored by, or operated by Vinted."
            )
        )

        notice.setObjectName(
            "informationText"
        )

        notice.setWordWrap(
            True
        )

        notice_layout.addWidget(
            notice_heading
        )

        notice_layout.addWidget(
            notice
        )

        layout.addWidget(
            notice_frame
        )

        layout.addStretch()

        # -------------------------------------------------
        # Buttons
        # -------------------------------------------------

        buttons = QHBoxLayout()

        buttons.setSpacing(
            8
        )

        project_button = QPushButton(
            "PROJECT PAGE"
        )

        project_button.setObjectName(
            "secondaryButton"
        )

        project_button.setMinimumHeight(
            40
        )

        project_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        project_button.clicked.connect(
            self._open_project_page
        )

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setObjectName(
            "primaryButton"
        )

        close_button.setMinimumHeight(
            40
        )

        close_button.setMinimumWidth(
            100
        )

        close_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        close_button.clicked.connect(
            self.accept
        )

        buttons.addWidget(
            project_button
        )

        buttons.addStretch()

        buttons.addWidget(
            close_button
        )

        layout.addLayout(
            buttons
        )

    def _open_project_page(
        self,
    ) -> None:
        QDesktopServices.openUrl(
            QUrl(
                PROJECT_URL
            )
        )