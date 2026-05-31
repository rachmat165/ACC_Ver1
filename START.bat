@echo off
REM ============================================================
REM  ARUNIKA COMMAND CENTRE - ONE CLICK START
REM  PT. Arunika Teknologi Global
REM
REM  Double-klik file ini untuk jalankan semua sekaligus:
REM    1. Cek / install Python portable
REM    2. Pasang semua dependensi Python
REM    3. Jalankan Webhook Server (port 5000)
REM    4. Jalankan ngrok (ekspos ke internet)
REM    5. Tampilkan URL untuk Twilio + salin ke clipboard
REM ============================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"
set "ACC_HOME=%cd%"
set "LOG_FILE=%ACC_HOME%\START_LOG.txt"

REM Clear log file
echo. > "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"
echo  ARUNIKA COMMAND CENTRE - STARTUP LOG >> "%LOG_FILE%"
echo  Waktu: %date% %time% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

cls
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  ARUNIKA COMMAND CENTRE - ONE CLICK START        ║
echo  ║  PT. Arunika Teknologi Global                    ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  Inisialisasi...
echo. >> "%LOG_FILE%"

REM Cek PowerShell tersedia
powershell.exe -NoProfile -Command "exit 0" >nul 2>&1
if errorlevel 1 (
    echo. >> "%LOG_FILE%"
    echo [ERROR] PowerShell tidak ditemukan atau tidak bisa dijalankan >> "%LOG_FILE%"
    echo. >> "%LOG_FILE%"
    echo [ERROR] PowerShell tidak ditemukan!
    echo.
    echo  Solusi:
    echo    - Windows 7/8: Upgrade ke PowerShell 3.0+
    echo    - Windows 10+: PowerShell seharusnya sudah ada
    echo    - Cek: Settings ^> Apps ^> Optional features ^> PowerShell
    echo.
    pause
    exit /b 1
)

REM Jalankan PowerShell script dengan error handling
echo Menjalankan START.ps1... >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { ^
     $ErrorActionPreference='Stop'; ^
     & '%ACC_HOME%\START.ps1' >> '%LOG_FILE%' 2>&1; ^
   } catch { ^
     Write-Host \"[ERROR] `$_\" >> '%LOG_FILE%'; ^
     Write-Host $_.Exception.Message >> '%LOG_FILE%'; ^
     exit 1; ^
   }"

set EXITCODE=%ERRORLEVEL%

REM Jika ada error, tampilkan log dan tunggu user
if %EXITCODE% neq 0 (
    cls
    echo.
    echo  ╔══════════════════════════════════════════════════╗
    echo  ║  [X] ERROR - STARTUP GAGAL                       ║
    echo  ╚══════════════════════════════════════════════════╝
    echo.
    echo  Detail error (lihat di bawah):
    echo  ════════════════════════════════════════════════════
    type "%LOG_FILE%"
    echo  ════════════════════════════════════════════════════
    echo.
    echo  DEBUG: Jika ada error, lapor dengan file ini:
    echo    %LOG_FILE%
    echo.
    pause
    exit /b %EXITCODE%
)

REM Jika sukses, tunggu user tutup manual
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  [OK] SERVER BERJALAN                            ║
echo  ║  Ctrl+C untuk berhenti                           ║
echo  ╚══════════════════════════════════════════════════╝
echo.
pause
