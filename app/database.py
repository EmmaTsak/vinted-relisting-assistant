from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import (
    create_engine,
    event,
    inspect,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)

from app.utils.paths import (
    DATABASE_PATH,
    ensure_app_directories,
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy database models.
    """

    pass


def _create_database_url() -> str:
    """
    Build the SQLite connection URL using the application's
    local database path.
    """
    return (
        "sqlite:///"
        f"{DATABASE_PATH.as_posix()}"
    )


ensure_app_directories()

DATABASE_URL = (
    _create_database_url()
)


engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={
        "check_same_thread": False,
    },
)


@event.listens_for(
    Engine,
    "connect",
)
def enable_sqlite_foreign_keys(
    dbapi_connection,
    connection_record,
) -> None:
    """
    Enable SQLite foreign-key enforcement for every database connection.
    """
    del connection_record

    cursor = (
        dbapi_connection.cursor()
    )

    try:
        cursor.execute(
            "PRAGMA foreign_keys=ON"
        )

    finally:
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def _run_lightweight_migrations() -> None:
    """
    Apply small SQLite schema updates that SQLAlchemy create_all()
    cannot add to an existing table.

    This keeps existing user data intact.
    """
    inspector = inspect(
        engine
    )

    table_names = set(
        inspector.get_table_names()
    )

    if "listings" not in table_names:
        return

    listing_columns = {
        column["name"]
        for column in inspector.get_columns(
            "listings"
        )
    }

    with engine.begin() as connection:
        if "isbn" not in listing_columns:
            connection.execute(
                text(
                    (
                        "ALTER TABLE listings "
                        "ADD COLUMN isbn VARCHAR(20)"
                    )
                )
            )

        connection.execute(
            text(
                (
                    "CREATE INDEX IF NOT EXISTS "
                    "ix_listings_isbn "
                    "ON listings (isbn)"
                )
            )
        )


def initialize_database() -> None:
    """
    Initialize the database and apply safe lightweight migrations.
    """
    ensure_app_directories()

    # Import models so all tables are registered before create_all().
    import app.models  # noqa: F401

    Base.metadata.create_all(
        bind=engine
    )

    _run_lightweight_migrations()

    with engine.connect() as connection:
        connection.execute(
            text(
                "SELECT 1"
            )
        )


def database_health_check() -> bool:
    """
    Verify that the application can connect to SQLite successfully.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    "SELECT 1"
                )
            )

            return (
                result.scalar_one()
                == 1
            )

    except Exception:
        return False




@contextmanager
def session_scope() -> Generator[
    Session,
    None,
    None,
]:
    """
    Provide a transactional SQLAlchemy session.

    Successful operations are committed automatically.
    Exceptions cause an automatic rollback.
    The session is always closed.
    """
    session = SessionLocal()

    try:
        yield session

        session.commit()

    except Exception:
        session.rollback()

        raise

    finally:
        session.close()