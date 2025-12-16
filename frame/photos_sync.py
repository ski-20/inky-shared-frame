import os
from pyicloud import PyiCloudService
from pathlib import Path

PHOTO_DIR = Path(os.environ["LOCAL_PHOTO_DIR"])
ALBUM_NAME = os.environ["ICLOUD_FOLDER"]

PHOTO_DIR.mkdir(exist_ok=True)

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
    raise RuntimeError(f"Shared album '{ALBUM_NAME}' not found")

downloaded = 0

for asset in album.photos:
    filename = asset.filename.replace("/", "_")
    path = PHOTO_DIR / filename

    if path.exists():
        continue

    try:
        with open(path, "wb") as f:
            f.write(asset.download())
        downloaded += 1
    except Exception as e:
        print(f"Failed {filename}: {e}")

print(f"Sync complete. Downloaded={downloaded}")
