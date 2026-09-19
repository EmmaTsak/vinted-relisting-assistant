from __future__ import annotations

import json
import os
import shutil
import sqlite3

from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent


def get_persistent_root() -> Path:
    local_app_data = os.environ.get(
        "LOCALAPPDATA"
    )

    if local_app_data:
        return (
            Path(local_app_data)
            / "VintedRelistingAssistant"
        )

    return (
        Path.home()
        / "AppData"
        / "Local"
        / "VintedRelistingAssistant"
    )


PERSISTENT_ROOT = get_persistent_root()

TARGET_DATA = (
    PERSISTENT_ROOT
    / "data"
)

TARGET_BACKUPS = (
    PERSISTENT_ROOT
    / "backups"
)


CANDIDATES = [
    (
        "Project database",
        PROJECT_ROOT
        / "data"
        / "database.sqlite",
    ),
    (
        "Normal EXE database",
        PROJECT_ROOT
        / "dist"
        / "VintedRelistingAssistant"
        / "data"
        / "database.sqlite",
    ),
    (
        "Debug EXE database",
        PROJECT_ROOT
        / "dist"
        / "VintedRelistingAssistantDebug"
        / "data"
        / "database.sqlite",
    ),
]


def table_exists(
    connection: sqlite3.Connection,
    table_name: str,
) -> bool:
    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?
        """,
        (
            table_name,
        ),
    ).fetchone()

    return row is not None


def get_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return {
        str(
            row[1]
        )
        for row in rows
    }


def find_listing_table(
    connection: sqlite3.Connection,
) -> str | None:
    for name in (
        "listings",
        "listing",
    ):
        if table_exists(
            connection,
            name,
        ):
            return name

    return None


def inspect_database(
    database_path: Path,
) -> dict[str, int | str]:
    result: dict[str, int | str] = {
        "listings": 0,
        "sold": 0,
        "relisted": 0,
        "history": 0,
    }

    try:
        connection = sqlite3.connect(
            f"file:{database_path.as_posix()}?mode=ro",
            uri=True,
        )

    except sqlite3.Error:
        return result

    try:
        listing_table = find_listing_table(
            connection
        )

        if listing_table:
            result["listings"] = int(
                connection.execute(
                    (
                        "SELECT COUNT(*) "
                        f"FROM {listing_table}"
                    )
                ).fetchone()[0]
            )

            columns = get_columns(
                connection,
                listing_table,
            )

            if "sold" in columns:
                result["sold"] = int(
                    connection.execute(
                        (
                            "SELECT COUNT(*) "
                            f"FROM {listing_table} "
                            "WHERE sold = 1"
                        )
                    ).fetchone()[0]
                )

            if (
                "number_of_times_relisted"
                in columns
            ):
                result["relisted"] = int(
                    connection.execute(
                        (
                            "SELECT COALESCE("
                            "SUM("
                            "number_of_times_relisted"
                            "), 0) "
                            f"FROM {listing_table}"
                        )
                    ).fetchone()[0]
                )

        for history_table in (
            "relist_history",
            "relist_histories",
        ):
            if table_exists(
                connection,
                history_table,
            ):
                result["history"] = int(
                    connection.execute(
                        (
                            "SELECT COUNT(*) "
                            f"FROM {history_table}"
                        )
                    ).fetchone()[0]
                )

                break

    except sqlite3.Error:
        pass

    finally:
        connection.close()

    return result


def patch_settings() -> None:
    settings_path = (
        TARGET_DATA
        / "settings.json"
    )

    if not settings_path.exists():
        return

    try:
        settings = json.loads(
            settings_path.read_text(
                encoding="utf-8-sig"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        print(
            "Could not update settings.json."
        )
        return

    settings[
        "photo_storage_directory"
    ] = str(
        TARGET_DATA
        / "listings"
    )

    settings[
        "backup_directory"
    ] = str(
        TARGET_BACKUPS
    )

    settings_path.write_text(
        json.dumps(
            settings,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def main() -> None:
    print()
    print(
        "Vinted Relisting Assistant"
    )

    print(
        "Persistent Data Migration"
    )

    print(
        "=" * 60
    )

    print()

    existing_candidates = []

    for label, path in CANDIDATES:
        if not path.exists():
            continue

        stats = inspect_database(
            path
        )

        modified = datetime.fromtimestamp(
            path.stat().st_mtime
        )

        existing_candidates.append(
            (
                label,
                path,
                stats,
                modified,
            )
        )

    if not existing_candidates:
        print(
            "No existing database was found."
        )

        return

    print(
        "I found these databases:"
    )

    print()

    for index, (
        label,
        path,
        stats,
        modified,
    ) in enumerate(
        existing_candidates,
        start=1,
    ):
        print(
            f"[{index}] {label}"
        )

        print(
            f"    {path}"
        )

        print(
            (
                "    Listings: "
                f"{stats['listings']}"
            )
        )

        print(
            (
                "    Sold: "
                f"{stats['sold']}"
            )
        )

        print(
            (
                "    Total relist count: "
                f"{stats['relisted']}"
            )
        )

        print(
            (
                "    History rows: "
                f"{stats['history']}"
            )
        )

        print(
            (
                "    Modified: "
                f"{modified}"
            )
        )

        print()

    while True:
        value = input(
            (
                "Which database contains your "
                "LATEST work? Enter its number: "
            )
        ).strip()

        try:
            selected_index = (
                int(
                    value
                )
                - 1
            )

        except ValueError:
            print(
                "Enter one of the numbers above."
            )
            continue

        if (
            0
            <= selected_index
            < len(
                existing_candidates
            )
        ):
            break

        print(
            "Enter one of the numbers above."
        )

    (
        selected_label,
        selected_database,
        selected_stats,
        selected_modified,
    ) = existing_candidates[
        selected_index
    ]

    del selected_stats
    del selected_modified

    source_data = (
        selected_database.parent
    )

    source_application_root = (
        source_data.parent
    )

    source_backups = (
        source_application_root
        / "backups"
    )

    print()
    print(
        f"Selected: {selected_label}"
    )

    print(
        selected_database
    )

    print()

    PERSISTENT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    if TARGET_DATA.exists():
        timestamp = datetime.now().strftime(
            "%Y%m%d-%H%M%S"
        )

        migration_backup_root = (
            PERSISTENT_ROOT
            / "migration-backups"
            / timestamp
        )

        migration_backup_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        safety_copy = (
            migration_backup_root
            / "data"
        )

        print(
            (
                "Creating safety copy of "
                "existing persistent data..."
            )
        )

        shutil.copytree(
            TARGET_DATA,
            safety_copy,
        )

        shutil.rmtree(
            TARGET_DATA
        )

    print(
        "Copying database, settings and photos..."
    )

    shutil.copytree(
        source_data,
        TARGET_DATA,
    )

    TARGET_BACKUPS.mkdir(
        parents=True,
        exist_ok=True,
    )

    if source_backups.exists():
        print(
            "Copying backups..."
        )

        shutil.copytree(
            source_backups,
            TARGET_BACKUPS,
            dirs_exist_ok=True,
        )

    patch_settings()

    print()
    print(
        "=" * 60
    )

    print(
        "MIGRATION COMPLETE"
    )

    print(
        "=" * 60
    )

    print()

    print(
        "Your permanent application data is now:"
    )

    print(
        PERSISTENT_ROOT
    )

    print()

    print(
        (
            "Do NOT delete your old project/dist "
            "data yet."
        )
    )

    print(
        (
            "First verify the application works "
            "with the new persistent database."
        )
    )

    print()


if __name__ == "__main__":
    main()