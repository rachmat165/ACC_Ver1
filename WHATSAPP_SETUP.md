# 📱 Setup WhatsApp API untuk ACC

Arunika Command Centre dapat dikendalikan via **WhatsApp Business API**. Setup otomatis membantu Anda memlih provider dan mengonfigurasi webhook.

## Alur Setup

### Saat Pertama Jalankan Launcher
```
launch.bat (Windows) atau ./launch.sh (macOS/Linux)
  ↓
[*] Mengecek Python...
[*] Membuat venv...
[*] Memasang dependensi...
[?] Setup WhatsApp API sekarang? (y/n) >
```

Jawab **`y`** untuk setup interaktif.

### Setup Interaktif
```
Pilih provider:
  [1] Telnyx (recommended)
  [2] Twilio (gratis sandbox)
  [3] Meta Cloud API
  [0] Skip

> 1
```

**Isi informasi:**
- API Key (dari dashboard provider)
- Nomor WhatsApp Anda
- Webhook URL (tempat ACC menerima pesan)

**Validasi koneksi** otomatis, simpan config ke `data/.env`.

---

## Rekomendasi Provider

| Provider | Setup | Test Gratis | Best For | Link |
|:---|:---|:---|:---|:---|
| **Telnyx** ⭐ | 1-2 hari | $0.01/msg | Production | https://telnyx.com/messaging/whatsapp |
| **Twilio** | 5 menit | Yes (sandbox) | Testing | https://www.twilio.com/whatsapp |
| **Meta** | 3-5 hari | $0 (limit) | Long-term | https://developers.facebook.com/whatsapp |

**Untuk production ACC: Telnyx** (cepat setup, harga kompetitif, developer-friendly).

---

## Webhook URL

ACC menerima pesan via webhook. Ada 3 opsi:

### 1️⃣ Lokal (Testing) — Gunakan **ngrok**
```bash
# Terminal lain:
ngrok http 5000

# Copy URL, contoh:
# https://xxxx.ngrok.io

# Webhook URL di setup:
https://xxxx.ngrok.io/wa-webhook
```

### 2️⃣ Server Public (Production)
```
https://yourdomain.com/wa-webhook
(domain + SSL wajib)
```

### 3️⃣ Heroku / Cloud (Alternative)
```
https://yourapp.herokuapp.com/wa-webhook
```

---

## Setup Manual (Jika Tidak Ingin Otomatis)

**Edit `data/.env` langsung:**
```env
WA_PROVIDER=telnyx
WA_API_TOKEN=sk-123abc...
WA_PHONE_NUMBER=62812xxxx
WA_WEBHOOK_URL=https://xxxx.ngrok.io/wa-webhook
```

**Lalu restart ACC:**
```
python src/acc.py menu
```

---

## Perintah Setup

**Setup pertama kali:**
```bash
./launch.bat  # atau ./launch.sh
```

**Setup ulang (kapan saja):**
```bash
python src/acc.py setup-whatsapp
```

---

## Verifikasi Webhook

Setelah setup, daftar webhook di dashboard provider:

**Telnyx:**
- Go to: Manage > Messaging > Messaging Profiles > edit > Webhooks
- URL: masukkan webhook URL Anda
- Event: Message Received

**Twilio:**
- Go to: Messaging > Services > select service > Integration > Webhook URL
- URL: masukkan webhook URL Anda

**Meta:**
- Go to: https://developers.facebook.com/apps > select app > WhatsApp > Configuration
- Verify & Register webhook

---

## Troubleshoot

| Masalah | Solusi |
|:---|:---|
| API key invalid | Periksa ulang format & copy dengan benar |
| Webhook tidak terdeteksi | Pastikan URL public/accessible dari internet |
| Pesan tidak masuk | Check webhook logs di `data/sessions/` |
| Permission denied | Nomor WhatsApp harus terdaftar di Business App |

---

## Next Steps

1. ✅ Setup WhatsApp API
2. Kirim pesan test ke nomor Anda dari WhatsApp:
   ```
   "Halo, riset pesaing kami"
   ```
3. ACC menerima → process → balas hasil

---

*Catatan: Pastikan ACC di-host 24/7 untuk menerima pesan real-time. Lokal + ngrok hanya untuk testing.*
