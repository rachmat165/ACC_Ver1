# 🚀 Setup Arunika Command Centre Ver. 1

**Lokasi:** `E:\ArunikaCommandCentre_V1\arunika-command-centre\`

## 1️⃣ Cara Jalankan (Pilih Salah Satu)

### ✅ Opsi 1: One-Click Launcher (Recommended)
```
Double-klik: START.bat
```
Otomatis setup Python, dependensi, webhook server, dan ngrok.

### ✅ Opsi 2: Fallback (Jika START.bat Error)
```
Double-klik: RUN-WEBHOOK.bat
```
Cukup jalankan webhook server saja. Ngrok harus dijalankan manual di terminal lain.

### ✅ Opsi 3: Manual (Classic)
```
1. Double-klik: launch.bat
2. Pilih menu [A] WhatsApp - Test kirim pesan (untuk cek Twilio)
3. Terminal baru: ngrok http 5000
4. Tempel URL ke Twilio Console
```

---

## 2️⃣ Jika START.bat Error

### Error akan tersimpan di:
```
START_LOG.txt
```

Cek file itu untuk lihat detail error.

### Common Issues:

**❌ "PowerShell tidak ditemukan"**
- Solusi: Update Windows atau install PowerShell 3.0+
- Alternatif: Gunakan RUN-WEBHOOK.bat

**❌ "Python tidak ditemukan"**
- Cek apakah folder `.cache\python\` ada
- START.bat seharusnya auto-download Python (~25 MB)
- Jika gagal: Download manual dari [python.org/downloads](https://www.python.org/downloads)

**❌ "Flask/fpdf2 tidak ketemu"**
- Pastikan `requirements.txt` ada di folder root
- Terminal baru, jalankan:
  ```
  python -m pip install flask fpdf2 --no-warn-script-location -q
  ```

**❌ "Ngrok tidak ditemukan"**
- Download dari [ngrok.com/download](https://ngrok.com/download)
- Ekstrak `ngrok.exe` ke folder saat ini
- Jalankan ulang START.bat

---

## 3️⃣ Setup Twilio WhatsApp (Sekali saja)

1. Buka https://console.twilio.com
2. **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Scroll ke bawah: **"WhatsApp Sandbox settings"**
4. Isi field **"When a message comes in"**:
   ```
   https://xxxx.ngrok.io/webhook/whatsapp
   ```
5. Klik **Save**
6. Kirim pesan WhatsApp ke nomor sandbox Twilio

---

## 4️⃣ Perintah WhatsApp yang Tersedia

| Perintah | Fungsi |
|----------|--------|
| Kirim teks biasa | AI membalas otomatis |
| `/skill riset` | Aktifkan skill riset |
| `/skill proposal` | Aktifkan skill proposal |
| `/skills` | Lihat semua skill |
| `/pdf` | Simpan respons terakhir sebagai PDF |
| `/pdf <prompt>` | Generate PDF dari prompt baru |
| `/reset` | Mulai sesi percakapan baru |
| `/help` | Lihat panduan |

---

## 5️⃣ Troubleshooting Checklist

- [ ] Windows 10+ atau PowerShell 3.0+ terinstall?
- [ ] Python terdeteksi? (`python --version` di terminal)
- [ ] `.cache\python\python.exe` ada? (atau Python system ada)
- [ ] `requirements.txt` ada di folder root?
- [ ] `data\.env` terisi dengan API keys?
- [ ] Webhook server berjalan di port 5000? (`http://127.0.0.1:5000`)
- [ ] Ngrok berjalan di terminal lain? (`ngrok http 5000`)
- [ ] URL ngrok sudah tempel ke Twilio Console?
- [ ] Sudah kirim pesan WhatsApp ke sandbox Twilio?

---

## 6️⃣ Port yang Digunakan

| Port | Layanan | Catatan |
|------|---------|---------|
| **5000** | Webhook Server | Lokal, diekspos via ngrok |
| **4040** | Ngrok Dashboard | Monitor tunnel, URL public |
| **1234** | LM Studio (opsional) | Jika gunakan model lokal |

---

## 7️⃣ Struktur Folder Penting

```
arunika-command-centre/
├── START.bat              ← Double-klik untuk one-click setup
├── RUN-WEBHOOK.bat        ← Fallback jika START.bat error
├── START.ps1              ← PowerShell launcher (dipanggil START.bat)
├── launch.bat             ← Classic launcher (ACC menu)
├── requirements.txt       ← Python dependencies
├── src/
│   ├── acc.py             ← Core ACC engine
│   ├── webhook_server.py  ← Flask webhook (port 5000)
│   ├── pdf_generator.py   ← PDF generator
│   ├── whatsapp_handler.py ← Twilio integration
│   └── ...
├── data/
│   ├── .env              ← API keys (jangan commit!)
│   ├── .env.example      ← Template
│   ├── config.yaml       ← Konfigurasi provider AI
│   ├── output/           ← PDF output
│   └── sessions/         ← Chat history
└── ...
```

---

## 8️⃣ Provider AI

Setup di `data/config.yaml` → `provider.active`:

| Provider | Key env | Setup |
|----------|---------|-------|
| **anthropic** | `ANTHROPIC_API_KEY` | Pakai Claude (recommended) |
| **openai** | `OPENAI_API_KEY` | Pakai GPT-4o |
| **openrouter** | `OPENROUTER_API_KEY` | 100+ model, harga bersaing |
| **lmstudio** | `LM_STUDIO_BASE_URL` | Model lokal gratis (download LM Studio) |

---

## 9️⃣ Support

- **GitHub**: https://github.com/rachmat165/ACC_Ver1
- **Email**: corsec@arunika2045.com
- **Docs**: Lihat README.md, WHATSAPP_SETUP.md

---

## 🎯 Quick Start (TL;DR)

```bash
1. Double-klik START.bat
2. Tunggu selesai (5-10 detik)
3. URL ngrok sudah di clipboard
4. Buka Twilio Console → tempel URL
5. Kirim pesan WhatsApp ke sandbox Twilio
6. ✅ Selesai!
```
