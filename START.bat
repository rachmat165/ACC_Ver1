@echo off
REM ============================================================
REM  ARUNIKA COMMAND CENTRE - WEBHOOK SERVER LAUNCHER
REM  PT. Arunika Teknologi Global
REM
REM  Jalankan launch.bat SEKALI DULU untuk setup Python.
REM  Setelah itu double-klik START.bat setiap kali ingin
REM  menjalankan WhatsApp Webhook Server.
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

echo ============================================
echo   ARUNIKA COMMAND CENTRE
echo   WhatsApp Webhook Server
echo   Drive: %~d0
echo ============================================
echo.

REM ---------- 1. Cek Python portable (logika sama dengan launch.bat) ----------
if exist "%PYEXE%" (
  "%PYEXE%" -c "import sys" >nul 2>nul && (
    echo [OK] Python portable ditemukan di USB.
    goto :PYREADY
  )
)

echo [X] Python portable tidak ditemukan di: %PYDIR%
echo.
echo  Solusi: Jalankan launch.bat terlebih dahulu.
echo  launch.bat akan menginstall Python portable (~25 MB).
echo  Setelah selesai, jalankan START.bat kembali.
echo.
pause
exit /b 1

:PYREADY
echo [OK] Menggunakan Python: %PYEXE%
"%PYEXE%" --version
echo.

REM ---------- 2. Set environment ----------
set "PYTHONPATH=%ACC_HOME%src;%PYTHONPATH%"

REM ---------- 3. Cek & pasang dependensi ----------
echo [*] Memeriksa dependensi webhook server...
"%PYEXE%" -c "import flask, fpdf, twilio, anthropic" >nul 2>&1
if errorlevel 1 (
    echo [!] Ada paket yang kurang, memasang...
    "%PYEXE%" -m pip install --no-warn-script-location --disable-pip-version-check -q ^
        flask fpdf2 twilio anthropic openai
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

REM ---------- 4. Siapkan folder ----------
if not exist "%ACC_HOME%data\output" mkdir "%ACC_HOME%data\output"
if not exist "%ACC_HOME%data\sessions" mkdir "%ACC_HOME%data\sessions"

REM ---------- 5. Jalankan Webhook Server ----------
echo ============================================
echo   SERVER BERJALAN DI PORT 5000
echo ============================================
echo.
echo   Langkah selanjutnya:
echo   [1] Buka terminal BARU
echo   [2] Jalankan: ngrok http 5000
echo   [3] Copy URL: https://xxxx.ngrok.io
echo   [4] Twilio Console ^> Sandbox settings
echo       Isi Webhook URL:
echo       https://xxxx.ngrok.io/webhook/whatsapp
echo   [5] Kirim /menu ke nomor sandbox Twilio
echo.
echo   Ctrl+C untuk menghentikan server.
echo ============================================
echo.

"%PYEXE%" "%ACC_HOME%src\webhook_server.py"

echo.
echo [OK] Server berhenti.
pause
