import time
from pathlib import Path

import magic

from .rules import has_temporary_suffix


def get_mime(path: Path) -> str:
    return magic.from_file(path, mime=True)


def is_old_enough(
    path: Path, min_age_hours: float, *, now: float | None = None
) -> bool:
    if now is None:
        now = time.time()

    modified_at = path.stat().st_mtime
    age_seconds = now - modified_at

    return age_seconds >= min_age_hours * 60 * 60


def should_process(path: Path, min_age_hours: float) -> bool:
    if path.is_symlink():
        return False

    if not path.is_file():
        return False

    if has_temporary_suffix(path):
        return False

    return is_old_enough(path, min_age_hours)


def find_available_path(path: Path) -> Path:
    if not path.exists():
        return path

    for number in range(1, 1000):
        candidate = path.with_stem(f"{path.stem} ({number})")

        if not candidate.exists():
            return candidate

    raise RuntimeError(f"Could not find unique destination for {path}")


def list_entries(directory: Path) -> list[Path]:
    return sorted(
        directory.iterdir(),
        key=lambda path: path.name.casefold(),
    )


def move_file(source: Path, destination: Path) -> Path:
    candidate = destination

    for _ in range(1000):
        try:
            source.rename(candidate)
            return candidate
        except FileExistsError:
            candidate = find_available_path(candidate)

    raise RuntimeError(f"Could not move {source}: too many collisions")
