@echo off
REM ============================================================
REM  ACC WEBHOOK SERVER - SIMPLE LAUNCHER (Fallback)
REM  Jalankan ini jika START.bat tidak bisa dijalankan
REM  Ini cukup jalankan webhook server saja, tanpa banyak logic
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║  ACC WEBHOOK SERVER - LAUNCHER FALLBACK  ║
echo  ║  PT. Arunika Teknologi Global            ║
echo  ╚══════════════════════════════════════════╝
echo.

REM Cari Python
set "PYEXE=python.exe"
if exist ".cache\python\python.exe" (
    set "PYEXE=.cache\python\python.exe"
    echo  [OK] Python portable ditemukan
) else (
    for /f "tokens=*" %%A in ('where python.exe 2^>nul') do (
        set "PYEXE=%%A"
        echo  [OK] Python system ditemukan: !PYEXE!
        goto :PYFOUND
    )
    echo  [X] Python tidak ditemukan!
    echo      Pastikan Python sudah terpasang atau ada di .cache\python\
    echo.
    pause
    exit /b 1
)

:PYFOUND
"%PYEXE%" --version
echo.

REM Cek flask
"%PYEXE%" -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo  [*] Flask belum terpasang, memasang sekarang...
    "%PYEXE%" -m pip install flask fpdf2 -q
)

REM Jalankan
echo  [*] Menjalankan Webhook Server (port 5000)...
echo      Buka terminal baru untuk ngrok: ngrok http 5000
echo.
set "ACC_HOME=%cd%"
set "PYTHONPATH=%ACC_HOME%\src;%PYTHONPATH%"
"%PYEXE%" "src\webhook_server.py"
