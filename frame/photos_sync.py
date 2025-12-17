import os
from pathlib import Path
from pyicloud import PyiCloudService
from datetime import datetime

PHOTO_DIR = Path(os.environ["LOCAL_PHOTO_DIR"])
ALBUM_NAME = os.environ["ICLOUD_FOLDER"]

def log(msg):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)

PHOTO_DIR.mkdir(exist_ok=True)

log("Connecting to iCloud")

api = PyiCloudService(
    os.environ["ICLOUD_EMAIL"],
    os.environ["ICLOUD_PASSWORD"]
)

photos = api.photos
streams = photos.shared_streams

album = None
for stream in streams:
    if stream.title == ALBUM_NAME:
        album = stream
        break

if not album:
    log(f"ERROR: Shared album '{ALBUM_NAME}' not found")
    raise RuntimeError(f"Album '{ALBUM_NAME}' not found")

log(f"Found shared album: {ALBUM_NAME}")

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
        log(f"FAILED {filename}: {e}")

log(
    f"SYNC SUMMARY — downloaded={downloaded}, skipped={skipped}, failed={failed}"
)
