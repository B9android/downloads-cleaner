import logging
import time
from pathlib import Path

from .filesystem import (
    get_mime,
    is_old_enough,
    list_entries,
    move_file,
)
from .models import OrganizeResult, PlannedMove, SkipReason
from .rules import destination_for, skip_reason_for

LOGGER = logging.getLogger("downloads-organizer")


def record_failure(
    result: OrganizeResult,
    path: Path,
    exc: Exception,
) -> None:
    result.add_failure(path, exc)
    LOGGER.error(
        "Failed to process %s: %s",
        path,
        exc,
    )


def organize(
    downloads: Path,
    *,
    min_age_hours: float = 6,
    dry_run: bool = False,
) -> OrganizeResult:
    result = OrganizeResult()

    if not downloads.exists():
        record_failure(
            result,
            downloads,
            FileNotFoundError(f"Downloads directory does not exist: {downloads}"),
        )
        return result

    if not downloads.is_dir():
        record_failure(
            result,
            downloads,
            NotADirectoryError(f"Downloads path is not a directory: {downloads}"),
        )
        return result

    try:
        paths = list_entries(downloads)
    except OSError as exc:
        record_failure(result, downloads, exc)
        return result

    scan_time = time.time()

    LOGGER.info(
        "Scanning %s (%d entries)",
        downloads,
        len(paths),
    )

    for path in paths:
        process_file(
            path,
            result,
            min_age_hours=min_age_hours,
            dry_run=dry_run,
            scan_time=scan_time,
        )

    LOGGER.info(
        "Finished: moved=%d would_move=%d skipped=%d failed=%d",
        result.moved,
        result.would_move,
        result.skipped,
        result.failed,
    )

    for reason, count in result.skipped_reasons.items():
        LOGGER.debug(
            "Skipped (%s): %d",
            reason.value,
            count,
        )

    return result


def process_file(
    path: Path,
    result: OrganizeResult,
    *,
    min_age_hours: float,
    dry_run: bool,
    scan_time: float,
) -> None:
    try:
        skip_reason = skip_reason_for(path)

        if skip_reason is not None:
            LOGGER.debug("Skipping %s: %s", path, skip_reason.value)
            result.add_skip(skip_reason)
            return

        if not is_old_enough(
            path,
            min_age_hours,
            now=scan_time,
        ):
            LOGGER.debug(
                "Skipping recent file: %s",
                path,
            )
            result.add_skip(SkipReason.TOO_RECENT)
            return

        mime = get_mime(path)

        LOGGER.debug(
            "Detected MIME type for %s: %s",
            path,
            mime,
        )

        destination = destination_for(mime)

        if destination is None:
            LOGGER.info(
                "Skipping unsupported MIME type: %s (%s)",
                path,
                mime,
            )
            result.add_skip(SkipReason.UNSUPPORTED_MIME)
            return

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        target = destination / path.name

        if dry_run:
            move = PlannedMove(
                source=path,
                destination=target,
                mime=mime,
            )

            result.add_would_move(move)

            LOGGER.info(
                "Would move: %s -> %s",
                path,
                target,
            )
            return

        actual_target = move_file(path, target)

        LOGGER.info(
            "Moved: %s -> %s",
            path,
            actual_target,
        )

        result.add_move()

    except (OSError, RuntimeError) as exc:
        record_failure(result, path, exc)

    except Exception as exc:
        result.add_failure(path, exc)
        LOGGER.exception(
            "Unexpected error while processing %s",
            path,
        )
