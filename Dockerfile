# ==============================================================================
# InterviewIQ — Hardened Production Containerization
# MBA Digital Transformation AI Assessment & Placement Preparation Platform
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    HOME=/home/appuser

WORKDIR /app

# Install minimal OS dependencies including ffmpeg for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -U pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy application source code (strictly filtered by .dockerignore)
COPY . /app/

# Setup persistent directory structure & unprivileged non-root user (UID 1000)
RUN mkdir -p /app/data/sessions /home/appuser && \
    useradd -u 1000 -r -d /home/appuser -s /bin/bash appuser && \
    chown -R appuser:appuser /app /home/appuser && \
    chmod -R 775 /app/data

USER appuser

# Expose Streamlit application port
EXPOSE 8501

# Container Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Launch InterviewIQ Streamlit Web Application
ENTRYPOINT ["streamlit", "run", "frontend/app.py"]
