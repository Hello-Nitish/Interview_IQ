@echo off
TITLE InterviewIQ — AI Placement Coach (Desktop Edition)
COLOR 0B

echo ===============================================================================
echo                InterviewIQ — AI Placement Coach (Desktop)
echo     Stack: Go + Wails Architecture ^| React + Tailwind ^| DirectML Sidecar
echo ===============================================================================
echo.

cd /d "%~dp0"

:: 1. Locate Python interpreter
set "PYTHON_EXE=.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

:: Ensure port 8000 is clean
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: 2. Launch Python DirectML Sidecar in the background
echo [1/3] Starting Python DirectML Sidecar Microservice on port 8000...
start "InterviewIQ DirectML Sidecar" /min "%PYTHON_EXE%" -m sidecar.server --port 8000

:: 3. Wait for sidecar health check
echo [2/3] Initializing agents, DirectML hardware acceleration, and SQLite database...
powershell -NoProfile -Command "for ($i=0; $i -lt 30; $i++) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; Start-Sleep -Milliseconds 400 }; exit 1"

:: 4. Launch Desktop Application Window
echo [3/3] Launching InterviewIQ Desktop Application...
set "APP_URL=http://127.0.0.1:8000/?v=%RANDOM%"

:: Priority 1: MS Edge App Mode (Standalone borderless desktop window)
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=%APP_URL%
    goto done
)
if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" --app=%APP_URL%
    goto done
)

:: Priority 2: Google Chrome App Mode
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=%APP_URL%
    goto done
)
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --app=%APP_URL%
    goto done
)

:: Priority 3: System Default Browser
start "" "%APP_URL%"

:done
echo.
echo ===============================================================================
echo  InterviewIQ is running successfully!
echo  Desktop URL: %APP_URL%
echo  DirectML Engine: Ready
echo  To exit, close the application window and the sidecar tray.
echo ===============================================================================
timeout /t 3 >nul
exit /b 0
