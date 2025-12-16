import os, time, json, random, threading, subprocess
from pathlib import Path
from datetime import datetime, timedelta
from inky.auto import auto
from PIL import Image
import RPi.GPIO as GPIO

PHOTO_DIR = Path(os.environ["LOCAL_PHOTO_DIR"])
STATE_FILE = Path(os.environ["STATE_FILE"])

BUTTON_A = 5
MAX_HISTORY = 10

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen": [], "last_shown": {}, "history": []}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def list_images():
    return sorted(
        p.name for p in PHOTO_DIR.iterdir()
        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    )

def choose_next_image(state, images):
    now = time.time()
    unseen = [img for img in images if img not in state["seen"]]

    if unseen:
        choice = random.choice(unseen)
    else:
        candidates = [i for i in state["seen"] if i not in state["history"]]
        if not candidates:
            candidates = state["seen"]
        weights = [now - state["last_shown"].get(i, 0) for i in candidates]
        choice = random.choices(candidates, weights=weights, k=1)[0]

    if choice not in state["seen"]:
        state["seen"].append(choice)

    state["last_shown"][choice] = now
    state["history"].append(choice)
    state["history"] = state["history"][-MAX_HISTORY:]
    save_state(state)
    return choice

def show_image(inky, path):
    img = Image.open(path).convert("RGB")

    if img.width > img.height:
        img = img.rotate(90, expand=True)

    img.thumbnail((inky.width, inky.height), Image.LANCZOS)

    canvas = Image.new("RGB", (inky.width, inky.height), "white")
    x = (inky.width - img.width) // 2
    y = (inky.height - img.height) // 2
    canvas.paste(img, (x, y))

    inky.set_image(canvas)
    inky.show()
    print("Displaying", path.name)

def sync_photos():
    subprocess.run(
        ["/home/lu/inkyenv/bin/python", "/home/lu/inkyframe/photos_sync.py"],
        check=False
    )

def next_midnight():
    now = datetime.now()
    return datetime.combine(now.date() + timedelta(days=1), datetime.min.time())

def button_thread(inky, state):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    while True:
        if GPIO.input(BUTTON_A) == GPIO.LOW:
            print("BUTTON A PRESSED — NEXT IMAGE")
            images = list_images()
            if images:
                chosen = choose_next_image(state, images)
                show_image(inky, PHOTO_DIR / chosen)
            time.sleep(0.6)
        time.sleep(0.1)

def main():
    print("FRAME MAIN LOOP STARTED")
    inky = auto()
    state = load_state()

    images = list_images()
    if images:
        show_image(inky, PHOTO_DIR / choose_next_image(state, images))

    threading.Thread(
        target=button_thread,
        args=(inky, state),
        daemon=True
    ).start()

    next_update = next_midnight()
    print("Next update at", next_update)

    while True:
        if datetime.now() >= next_update:
            sync_photos()
            images = list_images()
            if images:
                show_image(inky, PHOTO_DIR / choose_next_image(state, images))
            next_update = next_midnight()
        time.sleep(30)

if __name__ == "__main__":
    main()
