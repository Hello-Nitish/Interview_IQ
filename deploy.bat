@echo off
REM ==============================================================================
REM InterviewIQ — Docker Deployment Automation Script
REM ==============================================================================

echo [InterviewIQ] Building and starting Docker container...
docker-compose up -d --build

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker build or start failed. Ensure Docker Desktop is running.
    exit /b %ERRORLEVEL%
)

echo.
echo ==============================================================================
echo [InterviewIQ] Successfully deployed in Docker!
echo Access the application at: http://localhost:8501
echo View logs with: docker-compose logs -f
echo Stop container with: docker-compose down
echo ==============================================================================
