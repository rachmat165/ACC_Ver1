@echo off
REM ============================================================
REM  ARUNIKA COMMAND CENTRE - ONE CLICK START
REM  PT. Arunika Teknologi Global
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "ACC_HOME=%~dp0"
set "PYEXE=%~dp0.cache\python\python.exe"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"

cls
echo.
echo  ============================================
echo    ARUNIKA COMMAND CENTRE  -  ACC Ver.1
echo    PT. Arunika Teknologi Global
echo  ============================================
echo.

REM Cek Python
if not exist "%PYEXE%" (
    echo  [X] Python tidak ditemukan!
    echo      Jalankan launch.bat dulu sekali untuk setup Python.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%V in ('"%PYEXE%" --version 2^>^&1') do set PY_VER=%%V
echo  [OK] !PY_VER!

REM Cek dependensi
echo  [*] Memeriksa paket...
"%PYEXE%" -c "import flask, fpdf, twilio, anthropic" >nul 2>&1
if errorlevel 1 (
    echo  [!] Memasang paket yang kurang...
    "%PYEXE%" -m pip install -q flask fpdf2 twilio anthropic openai --no-warn-script-location
)
echo  [OK] Paket siap

REM Siapkan folder
if not exist "%ACC_HOME%data\output"   mkdir "%ACC_HOME%data\output"
if not exist "%ACC_HOME%data\sessions" mkdir "%ACC_HOME%data\sessions"
echo.

REM Jalankan Webhook Server di window baru (minimized)
echo  [*] Menjalankan Webhook Server di background...
start "ACC-Webhook" /min "%PYEXE%" "%ACC_HOME%src\webhook_server.py"

REM Tunggu server siap
echo  [*] Menunggu server siap...
timeout /t 4 /nobreak >nul
echo  [OK] Webhook Server berjalan di port 5000
echo.

REM Jalankan Tunnel di window ini
echo  [*] Membuka tunnel publik (Cloudflare)...
echo  ============================================
echo.
"%PYEXE%" "%ACC_HOME%src\tunnel.py"

echo.
pause
