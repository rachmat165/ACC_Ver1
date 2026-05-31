# ============================================================
# ACC WhatsApp Webhook Server - PowerShell Startup Script
# PT. Arunika Teknologi Global
# ============================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AccHome = Split-Path -Parent $ScriptDir

Write-Host ""
Write-Host " ============================================" -ForegroundColor Cyan
Write-Host "   ARUNIKA COMMAND CENTRE" -ForegroundColor Cyan
Write-Host "   WhatsApp Webhook Server" -ForegroundColor Cyan
Write-Host " ============================================" -ForegroundColor Cyan
Write-Host ""

# Cari Python
$PythonExe = Join-Path $AccHome ".cache\python\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

# Set environment
$env:ACC_HOME = $AccHome
$env:PYTHONPATH = "$AccHome\src;$env:PYTHONPATH"

# Cek Flask
$flaskCheck = & $PythonExe -c "import flask" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host " [!] Flask belum terpasang. Memasang..." -ForegroundColor Yellow
    & $PythonExe -m pip install flask fpdf2 --quiet
}

Write-Host " [OK] Menjalankan webhook server di port 5000..." -ForegroundColor Green
Write-Host ""
Write-Host " Setelah server berjalan:" -ForegroundColor White
Write-Host "   - Buka terminal baru, jalankan: ngrok http 5000" -ForegroundColor Gray
Write-Host "   - Set URL ngrok di Twilio Console sebagai Webhook" -ForegroundColor Gray
Write-Host ""

& $PythonExe "$AccHome\src\webhook_server.py"
