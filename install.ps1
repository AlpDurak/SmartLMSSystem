# Smart LMS — Windows PowerShell one-line installer
# Usage: irm https://raw.githubusercontent.com/AlpDurak/SmartLMSSystem/main/install.ps1 | iex
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$REPO_URL   = "https://github.com/AlpDurak/SmartLMSSystem.git"
$INSTALL_DIR = if ($env:SMART_LMS_DIR) { $env:SMART_LMS_DIR } else { "$env:USERPROFILE\.smart-lms-app" }

Write-Host ""
Write-Host "  Smart LMS MCP Installer" -ForegroundColor Cyan
Write-Host ""

# Clone or update
if (Test-Path "$INSTALL_DIR\.git") {
    Write-Host "  Updating existing install at $INSTALL_DIR ..."
    git -C $INSTALL_DIR pull --quiet
} else {
    Write-Host "  Cloning into $INSTALL_DIR ..."
    git clone --quiet $REPO_URL $INSTALL_DIR
}

# Find Python
$py = @("python", "python3", "C:\Python313\python.exe", "C:\Python312\python.exe",
        "C:\Python311\python.exe") |
      Where-Object { try { & $_ --version 2>$null; $true } catch { $false } } |
      Select-Object -First 1

if (-not $py) {
    Write-Host "  ERROR: Python 3.11+ not found. Install it from https://python.org" -ForegroundColor Red
    exit 1
}

& $py "$INSTALL_DIR\install.py" --repo $INSTALL_DIR @args
