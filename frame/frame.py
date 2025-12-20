#!/usr/bin/env python3

import os
import sys
import time
import json
import random
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import RPi.GPIO as GPIO
from inky.auto import auto
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

# --------------------
# ENVIRONMENT
# --------------------

PHOTO_DIR = Path(os.environ["LOCAL_PHOTO_DIR"])
STATE_FILE = Path(os.environ["STATE_FILE"])
PYTHON_BIN = sys.executable
SYNC_SCRIPT = str(Path(__file__).parent / "photos_sync.py")

# --------------------
# GPIO (BCM)
# --------------------

BUTTON_A = 5
BUTTON_B = 6
BUTTON_C = 25
BUTTON_D = 27

# --------------------
# IMAGE CONFIG
# --------------------

INKY_SIZE = (1600, 1200)

# --------------------
# LOGGING
# --------------------

def log(msg: str):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)

# --------------------
# STATE
# --------------------

def load_state():
    default = {
        "seen": [],
        "unseen_new": [],
        "style": "normal"
    }

    if not STATE_FILE.exists():
        log("STATE: No state file found — creating fresh state")
        save_state(default)
        return default

    try:
        state = json.loads(STATE_FILE.read_text())
    except Exception as e:
        log(f"STATE ERROR: Failed to read state file — {e}")
        log("STATE: Resetting to defaults")
        save_state(default)
        return default

    # Validate keys
    changed = False
    for key, value in default.items():
        if key not in state:
            log(f"STATE WARNING: Missing key '{key}' — restoring default")
            state[key] = value
            changed = True

    if changed:
        save_state(state)

    return state

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

# --------------------
# IMAGE PROCESSING
# --------------------

def preprocess_normal(img):
    img = img.convert("RGB")
    img = ImageOps.fit(img, INKY_SIZE, Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.6)
    img = ImageEnhance.Color(img).enhance(1.25)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3))
    return img

def preprocess_posterize(img):
    img = preprocess_normal(img)
    return ImageOps.posterize(img, bits=4)

def preprocess_painterly(img):
    img = preprocess_normal(img)
    img = img.filter(ImageFilter.ModeFilter(size=3))
    img = img.filter(ImageFilter.SMOOTH_MORE)
    return img

def preprocess(img, style):
    if style == "posterize":
        return preprocess_posterize(img)
    if style == "painterly":
        return preprocess_painterly(img)
    return preprocess_normal(img)

# --------------------
# IMAGE SELECTION
# --------------------

def list_images():
    return sorted(p.name for p in PHOTO_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})

def choose_next_image(state, images):
    unseen = [i for i in state["unseen_new"] if i in images]
    if unseen:
        chosen = unseen.pop(0)
        state["unseen_new"] = unseen
        state["seen"].append(chosen)
        save_state(state)
        return chosen

    weights = [5 if img not in state["seen"] else 1 for img in images]
    chosen = random.choices(images, weights=weights, k=1)[0]

    if chosen not in state["seen"]:
        state["seen"].append(chosen)
        save_state(state)

    return chosen

# --------------------
# DISPLAY
# --------------------

def show_image(inky, path, state):
    try:
        log(f"Displaying {path.name} [{state['style']}]")
        img = Image.open(path)
        img = preprocess(img, state["style"])
        inky.set_image(img)
        inky.show()
    except Exception as e:
        log(f"ERROR displaying image {path.name}: {e}")

# --------------------
# SYNC
# --------------------

def sync_photos():
    log("SYNC STARTED")

    before = set(list_images())

    result = subprocess.run(
        [PYTHON_BIN, SYNC_SCRIPT],
        capture_output=True,
        text=True
    )

    if result.stdout:
        log(result.stdout.strip())

    if result.returncode != 0:
        log(f"SYNC FAILED — exit={result.returncode}")
        if result.stderr:
            log(f"SYNC STDERR: {result.stderr.strip()}")
        return False, [], []

    after = set(list_images())
    new_images = sorted(after - before)
    deleted_images = sorted(before - after)

    log(f"SYNC COMPLETE — added={len(new_images)}, removed={len(deleted_images)}")

    return True, deleted_images, new_images

# --------------------
# TIME
# --------------------

def next_midnight():
    tomorrow = datetime.now() + timedelta(days=1)
    return datetime.combine(tomorrow.date(), datetime.min.time())

# --------------------
# BUTTON THREAD
# --------------------

def button_thread(inky, state):
    while True:
        if GPIO.input(BUTTON_A) == GPIO.LOW:
            log("BUTTON A PRESSED — NEXT IMAGE")

            images = list_images()
            log(f"BUTTON A: found {len(images)} images")

            if images:
                chosen = choose_next_image(state, images)
                log(f"BUTTON A: chosen image = {chosen}")
                show_image(inky, PHOTO_DIR / chosen, state)

            time.sleep(1)

        elif GPIO.input(BUTTON_B) == GPIO.LOW:
            log("BUTTON B PRESSED — MANUAL SYNC")

            success, _, new = sync_photos()

            if success:
                if new:
                    state["unseen_new"].extend(new)
                    save_state(state)
                    log(f"{len(new)} new images queued")
                else:
                    log("No new images — forcing refresh")

                images = list_images()
                if images:
                    chosen = choose_next_image(state, images)
                    show_image(inky, PHOTO_DIR / chosen, state)

                log("MANUAL SYNC COMPLETE")
            else:
                log("MANUAL SYNC FAILED — NO REFRESH")

            time.sleep(1)

        elif GPIO.input(BUTTON_C) == GPIO.LOW:
            state["style"] = "posterize"
            save_state(state)
            log("BUTTON C — STYLE = POSTERIZE")
            time.sleep(1)

        elif GPIO.input(BUTTON_D) == GPIO.LOW:
            state["style"] = "painterly"
            save_state(state)
            log("BUTTON D — STYLE = PAINTERLY")
            time.sleep(1)

        time.sleep(0.1)

# --------------------
# MAIN
# --------------------

def main():
    log("FRAME MAIN LOOP STARTED")
    log(f"PHOTO_DIR = {PHOTO_DIR}")
    log(f"PHOTO_DIR exists = {PHOTO_DIR.exists()}")

    GPIO.setmode(GPIO.BCM)
    for pin in (BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_D):
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    inky = auto()
    state = load_state()

    images = list_images()
    if images:
        chosen = choose_next_image(state, images)
        show_image(inky, PHOTO_DIR / chosen, state)

    threading.Thread(
        target=button_thread,
        args=(inky, state),
        daemon=True
    ).start()

    next_update = next_midnight()
    log(f"Next scheduled update at {next_update}")

    while True:
        if datetime.now() >= next_update:
            success, _, new = sync_photos()

            if success:
                if new:
                    state["unseen_new"].extend(new)
                    save_state(state)
                    log(f"{len(new)} new images added to unseen pool")
                else:
                    log("No new images — forcing refresh")

                images = list_images()
                if images:
                    chosen = choose_next_image(state, images)
                    show_image(inky, PHOTO_DIR / chosen, state)
            else:
                log("Midnight sync failed — skipping refresh")

            next_update = next_midnight()
            log(f"Next scheduled update at {next_update}")

        time.sleep(30)

# --------------------

if __name__ == "__main__":
    main()
