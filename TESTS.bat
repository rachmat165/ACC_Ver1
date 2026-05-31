@echo off
REM ============================================================
REM  ACC - AGENTIC SELF-TESTING FRAMEWORK
REM  Validasi semua modul sebelum dipakai produksi
REM ============================================================
cd /d "%~dp0"
set "PYEXE=%~dp0.cache\python\python.exe"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
set "PYTHONIOENCODING=utf-8"

if not exist "%PYEXE%" (
    echo [X] Python tidak ditemukan. Jalankan launch.bat dulu.
    pause
    exit /b 1
)

"%PYEXE%" "%~dp0tests\run_all.py"

echo.
pause
