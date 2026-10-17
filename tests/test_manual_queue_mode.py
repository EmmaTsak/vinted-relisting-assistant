from __future__ import annotations

from datetime import (
    date,
    timedelta,
)

from app.models import (
    QueueMode,
)
from app.services.queue_service import (
    add_listings_to_today_queue,
    get_queue_mode,
    get_today_queue,
    mark_as_relisted,
    set_queue_mode,
)


TODAY = date(
    2026,
    10,
    17,
)


def old_date(
    days: int = 90,
) -> date:
    return (
        TODAY
        - timedelta(
            days=days
        )
    )


def test_default_mode_is_smart() -> None:
    assert (
        get_queue_mode(
            today=TODAY
        )
        == QueueMode.SMART
    )


def test_switching_to_manual_removes_waiting_smart_items(
    make_listing,
) -> None:
    make_listing(
        title="Coat",
        original_created_date=old_date(),
    )

    make_listing(
        title="Jumper",
        original_created_date=old_date(),
    )

    smart = get_today_queue(
        configured_limit=2,
        minimum_age_days=14,
        today=TODAY,
    )

    assert len(
        smart.queued_items
    ) == 2

    set_queue_mode(
        QueueMode.MANUAL,
        today=TODAY,
    )

    manual = get_today_queue(
        configured_limit=2,
        minimum_age_days=14,
        today=TODAY,
    )

    assert (
        manual.mode
        == QueueMode.MANUAL
    )

    assert (
        manual.queued_items
        == []
    )


def test_manual_mode_does_not_autofill(
    make_listing,
) -> None:
    chosen = make_listing(
        title="Chosen Coat",
        original_created_date=old_date(),
    )

    make_listing(
        title="Other Coat",
        original_created_date=old_date(),
    )

    make_listing(
        title="Third Coat",
        original_created_date=old_date(),
    )

    result = (
        add_listings_to_today_queue(
            [
                chosen,
            ],
            configured_limit=3,
            minimum_age_days=14,
            today=TODAY,
        )
    )

    assert result.added == 1

    snapshot = get_today_queue(
        configured_limit=3,
        minimum_age_days=14,
        today=TODAY,
    )

    assert (
        snapshot.mode
        == QueueMode.MANUAL
    )

    assert [
        item.listing.id
        for item
        in snapshot.queued_items
    ] == [
        chosen,
    ]


def test_manual_add_uses_existing_age_rule(
    make_listing,
) -> None:
    eligible = make_listing(
        title="Old Coat",
        original_created_date=old_date(),
    )

    too_new = make_listing(
        title="New Coat",
        original_created_date=(
            TODAY
            - timedelta(
                days=2
            )
        ),
    )

    result = (
        add_listings_to_today_queue(
            [
                eligible,
                too_new,
            ],
            configured_limit=10,
            minimum_age_days=14,
            today=TODAY,
        )
    )

    assert result.added == 1

    assert (
        result.skipped_ineligible
        == 1
    )


def test_manual_add_respects_daily_limit(
    make_listing,
) -> None:
    ids = [
        make_listing(
            title=(
                f"Listing {index}"
            ),
            original_created_date=(
                old_date()
            ),
        )
        for index in range(
            3
        )
    ]

    result = (
        add_listings_to_today_queue(
            ids,
            configured_limit=2,
            minimum_age_days=14,
            today=TODAY,
        )
    )

    assert result.added == 2

    assert (
        result.skipped_limit
        == 1
    )


def test_same_listing_is_not_added_twice(
    make_listing,
) -> None:
    listing_id = make_listing(
        title="Winter Coat",
        original_created_date=old_date(),
    )

    first = (
        add_listings_to_today_queue(
            [
                listing_id,
            ],
            configured_limit=10,
            minimum_age_days=14,
            today=TODAY,
        )
    )

    second = (
        add_listings_to_today_queue(
            [
                listing_id,
            ],
            configured_limit=10,
            minimum_age_days=14,
            today=TODAY,
        )
    )

    assert first.added == 1
    assert second.added == 0

    assert (
        second.skipped_existing
        == 1
    )


def test_switching_back_to_smart_fills_remaining_slots(
    make_listing,
) -> None:
    chosen = make_listing(
        title="Chosen",
        original_created_date=old_date(),
    )

    make_listing(
        title="Automatic 1",
        original_created_date=old_date(),
    )

    make_listing(
        title="Automatic 2",
        original_created_date=old_date(),
    )

    add_listings_to_today_queue(
        [
            chosen,
        ],
        configured_limit=3,
        minimum_age_days=14,
        today=TODAY,
    )

    set_queue_mode(
        QueueMode.SMART,
        today=TODAY,
    )

    snapshot = get_today_queue(
        configured_limit=3,
        minimum_age_days=14,
        today=TODAY,
    )

    assert (
        snapshot.mode
        == QueueMode.SMART
    )

    assert len(
        snapshot.queued_items
    ) == 3

    assert chosen in {
        item.listing.id
        for item
        in snapshot.queued_items
    }


def test_completed_item_survives_switch_to_manual(
    make_listing,
) -> None:
    listing_id = make_listing(
        title="Completed Coat",
        original_created_date=old_date(),
    )

    get_today_queue(
        configured_limit=1,
        minimum_age_days=14,
        today=TODAY,
    )

    mark_as_relisted(
        listing_id=listing_id,
        configured_limit=1,
        minimum_age_days=14,
        today=TODAY,
    )

    set_queue_mode(
        QueueMode.MANUAL,
        today=TODAY,
    )

    snapshot = get_today_queue(
        configured_limit=1,
        minimum_age_days=14,
        today=TODAY,
    )

    assert (
        snapshot.completed_count
        == 1
    )

    assert (
        snapshot.mode
        == QueueMode.MANUAL
    )
