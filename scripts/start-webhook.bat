@echo off
:: ============================================================
:: ACC WhatsApp Webhook Server - Startup Script
:: PT. Arunika Teknologi Global
::
:: Cara pakai:
::   1. Double-klik file ini dari Drive E:
::   2. Di terminal baru: ngrok http 5000
::   3. Copy URL ngrok ke Twilio Console -> Sandbox Webhook
::
:: Lokasi: E:\ArunikaCommandCentre_V1\arunika-command-centre\
:: ============================================================

title ACC WhatsApp Webhook Server

:: Deteksi lokasi script ini (agar bisa dijalankan dari mana saja)
set SCRIPT_DIR=%~dp0
set ACC_HOME=%SCRIPT_DIR%..

echo.
echo  ============================================
echo    ARUNIKA COMMAND CENTRE
echo    WhatsApp Webhook Server
echo  ============================================
echo.

:: Cari Python (coba .cache/python dulu, lalu python system)
set PYTHON_EXE=%ACC_HOME%\.cache\python\python.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

:: Cek apakah Python bisa dijalankan
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo  [X] Python tidak ditemukan!
    echo      Pastikan Python sudah terpasang atau tersedia di .cache\python\
    pause
    exit /b 1
)

:: Set environment
set ACC_HOME=%ACC_HOME%
set PYTHONPATH=%ACC_HOME%\src;%PYTHONPATH%

:: Cek Flask
"%PYTHON_EXE%" -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo  [!] Flask belum terpasang. Memasang sekarang...
    "%PYTHON_EXE%" -m pip install flask fpdf2 --quiet
)

:: Cek fpdf2
"%PYTHON_EXE%" -c "import fpdf" >nul 2>&1
if errorlevel 1 (
    echo  [!] fpdf2 belum terpasang. Memasang sekarang...
    "%PYTHON_EXE%" -m pip install fpdf2 --quiet
)

echo  [OK] Dependensi siap.
echo.
echo  LANGKAH SELANJUTNYA:
echo  1. Buka terminal BARU, jalankan: ngrok http 5000
echo  2. Copy URL ngrok (https://xxxx.ngrok.io)
echo  3. Buka https://console.twilio.com
echo     -> Messaging -> Try it out -> Send a WhatsApp message
echo     -> Sandbox settings -> isi Webhook URL:
echo        https://xxxx.ngrok.io/webhook/whatsapp
echo  4. Kirim pesan WhatsApp ke nomor sandbox Twilio
echo.
echo  ============================================
echo.

:: Jalankan webhook server
"%PYTHON_EXE%" "%ACC_HOME%\src\webhook_server.py"

echo.
echo  Server berhenti. Tekan tombol apa saja untuk keluar.
pause >nul
