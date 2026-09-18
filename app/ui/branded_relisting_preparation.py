from __future__ import annotations

from PySide6.QtCore import (
    QUrl,
)
from PySide6.QtGui import (
    QDesktopServices,
)
from PySide6.QtWidgets import (
    QWidget,
)

from app.services.queue_service import (
    DAILY_RELIST_LIMIT,
    DEFAULT_MINIMUM_RELIST_AGE_DAYS,
    DailyLimitReachedError,
    QueueEntryNotFoundError,
    get_today_queue,
    mark_as_relisted,
)
from app.ui.components.dialogs.message_dialog import (
    BrandedMessageDialog,
)
from app.ui.components.dialogs.error_feedback import (
    log_background_error,
    show_logged_error,
)
from app.ui.relisting_preparation import (
    DEFAULT_VINTED_URL,
    RelistingPreparationDialog,
)
from app.ui.components.dialogs.success_dialog import (
    BrandedSuccessDialog,
)
from app.utils.clipboard import (
    copy_text,
)
from app.utils.paths import (
    get_listing_photos_directory,
)


class BrandedRelistingPreparationDialog(
    RelistingPreparationDialog
):
    """
    Product-polished version of the preparation workspace.

    The existing preparation workflow stays unchanged.

    This layer provides:
    - compact branded confirmations
    - compact branded warnings
    - friendly logged errors
    - branded success feedback
    """

    def __init__(
        self,
        listing_id: int,
        parent: QWidget | None = None,
        configured_limit: int = DAILY_RELIST_LIMIT,
        minimum_age_days: int = DEFAULT_MINIMUM_RELIST_AGE_DAYS,
        vinted_url: str = DEFAULT_VINTED_URL,
    ) -> None:
        super().__init__(
            listing_id=listing_id,
            parent=parent,
            configured_limit=configured_limit,
            minimum_age_days=minimum_age_days,
            vinted_url=vinted_url,
        )

    # =====================================================
    # Clipboard
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
                "Relisting â€” Copied"
            )
        )

    # =====================================================
    # Photo folder
    # =====================================================

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
    # Relisting confirmation
    # =====================================================

    def _mark_as_relisted(
        self,
    ) -> None:
        confirmed = (
            BrandedMessageDialog.ask(
                self,
                title="Mark as Relisted?",
                message=(
                    "Only confirm after you've published "
                    "this listing on Vinted."
                ),
                confirm_text="YES, RELISTED",
                cancel_text="NOT YET",
            )
        )

        if not confirmed:
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

        # -------------------------------------------------
        # Build success feedback
        # -------------------------------------------------

        success_title = (
            "Relisting recorded"
        )

        success_message = (
            "Nice â€” this listing is now recorded as relisted."
        )

        success_detail = (
            "Your daily progress has been updated."
        )

        try:
            snapshot = get_today_queue(
                configured_limit=(
                    self.configured_limit
                ),
                minimum_age_days=(
                    self.minimum_age_days
                ),
            )

            if snapshot.is_complete:
                success_title = (
                    "Today's target is complete"
                )

                success_message = (
                    "You've reached today's relisting target."
                )

                success_detail = (
                    "Your queue is finished for today."
                )

            else:
                remaining = (
                    snapshot.remaining_completions
                )

                if remaining == 1:
                    success_detail = (
                        "1 relist left today."
                    )

                else:
                    success_detail = (
                        f"{remaining} relists left today."
                    )

        except Exception as exc:
            log_background_error(
                context=(
                    "Unable to calculate queue progress after "
                    "Relisting Preparation successfully recorded "
                    f"listing #{self.listing_id}"
                ),
                exception=exc,
            )

        dialog = BrandedSuccessDialog(
            title=success_title,
            message=success_message,
            detail=success_detail,
            parent=self,
        )

        dialog.exec()

        self.relisted.emit(
            self.listing_id
        )

        self.accept()

