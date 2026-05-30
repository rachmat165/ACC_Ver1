# 🛸 Arunika Command Centre (ACC)

Agentic AI portable — multi-tenant, USB-ready, WhatsApp-driven.
Dijalankan satu operator untuk mengendalikan perusahaan otonom (R&D, Sales, Ops, Finance).

**PT. Arunika Teknologi Global** · Jl. Calung No. 7, Kota Bandung · corsec@arunika2045.com

---

## ⚡ Cara Cepat (Quick Start)

### Windows
Double-click **`launch.bat`** (atau jalankan di PowerShell).

### macOS / Linux
```bash
chmod +x launch.sh
./launch.sh
```

Saat pertama jalan, launcher akan:
1. Mengecek Python (≥3.9) & membuat virtual env lokal di `.venv/`.
2. Memasang dependensi dari `requirements.txt`.
3. Menyalin `data/.env.example` → `data/.env` (isi API key Anda di sana).
4. Membuka menu terminal ACC.

> Belum punya API key? Buka `data/.env` dan isi salah satu provider (Anthropic/OpenAI/dll).

---

## 📁 Struktur

```
arunika-command-centre/
├── launch.bat / launch.sh      # Launcher lintas-platform
├── requirements.txt
├── scripts/
│   ├── setup-unix.sh
│   ├── setup-windows.ps1
│   └── cron-runner.sh / .ps1   # Eksekusi tugas terjadwal
├── agent/                      # Otak agent
│   ├── SOUL.md  HEARTBEAT.md  DESIGN.md
│   └── skills/*.md
├── data/                       # [ENKRIPSI INI] privasi penuh
│   ├── config.yaml  .env  mcp.json  schedule.yaml
│   ├── tenants/  sessions/  memories/
├── company/                    # Departemen agentic + COMPANY.md
└── src/                        # Source code agent core (Python)
```

## 🗝️ Konfigurasi Model
Edit `data/.env` (API key) dan/atau `data/mcp.json` (koneksi MCP), lalu `data/config.yaml` untuk routing.

## 🔒 Keamanan
Folder ini berisi API key & riwayat percakapan. **Enkripsi drive** (BitLocker/FileVault/VeraCrypt).

## ⚠️ Catatan
Ini kerangka starter untuk dikembangkan di VS Code. Modul WhatsApp, generator dokumen, dan integrasi
penuh masih perlu diimplementasikan sesuai roadmap. Laporan keuangan butuh verifikasi akuntan.

---

## 🔁 Self-Healing Code Loop (Generate → Test → Verify → Fix → Deploy)

ACC dapat menulis kode, mengujinya, membaca error, memperbaiki sendiri, lalu deploy
setelah seluruh test lulus.

```
python src/self_healing.py "Buat fungsi hitung PPN 11% beserta testnya"
python src/self_healing.py --spec spec.txt --max-iter 5 --workdir build/tugas1
python src/self_healing.py "..." --approve     # izinkan deploy nyata
```
Atau lewat menu launcher: opsi **[6]**.

Alur: GENERATE kode+test → TEST (pytest, terisolasi+timeout) → VERIFY → FIX (AI baca
error, perbaiki akar masalah) → ulang → DEPLOY (default staging; deploy nyata butuh
persetujuan / `--approve`). Setiap fase dicatat ke `_healing_log.jsonl`.

Keamanan: test berjalan di subprocess dengan timeout; tidak ada test yang dilonggarkan
agar lulus; deploy nyata memerlukan persetujuan operator (`require_human_approval`).

---

## 🔧 Auto-Setup Python
Sejak versi ini, `launch.bat` (Windows) dan `launch.sh` (macOS/Linux) otomatis:
1. Mengecek apakah Python ≥ 3.9 ada.
2. Bila belum: **mengunduh & memasang Python otomatis** (Windows: installer resmi python.org; macOS: Homebrew; Linux: apt/dnf/pacman/zypper — perlu sudo).
3. Membuat `.venv`, memasang dependensi `requirements.txt`, menyiapkan `.env`, lalu menjalankan ACC.

Catatan: di Windows, bila Python baru pertama kali dipasang, kadang perlu **menutup & menjalankan `launch.bat` sekali lagi** agar PATH terbaca.

---

## 📱 WhatsApp Business API

ACC dapat dikendalikan via WhatsApp. **Setup otomatis saat pertama jalankan launcher.**

Tanya provider → isi API key & nomor → automatic config → siap terima pesan.

Provider recommended: **Telnyx** (cepat, harga kompetitif, developer-friendly).

Lihat: `WHATSAPP_SETUP.md` untuk detail lengkap.

---

## 🔌 USB Portable Mode

ACC dirancang **fully portable** dari USB drive (E:\, F:\, dll.):

- Saat pertama jalan, otomatis **unduh & pasang Python embeddable + pip + dependensi DI DALAM USB** (`.cache\python\`).
- Tidak menyentuh Windows host: tidak install Python, tidak menulis ke `C:\Users\`, tidak perlu admin.
- Cabut USB → colok ke PC lain → langsung jalan. Self-contained.

Lihat `USB_PORTABLE.md` untuk detail.

**Pertama jalan**: ~25 MB unduh Python + ~200 MB dependensi (1-3 menit di USB 3.0).
**Selanjutnya**: instan, semua sudah di USB.
