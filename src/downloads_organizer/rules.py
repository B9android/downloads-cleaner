from pathlib import Path

from .config import MIME_RULES, TEMP_SUFFIXES
from .models import SkipReason


def destination_for(mime: str) -> Path | None:
    destination = MIME_RULES["exact"].get(mime)

    if destination is not None:
        return destination

    for prefix, destination in MIME_RULES["prefix"].items():
        if mime.startswith(prefix):
            return destination

    return None


def has_temporary_suffix(path: Path) -> bool:
    return path.suffix.lower() in TEMP_SUFFIXES


def skip_reason_for(path: Path) -> SkipReason | None:
    if path.is_symlink():
        return SkipReason.SYMLINK

    if not path.is_file():
        return SkipReason.NOT_FILE

    if path.name.startswith("."):
        return SkipReason.HIDDEN

    if path.suffix.lower() in TEMP_SUFFIXES:
        return SkipReason.TEMPORARY

    return None
