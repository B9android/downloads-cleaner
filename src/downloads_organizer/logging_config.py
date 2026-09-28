import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER = logging.getLogger("downloads_organizer")


def configure_logging(
    log_file: Path | None = None,
    *,
    verbose: bool = False,
) -> None:
    level = logging.DEBUG if verbose else logging.INFO

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handlers: list[logging.Handler] = []

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    handlers.append(console)

    if log_file is not None:
        try:
            log_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=1_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        except OSError as exc:
            LOGGER.warning(
                "Could not open log file %s: %s",
                log_file,
                exc,
            )
            print(f"Warning: could not open log file {log_file}: {exc}")

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )
