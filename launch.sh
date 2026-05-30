#!/usr/bin/env bash
# ============================================================
#  ARUNIKA COMMAND CENTRE - Launcher (macOS / Linux)
#  PT. Arunika Teknologi Global
#  Otomatis: cek Python -> install bila belum ada (via paket OS)
#            -> buat venv -> pasang dependensi -> jalankan
# ============================================================
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
export ACC_HOME="$HERE"

echo "============================================"
echo "  🛸  ARUNIKA COMMAND CENTRE"
echo "  PT. Arunika Teknologi Global"
echo "============================================"
echo

# ---------- 1. Cek Python >= 3.9 ----------
PYEXE=""
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys;assert sys.version_info[:2]>=(3,9)' 2>/dev/null; then
  PYEXE="python3"
fi

# ---------- 2. Install otomatis bila belum ada ----------
if [ -z "$PYEXE" ]; then
  echo "[!] Python >= 3.9 tidak ditemukan. Mencoba memasang otomatis..."
  OS="$(uname -s)"
  if [ "$OS" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
      echo "[*] Memasang Python via Homebrew..."
      brew install python
    else
      echo "[X] Homebrew tidak ada. Pasang dulu dari https://brew.sh lalu ulangi,"
      echo "    atau unduh Python dari https://www.python.org/downloads/"
      exit 1
    fi
  elif command -v apt-get >/dev/null 2>&1; then
    echo "[*] Memasang Python via apt (butuh sudo)..."
    sudo apt-get update -y && sudo apt-get install -y python3 python3-venv python3-pip
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3 python3-pip
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm python python-pip
  elif command -v zypper >/dev/null 2>&1; then
    sudo zypper install -y python3 python3-pip
  else
    echo "[X] Paket manager tidak dikenali. Pasang Python 3.9+ manual lalu ulangi."
    exit 1
  fi
  if command -v python3 >/dev/null 2>&1; then PYEXE="python3"; else
    echo "[X] Python masih belum terdeteksi. Tutup terminal, buka lagi, jalankan ulang."
    exit 1
  fi
fi
echo "[OK] Menggunakan Python: $($PYEXE --version 2>&1)"
echo

# ---------- 3. Pastikan modul venv ----------
if ! $PYEXE -c 'import venv' >/dev/null 2>&1; then
  echo "[!] Modul venv belum ada. Coba pasang (Debian/Ubuntu): sudo apt-get install -y python3-venv"
fi

# ---------- 4. Virtual environment lokal ----------
if [ ! -x ".venv/bin/python" ]; then
  echo "[*] Membuat virtual environment lokal .venv ..."
  $PYEXE -m venv .venv
  ./.venv/bin/python -m pip install --upgrade pip >/dev/null
  echo "[*] Memasang dependensi dari requirements.txt ..."
  ./.venv/bin/pip install -r requirements.txt
fi

# ---------- 5. Siapkan .env ----------
if [ ! -f "data/.env" ]; then
  cp data/.env.example data/.env
  echo "[!] data/.env dibuat. Isi API key Anda di sana sebelum mulai chat."
fi

# ---------- 6. Setup WhatsApp (opsional) ----------
echo
read -p "[?] Setup WhatsApp API sekarang? (y/n) > " -n 1 WA_ANS
echo
if [ "$WA_ANS" = "y" ] || [ "$WA_ANS" = "Y" ]; then
  echo
  ./.venv/bin/python src/setup_whatsapp.py
  echo
fi

# ---------- 7. Jalankan aplikasi ----------
echo
echo "[OK] Semua siap. Menjalankan Arunika Command Centre..."
echo
./.venv/bin/python src/acc.py menu
