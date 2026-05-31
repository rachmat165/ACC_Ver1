@echo off
:: ============================================================
::  ARUNIKA COMMAND CENTRE - ONE CLICK START
::  PT. Arunika Teknologi Global
::
::  Double-klik file ini untuk jalankan semua sekaligus:
::    1. Cek / install Python portable
::    2. Pasang semua dependensi Python
::    3. Jalankan Webhook Server (port 5000)
::    4. Jalankan ngrok (ekspos ke internet)
::    5. Tampilkan URL untuk Twilio + salin ke clipboard
:: ============================================================
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0START.ps1"
