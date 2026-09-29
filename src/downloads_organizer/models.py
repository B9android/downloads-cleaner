from collections import Counter
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class SkipReason(StrEnum):
    SYMLINK = "symlink"
    NOT_FILE = "not_file"
    HIDDEN = "hidden"
    TEMPORARY = "temporary"
    TOO_RECENT = "too_recent"
    UNSUPPORTED_MIME = "unsupported_mime"


@dataclass
class PlannedMove:
    source: Path
    destination: Path
    mime: str


@dataclass
class OrganizeResult:
    moved: int = 0
    would_move: int = 0
    skipped: int = 0
    failed: int = 0
    planned_moves: list[PlannedMove] = field(default_factory=list)
    skipped_reasons: Counter[SkipReason] = field(default_factory=Counter)
    errors: list[tuple[Path, Exception]] = field(default_factory=list)

    def add_skip(self, reason: SkipReason) -> None:
        self.skipped += 1
        self.skipped_reasons[reason] += 1

    def add_move(self) -> None:
        self.moved += 1

    def add_would_move(self, move: PlannedMove) -> None:
        self.would_move += 1
        self.planned_moves.append(move)

    def add_failure(self, path: Path, exc: Exception) -> None:
        self.failed += 1
        self.errors.append((path, exc))

    @property
    def success(self) -> bool:
        return self.failed == 0
