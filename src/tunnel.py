"""
ACC Tunnel Launcher - Cloudflare Tunnel
Otomatis download cloudflared dan ekspos port 5000 ke internet.
Tidak butuh akun, tidak butuh authtoken.
"""
import os
import sys
import re
import time
import threading
import subprocess
import urllib.request
from pathlib import Path

ACC_HOME = Path(os.environ.get("ACC_HOME", Path(__file__).resolve().parent.parent))
PORT     = int(os.environ.get("ACC_WEBHOOK_PORT", 5000))
CF_DIR   = ACC_HOME / ".cache" / "cloudflared"
CF_EXE   = CF_DIR / "cloudflared.exe"
CF_URL   = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"


def download_with_progress(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    downloaded = [0]
    total      = [0]

    def hook(count, block, total_size):
        downloaded[0] = count * block
        total[0]      = total_size
        if total_size > 0:
            pct   = min(int(downloaded[0] / total_size * 100), 100)
            done  = int(pct / 2)
            bar   = "█" * done + "░" * (50 - done)
            mb    = downloaded[0] / 1_048_576
            print(f"\r  [{bar}] {pct}% ({mb:.1f} MB)", end="", flush=True)

    urllib.request.urlretrieve(url, dest, reporthook=hook)
    print()


def copy_clipboard(text: str):
    try:
        subprocess.run(["clip"], input=text.encode("utf-8"), check=True)
    except Exception:
        pass


def main():
    print()
    print("  ============================================")
    print("    ACC - CLOUDFLARE TUNNEL")
    print("    PT. Arunika Teknologi Global")
    print("  ============================================")
    print()

    # 1. Download cloudflared jika belum ada
    if not CF_EXE.exists():
        print("  Cloudflare Tunnel belum ada.")
        print("  Mengunduh (~35 MB, sekali saja)...")
        print()
        try:
            download_with_progress(CF_URL, CF_EXE)
            print(f"  [OK] Download selesai: {CF_EXE}")
        except Exception as e:
            print(f"\n  [X] Gagal download: {e}")
            print()
            print("  Coba download manual:")
            print("  https://github.com/cloudflare/cloudflared/releases/latest")
            print(f"  Simpan file sebagai:\n  {CF_EXE}")
            input("\n  Tekan Enter untuk keluar...")
            sys.exit(1)
    else:
        print(f"  [OK] Cloudflared ditemukan")

    print(f"  [*] Membuka tunnel ke http://localhost:{PORT}...")
    print()

    # 2. Jalankan cloudflared
    try:
        proc = subprocess.Popen(
            [str(CF_EXE), "tunnel", "--url", f"http://localhost:{PORT}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as e:
        print(f"  [X] Gagal jalankan cloudflared: {e}")
        input("  Tekan Enter untuk keluar...")
        sys.exit(1)

    # 3. Baca URL dari output (timeout 30 detik)
    url     = None
    deadline = time.time() + 30
    print("  Menunggu URL tunnel", end="", flush=True)

    while time.time() < deadline:
        if proc.poll() is not None:
            print("\n  [X] cloudflared berhenti tiba-tiba.")
            break
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.3)
            continue
        print(".", end="", flush=True)
        match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
        if match:
            url = match.group(0)
            break

    print()
    print()

    if not url:
        print("  [X] URL tidak terdeteksi dalam 30 detik.")
        print("  Pastikan webhook server sudah jalan di port 5000.")
        proc.terminate()
        input("  Tekan Enter untuk keluar...")
        sys.exit(1)

    # 4. Tampilkan & salin ke clipboard
    webhook_url = f"{url}/webhook/whatsapp"
    copy_clipboard(webhook_url)

    print("  ============================================")
    print("  TUNNEL AKTIF! URL SUDAH DI CLIPBOARD")
    print("  ============================================")
    print()
    print(f"  URL Publik  : {url}")
    print(f"  Webhook URL : {webhook_url}")
    print()
    print("  ============================================")
    print("  LANGKAH TERAKHIR (paste URL ke Twilio):")
    print()
    print("  1. Buka https://console.twilio.com")
    print("  2. Messaging -> Try it out")
    print("     -> Send a WhatsApp message")
    print("  3. Tab: Sandbox settings")
    print("  4. Field: 'When a message comes in'")
    print("     Tekan Ctrl+V (sudah di clipboard!)")
    print("  5. Klik Save")
    print("  6. Kirim /menu dari WhatsApp")
    print("     ke nomor: +1 415 523 8886")
    print("  ============================================")
    print()
    print("  Tunnel berjalan. JANGAN tutup window ini.")
    print("  Tekan Ctrl+C untuk berhenti.")
    print()

    # 5. Drain output agar proses tidak hang
    try:
        for line in proc.stdout:
            pass
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        print("\n  Tunnel dihentikan.")


if __name__ == "__main__":
    main()
