from pathlib import Path

from PyInstaller.building.build_main import Analysis
from PyInstaller.building.api import (
    COLLECT,
    EXE,
    PYZ,
)


PROJECT_ROOT = Path.cwd()


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
    datas=[],
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
)


coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="VintedRelistingAssistant",
)