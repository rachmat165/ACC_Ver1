@echo off
REM ============================================================
REM  ACC - STOP SEMUA SERVER
REM  Tutup webhook server, tunnel, dan proses terkait
REM ============================================================
echo.
echo  ============================================
echo    MENGHENTIKAN SEMUA SERVER ACC
echo  ============================================
echo.

REM Tutup proses yang pegang port 5000
echo  [*] Menutup webhook server (port 5000)...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%P >nul 2>&1
    echo      Proses PID %%P ditutup
)

REM Tutup window berdasarkan judul
taskkill /F /FI "WINDOWTITLE eq ACC-Webhook*"      >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq ACC-cloudflared*"  >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq ACC-ngrok*"        >nul 2>&1

REM Tutup cloudflared
taskkill /F /IM cloudflared.exe >nul 2>&1
taskkill /F /IM ngrok.exe       >nul 2>&1

echo.
echo  [OK] Semua server ACC sudah dihentikan.
echo.
echo  Untuk menjalankan lagi: double-klik START.bat
echo  ============================================
echo.
pause
