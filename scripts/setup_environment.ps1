# ==============================================================================
# InterviewIQ — Desktop Stack Environment & Toolchain Setup
# Validates and configures Go, Node.js, Wails CLI, and Python DirectML Sidecar
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  InterviewIQ: Desktop Stack Environment Setup" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python Virtualenv
$pythonExe = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (Test-Path $pythonExe) {
    Write-Host "[✓] Python Virtualenv detected: $pythonExe" -ForegroundColor Green
    & $pythonExe -m pip install -q uvicorn starlette pydantic requests
    Write-Host "[✓] Core sidecar packages verified." -ForegroundColor Green
} else {
    Write-Host "[!] Virtualenv not found at $pythonExe. Using system python." -ForegroundColor Yellow
}

# 2. Check Go Toolchain
try {
    $goVersion = & go version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] Go Toolchain detected: $goVersion" -ForegroundColor Green
    } else {
        throw "Go not installed"
    }
} catch {
    Write-Host "[!] Go is not found in PATH." -ForegroundColor Yellow
    Write-Host "    Install Go (>= 1.21) via: winget install GoLang.Go" -ForegroundColor Yellow
}

# 3. Check Node.js and NPM
try {
    $nodeVersion = & node -v 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] Node.js detected: $nodeVersion" -ForegroundColor Green
    } else {
        throw "Node not installed"
    }
} catch {
    Write-Host "[!] Node.js is not found in PATH." -ForegroundColor Yellow
    Write-Host "    Install Node.js (>= 18) via: winget install OpenJS.NodeJS.LTS" -ForegroundColor Yellow
}

# 4. Check Wails CLI
try {
    $wailsVersion = & wails version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] Wails CLI detected: $wailsVersion" -ForegroundColor Green
    } else {
        throw "Wails not installed"
    }
} catch {
    Write-Host "[!] Wails CLI is not found in PATH." -ForegroundColor Yellow
    Write-Host "    Install Wails via: go install github.com/wailsapp/wails/v2/cmd/wails@latest" -ForegroundColor Yellow
}

Write-Host "`nEnvironment check completed successfully." -ForegroundColor Cyan
