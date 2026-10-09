<#
    Install-OpeningCandle.ps1
    Copies OpeningCandle_EA.mq5 into every MetaTrader 5 on this PC and compiles it.
    Also updates the lab app (lab_app.py and the EA log setting) if the ywo-lab folder is found.
    Portable MetaTrader? Run:  .\Install-OpeningCandle.ps1 -DataFolder "C:\path\to\MT5"
#>
param([string]$DataFolder = '')
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$ea = Join-Path $here 'OpeningCandle_EA.mq5'
if (-not (Test-Path -LiteralPath $ea)) { Write-Host "OpeningCandle_EA.mq5 is missing next to this script." -ForegroundColor Red; exit 1 }

function Read-TextFile([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { return '' }
    $bytes = [System.IO.File]::ReadAllBytes($path)
    if ($bytes.Length -ge 2 -and ($bytes[1] -eq 0 -or ($bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE))) { return [System.Text.Encoding]::Unicode.GetString($bytes) }
    return [System.Text.Encoding]::UTF8.GetString($bytes)
}
function Install-One([string]$editor, [string]$source, [string]$folder) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    $dest = Join-Path $folder (Split-Path -Leaf $source)
    Copy-Item -LiteralPath $source -Destination $dest -Force
    $file = Split-Path -Leaf $dest
    Write-Host "   copied $file"
    if (-not $editor) { Write-Host "   MetaEditor not found. Open $file in MetaEditor and press F7." -ForegroundColor Yellow; return $false }
    $log = Join-Path $env:TEMP 'OpeningCandle_compile.log'
    Remove-Item -LiteralPath $log -ErrorAction SilentlyContinue
    $exPath = [System.IO.Path]::ChangeExtension($dest, '.ex5')
    $started = Get-Date
    Start-Process -FilePath $editor -ArgumentList "/compile:`"$dest`" /log:`"$log`"" -Wait -WindowStyle Hidden
    $text = Read-TextFile $log
    $lines = $text -split "`r?`n"
    $errors = @($lines | Where-Object { $_ -match ':\s*error\s' })
    $result = $lines | Where-Object { $_ -match '^\s*result' } | Select-Object -Last 1
    $built = (Test-Path -LiteralPath $exPath) -and ((Get-Item -LiteralPath $exPath).LastWriteTime -ge $started.AddSeconds(-5))
    if ($built -and $errors.Count -eq 0) { Write-Host "   $file compiled OK   $result" -ForegroundColor Green; return $true }
    if ($text -eq '') { Write-Host "   $file : MetaEditor wrote no log. Close MetaEditor if it is open and run this again." -ForegroundColor Yellow; return $false }
    Write-Host "   $file compile FAILED. Copy these lines and paste them to Claude:" -ForegroundColor Red
    if ($errors.Count -gt 0) { foreach ($e in $errors) { Write-Host "   $e" } } else { Write-Host $text }
    return $false
}

# 1) MetaTrader 5 data folders
$folders = New-Object System.Collections.Generic.List[string]
if ($DataFolder -ne '') { $folders.Add((Resolve-Path -LiteralPath $DataFolder).Path) }
$root = Join-Path $env:APPDATA 'MetaQuotes\Terminal'
if (Test-Path -LiteralPath $root) {
    foreach ($d in Get-ChildItem -LiteralPath $root -Directory) {
        if (Test-Path -LiteralPath (Join-Path $d.FullName 'MQL5')) { $folders.Add($d.FullName) }
    }
}
if ($folders.Count -eq 0) { Write-Host "No MetaTrader 5 data folder found under $root. Open MT5 once, then run this again." -ForegroundColor Red; exit 1 }

$ok = 0
foreach ($dir in $folders) {
    try {
        $installDir = $dir
        $origin = Join-Path $dir 'origin.txt'
        if (Test-Path -LiteralPath $origin) { $installDir = ((Read-TextFile $origin) -replace '[\uFEFF\x00\r\n\t]', '').Trim() }
        Write-Host ""; Write-Host "== $(Split-Path -Leaf $installDir)" -ForegroundColor Cyan
        $editor = $null
        foreach ($exe in @('MetaEditor64.exe', 'metaeditor.exe')) { $p = Join-Path $installDir $exe; if (Test-Path -LiteralPath $p) { $editor = $p; break } }
        if (Install-One $editor $ea (Join-Path $dir 'MQL5\Experts')) { $ok++ }
    } catch { Write-Host "   failed: $($_.Exception.Message)" -ForegroundColor Red }
}

# 2) update the lab app so its report reads this EA's trade log
Write-Host ""; Write-Host "== lab app" -ForegroundColor Cyan
$labDirs = @()
foreach ($r in @('C:\ywo-lab', 'C:\Shen\28Aug2022\Trading', (Join-Path $env:USERPROFILE 'Downloads'))) {
    if (Test-Path -LiteralPath $r) {
        $labDirs += Get-ChildItem -LiteralPath $r -Recurse -Depth 3 -Filter 'lab_app.py' -ErrorAction SilentlyContinue | ForEach-Object { $_.DirectoryName }
    }
}
$labDirs = $labDirs | Select-Object -Unique
if ($labDirs.Count -eq 0) { Write-Host "   lab app not found; its report will not show live trades until lab_app.py is updated." -ForegroundColor Yellow }
foreach ($ld in $labDirs) {
    Copy-Item -LiteralPath (Join-Path $here 'lab_app.py') -Destination (Join-Path $ld 'lab_app.py') -Force
    $cfgPath = Join-Path $ld 'config.json'
    if (Test-Path -LiteralPath $cfgPath) {
        $cfg = Get-Content -LiteralPath $cfgPath -Raw | ConvertFrom-Json
        $cfg.ea_log = 'common:OpeningCandle_trades.csv'
        $cfg | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $cfgPath -Encoding UTF8
    }
    Write-Host "   updated $ld" -ForegroundColor Green
}

Write-Host ""
if ($ok -gt 0) {
    Write-Host "Done: EA compiled in $ok terminal(s)." -ForegroundColor Green
    Write-Host "In MT5: Navigator > Expert Advisors > right-click > Refresh. Then drag OpeningCandle_EA onto a TSLA chart and onto a US100.cash chart."
} else {
    Write-Host "Nothing compiled. Copy the messages above and paste them to Claude." -ForegroundColor Yellow
}
Read-Host "Press Enter to close"
