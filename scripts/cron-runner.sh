#!/usr/bin/env bash
# Eksekutor tugas terjadwal. Daftarkan ke crontab OS, mis:
#   */30 * * * * /path/arunika-command-centre/scripts/cron-runner.sh
set -e
cd "$(dirname "$0")/.."
./.venv/bin/python src/acc.py cron
