from __future__ import annotations

from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(
    __file__
).resolve().parent

ASSETS_DIR = (
    PROJECT_ROOT
    / "app"
    / "assets"
)

SOURCE_PATH = (
    ASSETS_DIR
    / "brand_icon_source.png"
)

RUNTIME_PNG_PATH = (
    ASSETS_DIR
    / "app_icon.png"
)

ICO_PATH = (
    ASSETS_DIR
    / "app_icon.ico"
)


PNG_SIZE = 512

ICO_SIZES = [
    (16, 16),
    (24, 24),
    (32, 32),
    (48, 48),
    (64, 64),
    (128, 128),
    (256, 256),
]


def load_source_image() -> Image.Image:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            (
                "Source icon not found.\n\n"
                "Please save your icon here:\n"
                f"{SOURCE_PATH}"
            )
        )

    image = Image.open(
        SOURCE_PATH
    ).convert(
        "RGBA"
    )

    return image


def save_runtime_png(
    image: Image.Image,
) -> None:
    runtime_image = image.resize(
        (
            PNG_SIZE,
            PNG_SIZE,
        ),
        Image.Resampling.LANCZOS,
    )

    runtime_image.save(
        RUNTIME_PNG_PATH,
        format="PNG",
    )


def save_ico(
    image: Image.Image,
) -> None:
    image.save(
        ICO_PATH,
        format="ICO",
        sizes=ICO_SIZES,
    )


def main() -> None:
    ASSETS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    image = load_source_image()

    save_runtime_png(
        image
    )

    save_ico(
        image
    )

    print(
        "Created branding assets:"
    )
    print(
        f"- {RUNTIME_PNG_PATH}"
    )
    print(
        f"- {ICO_PATH}"
    )


if __name__ == "__main__":
    main()