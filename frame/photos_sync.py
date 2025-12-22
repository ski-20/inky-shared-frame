import os
import sys
from pathlib import Path
from datetime import datetime
from pyicloud import PyiCloudService

from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

PHOTO_DIR = Path(os.environ["LOCAL_PHOTO_DIR"])
ALBUM_NAME = os.environ["ICLOUD_FOLDER"]
STATE_FILE = Path(os.environ.get("STATE_FILE", "/home/lu/.inkyframe_state.json"))
COOKIE_DIR = os.environ.get("PYICLOUD_COOKIE_DIRECTORY", "/home/lu/.pyicloud")


def log(msg):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


PHOTO_DIR.mkdir(parents=True, exist_ok=True)

log("Starting iCloud photo sync")

# -----------------------------
# Connect to iCloud
# -----------------------------
try:
    api = PyiCloudService(
        os.environ["ICLOUD_EMAIL"],
        os.environ["ICLOUD_PASSWORD"],
        cookie_directory=COOKIE_DIR
    )
    log(f"Using PYICLOUD_COOKIE_DIRECTORY={COOKIE_DIR}")
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
# Phase 1: Enumerate iCloud assets
# -----------------------------
icloud_assets = {}

try:
    for asset in album.photos:
        asset_id = asset.id.replace("/", "_")
        ext = asset.filename.split(".")[-1].lower()
        icloud_assets[asset_id] = ext
except Exception as e:
    log(f"FATAL: Failed while enumerating iCloud photos: {e}")
    sys.exit(1)

log(f"iCloud asset count: {len(icloud_assets)}")

# -----------------------------
# Phase 2: Download missing assets
# -----------------------------
downloaded = 0
skipped = 0
failed = 0

for asset in album.photos:
    asset_id = asset.id.replace("/", "_")
    local_path = PHOTO_DIR / f"{asset_id}.jpg"

    if local_path.exists():
        skipped += 1
        continue

    try:
        log(f"Downloading asset {asset_id} ({asset.filename})")
        raw = asset.download()

        if asset.filename.lower().endswith(".heic"):
            img = Image.open(raw)
            img.save(local_path, format="JPEG", quality=95, subsampling=0)
        else:
            with open(local_path, "wb") as f:
                f.write(raw)

        downloaded += 1
    except Exception as e:
        failed += 1
        log(f"ERROR: Failed to process {asset.filename}: {e}")

# Abort if anything failed
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
# Phase 3: STRICT DELETE MODE
# -----------------------------
deleted = 0

valid_filenames = {f"{aid}.jpg" for aid in icloud_assets.keys()}

for local_file in PHOTO_DIR.iterdir():
    if not local_file.is_file():
        continue

    if local_file.name not in valid_filenames:
        log(f"Deleting orphaned file {local_file.name}")
        local_file.unlink()
        deleted += 1

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
