# ============================================================
#  ARUNIKA COMMAND CENTRE - ONE-CLICK LAUNCHER
#  PT. Arunika Teknologi Global
#
#  Jalankan dengan double-klik START.bat
#  Urutan otomatis:
#    [1] Cek / install Python portable
#    [2] Pasang semua dependensi
#    [3] Jalankan Webhook Server (port 5000)
#    [4] Jalankan ngrok (ekspos port 5000)
#    [5] Tampilkan URL ngrok -> tempel ke Twilio Console
# ============================================================
$host.UI.RawUI.WindowTitle = "ACC Launcher - PT. Arunika Teknologi Global"

# ─── Konstanta ───────────────────────────────────────────────
$ACC_HOME   = Split-Path -Parent $MyInvocation.MyCommand.Path
$PYDIR      = Join-Path $ACC_HOME ".cache\python"
$PYEXE      = Join-Path $PYDIR "python.exe"
$PIPCACHE   = Join-Path $ACC_HOME ".cache\pip"
$PYVER      = "3.12.7"
$PYARCH     = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "arm64" } else { "amd64" }
$PYURL      = "https://www.python.org/ftp/python/$PYVER/python-$PYVER-embed-$PYARCH.zip"
$WEBHOOK_PORT = 5000
$NGROK_API  = "http://localhost:4040/api/tunnels"

# ─── Warna & UI ──────────────────────────────────────────────
$C_HEADER = "Cyan"
$C_OK     = "Green"
$C_WARN   = "Yellow"
$C_ERR    = "Red"
$C_DIM    = "DarkGray"
$C_WHITE  = "White"
$C_ACCENT = "Magenta"

function Write-Header {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor $C_HEADER
    Write-Host "  ║   ARUNIKA COMMAND CENTRE  —  ACC Ver.1           ║" -ForegroundColor $C_HEADER
    Write-Host "  ║   PT. Arunika Teknologi Global                   ║" -ForegroundColor $C_HEADER
    Write-Host "  ║   One-Click WhatsApp AI Server Launcher          ║" -ForegroundColor $C_HEADER
    Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor $C_HEADER
    Write-Host ""
}

# Error handler global
$ErrorActionPreference = "Stop"
$PSDefaultParameterValues['*:ErrorAction'] = 'Stop'

trap {
    Write-Host ""
    Write-Host "  [ERROR] $_" -ForegroundColor $C_ERR
    Write-Host "  Stack trace:" -ForegroundColor $C_ERR
    Write-Host $_.ScriptStackTrace -ForegroundColor $C_DIM
    exit 1
}

function Write-Step {
    param([int]$Num, [string]$Total, [string]$Label, [string]$Status = "...")
    $icon = switch ($Status) {
        "done"    { "✔" }
        "fail"    { "✘" }
        "skip"    { "─" }
        default   { "►" }
    }
    $color = switch ($Status) {
        "done" { $C_OK }
        "fail" { $C_ERR }
        "skip" { $C_DIM }
        default { $C_WHITE }
    }
    Write-Host "  [$Num/$Total] $icon  $Label" -ForegroundColor $color
}

function Write-Progress-Bar {
    param([int]$Pct, [string]$Label = "", [int]$Width = 40)
    $filled = [int]($Pct / 100 * $Width)
    $empty  = $Width - $filled
    $bar    = ("█" * $filled) + ("░" * $empty)
    Write-Host -NoNewline "`r  $bar $Pct%  $Label   " -ForegroundColor $C_ACCENT
    if ($Pct -ge 100) { Write-Host "" }
}

function Write-Spin {
    param([string]$Label, [int]$Seconds = 1)
    $frames = "⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"
    $end = (Get-Date).AddSeconds($Seconds)
    $i = 0
    while ((Get-Date) -lt $end) {
        Write-Host -NoNewline "`r  $($frames[$i % $frames.Count])  $Label   " -ForegroundColor $C_ACCENT
        Start-Sleep -Milliseconds 100
        $i++
    }
    Write-Host ""
}

function Test-Port {
    param([int]$Port)
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $conn = $tcp.BeginConnect("127.0.0.1", $Port, $null, $null)
        $ok = $conn.AsyncWaitHandle.WaitOne(500, $false)
        $tcp.Close()
        return $ok
    } catch { return $false }
}

function Get-NgrokUrl {
    try {
        $resp = Invoke-RestMethod -Uri $NGROK_API -TimeoutSec 3 -ErrorAction Stop
        $https = $resp.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1
        if ($https) { return $https.public_url }
        $any = $resp.tunnels | Select-Object -First 1
        return $any.public_url
    } catch { return $null }
}

function Get-PythonExe {
    if (Test-Path $PYEXE) {
        $ok = & $PYEXE -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { return $PYEXE }
    }
    $sys = Get-Command python -ErrorAction SilentlyContinue
    if ($sys) { return $sys.Source }
    return $null
}

# ════════════════════════════════════════════════════════════════
Write-Header

# ─── LANGKAH 1: Python ───────────────────────────────────────
Write-Host "  ┌─ PERSIAPAN SISTEM ─────────────────────────────────┐" -ForegroundColor $C_DIM
$pyExe = Get-PythonExe
if ($pyExe) {
    $pyVer = & $pyExe --version 2>&1
    Write-Step 1 5 "Python  ─  $pyVer" "done"
} else {
    Write-Step 1 5 "Python portable belum ada. Mengunduh..." "..."

    Write-Host ""
    $PYZIP = "$env:TEMP\python-embed-$PYVER-$PYARCH.zip"
    New-Item -ItemType Directory -Force -Path $PYDIR | Out-Null
    New-Item -ItemType Directory -Force -Path $PIPCACHE | Out-Null

    # Download Python embeddable dengan progress
    Write-Host "  Mengunduh Python $PYVER ($PYARCH) ~25 MB..." -ForegroundColor $C_DIM
    try {
        $wc = New-Object System.Net.WebClient
        $wc.DownloadProgressChanged += {
            Write-Progress-Bar -Pct $_.ProgressPercentage -Label "python-embed.zip"
        }
        $task = $wc.DownloadFileTaskAsync($PYURL, $PYZIP)
        while (-not $task.IsCompleted) { Start-Sleep -Milliseconds 200 }
        Write-Progress-Bar 100 "Selesai"
    } catch {
        Write-Host "  [!] Gagal download: $_" -ForegroundColor $C_ERR
        Write-Host "  Cek koneksi internet lalu jalankan ulang." -ForegroundColor $C_WARN
        pause; exit 1
    }

    # Extract
    Write-Host "  Mengekstrak..." -ForegroundColor $C_DIM
    Expand-Archive -Path $PYZIP -DestinationPath $PYDIR -Force
    Remove-Item $PYZIP -Force

    # Aktifkan site-packages
    Get-ChildItem "$PYDIR\python*._pth" | ForEach-Object {
        "python312.zip`n.`nLib\site-packages`nimport site" | Set-Content $_.FullName -Encoding utf8
    }

    # Pasang pip
    Write-Host "  Memasang pip..." -ForegroundColor $C_DIM
    $getPip = "$env:TEMP\get-pip.py"
    Invoke-WebRequest "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip -UseBasicParsing
    & $PYDIR\python.exe $getPip --no-warn-script-location -q
    Remove-Item $getPip -Force

    $pyExe = $PYEXE
    $pyVer = & $pyExe --version 2>&1
    Write-Step 1 5 "Python terpasang  ─  $pyVer" "done"
}

# ─── LANGKAH 2: Dependensi ───────────────────────────────────
Write-Step 2 5 "Memeriksa dependensi Python..." "..."
$env:PIP_CACHE_DIR   = $PIPCACHE
$env:PYTHONDONTWRITEBYTECODE = "1"

# Cek apakah flask & fpdf2 sudah ada
$flaskOk = & $pyExe -c "import flask, fpdf, anthropic, twilio" 2>$null; $allOk = ($LASTEXITCODE -eq 0)

if ($allOk) {
    Write-Step 2 5 "Dependensi sudah lengkap" "done"
} else {
    Write-Host ""
    $reqFile = Join-Path $ACC_HOME "requirements.txt"
    $packages = Get-Content $reqFile | Where-Object { $_ -and -not $_.StartsWith("#") }
    $total = $packages.Count
    $i = 0
    foreach ($pkg in $packages) {
        $i++
        $pct = [int]($i / $total * 100)
        Write-Progress-Bar -Pct $pct -Label $pkg
        & $pyExe -m pip install $pkg --no-warn-script-location --disable-pip-version-check -q 2>$null
    }
    Write-Step 2 5 "Dependensi terpasang ($total paket)" "done"
}

# ─── LANGKAH 3: Siapkan .env ─────────────────────────────────
$envFile = Join-Path $ACC_HOME "data\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $ACC_HOME "data\.env.example") $envFile
    Write-Step 3 5 "data\.env dibuat dari template  ─  isi API key Anda!" "skip"
} else {
    Write-Step 3 5 "Konfigurasi .env ditemukan" "done"
}

# ─── LANGKAH 4: Webhook Server ───────────────────────────────
Write-Host ""
Write-Host "  ┌─ MENJALANKAN SERVER ───────────────────────────────┐" -ForegroundColor $C_DIM

if (Test-Port $WEBHOOK_PORT) {
    Write-Step 4 5 "Webhook server sudah berjalan di port $WEBHOOK_PORT" "done"
} else {
    Write-Step 4 5 "Menjalankan Webhook Server (port $WEBHOOK_PORT)..." "..."
    $webhookScript = Join-Path $ACC_HOME "src\webhook_server.py"
    $env:ACC_HOME   = $ACC_HOME
    $env:PYTHONPATH = "$ACC_HOME\src;$env:PYTHONPATH"

    Start-Process -WindowStyle Minimized -FilePath $pyExe `
        -ArgumentList "`"$webhookScript`"" `
        -WorkingDirectory $ACC_HOME

    # Tunggu server ready
    $waited = 0
    while (-not (Test-Port $WEBHOOK_PORT) -and $waited -lt 15) {
        Write-Progress-Bar -Pct ([int]($waited / 15 * 100)) -Label "menunggu server siap..."
        Start-Sleep -Milliseconds 500
        $waited++
    }
    if (Test-Port $WEBHOOK_PORT) {
        Write-Progress-Bar 100 "Server siap"
        Write-Step 4 5 "Webhook Server aktif  ─  http://127.0.0.1:$WEBHOOK_PORT" "done"
    } else {
        Write-Step 4 5 "Server lambat start, periksa window server" "skip"
    }
}

# ─── LANGKAH 5: Ngrok ────────────────────────────────────────
Write-Step 5 5 "Memeriksa ngrok..." "..."
$ngrokExe = Get-Command ngrok -ErrorAction SilentlyContinue
$ngrokLocal = Get-ChildItem "$ACC_HOME\.cache", "$ACC_HOME", "C:\ngrok", "$env:USERPROFILE\Downloads" `
    -Filter "ngrok.exe" -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $ngrokExe -and $ngrokLocal) {
    $ngrokExe = $ngrokLocal
}

$ngrokUrl = Get-NgrokUrl
if ($ngrokUrl) {
    Write-Step 5 5 "Ngrok sudah berjalan" "done"
} elseif ($ngrokExe) {
    Start-Process -WindowStyle Minimized -FilePath $ngrokExe.Source `
        -ArgumentList "http $WEBHOOK_PORT" -WorkingDirectory $ACC_HOME

    Write-Host ""
    $waited = 0
    while (-not $ngrokUrl -and $waited -lt 20) {
        Write-Progress-Bar -Pct ([int]($waited / 20 * 100)) -Label "menunggu ngrok tunnel..."
        Start-Sleep -Milliseconds 500
        $waited++
        $ngrokUrl = Get-NgrokUrl
    }
    Write-Progress-Bar 100 "Ngrok terhubung"
    if ($ngrokUrl) {
        Write-Step 5 5 "Ngrok aktif" "done"
    } else {
        Write-Step 5 5 "Ngrok tidak merespons, jalankan manual" "skip"
    }
} else {
    Write-Host ""
    Write-Host "  [!] ngrok tidak ditemukan." -ForegroundColor $C_WARN
    Write-Host "      Download: https://ngrok.com/download" -ForegroundColor $C_DIM
    Write-Host "      Ekstrak ngrok.exe ke folder ini lalu jalankan ulang." -ForegroundColor $C_DIM
    Write-Step 5 5 "ngrok tidak ada  ─  jalankan manual" "skip"
}

# ════════════════════════════════════════════════════════════════
#  STATUS AKHIR
# ════════════════════════════════════════════════════════════════
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor $C_OK
Write-Host "  ║              SERVER SIAP DIGUNAKAN               ║" -ForegroundColor $C_OK
Write-Host "  ╠══════════════════════════════════════════════════╣" -ForegroundColor $C_OK

Write-Host "  ║  Webhook lokal  : " -NoNewline -ForegroundColor $C_OK
Write-Host "http://127.0.0.1:$WEBHOOK_PORT/webhook/whatsapp" -NoNewline -ForegroundColor $C_WHITE
Write-Host "  ║" -ForegroundColor $C_OK

if ($ngrokUrl) {
    $webhookPublic = "$ngrokUrl/webhook/whatsapp"
    Write-Host "  ║  URL Publik     : " -NoNewline -ForegroundColor $C_OK
    Write-Host $webhookPublic -NoNewline -ForegroundColor "Cyan"
    Write-Host "" -ForegroundColor $C_OK
    Write-Host "  ╠══════════════════════════════════════════════════╣" -ForegroundColor $C_OK
    Write-Host "  ║  LANGKAH TERAKHIR (1x setup, tersimpan):         ║" -ForegroundColor $C_WARN
    Write-Host "  ║  1. Buka https://console.twilio.com              ║" -ForegroundColor $C_WHITE
    Write-Host "  ║  2. Messaging -> Try it out -> WhatsApp          ║" -ForegroundColor $C_WHITE
    Write-Host "  ║  3. Sandbox settings -> isi Webhook URL:         ║" -ForegroundColor $C_WHITE
    Write-Host "  ║     $webhookPublic" -ForegroundColor "Cyan"
    Write-Host "  ║  4. Kirim pesan WhatsApp ke sandbox Twilio!      ║" -ForegroundColor $C_WHITE

    # Salin ke clipboard
    try {
        $webhookPublic | Set-Clipboard
        Write-Host "  ║  [OK] URL sudah disalin ke clipboard!            ║" -ForegroundColor $C_OK
    } catch {}
} else {
    Write-Host "  ║  Ngrok URL      : " -NoNewline -ForegroundColor $C_OK
    Write-Host "(jalankan: ngrok http $WEBHOOK_PORT)" -NoNewline -ForegroundColor $C_WARN
    Write-Host "" -ForegroundColor $C_OK
    Write-Host "  ╠══════════════════════════════════════════════════╣" -ForegroundColor $C_OK
    Write-Host "  ║  Jalankan di terminal baru:                       ║" -ForegroundColor $C_WARN
    Write-Host "  ║     ngrok http $WEBHOOK_PORT                             ║" -ForegroundColor $C_WHITE
    Write-Host "  ║  Lalu tempel URL ke Twilio Sandbox Webhook.       ║" -ForegroundColor $C_WHITE
}

Write-Host "  ╠══════════════════════════════════════════════════╣" -ForegroundColor $C_OK
Write-Host "  ║  Perintah WhatsApp yang tersedia:                 ║" -ForegroundColor $C_DIM
Write-Host "  ║   • Kirim pesan biasa  -> AI membalas otomatis    ║" -ForegroundColor $C_DIM
Write-Host "  ║   • /skill riset       -> aktifkan skill riset     ║" -ForegroundColor $C_DIM
Write-Host "  ║   • /pdf               -> hasil jadi PDF           ║" -ForegroundColor $C_DIM
Write-Host "  ║   • /skills            -> lihat semua skill        ║" -ForegroundColor $C_DIM
Write-Host "  ║   • /reset             -> mulai sesi baru          ║" -ForegroundColor $C_DIM
Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor $C_OK
Write-Host ""

# ─── Monitor log server ──────────────────────────────────────
Write-Host "  Memantau log server (Ctrl+C untuk berhenti)..." -ForegroundColor $C_DIM
Write-Host "  ─────────────────────────────────────────────────────" -ForegroundColor $C_DIM
Write-Host ""

# Keep alive — tampilkan timestamp setiap menit + status
$lastNgrokCheck = Get-Date
while ($true) {
    Start-Sleep -Seconds 30

    # Cek webhook server masih hidup
    $whOk = Test-Port $WEBHOOK_PORT

    # Cek ngrok setiap 2 menit
    $now = Get-Date
    if (($now - $lastNgrokCheck).TotalSeconds -gt 120) {
        $newUrl = Get-NgrokUrl
        if ($newUrl -and $newUrl -ne $ngrokUrl) {
            $ngrokUrl = $newUrl
            Write-Host "  [$(Get-Date -Format 'HH:mm')] URL ngrok berubah: $ngrokUrl/webhook/whatsapp" -ForegroundColor $C_WARN
            try { "$ngrokUrl/webhook/whatsapp" | Set-Clipboard } catch {}
        }
        $lastNgrokCheck = $now
    }

    $whStatus = if ($whOk) { "✔ aktif" } else { "✘ mati!" }
    $whColor  = if ($whOk) { $C_OK } else { $C_ERR }
    $ngStatus = if ($ngrokUrl) { "✔ $ngrokUrl" } else { "─ tidak ada" }
    Write-Host "  [$(Get-Date -Format 'HH:mm')] Webhook: " -NoNewline -ForegroundColor $C_DIM
    Write-Host $whStatus -NoNewline -ForegroundColor $whColor
    Write-Host "  │  Ngrok: $ngStatus" -ForegroundColor $C_DIM
}
