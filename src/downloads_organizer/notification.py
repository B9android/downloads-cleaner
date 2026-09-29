import logging
import shutil
import subprocess
from collections.abc import Sequence

LOGGER = logging.getLogger("downloads-organizer")


def notify(
    title: str,
    message: str,
    *,
    urgency: str = "normal",
    actions: Sequence[tuple[str, str]] = (),
) -> str | None:
    notify_send = shutil.which("notify-send")

    if notify_send is None:
        LOGGER.error("notify-send was not found in PATH")
        return None

    command = [
        notify_send,
        "--urgency",
        urgency,
        "--wait",
    ]

    for action_id, label in actions:
        command.extend(
            [
                "--action",
                f"{action_id}={label}",
            ]
        )

    command.extend(
        [
            title,
            message,
        ]
    )

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        LOGGER.exception("Failed to execute notify-send")
        return None

    if completed.returncode != 0:
        LOGGER.error(
            "notify-send failed with exit code %d: %s",
            completed.returncode,
            completed.stderr.strip(),
        )
        return None

    action = completed.stdout.strip()

    if not action:
        LOGGER.info("Notification was dismissed")
        return None

    LOGGER.info(
        "Notification action selected: %s",
        action,
    )

    return action


def notify_organization_available(count: int) -> str | None:
    noun = "file" if count == 1 else "files"

    message = f"{count} {noun} ready to organize."

    return notify(
        "Downloads Organizer",
        message,
        actions=(
            ("plan", "View Plan"),
            ("organize", "Organize"),
            ("dismiss", "Dismiss"),
        ),
    )
