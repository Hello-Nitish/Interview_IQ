@echo off
TITLE InterviewIQ — Native Desktop (Go + Wails + DirectML)
COLOR 0B

echo =====================================================================
echo   InterviewIQ — AI Placement Coach (Desktop Edition)
echo   Stack: Go + Wails v2 + React 18 + Tailwind CSS + Python DirectML
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Verifying Python DirectML Sidecar...
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
) else (
    set "PYTHON_CMD=python"
)

echo [2/3] Starting Python DirectML Sidecar Microservice on port 8000...
start "InterviewIQ DirectML Sidecar" /min "%PYTHON_CMD%" -m sidecar.server --port 8000

echo [3/3] Checking Desktop Frontend...
if exist "frontend\node_modules" (
    echo Starting Wails Desktop App...
    where wails >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        wails dev
    ) else (
        echo [!] Wails CLI not found in PATH. Starting Vite dev server...
        cd frontend && npm run dev
    )
) else (
    echo [!] Frontend dependencies not installed yet.
    echo Please run 'npm install' inside the frontend directory.
    echo Opening browser to http://127.0.0.1:8000/health
    start http://127.0.0.1:8000/health
)

pause
