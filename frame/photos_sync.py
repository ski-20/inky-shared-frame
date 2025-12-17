import os
from pathlib import Path
from pyicloud import PyiCloudService
from datetime import datetime
import sys

PHOTO_DIR = Path(os.environ["LOCAL_PHOTO_DIR"])
ALBUM_NAME = os.environ["ICLOUD_FOLDER"]

def log(msg):
    print(
        f"[{datetime.now().isoformat(timespec='seconds')}] {msg}",
        flush=True
    )

PHOTO_DIR.mkdir(parents=True, exist_ok=True)

log("Starting iCloud photo sync")

# -----------------------------
# Connect to iCloud
# -----------------------------
try:
    api = PyiCloudService(
        os.environ["ICLOUD_EMAIL"],
        os.environ["ICLOUD_PASSWORD"]
    )
except Exception as e:
    log(f"FATAL: Failed to initialize iCloud client: {e}")
    sys.exit(1)

# -----------------------------
# Access Photos service
# -----------------------------
try:
    photos = api.photos
except Exception as e:
    log(f"FATAL: Unable to access Photos service: {e}")
    sys.exit(1)

# -----------------------------
# Locate shared album
# -----------------------------
album = None
for stream in photos.shared_streams:
    if stream.title == ALBUM_NAME:
        album = stream
        break

if not album:
    log(f"FATAL: Shared album '{ALBUM_NAME}' not found")
    sys.exit(1)

log(f"Found shared album: {ALBUM_NAME}")

# -----------------------------
# Phase 1: Enumerate source
# -----------------------------
icloud_files = set()

try:
    for asset in album.photos:
        filename = asset.filename.replace("/", "_")
        icloud_files.add(filename)
except Exception as e:
    log(f"FATAL: Failed while enumerating iCloud photos: {e}")
    sys.exit(1)

log(f"iCloud photo count: {len(icloud_files)}")

# -----------------------------
# Phase 2: Download missing files
# -----------------------------
downloaded = 0
skipped = 0
failed = 0

for asset in album.photos:
    filename = asset.filename.replace("/", "_")
    path = PHOTO_DIR / filename

    if path.exists():
        skipped += 1
        continue

    try:
        log(f"Downloading {filename}")
        with open(path, "wb") as f:
            f.write(asset.download())
        downloaded += 1
    except Exception as e:
        failed += 1
        log(f"ERROR: Failed to download {filename}: {e}")

# If any downloads failed, we DO NOT DELETE
if failed > 0:
    log(
        f"SYNC ABORTED — download failures detected "
        f"(downloaded={downloaded}, failed={failed})"
    )
    sys.exit(1)

log(
    f"Download phase complete — downloaded={downloaded}, skipped={skipped}"
)

# -----------------------------
# Phase 3: Delete orphaned local files
# -----------------------------
deleted = 0

try:
    for local_file in PHOTO_DIR.iterdir():
        if not local_file.is_file():
            continue

        if local_file.name not in icloud_files:
            log(f"Deleting orphaned file {local_file.name}")
            local_file.unlink()
            deleted += 1
except Exception as e:
    log(f"FATAL: Deletion phase failed: {e}")
    sys.exit(1)

# -----------------------------
# Final summary
# -----------------------------
log(
    "SYNC COMPLETE — "
    f"downloaded={downloaded}, "
    f"skipped={skipped}, "
    f"deleted={deleted}"
)

sys.exit(0)
