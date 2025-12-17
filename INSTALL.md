# 🛠️ InkyFrame – Fresh Install Instructions
Raspberry Pi OS Lite (Trixie)

This document describes **exactly what to do after booting a brand-new
Raspberry Pi OS Lite image** to get InkyFrame running as a system service.

---

## Assumptions

- Raspberry Pi OS Lite (Trixie)
- User account already created (examples assume user: `lu`)
- SSH enabled
- Internet access available
- Inky Impression connected

---


## 1️⃣ First Login

SSH into the Pi:

```bash
ssh lu@impression.local


2️⃣ Update System

sudo apt update
sudo apt full-upgrade -y
sudo reboot


3️⃣ Install System Dependencies

sudo apt install -y \
  git \
  python3 \
  python3-venv \
  python3-pip \
  python3-rpi.gpio \
  libjpeg-dev \
  libopenjp2-7 \
  libatlas-base-dev


4️⃣ Enable SPI (Required for Inky)

sudo raspi-config


5️⃣ Clone Repository

cd ~
git clone https://github.com/YOUR_ORG/inkyframe.git
cd inkyframe


6️⃣ Create Python Virtual Environment

python3 -m venv inkyenv
source inkyenv/bin/activate
pip install --upgrade pip
pip install pillow inky pyicloud


7️⃣ Create Runtime Environment File

cp .env.example .env
nano .env
ICLOUD_EMAIL=your@email.com
ICLOUD_PASSWORD=yourpassword
ICLOUD_FOLDER=InkyFrame
LOCAL_PHOTO_DIR=/home/lu/photos
PYICLOUD_NO_KEYRING=1


8️⃣ Create Local Photo Directory

mkdir -p /home/lu/photos


9️⃣ First Manual Test (Recommended)

source inkyenv/bin/activate
python src/photos_sync.py
ls /home/lu/photos
python src/frame.py


🔟 Install Systemd Service

sudo cp systemd/inky-frame.service /etc/systemd/system/inky-frame.service
sudo systemctl daemon-reload
sudo systemctl enable inky-frame
sudo systemctl start inky-frame


1️⃣1️⃣ Verify Service

systemctl status inky-frame
journalctl -u inky-frame -f

