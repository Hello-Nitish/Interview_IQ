@echo off
REM ==============================================================================
REM InterviewIQ — Docker Deployment Automation Script (Windows)
REM ==============================================================================

echo [InterviewIQ] Initializing production deployment...

REM Pre-flight: Ensure persistent data directory exists
if not exist "data\sessions" (
    mkdir "data\sessions"
)

REM Pre-flight: Detect Docker Compose command
docker compose version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set COMPOSE_CMD=docker compose
) else (
    set COMPOSE_CMD=docker-compose
)

echo [InterviewIQ] Using Compose engine: %COMPOSE_CMD%
echo [InterviewIQ] Building and starting Docker container...
%COMPOSE_CMD% up -d --build

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Docker build or start failed. Please ensure Docker Desktop is running.
    exit /b %ERRORLEVEL%
)

echo.
echo ==============================================================================
echo [InterviewIQ] Successfully deployed in Docker!
echo Access the application at: http://localhost:8501
echo View logs with: %COMPOSE_CMD% logs -f
echo Stop container with: %COMPOSE_CMD% down
echo ==============================================================================
