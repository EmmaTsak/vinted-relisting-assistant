from pathlib import Path

from PyInstaller.building.api import (
    COLLECT,
    EXE,
    PYZ,
)
from PyInstaller.building.build_main import (
    Analysis,
)


PROJECT_ROOT = Path.cwd()

ICON_PATH = (
    PROJECT_ROOT
    / "app"
    / "assets"
    / "app_icon.ico"
)

RUNTIME_ICON_PATH = (
    PROJECT_ROOT
    / "app"
    / "assets"
    / "app_icon.png"
)

VERSION_INFO_PATH = (
    PROJECT_ROOT
    / "version_info.txt"
)


if not ICON_PATH.exists():
    raise FileNotFoundError(
        (
            "Application icon is missing.\n"
            "Run:\n"
            "python build_brand_assets.py"
        )
    )


if not RUNTIME_ICON_PATH.exists():
    raise FileNotFoundError(
        (
            "Runtime application icon is missing.\n"
            "Run:\n"
            "python build_brand_assets.py"
        )
    )


if not VERSION_INFO_PATH.exists():
    raise FileNotFoundError(
        "version_info.txt is missing."
    )


hidden_imports = [
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.sqlite.pysqlite",
    "PIL.BmpImagePlugin",
    "PIL.JpegImagePlugin",
    "PIL.PngImagePlugin",
    "PIL.WebPImagePlugin",
]


a = Analysis(
    [
        str(
            PROJECT_ROOT
            / "app"
            / "main.py"
        )
    ],
    pathex=[
        str(
            PROJECT_ROOT
        )
    ],
    binaries=[],
    datas=[
        (
            str(
                RUNTIME_ICON_PATH
            ),
            "app/assets",
        ),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)


pyz = PYZ(
    a.pure,
)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VintedRelistingAssistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(
        ICON_PATH
    ),
    version=str(
        VERSION_INFO_PATH
    ),
)


coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="VintedRelistingAssistant",
)