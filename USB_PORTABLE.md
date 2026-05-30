# 🔌 ACC USB Portable Mode

ACC sepenuhnya bisa dijalankan dari USB flash drive (E:\, F:\, dll.) tanpa menyentuh komputer host.

## Cara Kerja

Saat pertama kali `launch.bat` dijalankan dari USB:
1. **Unduh Python embeddable** (~25 MB, sekali saja) dari python.org.
2. **Ekstrak ke `.cache\python\`** di dalam USB.
3. **Pasang pip** ke Python portable itu (via `get-pip.py`).
4. **Pasang dependensi** dari `requirements.txt` ke USB.
5. **Jalankan aplikasi.**

Sejak itu, Python + pip + semua paket tinggal di USB. Cabut USB → colok ke komputer lain → jalankan lagi. Python di host tidak disentuh.

## Struktur Setelah Pertama Jalan

```
E:\arunika-command-centre\
├── launch.bat
├── .cache\
│   ├── python\          ← Python portable (Anda copy ini)
│   │   ├── python.exe
│   │   ├── python312.dll
│   │   ├── Lib\site-packages\  ← semua paket di sini
│   │   └── Scripts\
│   └── pip\             ← pip cache (mempercepat install ulang)
├── data\
├── agent\
└── ...
```

## Lingkungan Variabel yang Dipakai

`launch.bat` mengatur agar SEMUA aktivitas tinggal di USB:

| Variabel | Nilai | Tujuan |
| :--- | :--- | :--- |
| `PIP_CACHE_DIR` | `.cache\pip\` di USB | pip cache di USB, bukan host |
| `PYTHONUSERBASE` | `.cache\pyuser\` di USB | user-site di USB |
| `PYTHONDONTWRITEBYTECODE` | `1` | hindari `.pyc` berserakan |
| `ACC_HOME` | folder USB | semua path relatif ke sini |

## Persyaratan Host

- Windows 10/11 (64-bit atau ARM64)
- PowerShell (bawaan Windows)
- **Tidak perlu Python**, tidak perlu admin, tidak perlu instalasi apa pun

## Performa

- **USB 2.0**: bisa jalan tapi lambat (start ~30-60 detik)
- **USB 3.0**: nyaman (start ~10-15 detik)
- **SSD eksternal (USB 3.1/Type-C)**: terbaik (start <5 detik)

> 💡 **Saran:** Pakai SSD eksternal untuk produksi. Flash drive boleh untuk demo/test.

## Mac/Linux

Untuk Mac/Linux, mode portable USB lebih kompleks karena Python binary berbeda per OS/arch. Untuk sekarang, `launch.sh` masih memakai Python host. Versi portable Mac/Linux bisa dibangun terpisah (PyOxidizer / Nuitka) di iterasi berikutnya.

## Backup & Pindah

Folder USB ini self-contained. Untuk backup:
- Copy seluruh folder `arunika-command-centre\` (termasuk `.cache\` jika ingin tanpa unduh ulang).
- Atau zip seluruhnya.

Untuk pindah ke USB baru:
- Copy ke USB baru → `launch.bat` jalan langsung tanpa setup ulang.

## Keamanan

USB berisi:
- `data\.env` — API keys
- `data\sessions\` — riwayat percakapan
- `data\tenants\` — data klien

**Wajib enkripsi drive** (BitLocker, VeraCrypt) untuk produksi. Jangan kehilangan USB tanpa enkripsi.

## Hemat Tempat (opsional)

Setelah pertama dipasang, ukuran kira-kira:
- Python embeddable: ~25 MB
- pip + dependensi: ~150-200 MB (anthropic, openai, dll.)
- **Total: ~250 MB**

Jika ingin reset:
```cmd
rmdir /s /q .cache
```
Lalu jalankan `launch.bat` lagi (akan re-download).
