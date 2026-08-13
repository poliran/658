# Lottery Prediction System - Multi-stage Docker Build
# Stage 1: Builder - compile dependencies
# Stage 2: Runtime - minimal production image

# ============================================================================
# STAGE 1: Builder
# Purpose: Install dependencies in an isolated layer
# ============================================================================
FROM python:3.12-slim AS builder

LABEL maintainer="Lottery Prediction Team"

# Set build args for potential customization
ARG PIP_NO_CACHE_DIR=1
ARG PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching optimization)
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Verify installation
RUN /opt/venv/bin/python -c "import numpy, pandas, sklearn, xgboost, yaml; print('Dependencies verified')"

# ============================================================================
# STAGE 2: Runtime
# Purpose: Minimal production image with only runtime requirements
# ============================================================================
FROM python:3.12-slim

LABEL maintainer="Lottery Prediction Team" \
      description="Lottery prediction system using ML ensemble" \
      version="1.0.0"

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    LOG_LEVEL=INFO

WORKDIR /app

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code and data
COPY src/ src/
COPY config/ config/
COPY data/ data/
COPY cli.py .
COPY setup.py .

# Create necessary directories with proper permissions
RUN mkdir -p models outputs logs && \
    chmod 755 models outputs logs

# Create non-root user for security
RUN useradd -m -u 1000 -s /sbin/nologin appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check: verify Python and imports work
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; from src.predictor.constants import RiskLevel; sys.exit(0)" || exit 1

# Default command
CMD ["python", "cli.py", "predict"]
