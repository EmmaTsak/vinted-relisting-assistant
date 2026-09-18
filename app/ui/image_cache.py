from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


MAX_CACHED_PIXMAPS = 256


_pixmap_cache: OrderedDict[
    str,
    QPixmap,
] = OrderedDict()


def get_scaled_pixmap(
    path: str | Path,
    maximum_width: int,
    maximum_height: int,
) -> QPixmap:
    """
    Load and scale an image with a small in-memory LRU cache.

    The cache key contains:
    - full path
    - file modification time
    - file size
    - requested dimensions

    If a photo is replaced or rotated, its modification time
    changes and a fresh pixmap is loaded automatically.
    """
    image_path = Path(
        path
    )

    try:
        stat = image_path.stat()

    except OSError:
        return QPixmap()

    try:
        resolved_path = (
            image_path.resolve()
        )

    except OSError:
        resolved_path = (
            image_path.absolute()
        )

    cache_key = (
        f"{resolved_path}"
        f"|{stat.st_mtime_ns}"
        f"|{stat.st_size}"
        f"|{maximum_width}x{maximum_height}"
    )

    cached = _pixmap_cache.get(
        cache_key
    )

    if cached is not None:
        _pixmap_cache.move_to_end(
            cache_key
        )

        return cached

    pixmap = QPixmap(
        str(
            image_path
        )
    )

    if pixmap.isNull():
        return pixmap

    if (
        pixmap.width()
        > maximum_width
        or pixmap.height()
        > maximum_height
    ):
        pixmap = pixmap.scaled(
            maximum_width,
            maximum_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    _pixmap_cache[
        cache_key
    ] = pixmap

    _pixmap_cache.move_to_end(
        cache_key
    )

    _trim_cache()

    return pixmap


def clear_pixmap_cache() -> None:
    """
    Remove every cached thumbnail.

    Normally this is not required because file modification
    timestamps automatically invalidate changed images.
    """
    _pixmap_cache.clear()


def get_pixmap_cache_size() -> int:
    """
    Return the number of currently cached scaled images.
    """
    return len(
        _pixmap_cache
    )


def _trim_cache() -> None:
    """
    Keep the cache within its configured maximum size.
    """
    while (
        len(
            _pixmap_cache
        )
        > MAX_CACHED_PIXMAPS
    ):
        _pixmap_cache.popitem(
            last=False
        )