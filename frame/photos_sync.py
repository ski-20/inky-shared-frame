#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
from pyicloud import PyiCloudService
from datetime import datetime
from PIL import Image

# HEIC support
from pillow_heif import register_heif_opener
register_heif_opener()

# ------------------------------------------------------------------
# Environment
# ------------------------------------------------------------------
PHOTO_DIR = Path(os.environ["LOCAL_PHOTO_DIR"])
ALBUM_NAME = os.environ["ICLOUD_FOLDER"]
STATE_FILE = Path(os.environ["STATE_FILE"])
COOKIE_DIR = os.environ.get("PYICLOUD_COOKIE_DIRECTORY", "/home/lu/.pyicloud")

PHOTO_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
def log(msg):
    print(
        f"[{datetime.now().isoformat(timespec='seconds')}] {msg}",
        flush=True
    )

log("Starting iCloud photo sync")

# ------------------------------------------------------------------
# State (asset-ID based)
# ------------------------------------------------------------------
def load_state():
    if not STATE_FILE.exists():
        return {"assets": {}}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"assets": {}}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

state = load_state()
known_assets = state.setdefault("assets", {})

# ------------------------------------------------------------------
# Connect to iCloud 
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# Access Photos service
# ------------------------------------------------------------------
try:
    photos = api.photos
except Exception as e:
    log(f"FATAL: Unable to access Photos service: {e}")
    sys.exit(1)

# ------------------------------------------------------------------
# Locate shared album
# ------------------------------------------------------------------
album = None
for stream in photos.shared_streams:
    if stream.title == ALBUM_NAME:
        album = stream
        break

if not album:
    log(f"FATAL: Shared album '{ALBUM_NAME}' not found")
    sys.exit(1)

log(f"Found shared album: {ALBUM_NAME}")

# ------------------------------------------------------------------
# Phase 1: Enumerate source (ASSET IDS)
# ------------------------------------------------------------------
icloud_asset_ids = set()

try:
    for asset in album.photos:
        icloud_asset_ids.add(asset.id)
except Exception as e:
    log(f"FATAL: Failed while enumerating iCloud photos: {e}")
    sys.exit(1)

log(f"iCloud photo count: {len(icloud_asset_ids)}")

# ------------------------------------------------------------------
# Phase 2: Download + convert new assets
# ------------------------------------------------------------------
downloaded = 0
skipped = 0
failed = 0

for asset in album.photos:
    asset_id = asset.id

    if asset_id in known_assets:
        skipped += 1
        continue

    suffix = Path(asset.filename).suffix.lower()
    tmp_path = PHOTO_DIR / f"{asset_id}{suffix}"
    final_path = PHOTO_DIR / f"{asset_id}.jpg"

    try:
        log(f"Downloading asset {asset_id} ({asset.filename})")
        with open(tmp_path, "wb") as f:
            f.write(asset.download())

        # Normalize EVERYTHING to JPG
        with Image.open(tmp_path) as im:
            im.convert("RGB").save(
                final_path,
                "JPEG",
                quality=92,
                subsampling=0
            )

        tmp_path.unlink(missing_ok=True)

        known_assets[asset_id] = {
            "file": final_path.name,
            "added": datetime.now().isoformat(timespec="seconds"),
        }

        downloaded += 1

    except Exception as e:
        failed += 1
        log(f"ERROR: Failed to process {asset.filename}: {e}")
        if tmp_path.exists():
            tmp_path.unlink()

# If any downloads failed → NO DELETE PHASE
if failed > 0:
    log(
        f"SYNC ABORTED — download failures detected "
        f"(downloaded={downloaded}, failed={failed})"
    )
    save_state(state)
    sys.exit(1)

log(
    f"Download phase complete — downloaded={downloaded}, skipped={skipped}"
)

# ------------------------------------------------------------------
# Phase 3: Delete orphaned local files 
# ------------------------------------------------------------------
deleted = 0

orphans = set(known_assets.keys()) - icloud_asset_ids

for asset_id in orphans:
    fname = known_assets[asset_id]["file"]
    path = PHOTO_DIR / fname

    log(f"Deleting orphaned file {fname}")
    if path.exists():
        path.unlink()

    del known_assets[asset_id]
    deleted += 1

# ------------------------------------------------------------------
# Finalize
# ------------------------------------------------------------------
save_state(state)

log(
    "SYNC COMPLETE — "
    f"downloaded={downloaded}, "
    f"skipped={skipped}, "
    f"deleted={deleted}"
)

sys.exit(0)
