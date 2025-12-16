import RPi.GPIO as GPIO
import time

BUTTONS = {
    "A": 5,
    "B": 6,
    "C": 25,
    "D": 24
}

GPIO.setmode(GPIO.BCM)

for pin in BUTTONS.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Press buttons (Ctrl+C to exit)")

try:
    while True:
        for name, pin in BUTTONS.items():
            if GPIO.input(pin) == GPIO.LOW:
                print(f"Button {name} pressed")
                time.sleep(0.4)
        time.sleep(0.05)
except KeyboardInterrupt:
    GPIO.cleanup()
