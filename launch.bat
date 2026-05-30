@echo off
REM ============================================================
REM  ARUNIKA COMMAND CENTRE - USB PORTABLE Launcher (Windows)
REM  PT. Arunika Teknologi Global
REM
REM  Mode portable: Python + pip + semua dependensi dipasang
REM  di dalam folder USB (.cache\python\). Tidak menyentuh host.
REM  Bisa dijalankan dari drive USB mana pun (E:\, F:\, dll).
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "ACC_HOME=%~dp0"
set "PYVER=3.12.7"
set "PYDIR=%ACC_HOME%.cache\python"
set "PYEXE=%PYDIR%\python.exe"
set "PIPCACHE=%ACC_HOME%.cache\pip"
set "PYTHONUSERBASE=%ACC_HOME%.cache\pyuser"

REM Penting: simpan cache & user dir di USB, jangan di profile host
set "PIP_CACHE_DIR=%PIPCACHE%"
set "PYTHONDONTWRITEBYTECODE=1"

echo ============================================
echo   ARUNIKA COMMAND CENTRE - USB PORTABLE
echo   PT. Arunika Teknologi Global
echo   Drive: %~d0
echo ============================================
echo.

REM ---------- 1. Cek Python portable di USB ----------
if exist "%PYEXE%" (
  "%PYEXE%" -c "import sys" >nul 2>nul && (
    echo [OK] Python portable ditemukan di USB.
    goto :PYREADY
  )
)

REM ---------- 2. Belum ada: unduh Python embeddable & pasang di USB ----------
echo [*] Python portable belum ada di USB. Memasang sekarang...
echo     Lokasi: %PYDIR%
echo     Ukuran ^~ 25 MB, sekali unduh.
echo.

set "ARCH=amd64"
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "ARCH=arm64"
set "PYZIP=%TEMP%\python-embed-%PYVER%-%ARCH%.zip"
set "PYURL=https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-embed-%ARCH%.zip"

if not exist "%PYDIR%" mkdir "%PYDIR%"
if not exist "%PIPCACHE%" mkdir "%PIPCACHE%"

echo [*] Mengunduh Python embeddable...
echo     %PYURL%
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYURL%' -OutFile '%PYZIP%' -UseBasicParsing; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }"
if errorlevel 1 (
  call :FATAL "Gagal mengunduh Python embeddable. Cek koneksi internet & coba lagi."
  goto :END
)

echo [*] Mengekstrak ke %PYDIR%...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Expand-Archive -Path '%PYZIP%' -DestinationPath '%PYDIR%' -Force; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }"
if errorlevel 1 (
  call :FATAL "Gagal ekstrak ZIP. Pastikan PowerShell tersedia & USB writable."
  goto :END
)
del "%PYZIP%" >nul 2>nul

echo [*] Mengaktifkan site-packages di Python portable...
REM Cari file ._pth (nama tergantung versi, mis. python312._pth)
for %%F in ("%PYDIR%\python*._pth") do (
  echo python312.zip > "%%F.new"
  echo .            >> "%%F.new"
  echo Lib\site-packages >> "%%F.new"
  echo import site  >> "%%F.new"
  move /y "%%F.new" "%%F" >nul
)

echo [*] Memasang pip ke Python portable...
set "GETPIP=%TEMP%\get-pip.py"
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%GETPIP%' -UseBasicParsing; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  call :FATAL "Gagal mengunduh get-pip.py."
  goto :END
)
"%PYEXE%" "%GETPIP%" --no-warn-script-location
del "%GETPIP%" >nul 2>nul

"%PYEXE%" -m pip --version >nul 2>nul
if errorlevel 1 (
  call :FATAL "pip gagal terpasang ke Python portable."
  goto :END
)
echo [OK] Python + pip portable berhasil dipasang di USB.
echo.

:PYREADY
echo [OK] Menggunakan Python: %PYEXE%
"%PYEXE%" --version
echo.

REM ---------- 3. Pasang dependensi (ke Python portable, BUKAN venv) ----------
echo [*] Memastikan dependensi terpasang di USB...
"%PYEXE%" -m pip install --no-warn-script-location --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
  echo [!] Sebagian dependensi gagal. Cek koneksi/log di atas.
)
echo.

REM ---------- 4. Siapkan .env ----------
if not exist "data\.env" (
  copy "data\.env.example" "data\.env" >nul
  echo [!] data\.env dibuat. Isi API key Anda sebelum chat.
)

REM ---------- 5. Setup Profil Lembaga (jika belum ada) ----------
if not exist "data\profile.yaml" (
  echo.
  echo [?] Setup Profil Lembaga sekarang? (recommended - sekali isi untuk semua dokumen)
  set /p PROF_ANS="    (y/n, default y) > "
  if /i not "!PROF_ANS!"=="n" (
    echo.
    "%PYEXE%" src\setup_profile.py
    echo.
    pause
  )
)

REM ---------- 6. Setup WhatsApp (opsional) ----------
echo.
echo [?] Setup WhatsApp API sekarang? (recommended)
set /p WA_ANS="    (y/n, default n) > "
if /i "%WA_ANS%"=="y" (
  echo.
  "%PYEXE%" src\setup_whatsapp.py
  echo.
  pause
)

REM ---------- 6. Jalankan aplikasi ----------
echo.
echo [OK] Semua siap. Menjalankan ACC dari USB...
echo.
"%PYEXE%" src\acc.py menu

goto :END

REM ============================================================
:FATAL
echo.
echo ============================================
echo  [X] ERROR
echo ============================================
echo  %~1
echo ============================================
exit /b 1

:END
echo.
echo Tekan tombol apa saja untuk menutup jendela ini...
pause >nul
endlocal
