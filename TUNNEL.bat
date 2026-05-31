@echo off
cd /d "%~dp0"
set "ACC_HOME=%~dp0"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
set "PYEXE=%~dp0.cache\python\python.exe"

if not exist "%PYEXE%" (
    echo [X] Python tidak ditemukan. Jalankan launch.bat dulu.
    pause
    exit /b 1
)

"%PYEXE%" "src\tunnel.py"
pause
