from pathlib import Path

HOME = Path.home()

DOWNLOADS = HOME / "Downloads"

DOCUMENTS = HOME / "Documents"
PICTURES = HOME / "Pictures"
MUSIC = HOME / "Music"
VIDEOS = HOME / "Videos"
ARCHIVES = HOME / "Archives"
APPLICATIONS = HOME / "Applications"

LOG_FILE = HOME / ".local" / "state" / "downloads-organizer.log"

TEMP_SUFFIXES = {
    ".part",
    ".crdownload",
    ".download",
    ".tmp",
}

MIME_RULES = {
    "exact": {
        "application/pdf": DOCUMENTS,
        "application/zip": ARCHIVES,
        "application/gzip": ARCHIVES,
        "application/x-gzip": ARCHIVES,
        "application/x-bzip2": ARCHIVES,
        "application/x-xz": ARCHIVES,
        "application/x-7z-compressed": ARCHIVES,
        "application/x-rar": ARCHIVES,
        "application/x-tar": ARCHIVES,
        "application/x-executable": APPLICATIONS,
        "application/x-pie-executable": APPLICATIONS,
    },
    "prefix": {
        "text/": DOCUMENTS,
        "image/": PICTURES,
        "audio/": MUSIC,
        "video/": VIDEOS,
    },
}
