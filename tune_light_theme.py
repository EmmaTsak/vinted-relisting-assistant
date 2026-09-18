from __future__ import annotations

from pathlib import Path
import shutil


PROJECT_ROOT = Path(
    __file__
).resolve().parent

THEME_PATH = (
    PROJECT_ROOT
    / "app"
    / "ui"
    / "theme.py"
)

BACKUP_PATH = (
    PROJECT_ROOT
    / "app"
    / "ui"
    / "theme.py.pre_blush_tune.bak"
)


REPLACEMENTS = {
    # Main light background:
    # less white, more soft blush.
    "#FFF8F6": "#F9ECEF",

    # Main card/input surface:
    # still clean, but visibly warmer.
    "#FFFCFA": "#FFF3F5",

    # Secondary cards / read-only fields.
    "#FAF0F2": "#F7E5EA",

    # Hover surfaces.
    "#F8E7EC": "#F1D8E0",

    # Card/input borders.
    "#E8D8DD": "#DFC5CF",

    # Hover/focus-adjacent border.
    "#D1A9B8": "#CA93A6",

    # Sidebar.
    "#F8E4EB": "#F3D5DF",

    # Sidebar hover.
    "#F2D3DE": "#EBC3D1",
}


def main() -> None:
    if not THEME_PATH.exists():
        raise FileNotFoundError(
            f"Could not find:\n{THEME_PATH}"
        )

    text = THEME_PATH.read_text(
        encoding="utf-8"
    )

    missing: list[str] = []

    for old_value in REPLACEMENTS:
        if old_value not in text:
            missing.append(
                old_value
            )

    if missing:
        print(
            "No changes were made."
        )

        print(
            "The current theme.py does not contain "
            "all expected colours:"
        )

        for value in missing:
            print(
                f"- {value}"
            )

        raise SystemExit(
            1
        )

    shutil.copy2(
        THEME_PATH,
        BACKUP_PATH,
    )

    for old_value, new_value in (
        REPLACEMENTS.items()
    ):
        text = text.replace(
            old_value,
            new_value,
        )

    THEME_PATH.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Light theme updated successfully."
    )

    print(
        f"Backup created:\n{BACKUP_PATH}"
    )


if __name__ == "__main__":
    main()