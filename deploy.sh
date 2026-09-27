#!/usr/bin/env bash
# ==============================================================================
# InterviewIQ — Docker Deployment Automation Script (POSIX)
# ==============================================================================

set -e

echo "[InterviewIQ] Building and launching Docker container..."
docker-compose up -d --build

echo ""
echo "=============================================================================="
echo "[InterviewIQ] Successfully deployed in Docker!"
echo "Access the application at: http://localhost:8501"
echo "View logs with: docker-compose logs -f"
echo "Stop container with: docker-compose down"
echo "=============================================================================="
