@echo off
REM ============================================================
REM  ARUNIKA COMMAND CENTRE - START WEBHOOK SERVER
REM  PT. Arunika Teknologi Global
REM
REM  Prasyarat: Python portable sudah ada di .cache\python\
REM            (auto-installed oleh launch.bat sebelumnya)
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "ACC_HOME=%~dp0"
set "PYDIR=%ACC_HOME%.cache\python"
set "PYEXE=%PYDIR%\python.exe"

cls
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   ARUNIKA COMMAND CENTRE                         ║
echo  ║   WhatsApp Webhook Server                        ║
echo  ║   PT. Arunika Teknologi Global                   ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM ─── Cek Python ───────────────────────────────────────
if not exist "%PYEXE%" (
    echo  [X] Python portable tidak ditemukan!
    echo      Lokasi: %PYDIR%
    echo.
    echo  Solusi:
    echo    - Jalankan launch.bat dulu (akan install Python)
    echo    - Atau download Python dari python.org
    echo.
    pause
    exit /b 1
)

echo  [OK] Python ditemukan
"%PYEXE%" --version
echo.

REM ─── Cek dependensi ───────────────────────────────────
echo  Memeriksa dependensi...
"%PYEXE%" -c "import flask, fpdf, anthropic, twilio" >nul 2>&1
if errorlevel 1 (
    echo  [!] Ada paket yang kurang. Memasang...
    "%PYEXE%" -m pip install -q flask fpdf2 --no-warn-script-location
    if errorlevel 1 (
        echo  [X] Gagal install dependensi.
        echo      Coba jalankan manual di terminal:
        echo        python -m pip install flask fpdf2
        echo.
        pause
        exit /b 1
    )
)
echo  [OK] Semua dependensi tersedia
echo.

REM ─── Persiapan folder ─────────────────────────────────
if not exist "%ACC_HOME%data\output" mkdir "%ACC_HOME%data\output"

REM ─── Jalankan webhook server ──────────────────────────
echo  ╔══════════════════════════════════════════════════╗
echo  ║  STARTING WEBHOOK SERVER (port 5000)             ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  Langkah selanjutnya:
echo    1. Buka terminal BARU
echo    2. Jalankan: ngrok http 5000
echo    3. Copy URL ngrok (https://xxxx.ngrok.io)
echo    4. Tempel ke Twilio Console ^> Sandbox settings
echo    5. Kirim pesan WhatsApp ke nomor sandbox Twilio
echo.
echo  Server berjalan... (Ctrl+C untuk berhenti)
echo  ─────────────────────────────────────────────────────
echo.

set "PYTHONPATH=%ACC_HOME%src;%PYTHONPATH%"
"%PYEXE%" "%ACC_HOME%src\webhook_server.py"

echo.
echo  ─────────────────────────────────────────────────────
echo  [OK] Server berhenti.
echo.
pause
