# 🚀 QUICKSTART — Arunika Command Centre

## 1. Buka di VS Code
File > Open Folder > pilih `arunika-command-centre`.

## 2. Jalankan
- **Windows**: double-click `launch.bat` (atau di terminal: `.\launch.bat`)
- **macOS/Linux**: `chmod +x launch.sh && ./launch.sh`

Launcher otomatis membuat `.venv`, memasang dependensi, dan menyalin `.env`.

## 3. Isi API Key
Buka `data/.env`, isi minimal satu, contoh:
```
ANTHROPIC_API_KEY=sk-ant-xxxx
```
Lalu pastikan `data/config.yaml` -> `provider.active: anthropic`.

## 4. Coba
Di menu pilih `[1] Chat`, atau dari terminal:
```
python src/acc.py doctor    # cek konfigurasi
python src/acc.py chat      # ngobrol dgn Arunika
python src/acc.py cron      # jalankan tugas terjadwal yg jatuh tempo
```

## 5. Jadwalkan otomatis (opsional)
- Linux/macOS (crontab):
  ```
  */30 * * * * /path/arunika-command-centre/scripts/cron-runner.sh
  ```
- Windows: Task Scheduler -> jalankan `scripts\cron-runner.ps1` tiap 30 menit.

## 6. Portable USB
Salin seluruh folder ke USB 3.0 / SSD. `.venv` & data ikut. Enkripsi drive.

## Yang perlu Anda kembangkan (di VS Code)
- `src/` : sambungkan webhook WhatsApp Business API
- generator dokumen (DOCX/PPTX/XLSX/PDF) per skill
- koneksi MCP penuh (`data/mcp.json`)
- vector memory untuk RAG

## 7. Self-Healing Code Loop
```
python src/self_healing.py "Buat fungsi X + test"      # otomatis perbaiki sampai lulus
```
Hasil lulus-test di-stage ke `build/deploy/`. Tambah `--approve` untuk deploy nyata.

## 8. WhatsApp Setup (Opsional)

Saat jalankan launcher:
```
[?] Setup WhatsApp API sekarang? (y/n) > y
```

Pilih provider, isi API key, nomor, webhook URL. Config auto-saved.

Atau setup manual kapan saja:
```bash
python src/acc.py setup-whatsapp
```
