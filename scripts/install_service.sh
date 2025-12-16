#!/bin/bash
set -e

echo "⚙️ Installing inky-frame systemd service"

sudo cp /home/lu/inky-shared-frame/systemd/inky-frame.service \
        /etc/systemd/system/inky-frame.service

sudo systemctl daemon-reload
sudo systemctl enable inky-frame
sudo systemctl restart inky-frame

echo "✅ Service installed and started"
