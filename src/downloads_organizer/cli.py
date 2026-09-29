import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .config import DOWNLOADS, LOG_FILE
from .logging_config import configure_logging
from .models import OrganizeResult
from .notification import notify_organization_available
from .organizer import organize

LOGGER = logging.getLogger("downloads-organizer")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Organize files from ~/Downloads into home directories based on MIME type."
        )
    )

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be moved without moving files.",
    )

    mode.add_argument(
        "--run", action="store_true", help="Actually organize eligible files."
    )

    parser.add_argument(
        "--notify",
        action="store_true",
        help="Show an actionable desktop notification when the dry run finds files to organize.",
    )

    parser.add_argument(
        "--plan",
        action="store_true",
        help=("Show the complete planned run. Implies --dry-run."),
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


def format_notification_summary(result: OrganizeResult, *, max_entries: int = 5) -> str:
    lines: list[str] = []

    for move in result.planned_moves[:max_entries]:
        lines.append(f"{move.source.name} -> {move.destination.parent.name}")

    remaining = len(result.planned_moves) - max_entries

    if remaining > 0:
        lines.append(f"... and {remaining} more")

    return "\n".join(lines)


def print_plan(result: OrganizeResult) -> None:
    """Print the complete planned set of moves."""
    if not result.planned_moves:
        print("Nothing to organize.")
        return

    print()
    print(f"Planned moves: {len(result.planned_moves)}")
    print()

    for move in result.planned_moves:
        print(f"{move.source} -> {move.destination}")

    print()
    print(f"Would move: {result.would_move}")

    if result.skipped:
        print(f"Skipped: {result.skipped}")

    if result.failed:
        print(f"Failed: {result.failed}")


def format_summary(
    result: OrganizeResult,
) -> None:
    print()

    print(
        f"moved: {result.moved}, "
        f"would move: {result.would_move}, "
        f"skipped: {result.skipped}, "
        f"failed: {result.failed}"
    )

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


def run_organizer(
    *, dry_run: bool, age: float, log_file: Path, verbose: bool
) -> OrganizeResult:
    configure_logging(
        log_file,
        verbose=verbose,
    )

    LOGGER.info("Starting Downloads organizer")
    LOGGER.info("Downloads: %s", DOWNLOADS)
    LOGGER.info("Minimum age: %.2f hours", age)
    LOGGER.info("Mode: %s", "dry-run" if dry_run else "run")

    result = organize(
        DOWNLOADS,
        min_age_hours=age,
        dry_run=dry_run,
    )

    return result


def find_terminal() -> str | None:
    for terminal in (
        "kitty",
        "foot",
        "alacritty",
        "wezterm",
    ):
        if shutil.which(terminal):
            return terminal

    return None


def open_plan_in_terminal(*, age: float, log_file: Path, verbose: bool) -> bool:
    terminal = find_terminal()

    if terminal is None:
        LOGGER.error(
            "Could not find a supported terminal emulator "
            "(tried kitty, foot, alacritty, wezterm)"
        )
        return False

    command = [
        sys.executable,
        "-m",
        "downloads_organizer",
        "--plan",
        "--age",
        str(age),
        "--log-file",
        str(log_file),
    ]

    if verbose:
        command.append("--verbose")

    if terminal == "kitty" or terminal == "foot":
        terminal_command = [
            terminal,
            "--hold",
            *command,
        ]

    elif terminal == "alacritty":
        terminal_command = [
            terminal,
            "-e",
            *command,
        ]

    elif terminal == "wezterm":
        terminal_command = [
            terminal,
            "start",
            "--",
            *command,
        ]

    else:
        return False

    try:
        subprocess.Popen(terminal_command, env=os.environ.copy())
    except OSError:
        LOGGER.exception("Failed to open terminal for plan")
        return False

    LOGGER.info("Opened plan in %s", terminal)

    return True


def handle_notification(
    result: OrganizeResult, *, age: float, log_file: Path, verbose: bool
) -> int:
    if result.would_move == 0:
        LOGGER.info("Nothing to organize; no notification needed.")
        return 0

    action = notify_organization_available(result.would_move)

    if action == "plan":
        if not open_plan_in_terminal(age=age, log_file=log_file, verbose=verbose):
            return 1
        return 0

    if action != "organize":
        LOGGER.info("Organization was not approved.")
        return 0

    LOGGER.info("Organization approved; starting fresh run.")

    command = [
        sys.executable,
        "-m",
        "downloads_organizer",
        "--run",
        "--age",
        str(age),
        "--log-file",
        str(log_file),
    ]

    if verbose:
        command.append("--verbose")

    completed = subprocess.run(command, check=False)

    return completed.returncode


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.age < 0:
        parser.error("--age must be non-negative")

    if args.notify and not args.dry_run:
        parser.error("--notify can only be used with --dry-run")

    if args.plan:
        result = run_organizer(
            dry_run=True,
            age=args.age,
            log_file=args.log_file,
            verbose=args.verbose,
        )

        print_plan(result)

        return 0 if result.success else 1

    result = run_organizer(
        dry_run=args.dry_run,
        age=args.age,
        log_file=args.log_file,
        verbose=args.verbose,
    )

    format_summary(result)

    if args.notify:
        return handle_notification(
            result,
            age=args.age,
            log_file=args.log_file,
            verbose=args.verbose,
        )

    return 0 if result.success else 1
