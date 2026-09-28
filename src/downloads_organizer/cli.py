import argparse
import logging
from pathlib import Path

from .config import DOWNLOADS, LOG_FILE
from .logging_config import configure_logging
from .models import OrganizeResult
from .organizer import organize

LOGGER = logging.getLogger("downloads-organizer")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Organize files from ~/Downloads into home directories based on MIME type."
        )
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be moved without moving files.",
    )

    parser.add_argument(
        "--age",
        type=float,
        default=6,
        metavar="HOURS",
        help="Minimum file age in hours (default: 6).",
    )

    parser.add_argument(
        "--log-file",
        type=Path,
        default=LOG_FILE,
        metavar="PATH",
        help=f"Log file (default: {LOG_FILE}).",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )

    return parser


def print_summary(result: OrganizeResult) -> None:
    print()
    print(f"moved: {result.moved}, skipped: {result.skipped}, failed: {result.failed}")

    if result.skipped_reasons:
        print()
        print("skip reasons:")

        for reason, count in sorted(
            result.skipped_reasons.items(),
            key=lambda item: item[0].value,
        ):
            print(f"  {reason.value}: {count}")

    if result.errors:
        print()
        print("errors:")

        for path, exc in result.errors:
            print(f"  {path}: {exc}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.age < 0:
        parser.error("--age must be non-negative")

    configure_logging(
        args.log_file,
        verbose=args.verbose,
    )

    LOGGER.info("Starting Downloads organizer")
    LOGGER.info("Downloads: %s", DOWNLOADS)
    LOGGER.info("Minimum age: %.2f hours", args.age)
    LOGGER.info("Dry run: %s", args.dry_run)

    result = organize(
        DOWNLOADS,
        min_age_hours=args.age,
        dry_run=args.dry_run,
    )

    print_summary(result)

    exit_code = 0 if result.success else 1

    LOGGER.info("Organizer exited with status %d", exit_code)

    return exit_code
