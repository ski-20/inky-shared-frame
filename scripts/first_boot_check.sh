#!/bin/bash
set -e

echo "🔍 Inky Frame First Boot Check"

echo "• Checking SPI..."
ls /dev/spidev* || echo "⚠️ SPI not enabled"

echo "• Checking GPIO access..."
groups | grep -q gpio && echo "✔ GPIO group OK" || echo "⚠️ User not in gpio group"

echo "• Checking Python..."
python3 --version

echo "• Checking disk space..."
df -h /

echo "• Checking network..."
ping -c 1 8.8.8.8 >/dev/null && echo "✔ Network OK" || echo "⚠️ No network"

echo "✅ First boot check complete"
