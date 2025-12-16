# 🖼 Inky Shared Album Photo Frame

A zero-touch digital photo frame built on the **Pimoroni Inky Impression 13.3"** display.  
Family members simply upload photos to a **shared iCloud album** — the frame updates itself automatically.

Designed to be:
- Headless
- Appliance-like
- Family-proof
- Recoverable after power loss

---

## ✨ Features

- Daily update at **midnight**
- iCloud **shared album ingestion**
- New photos **guaranteed to display at least once**
- Intelligent resurfacing of older photos (hybrid weighted random)
- Button **A → next image immediately**
- Persistent state across reboots
- No cron jobs, no GUI, no manual maintenance

---

## 🧰 Hardware

- Raspberry Pi (Zero 2 W / 3 / 4 recommended)
- Inky Impression 13.3"
- Stable USB power supply (important for e-ink refresh reliability)

---

## 🖥 Operating System

- **Raspberry Pi OS Lite (Trixie, 64-bit)**

Enable:
```bash
sudo raspi-config
