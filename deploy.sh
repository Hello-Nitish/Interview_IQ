#!/usr/bin/env bash
# ==============================================================================
# InterviewIQ — Docker Deployment Automation Script (POSIX)
# ==============================================================================

set -e

echo "[InterviewIQ] Initializing production deployment..."

# Pre-flight: Ensure persistent data directory exists with write permissions
mkdir -p data/sessions
chmod -R 775 data 2>/dev/null || true

# Pre-flight: Detect Docker Compose command syntax
if command -v docker &>/dev/null && docker compose version &>/dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "[ERROR] Neither 'docker compose' nor 'docker-compose' found on system."
    echo "Please install Docker Desktop or Docker Engine CE."
    exit 1
fi

echo "[InterviewIQ] Using Compose engine: $COMPOSE_CMD"
echo "[InterviewIQ] Building and launching container..."
$COMPOSE_CMD up -d --build

echo ""
echo "=============================================================================="
echo "[InterviewIQ] Successfully deployed in Docker!"
echo "Access the application at: http://localhost:8501"
echo "View logs with: $COMPOSE_CMD logs -f"
echo "Stop container with: $COMPOSE_CMD down"
echo "=============================================================================="
