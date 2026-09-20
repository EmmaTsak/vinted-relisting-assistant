from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import (
    QSize,
    Qt,
    QUrl,
    Signal,
    QEvent,
)
from PySide6.QtGui import (
    QDesktopServices,
    QIcon,
    QPixmap,
)
from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services.listing_service import (
    ListingNotFoundError,
    get_listing,
    update_listing_price,
)
from app.services.photo_service import (
    get_listing_photos,
    get_thumbnail_path,
    resolve_photo_path,
)
from app.services.queue_service import (
    DAILY_RELIST_LIMIT,
    DEFAULT_MINIMUM_RELIST_AGE_DAYS,
    DailyLimitReachedError,
    QueueEntryNotFoundError,
    mark_as_relisted,
)
from app.ui.components.dialogs.error_feedback import (
    show_logged_error,
)
from app.ui.components.dialogs.message_dialog import (
    BrandedMessageDialog,
)
from app.ui.components.states.photo_fallback import (
    show_photo_fallback,
)
from app.utils.clipboard import (
    copy_text,
)
from app.utils.paths import (
    get_listing_photos_directory,
)


DEFAULT_VINTED_URL = "https://www.vinted.gr/"


from app.ui.dialog_geometry import (
    fit_dialog_to_screen,
)

class PreparedPriceSpinBox(QDoubleSpinBox):
    """
    Relisting price editor with normal text-field behaviour.

    When the field receives focus, its current numeric value is
    selected so the next typed number replaces it immediately.

    Once the field already has focus, mouse clicks behave normally
    and can position the text cursor.
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            **kwargs,
        )

        editor = self.lineEdit()

        if editor is not None:
            editor.installEventFilter(
                self
            )

    def eventFilter(
        self,
        watched,
        event,
    ) -> bool:
        editor = self.lineEdit()

        if watched is editor:
            if (
                event.type()
                == QEvent.Type.FocusIn
            ):
                editor.selectAll()

            elif (
                event.type()
                == QEvent.Type.MouseButtonPress
                and not editor.hasFocus()
            ):
                editor.setFocus(
                    Qt.FocusReason.MouseFocusReason
                )

                editor.selectAll()

                # Consume only the first click that gave the
                # editor focus. Further clicks behave normally.
                return True

        return super().eventFilter(
            watched,
            event,
        )




class RelistingPreparationDialog(QDialog):
    """
    Manual relisting preparation workspace.

    The assistant prepares local information only.
    Publishing remains entirely manual.
    """

    relisted = Signal(int)

    BUTTON_HEIGHT = 40

    def __init__(
        self,
        listing_id: int,
        parent: QWidget | None = None,
        configured_limit: int = DAILY_RELIST_LIMIT,
        minimum_age_days: int = DEFAULT_MINIMUM_RELIST_AGE_DAYS,
        vinted_url: str = DEFAULT_VINTED_URL,
    ) -> None:
        super().__init__(
            parent
        )

        self.listing_id = listing_id

        self.configured_limit = (
            configured_limit
        )

        self.minimum_age_days = (
            minimum_age_days
        )

        self.vinted_url = vinted_url

        self.listing = None

        self.photos = []

        self.setWindowTitle(
            "Prepare Listing for Relisting"
        )

        self.setModal(
            True
        )

        self.resize(
            900,
            700,
        )

        self.setMinimumSize(
            720,
            560,
        )

        try:
            self.listing = get_listing(
                self.listing_id
            )

            self.photos = (
                get_listing_photos(
                    self.listing_id
                )
            )

        except ListingNotFoundError as exc:
            BrandedMessageDialog.error(
                self,
                title="Listing Not Found",
                message=(
                    "This listing could not be found."
                ),
            )

            return

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Load Listing",
                message=(
                    "The listing could not be loaded for relisting."
                ),
                context=(
                    "Unable to load listing "
                    f"#{self.listing_id} for relisting preparation"
                ),
                exception=exc,
            )

            return

        self._build_ui()

        self._install_price_editor_panel()


        self._load_photo_gallery()

        self._apply_styles()

        fit_dialog_to_screen(
            self,
            preferred_width=900,
            preferred_height=700,
            minimum_width=720,
            minimum_height=560,
            width_ratio=0.84,
            height_ratio=0.80,
        )

    # =====================================================
    # Main UI
    # =====================================================

    def _build_ui(
        self,
    ) -> None:
        if self.listing is None:
            return

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            22,
            22,
            22,
            20,
        )

        main_layout.setSpacing(
            14
        )

        main_layout.addLayout(
            self._create_header()
        )

        main_layout.addWidget(
            self._create_workflow_bar()
        )

        content_layout = QHBoxLayout()

        content_layout.setSpacing(
            18
        )

        content_layout.addWidget(
            self._create_photo_panel()
        )

        content_layout.addWidget(
            self._create_details_panel(),
            1,
        )

        main_layout.addLayout(
            content_layout,
            1,
        )

        main_layout.addLayout(
            self._create_footer()
        )



    def _create_header(
        self,
    ) -> QHBoxLayout:
        row = QHBoxLayout()

        row.setSpacing(
            14
        )

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            3
        )

        heading = QLabel(
            "Prepare Listing"
        )

        heading.setObjectName(
            "preparationHeading"
        )

        subtitle = QLabel(
            (
                "Prepare the listing here, then publish "
                "it manually on Vinted."
            )
        )

        subtitle.setObjectName(
            "subtitle"
        )

        subtitle.setWordWrap(
            True
        )

        text_layout.addWidget(
            heading
        )

        text_layout.addWidget(
            subtitle
        )

        row.addLayout(
            text_layout,
            1,
        )

        return row





    # =====================================================
    # Workflow
    # =====================================================

    def _create_workflow_bar(
        self,
    ) -> QFrame:
        frame = QFrame()

        frame.setObjectName(
            "informationBox"
        )

        layout = QHBoxLayout(
            frame
        )

        layout.setContentsMargins(
            16,
            12,
            16,
            12,
        )

        layout.setSpacing(
            10
        )

        self._add_workflow_step(
            layout,
            "1",
            "COPY DETAILS",
            (
                "Copy the information "
                "you need."
            ),
        )

        arrow_1 = QLabel(
            "→"
        )

        arrow_1.setObjectName(
            "informationText"
        )

        layout.addWidget(
            arrow_1
        )

        self._add_workflow_step(
            layout,
            "2",
            "PUBLISH MANUALLY",
            (
                "Upload photos and publish "
                "in Vinted yourself."
            ),
        )

        arrow_2 = QLabel(
            "→"
        )

        arrow_2.setObjectName(
            "informationText"
        )

        layout.addWidget(
            arrow_2
        )

        self._add_workflow_step(
            layout,
            "3",
            "CONFIRM RELIST",
            (
                "Record it here only after "
                "publishing succeeds."
            ),
        )

        return frame

    def _add_workflow_step(
        self,
        layout: QHBoxLayout,
        number: str,
        title: str,
        description: str,
    ) -> None:
        container = QWidget()

        container_layout = QHBoxLayout(
            container
        )

        container_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        container_layout.setSpacing(
            8
        )

        number_label = QLabel(
            number
        )

        number_label.setObjectName(
            "activeBadge"
        )

        number_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        number_label.setMinimumWidth(
            28
        )

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            1
        )

        heading = QLabel(
            title
        )

        heading.setObjectName(
            "sectionHeading"
        )

        help_text = QLabel(
            description
        )

        help_text.setObjectName(
            "informationText"
        )

        help_text.setWordWrap(
            True
        )

        text_layout.addWidget(
            heading
        )

        text_layout.addWidget(
            help_text
        )

        container_layout.addWidget(
            number_label
        )

        container_layout.addLayout(
            text_layout,
            1,
        )

        layout.addWidget(
            container,
            1,
        )

    # =====================================================
    # Photos
    # =====================================================

    def _create_photo_panel(
        self,
    ) -> QWidget:
        panel = QFrame()

        panel.setObjectName(
            "photoPanel"
        )

        panel.setFixedWidth(
            300
        )

        layout = QVBoxLayout(
            panel
        )

        layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        layout.setSpacing(
            10
        )

        title_row = QHBoxLayout()

        title = QLabel(
            "PHOTOS"
        )

        title.setObjectName(
            "sectionTitle"
        )

        photo_count = QLabel(
            (
                f"{len(self.photos)} "
                + (
                    "photo"
                    if len(self.photos) == 1
                    else "photos"
                )
            )
        )

        photo_count.setObjectName(
            "informationText"
        )

        title_row.addWidget(
            title
        )

        title_row.addStretch()

        title_row.addWidget(
            photo_count
        )

        layout.addLayout(
            title_row
        )

        self.large_preview = QLabel()

        self.large_preview.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.large_preview.setFixedHeight(
            220
        )

        self.large_preview.setObjectName(
            "largePreview"
        )

        layout.addWidget(
            self.large_preview
        )

        self.photo_list = QListWidget()

        self.photo_list.setViewMode(
            QListWidget.ViewMode.IconMode
        )

        self.photo_list.setIconSize(
            QSize(
                78,
                78,
            )
        )

        self.photo_list.setMovement(
            QListWidget.Movement.Static
        )

        self.photo_list.setResizeMode(
            QListWidget.ResizeMode.Adjust
        )

        self.photo_list.setSpacing(
            6
        )

        self.photo_list.setVisible(
            False
        )

        self.photo_list.setFixedHeight(
            0
        )

        self.photo_list.currentItemChanged.connect(
            self._photo_selection_changed
        )

        layout.addWidget(
            self.photo_list
        )


        folder_button = QPushButton(
            "OPEN PHOTO FOLDER"
        )

        folder_button.setObjectName(
            "secondaryButton"
        )

        folder_button.setMinimumHeight(
            self.BUTTON_HEIGHT
        )

        folder_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        folder_button.clicked.connect(
            self._open_photo_folder
        )

        layout.addWidget(
            folder_button
        )

        layout.addStretch()

        return panel

    # =====================================================
    # Listing details
    # =====================================================

    def _create_details_panel(
        self,
    ) -> QWidget:
        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        container = QWidget()

        layout = QVBoxLayout(
            container
        )

        layout.setContentsMargins(
            0,
            0,
            8,
            0,
        )

        layout.setSpacing(
            10
        )

        listing = self.listing

        if listing is None:
            scroll.setWidget(
                container
            )

            return scroll

        essentials = QLabel(
            "LISTING ESSENTIALS"
        )

        essentials.setObjectName(
            "sectionTitle"
        )

        layout.addWidget(
            essentials
        )

        price = Decimal(
            str(
                listing.price
            )
        )

        self._add_detail_field(
            layout,
            "TITLE",
            listing.title,
        )

        self._add_detail_field(
            layout,
            "DESCRIPTION",
            listing.description,
            multiline=True,
        )


        # -------------------------------------------------
        # Optional details - collapsed initially
        # -------------------------------------------------

        self.item_details_toggle = (
            QPushButton(
                "ITEM DETAILS ▾"
            )
        )

        self.item_details_toggle.setObjectName(
            "secondaryButton"
        )

        self.item_details_toggle.setCheckable(
            True
        )

        self.item_details_toggle.setChecked(
            False
        )

        self.item_details_toggle.setMinimumHeight(
            self.BUTTON_HEIGHT
        )

        self.item_details_toggle.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.item_details_toggle.toggled.connect(
            self._toggle_item_details
        )

        layout.addWidget(
            self.item_details_toggle
        )

        self.item_details_container = (
            QFrame()
        )

        self.item_details_container.setObjectName(
            "informationBox"
        )

        item_details_layout = QVBoxLayout(
            self.item_details_container
        )

        item_details_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        item_details_layout.setSpacing(
            8
        )

        self._add_optional_field(
            item_details_layout,
            "CATEGORY",
            listing.category,
        )

        self._add_optional_field(
            item_details_layout,
            "SUBCATEGORY",
            listing.subcategory,
        )

        self._add_optional_field(
            item_details_layout,
            "BRAND",
            listing.brand,
        )

        self._add_optional_field(
            item_details_layout,
            "SIZE",
            listing.size,
        )

        self._add_optional_field(
            item_details_layout,
            "CONDITION",
            listing.condition,
        )

        self._add_optional_field(
            item_details_layout,
            "COLOUR",
            listing.colour,
        )

        self._add_optional_field(
            item_details_layout,
            "MATERIAL",
            listing.material,
        )

        self._add_optional_field(
            item_details_layout,
            "PARCEL SIZE",
            listing.parcel_size,
        )

        if listing.isbn:
            self._add_detail_field(
                item_details_layout,
                "ISBN",
                listing.isbn,
            )

        if (
            item_details_layout.count()
            == 0
        ):
            no_details = QLabel(
                "No optional item details have been saved."
            )

            no_details.setObjectName(
                "informationText"
            )

            no_details.setWordWrap(
                True
            )

            item_details_layout.addWidget(
                no_details
            )

        self.item_details_container.setVisible(
            False
        )

        layout.addWidget(
            self.item_details_container
        )

        # -------------------------------------------------
        # Local notes
        # -------------------------------------------------

        if listing.notes:
            notes_heading = QLabel(
                "PRIVATE NOTES"
            )

            notes_heading.setObjectName(
                "sectionTitle"
            )

            layout.addWidget(
                notes_heading
            )

            self._add_detail_field(
                layout,
                "LOCAL NOTES",
                listing.notes,
                multiline=True,
            )

        # -------------------------------------------------
        # Relisting information
        # -------------------------------------------------

        relisting_heading = QLabel(
            "RELISTING INFORMATION"
        )

        relisting_heading.setObjectName(
            "sectionTitle"
        )

        layout.addWidget(
            relisting_heading
        )

        information = QFrame()

        information.setObjectName(
            "informationBox"
        )

        information_layout = QVBoxLayout(
            information
        )

        information_layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        information_layout.setSpacing(
            5
        )

        if listing.last_relisted_date:
            last_relisted = (
                listing.last_relisted_date
                .strftime(
                    "%d %B %Y"
                )
            )
        else:
            last_relisted = "Never"

        original_label = QLabel(
            (
                "Original listing date: "
                f"{listing.original_created_date:%d %B %Y}"
            )
        )

        last_label = QLabel(
            f"Last relisted: {last_relisted}"
        )

        count_label = QLabel(
            (
                "Relist count: "
                f"{listing.number_of_times_relisted}"
            )
        )

        priority_label = QLabel(
            (
                "Priority: "
                f"{listing.priority.value.capitalize()}"
            )
        )

        for label in (
            original_label,
            last_label,
            count_label,
            priority_label,
        ):
            label.setObjectName(
                "metadataText"
            )

            information_layout.addWidget(
                label
            )

        layout.addWidget(
            information
        )

        layout.addStretch()

        scroll.setWidget(
            container
        )

        return scroll

    def _toggle_item_details(
        self,
        expanded: bool,
    ) -> None:
        self.item_details_container.setVisible(
            expanded
        )

        if expanded:
            self.item_details_toggle.setText(
                "ITEM DETAILS ▴"
            )
        else:
            self.item_details_toggle.setText(
                "ITEM DETAILS ▾"
            )

    def _add_optional_field(
        self,
        layout: QVBoxLayout,
        label: str,
        value: str | None,
    ) -> None:
        if value:
            self._add_detail_field(
                layout,
                label,
                value,
            )

    def _add_detail_field(
        self,
        layout: QVBoxLayout,
        label: str,
        value: str,
        multiline: bool = False,
    ) -> None:
        frame = QFrame()

        frame.setObjectName(
            "detailField"
        )

        field_layout = QHBoxLayout(
            frame
        )

        field_layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        field_layout.setSpacing(
            10
        )

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            4
        )

        heading = QLabel(
            label
        )

        heading.setObjectName(
            "fieldHeading"
        )

        text_layout.addWidget(
            heading
        )

        if multiline:
            value_widget = QTextEdit()

            value_widget.setPlainText(
                value
            )

            value_widget.setReadOnly(
                True
            )

            value_widget.setMinimumHeight(
                90
            )

            value_widget.setMaximumHeight(
                165
            )

            value_widget.setObjectName(
                "fieldTextEdit"
            )

        else:
            value_widget = QLabel(
                value
            )

            value_widget.setWordWrap(
                True
            )

            value_widget.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

            value_widget.setObjectName(
                "fieldValue"
            )

        text_layout.addWidget(
            value_widget
        )

        field_layout.addLayout(
            text_layout,
            1,
        )

        copy_button = QPushButton(
            "COPY"
        )

        copy_button.setObjectName(
            "copyButton"
        )

        copy_button.setFixedWidth(
            76
        )

        copy_button.setMinimumHeight(
            34
        )

        copy_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        copy_button.clicked.connect(
            lambda checked=False,
            text=value:
            self._copy_value(
                text
            )
        )

        field_layout.addWidget(
            copy_button,
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        layout.addWidget(
            frame
        )

    # =====================================================
    # Footer
    # =====================================================

    def _create_footer(
        self,
    ) -> QHBoxLayout:
        row = QHBoxLayout()

        row.setSpacing(
            8
        )

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setObjectName(
            "secondaryButton"
        )

        close_button.setMinimumHeight(
            self.BUTTON_HEIGHT
        )

        close_button.clicked.connect(
            self.reject
        )

        copy_full_button = QPushButton(
            "COPY FULL LISTING"
        )

        copy_full_button.setObjectName(
            "secondaryButton"
        )

        copy_full_button.setMinimumHeight(
            self.BUTTON_HEIGHT
        )

        copy_full_button.clicked.connect(
            self._copy_full_listing
        )

        open_vinted_button = QPushButton(
            "OPEN VINTED"
        )

        open_vinted_button.setObjectName(
            "secondaryButton"
        )

        open_vinted_button.setMinimumHeight(
            self.BUTTON_HEIGHT
        )

        open_vinted_button.clicked.connect(
            self._open_vinted
        )

        relisted_button = QPushButton(
            "MARK AS RELISTED"
        )

        relisted_button.setObjectName(
            "primaryButton"
        )

        relisted_button.setMinimumHeight(
            self.BUTTON_HEIGHT
        )

        relisted_button.clicked.connect(
            self._mark_as_relisted
        )

        for button in (
            close_button,
            copy_full_button,
            open_vinted_button,
            relisted_button,
        ):
            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

        row.addWidget(
            close_button
        )

        row.addStretch()

        row.addWidget(
            copy_full_button
        )

        row.addWidget(
            open_vinted_button
        )

        row.addWidget(
            relisted_button
        )

        return row

    # =====================================================
    # Photos
    # =====================================================

    def _load_photo_gallery(
        self,
    ) -> None:
        if not hasattr(
            self,
            "photo_list",
        ):
            return

        self.photo_list.clear()

        if not self.photos:
            show_photo_fallback(
                self.large_preview,
                object_name="largePreview",
            )

            return

        cover_index = 0

        for index, photo in enumerate(
            self.photos
        ):
            thumbnail = (
                get_thumbnail_path(
                    photo
                )
            )

            item = QListWidgetItem()

            item.setData(
                Qt.ItemDataRole.UserRole,
                photo.id,
            )

            pixmap = QPixmap(
                str(
                    thumbnail
                )
            )

            if not pixmap.isNull():
                item.setIcon(
                    QIcon(
                        pixmap
                    )
                )

            if photo.is_cover:
                item.setText(
                    "Cover"
                )

                cover_index = index

            self.photo_list.addItem(
                item
            )

        self.photo_list.setCurrentRow(
            cover_index
        )

        self._show_photo(
            self.photos[
                cover_index
            ]
        )

    def _photo_selection_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        del previous

        if current is None:
            return

        photo_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        for photo in self.photos:
            if photo.id == photo_id:
                self._show_photo(
                    photo
                )

                return

    def _show_photo(
        self,
        photo,
    ) -> None:
        path = resolve_photo_path(
            photo
        )

        if not path.exists():
            show_photo_fallback(
                self.large_preview,
                preview_unavailable=True,
                object_name="largePreview",
            )

            return

        pixmap = QPixmap(
            str(
                path
            )
        )

        if pixmap.isNull():
            show_photo_fallback(
                self.large_preview,
                preview_unavailable=True,
                object_name="largePreview",
            )

            return

        self.large_preview.clear()
        self.large_preview.setProperty(
            "photoFallback",
            False,
        )
        self.large_preview.setToolTip(
            ""
        )

        self.large_preview.setPixmap(
            pixmap.scaled(
                250,
                210,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _open_photo_folder(
        self,
    ) -> None:
        try:
            folder = (
                get_listing_photos_directory(
                    self.listing_id
                )
            )

            folder.mkdir(
                parents=True,
                exist_ok=True,
            )

            opened = (
                QDesktopServices.openUrl(
                    QUrl.fromLocalFile(
                        str(
                            folder.resolve()
                        )
                    )
                )
            )

            if not opened:
                raise RuntimeError(
                    "Windows could not open the photo folder."
                )

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Open Photo Folder",
                message=(
                    "The photo folder could not be opened."
                ),
                context=(
                    "Unable to open photo folder for "
                    f"listing #{self.listing_id}"
                ),
                exception=exc,
            )

    # =====================================================
    # Copying
    # =====================================================

    def _copy_value(
        self,
        value: str,
    ) -> None:
        try:
            copy_text(
                value
            )

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Copy",
                message=(
                    "The text could not be copied right now."
                ),
                context=(
                    "Clipboard copy failed inside "
                    "Relisting Preparation"
                ),
                exception=exc,
            )

            return

        self.setWindowTitle(
            (
                "Prepare Listing for "
                "Relisting - Copied"
            )
        )

    def _copy_full_listing(
        self,
    ) -> None:
        if self.listing is None:
            return

        listing = self.listing

        price = Decimal(
            str(
                listing.price
            )
        )

        lines = [
            "TITLE",
            listing.title,
            "",
            "DESCRIPTION",
            listing.description,
            "",
            "PRICE",
            (
                f"{price:.2f} "
                f"{listing.currency}"
            ),
        ]

        optional_values = [
            (
                "CATEGORY",
                listing.category,
            ),
            (
                "SUBCATEGORY",
                listing.subcategory,
            ),
            (
                "BRAND",
                listing.brand,
            ),
            (
                "SIZE",
                listing.size,
            ),
            (
                "CONDITION",
                listing.condition,
            ),
            (
                "COLOUR",
                listing.colour,
            ),
            (
                "MATERIAL",
                listing.material,
            ),
            (
                "PARCEL SIZE",
                listing.parcel_size,
            ),
            (
                "ISBN",
                listing.isbn,
            ),
        ]

        for heading, value in (
            optional_values
        ):
            if value:
                lines.extend(
                    [
                        "",
                        heading,
                        value,
                    ]
                )

        full_text = "\n".join(
            lines
        )

        self._copy_value(
            full_text
        )

    # =====================================================
    # Vinted
    # =====================================================

    def _open_vinted(
        self,
    ) -> None:
        """
        Open Vinted in the user's normal browser.

        No website automation is performed.
        """
        QDesktopServices.openUrl(
            QUrl(
                self.vinted_url
            )
        )

    # =====================================================
    # Relisting confirmation
    # =====================================================

    def _mark_as_relisted(
        self,
    ) -> None:
        """
        Record a relist after the user has manually published it.

        MARK AS RELISTED is itself the confirmation. On success the
        preparation window closes immediately without another routine
        confirmation or success modal.
        """
        if not self._save_prepared_price(
            show_feedback=False,
        ):
            return

        try:
            mark_as_relisted(
                listing_id=self.listing_id,
                configured_limit=(
                    self.configured_limit
                ),
                minimum_age_days=(
                    self.minimum_age_days
                ),
            )

        except DailyLimitReachedError:
            BrandedMessageDialog.warning(
                self,
                title="Daily Target Reached",
                message=(
                    "You've already reached today's "
                    "relisting target."
                ),
            )

            return

        except QueueEntryNotFoundError:
            BrandedMessageDialog.notice(
                self,
                title="Listing No Longer Queued",
                message=(
                    "This listing is no longer in "
                    "today's queue."
                ),
            )

            return

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Record Relisting",
                message=(
                    "The relisting could not be recorded."
                ),
                context=(
                    "Unable to record relisting from "
                    "Relisting Preparation for "
                    f"listing #{self.listing_id}"
                ),
                exception=exc,
            )

            return

        self.relisted.emit(
            self.listing_id
        )

        self.accept()

    def _apply_styles(
        self,
    ) -> None:
        """
        ThemeManager controls Light/Dark appearance globally.
        """
        return


    def _install_price_editor_panel(
        self,
    ) -> None:
        if self.listing is None:
            return

        root_layout = self.layout()

        if not isinstance(
            root_layout,
            QVBoxLayout,
        ):
            return

        panel = QFrame()

        panel.setObjectName(
            "informationBox"
        )

        panel_layout = QHBoxLayout(
            panel
        )

        panel_layout.setContentsMargins(
            16,
            10,
            16,
            10,
        )

        panel_layout.setSpacing(
            12
        )

        title = QLabel(
            "RELIST PRICE"
        )

        title.setObjectName(
            "sectionHeading"
        )

        panel_layout.addWidget(
            title
        )

        self.prepared_price_input = (
            PreparedPriceSpinBox()
        )

        self.prepared_price_input.setDecimals(
            2
        )

        self.prepared_price_input.setRange(
            0.01,
            999999.99,
        )

        self.prepared_price_input.setSingleStep(
            0.50
        )

        self.prepared_price_input.setMinimumHeight(
            40
        )

        self.prepared_price_input.setMinimumWidth(
            180
        )

        self.prepared_price_input.setValue(
            float(
                Decimal(
                    str(
                        self.listing.price
                    )
                )
            )
        )

        self.prepared_price_input.setSuffix(
            f" {self.listing.currency}"
        )

        panel_layout.addWidget(
            self.prepared_price_input
        )

        copy_button = QPushButton(
            "COPY PRICE"
        )

        copy_button.setObjectName(
            "secondaryButton"
        )

        copy_button.setMinimumHeight(
            40
        )

        copy_button.clicked.connect(
            self._copy_prepared_price
        )

        panel_layout.addWidget(
            copy_button
        )

        save_button = QPushButton(
            "SAVE PRICE"
        )

        save_button.setObjectName(
            "secondaryButton"
        )

        save_button.setMinimumHeight(
            40
        )

        save_button.clicked.connect(
            self._save_prepared_price
        )

        panel_layout.addWidget(
            save_button
        )

        self.prepared_price_status = QLabel(
            (
                "Current saved price: "
                f"{Decimal(str(self.listing.price)):.2f} "
                f"{self.listing.currency}"
            )
        )

        self.prepared_price_status.setObjectName(
            "informationText"
        )

        panel_layout.addWidget(
            self.prepared_price_status
        )

        panel_layout.addStretch()

        # Header = 0
        # Workflow = 1
        # Price editor = 2
        root_layout.insertWidget(
            2,
            panel,
        )

    def _prepared_price(
        self,
    ) -> Decimal:
        return Decimal(
            str(
                self.prepared_price_input.value()
            )
        ).quantize(
            Decimal("0.01")
        )

    def _copy_prepared_price(
        self,
        checked: bool = False,
    ) -> None:
        _ = checked

        self._copy_value(
            f"{self._prepared_price():.2f}"
        )

    def _save_prepared_price(
        self,
        checked: bool = False,
        *,
        show_feedback: bool = True,
    ) -> bool:
        _ = checked

        if self.listing is None:
            return False

        new_price = (
            self._prepared_price()
        )

        old_price = Decimal(
            str(
                self.listing.price
            )
        ).quantize(
            Decimal("0.01")
        )

        if new_price == old_price:
            self.prepared_price_status.setText(
                (
                    "Current saved price: "
                    f"{new_price:.2f} "
                    f"{self.listing.currency}"
                )
            )

            return True

        try:
            update_listing_price(
                self.listing_id,
                new_price,
            )

        except Exception as exc:
            show_logged_error(
                self,
                title="Unable to Update Price",
                message=(
                    "The relist price could not be saved."
                ),
                context=(
                    "Unable to save relist price for "
                    f"listing #{self.listing_id}"
                ),
                exception=exc,
            )

            return False

        old_display = (
            f"{old_price:.2f} "
            f"{self.listing.currency}"
        )

        new_display = (
            f"{new_price:.2f} "
            f"{self.listing.currency}"
        )

        self.listing.price = (
            new_price
        )

        self.prepared_price_status.setText(
            f"Saved price: {new_display}"
        )

        if show_feedback:
            BrandedMessageDialog.notice(
                self,
                title="Price Updated",
                message=(
                    f"Price changed from "
                    f"{old_display} to {new_display}."
                ),
            )

        return True




