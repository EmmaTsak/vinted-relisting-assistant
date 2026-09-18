from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.database as database
import app.models  # noqa: F401
from app.database import Base
from app.models import (
    Listing,
    ListingPriority,
    ListingStatus,
)


@pytest.fixture(
    autouse=True
)
def isolated_database(
    tmp_path,
    monkeypatch,
):
    """
    Every test gets its own temporary SQLite database.

    The real data/database.sqlite file is never touched.
    """
    database_path = (
        tmp_path
        / "test_database.sqlite"
    )

    test_engine = create_engine(
        (
            "sqlite:///"
            f"{database_path.as_posix()}"
        ),
        echo=False,
        future=True,
        connect_args={
            "check_same_thread": False,
        },
    )

    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )

    monkeypatch.setattr(
        database,
        "engine",
        test_engine,
    )

    monkeypatch.setattr(
        database,
        "SessionLocal",
        TestSessionLocal,
    )

    Base.metadata.create_all(
        bind=test_engine
    )

    yield

    test_engine.dispose()


@pytest.fixture
def make_listing():
    """
    Factory for inserting isolated test listings.
    """

    def _make_listing(
        *,
        title: str,
        original_created_date: date,
        price: Decimal = Decimal(
            "10.00"
        ),
        last_relisted_date: date | None = None,
        relist_count: int = 0,
        priority: ListingPriority = (
            ListingPriority.NORMAL
        ),
        status: ListingStatus = (
            ListingStatus.ACTIVE
        ),
        sold: bool = False,
        archived: bool = False,
        manually_excluded: bool = False,
        paused_until: date | None = None,
        paused_indefinitely: bool = False,
    ) -> int:
        with database.session_scope() as session:
            listing = Listing(
                title=title,
                description=(
                    f"Test description for {title}"
                ),
                price=price,
                currency="EUR",
                original_created_date=(
                    original_created_date
                ),
                last_relisted_date=(
                    last_relisted_date
                ),
                number_of_times_relisted=(
                    relist_count
                ),
                priority=priority,
                status=status,
                sold=sold,
                archived=archived,
                manually_excluded=(
                    manually_excluded
                ),
                paused_until=paused_until,
                paused_indefinitely=(
                    paused_indefinitely
                ),
            )

            session.add(
                listing
            )

            session.flush()

            listing_id = (
                listing.id
            )

        return listing_id

    return _make_listing