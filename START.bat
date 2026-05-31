@echo off
REM ============================================================
REM  ARUNIKA COMMAND CENTRE - WEBHOOK SERVER LAUNCHER
REM  PT. Arunika Teknologi Global
REM
REM  Jalankan launch.bat SEKALI DULU untuk setup Python.
REM  Setelah itu, double-klik file ini untuk jalankan
REM  WhatsApp Webhook Server langsung.
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "ACC_HOME=%~dp0"
set "PYVER=3.12.7"
set "PYDIR=%ACC_HOME%.cache\python"
set "PYEXE=%PYDIR%\python.exe"
set "PIPCACHE=%ACC_HOME%.cache\pip"
set "PYTHONUSERBASE=%ACC_HOME%.cache\pyuser"

set "PIP_CACHE_DIR=%PIPCACHE%"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONPATH=%ACC_HOME%src;%PYTHONPATH%"

echo ============================================
echo   ARUNIKA COMMAND CENTRE
echo   WhatsApp Webhook Server
echo   Drive: %~d0
echo ============================================
echo.

REM ---------- 1. Cek Python portable ----------
if exist "%PYEXE%" (
    "%PYEXE%" -c "import sys" >nul 2>nul && (
        echo [OK] Python portable ditemukan.
        goto :PYREADY
    )
)

REM Cek Python system
where python >nul 2>nul
if not errorlevel 1 (
    set "PYEXE=python"
    echo [OK] Python system ditemukan.
    goto :PYREADY
)

echo [X] Python tidak ditemukan!
echo.
echo  Solusi: Jalankan launch.bat dulu untuk install Python,
echo  lalu jalankan START.bat kembali.
echo.
pause
exit /b 1

:PYREADY
echo [OK] Menggunakan Python:
"%PYEXE%" --version
echo.

REM ---------- 2. Cek & pasang dependensi ----------
echo [*] Memeriksa dependensi...
"%PYEXE%" -c "import flask, fpdf, twilio" >nul 2>&1
if errorlevel 1 (
    echo [!] Paket belum lengkap, memasang...
    "%PYEXE%" -m pip install --no-warn-script-location --disable-pip-version-check -q flask fpdf2 twilio
    if errorlevel 1 (
        echo [X] Gagal install paket. Cek koneksi internet.
        pause
        exit /b 1
    )
    echo [OK] Dependensi terpasang.
) else (
    echo [OK] Semua dependensi tersedia.
)
echo.

REM ---------- 3. Siapkan folder output ----------
if not exist "%ACC_HOME%data\output" mkdir "%ACC_HOME%data\output"

REM ---------- 4. Jalankan Webhook Server ----------
echo ============================================
echo   SERVER SIAP - PORT 5000
echo ============================================
echo.
echo   Langkah berikutnya:
echo   [1] Buka terminal BARU
echo   [2] Jalankan: ngrok http 5000
echo   [3] Copy URL: https://xxxx.ngrok.io
echo   [4] Twilio Console ^> Sandbox settings
echo       Isi Webhook URL:
echo       https://xxxx.ngrok.io/webhook/whatsapp
echo   [5] Kirim pesan WhatsApp ke sandbox Twilio
echo.
echo   Tekan Ctrl+C untuk menghentikan server.
echo ============================================
echo.

"%PYEXE%" "%ACC_HOME%src\webhook_server.py"

echo.
echo [OK] Server berhenti.
pause
