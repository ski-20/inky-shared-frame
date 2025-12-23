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

sudo apt update
sudo apt install -y \
  git \
  python3 \
  python3-venv \
  python3-pip \
  python3-rpi.gpio \
  libjpeg-dev \
  libopenjp2-7 \
  libheif-dev


4️⃣ Enable SPI & i2c (Required for Inky)

sudo raspi-config #enable SPI &i2c
sudo reboot

# confirm spi dev exists with:
ls /dev/spidev*

5️⃣ Clone Repository

#add deploy key
ssh-keygen -t ed25519 -C "inkyframe-readonly" #gnereate key
# Press Enter for defaults (creates ~/.ssh/id_ed25519)
cat ~/.ssh/id_ed25519.pub #copy to github
ssh -T git@github.com #conenct to github


6️⃣ clone repo

cd ~
git clone git@github.com:ski-20/inky-shared-frame.git
cd inky-shared-frame


7️⃣ Create Python Virtual Environment

IMPORTANT: RPi.GPIO is installed system-wide and must be visible inside the venv.

python3 -m venv inkyenv --system-site-packages
source inkyenv/bin/activate

8️⃣ Create Runtime Environment File

cp .env.example .env
nano .env

ICLOUD_EMAIL=your@email.com
ICLOUD_PASSWORD=yourpassword
ICLOUD_FOLDER=InkyFrame
LOCAL_PHOTO_DIR=/home/lu/photos
STATE_FILE=/home/lu/.inkyframe_state.json
PYICLOUD_COOKIE_DIRECTORY=/home/lu/.pyicloud

sudo cp /home/lu/inky-shared-frame/.env /etc/inky-frame.env
sudo chown root:root /etc/inky-frame.env
sudo chmod 600 /etc/inky-frame.env
sudo -u lu mkdir -p /home/lu/.pyicloud
sudo -u lu chmod 700 /home/lu/.pyicloud
sudo -u lu rm -rf /home/lu/.pyicloud/*


9️⃣ Create Local Photo Directory

mkdir -p /home/lu/photos


🔟 ICloud access setup (required for apple 2FA)

pip install --upgrade pip
pip install pillow pillow-heif pyicloud inky

cd ~/inky-shared-frame
source inkyenv/bin/activate
set -a
source .env
set +a
python #then paste below

from pyicloud import PyiCloudService
import os

cookie_dir = os.environ.get("PYICLOUD_COOKIE_DIRECTORY", "/home/lu/.pyicloud")

print("Using cookie dir:", cookie_dir)

api = PyiCloudService(
    os.environ["ICLOUD_EMAIL"],
    os.environ["ICLOUD_PASSWORD"],
    cookie_directory=cookie_dir
)

print("Logged in")

if api.requires_2fa:
    print("2FA required.")
    code = input("Enter the 2FA code sent to your Apple device: ")
    if api.validate_2fa_code(code):
        print("2FA validation successful.")
    else:
        print("2FA validation failed.")
else:
    print("No 2FA required.")

print("Attempting Photos access…")
_ = api.photos
print("Photos access OK.")


#confirm if gpio is accesible from the venv
python - << 'EOF'
import RPi.GPIO as GPIO
print("RPi.GPIO OK")
EOF

exit


1️⃣1️⃣ Install Systemd Service

cd ~/inky-shared-frame/
sudo cp systemd/inky-frame.service /etc/systemd/system/inky-frame.service
sudo systemctl daemon-reload
sudo systemctl enable inky-frame
sudo systemctl start inky-frame


1️⃣1️⃣ Verify Service

systemctl status inky-frame
journalctl -u inky-frame -f


1️⃣2️⃣ Troubleshooting

#to trigger a manual sync
cd ~/inky-shared-frame
source inkyenv/bin/activate
set -a
source .env
set +a
python frame/photos_sync.py

