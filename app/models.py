from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database import Base


class ListingStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    SOLD = "sold"
    ARCHIVED = "archived"


class ListingPriority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class QueueEntryStatus(str, Enum):
    QUEUED = "queued"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class Listing(Base):
    """
    One locally stored listing.
    """

    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="EUR",
    )

    category: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    subcategory: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    brand: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    size: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    condition: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    colour: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    material: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    parcel_size: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    isbn: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )

    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    original_created_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        index=True,
    )

    last_relisted_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    number_of_times_relisted: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    priority: Mapped[ListingPriority] = mapped_column(
        SQLEnum(
            ListingPriority,
            native_enum=False,
            values_callable=lambda enum_class: [
                item.value
                for item in enum_class
            ],
        ),
        nullable=False,
        default=ListingPriority.NORMAL,
        index=True,
    )

    status: Mapped[ListingStatus] = mapped_column(
        SQLEnum(
            ListingStatus,
            native_enum=False,
            values_callable=lambda enum_class: [
                item.value
                for item in enum_class
            ],
        ),
        nullable=False,
        default=ListingStatus.ACTIVE,
        index=True,
    )

    sold: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    manually_excluded: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    paused_until: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    paused_indefinitely: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    photos: Mapped[list["ListingPhoto"]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
        order_by="ListingPhoto.display_order",
    )

    def __repr__(self) -> str:
        return (
            "<Listing("
            f"id={self.id!r}, "
            f"title={self.title!r}, "
            f"price={self.price!r}"
            ")>"
        )


class ListingPhoto(Base):
    """
    Metadata for a locally stored listing photo.
    """

    __tablename__ = "listing_photos"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    listing_id: Mapped[int] = mapped_column(
        ForeignKey(
            "listings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    file_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    is_cover: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    rotation_degrees: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    listing: Mapped["Listing"] = relationship(
        back_populates="photos",
    )


class DailyQueueEntry(Base):
    """
    Records a listing's participation in a particular day's queue.

    A listing can appear at most once per calendar day.
    """

    __tablename__ = "daily_queue_entries"

    __table_args__ = (
        UniqueConstraint(
            "queue_date",
            "listing_id",
            name="uq_daily_queue_date_listing",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    listing_id: Mapped[int] = mapped_column(
        ForeignKey(
            "listings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    queue_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    status: Mapped[QueueEntryStatus] = mapped_column(
        SQLEnum(
            QueueEntryStatus,
            native_enum=False,
            values_callable=lambda enum_class: [
                item.value
                for item in enum_class
            ],
        ),
        nullable=False,
        default=QueueEntryStatus.QUEUED,
        index=True,
    )

    selected_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    skipped_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


class RelistHistory(Base):
    """
    Permanent record of successful manual relisting confirmations.
    """

    __tablename__ = "relist_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    listing_id: Mapped[int] = mapped_column(
        ForeignKey(
            "listings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    relisted_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    previous_relisted_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )