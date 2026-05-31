@echo off
REM ============================================================
REM  ARUNIKA COMMAND CENTRE - ONE CLICK START
REM  PT. Arunika Teknologi Global
REM
REM  Double-klik = semua otomatis:
REM    1. Cek Python portable
REM    2. Cek dependensi
REM    3. Jalankan Webhook Server (background)
REM    4. Download ngrok jika belum ada
REM    5. Jalankan ngrok (background)
REM    6. Tampilkan URL ngrok -> tinggal copy ke Twilio
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "ACC_HOME=%~dp0"
set "PYDIR=%ACC_HOME%.cache\python"
set "PYEXE=%PYDIR%\python.exe"
set "PIPCACHE=%ACC_HOME%.cache\pip"
set "NGROK_EXE=%ACC_HOME%.cache\ngrok\ngrok.exe"
set "NGROK_ZIP=%ACC_HOME%.cache\ngrok\ngrok.zip"
set "NGROK_DIR=%ACC_HOME%.cache\ngrok"

set "PIP_CACHE_DIR=%PIPCACHE%"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONPATH=%ACC_HOME%src;%PYTHONPATH%"
set "ACC_WEBHOOK_PORT=5000"

cls
echo.
echo  ============================================
echo    ARUNIKA COMMAND CENTRE  -  ACC Ver.1
echo    PT. Arunika Teknologi Global
echo  ============================================
echo.

REM ── STEP 1: Cek Python ───────────────────────────────────
echo  [1/5] Memeriksa Python...
if not exist "%PYEXE%" (
    echo        [X] Python portable tidak ditemukan!
    echo.
    echo        Jalankan launch.bat dulu untuk install Python.
    echo        Setelah selesai, jalankan START.bat kembali.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%V in ('"%PYEXE%" --version 2^>^&1') do set PY_VER=%%V
echo  [1/5] OK - !PY_VER!

REM ── STEP 2: Cek dependensi ───────────────────────────────
echo  [2/5] Memeriksa dependensi...
"%PYEXE%" -c "import flask, fpdf, twilio, anthropic" >nul 2>&1
if errorlevel 1 (
    echo        Memasang paket yang kurang...
    "%PYEXE%" -m pip install --no-warn-script-location -q flask fpdf2 twilio anthropic openai
)
echo  [2/5] OK - Semua paket tersedia

REM ── STEP 3: Siapkan folder ──────────────────────────────
if not exist "%ACC_HOME%data\output"   mkdir "%ACC_HOME%data\output"
if not exist "%ACC_HOME%data\sessions" mkdir "%ACC_HOME%data\sessions"

REM ── STEP 4: Jalankan Webhook Server di background ───────
echo  [3/5] Menjalankan Webhook Server (port %ACC_WEBHOOK_PORT%)...
start "ACC-Webhook" /min cmd /c ""%PYEXE%" "%ACC_HOME%src\webhook_server.py" & pause"

REM Tunggu server siap (max 10 detik)
set /a WAIT=0
:WAIT_SERVER
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command "try { $r=(New-Object Net.Sockets.TcpClient); $r.Connect('127.0.0.1',%ACC_WEBHOOK_PORT%); $r.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto :SERVER_READY
set /a WAIT+=1
if !WAIT! lss 10 goto :WAIT_SERVER
echo        [!] Server lambat start, lanjutkan...
:SERVER_READY
echo  [3/5] OK - Webhook Server aktif di http://127.0.0.1:%ACC_WEBHOOK_PORT%

REM ── STEP 5: Cek / Download ngrok ────────────────────────
echo  [4/5] Memeriksa ngrok...

REM Cek ngrok di sistem (PATH)
where ngrok.exe >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%N in ('where ngrok.exe') do set "NGROK_EXE=%%N"
    echo  [4/5] OK - ngrok ditemukan di sistem
    goto :NGROK_READY
)

REM Cek ngrok di cache
if exist "%NGROK_EXE%" (
    echo  [4/5] OK - ngrok ditemukan di cache
    goto :NGROK_READY
)

REM Download ngrok - tulis ke file PS1 dulu agar tidak ada masalah karakter ^ di batch
echo        ngrok belum ada, mengunduh (~20 MB)...
if not exist "%NGROK_DIR%" mkdir "%NGROK_DIR%"
set "DL_SCRIPT=%TEMP%\acc_dl_ngrok.ps1"
echo [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12 > "%DL_SCRIPT%"
echo Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile '%NGROK_ZIP%' -UseBasicParsing >> "%DL_SCRIPT%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%DL_SCRIPT%"
del "%DL_SCRIPT%" >nul 2>&1
if not exist "%NGROK_ZIP%" (
    echo        [X] Gagal download ngrok. Cek koneksi internet.
    echo.
    echo        Download manual: https://ngrok.com/download
    echo        Ekstrak ngrok.exe ke: %NGROK_DIR%\
    echo.
    goto :NO_NGROK
)
powershell -NoProfile -Command "Expand-Archive -Path '%NGROK_ZIP%' -DestinationPath '%NGROK_DIR%' -Force"
del "%NGROK_ZIP%" >nul 2>&1
if exist "%NGROK_EXE%" (
    echo  [4/5] OK - ngrok berhasil diunduh
    goto :NGROK_READY
)
:NO_NGROK
echo  [4/5] SKIP - Jalankan ngrok manual di terminal baru
goto :SHOW_MANUAL

REM ── STEP 6: Jalankan ngrok ──────────────────────────────
:NGROK_READY
echo  [5/5] Menjalankan ngrok...
start "ACC-ngrok" /min cmd /c ""%NGROK_EXE%" http %ACC_WEBHOOK_PORT%"

REM Tunggu ngrok siap (max 15 detik)
echo        Menunggu ngrok tunnel...
set /a WAIT=0
set "NGROK_URL="
:WAIT_NGROK
timeout /t 1 /nobreak >nul
for /f "delims=" %%U in ('powershell -NoProfile -Command "try{$t=(Invoke-RestMethod http://localhost:4040/api/tunnels -EA Stop).tunnels;$h=$t|?{$_.proto -eq 'https'}|Select -First 1;if($h){$h.public_url}else{''}}catch{''}"') do set "NGROK_URL=%%U"
if "!NGROK_URL!"=="" (
    set /a WAIT+=1
    if !WAIT! lss 15 goto :WAIT_NGROK
)
if "!NGROK_URL!"=="" (
    echo        [!] Ngrok URL tidak terdeteksi.
    goto :SHOW_MANUAL
)

REM ── HASIL AKHIR ─────────────────────────────────────────
set "WEBHOOK_URL=!NGROK_URL!/webhook/whatsapp"

REM Salin URL ke clipboard
echo !WEBHOOK_URL! | clip

cls
echo.
echo  ============================================
echo    SERVER SIAP DIGUNAKAN
echo  ============================================
echo.
echo  Webhook lokal  : http://127.0.0.1:%ACC_WEBHOOK_PORT%/webhook/whatsapp
echo  URL Publik     : !NGROK_URL!
echo.
echo  ============================================
echo    COPY URL INI KE TWILIO (sudah di clipboard):
echo.
echo    !WEBHOOK_URL!
echo.
echo  ============================================
echo.
echo  LANGKAH TERAKHIR (sekali saja):
echo   1. Buka https://console.twilio.com
echo   2. Messaging - Try it out - Send a WhatsApp message
echo   3. Sandbox settings - When a message comes in:
echo      Paste URL di atas (sudah di clipboard!)
echo   4. Klik Save
echo   5. Kirim /menu ke nomor sandbox Twilio
echo.
echo  ============================================
echo  PERINTAH WHATSAPP:
echo    /menu    - tampilkan semua fitur
echo    /model   - ganti model AI
echo    /skill   - pilih skill
echo    /pdf     - export ke PDF
echo    /reset   - mulai ulang
echo  ============================================
echo.
echo  Server berjalan. Jangan tutup window ini.
echo  Tekan Ctrl+C untuk berhenti.
echo  ============================================
echo.
goto :MONITOR

:SHOW_MANUAL
echo.
echo  ============================================
echo    SERVER BERJALAN - NGROK MANUAL
echo  ============================================
echo.
echo  Webhook berjalan di: http://127.0.0.1:%ACC_WEBHOOK_PORT%
echo.
echo  Jalankan ngrok di terminal baru:
echo    ngrok http %ACC_WEBHOOK_PORT%
echo.
echo  Lalu copy URL ngrok ke Twilio Console.
echo  ============================================
echo.

:MONITOR
REM Tetap tampilkan status setiap 30 detik
:LOOP
timeout /t 30 /nobreak >nul

REM Cek webhook server masih hidup
powershell -NoProfile -Command "try { $r=New-Object Net.Sockets.TcpClient; $r.Connect('127.0.0.1',%ACC_WEBHOOK_PORT%); $r.Close() } catch { Write-Host '[!] Webhook server mati! Restart START.bat' }" 2>nul

REM Update URL ngrok jika berubah (setelah reconnect)
if not "!NGROK_URL!"=="" (
    for /f "delims=" %%U in ('powershell -NoProfile -Command "try{(Invoke-RestMethod http://localhost:4040/api/tunnels -EA Stop).tunnels|?{$_.proto -eq 'https'}|Select -ExpandProperty public_url -First 1}catch{''}"') do (
        if not "%%U"=="" if not "%%U"=="!NGROK_URL!" (
            set "NGROK_URL=%%U"
            set "WEBHOOK_URL=%%U/webhook/whatsapp"
            echo  [UPDATE] URL ngrok berubah: !WEBHOOK_URL!
            echo  !WEBHOOK_URL! | clip
        )
    )
)
goto :LOOP
