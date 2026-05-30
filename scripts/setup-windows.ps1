# Setup manual (Windows) - opsional, launch.bat sudah otomatis
Set-Location "$PSScriptRoot\.."
python -m venv .venv
.\.venv\Scripts\pip.exe install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
if (-not (Test-Path "data\.env")) { Copy-Item "data\.env.example" "data\.env" }
Write-Host "Setup selesai. Jalankan .\launch.bat"
