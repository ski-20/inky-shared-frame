#!/bin/bash
set -e

echo "🐍 Setting up Python virtual environment"

cd /home/lu

python3 -m venv inkyenv
source inkyenv/bin/activate

pip install --upgrade pip
pip install pillow inky pyicloud

echo "✅ Virtual environment ready"
