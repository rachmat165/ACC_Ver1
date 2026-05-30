#!/usr/bin/env bash
# Setup manual (macOS/Linux) - opsional, launch.sh sudah otomatis
set -e
cd "$(dirname "$0")/.."
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
[ -f data/.env ] || cp data/.env.example data/.env
echo "Setup selesai. Jalankan ./launch.sh"
