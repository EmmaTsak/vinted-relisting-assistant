from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

project_root_text = str(
    PROJECT_ROOT
)

if project_root_text not in sys.path:
    sys.path.insert(
        0,
        project_root_text,
    )


from app.database import (
    database_health_check,
    initialize_database,
)
from app.services.backup_service import create_backup
from app.services.vinted_export_service import (
    import_vinted_export,
)


def show_progress(
    current: int,
    total: int,
    title: str,
) -> None:
    safe_title = (
        title
        if len(title) <= 65
        else title[:62] + "..."
    )

    print(
        f"[{current:>3}/{total}] {safe_title}"
    )


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "Usage:"
        )

        print(
            (
                'python tools\\import_vinted_export.py '
                '"C:\\path\\to\\listings.zip"'
            )
        )

        return 1

    export_path = Path(
        sys.argv[
            1
        ]
    ).expanduser().resolve()

    print()
    print(
        "Vinted Relisting Assistant"
    )
    print(
        "Vinted Personal Data Import"
    )
    print(
        "=" * 45
    )
    print()

    initialize_database()

    if not database_health_check():
        print(
            "ERROR: Local database is unavailable."
        )

        return 1

    print(
        f"Export: {export_path}"
    )

    print()
    print(
        "Creating safety backup..."
    )

    try:
        backup = create_backup(
            prefix="pre-vinted-import"
        )

        print(
            f"Safety backup: {backup.path}"
        )

    except Exception as exc:
        print()
        print(
            "ERROR: Could not create safety backup."
        )
        print(
            exc
        )

        print()
        print(
            "Import cancelled. Nothing was imported."
        )

        return 1

    print()
    print(
        "Importing listings..."
    )
    print()

    try:
        result = import_vinted_export(
            export_path,
            progress_callback=show_progress,
        )

    except Exception as exc:
        print()
        print(
            "IMPORT FAILED"
        )
        print(
            exc
        )

        return 1

    print()
    print(
        "=" * 45
    )
    print(
        "IMPORT COMPLETE"
    )
    print(
        "=" * 45
    )
    print()

    print(
        f"Listings found:       {result.total_found}"
    )

    print(
        f"Listings imported:    {result.imported}"
    )

    print(
        f"Existing skipped:     {result.skipped_existing}"
    )

    print(
        f"Photos imported:      {result.photos_imported}"
    )

    print(
        f"Sold imported:        {result.sold_imported}"
    )

    print(
        f"Hidden / excluded:    {result.hidden_imported}"
    )

    print(
        f"Warnings:             {len(result.warnings)}"
    )

    if result.warnings:
        print()
        print(
            "WARNINGS"
        )
        print(
            "-" * 45
        )

        for warning in result.warnings:
            print(
                f"- {warning}"
            )

    print()
    print(
        "You can now open the application."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )