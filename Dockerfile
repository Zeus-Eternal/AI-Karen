ARG PROFILE=runtime

# -----------------------------
# Base build stage (common deps)
# -----------------------------
FROM python:3.11-slim AS base
WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel setuptools scikit-build

# -----------------------------
# Runtime stage (default: CPU-only, BLAS off)
# -----------------------------
FROM base AS runtime
ENV CC=/usr/bin/gcc \
    CXX=/usr/bin/g++ \
    CMAKE_ARGS="-DLLAMA_METAL=off -DLLAMA_CUBLAS=off -DLLAMA_BLAS=off"

ENV PIP_PREFER_BINARY=1 PIP_DEFAULT_TIMEOUT=120
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# -----------------------------
# Runtime-perf stage (OpenBLAS enabled)
# -----------------------------
FROM base AS runtime-perf
RUN apt-get update && apt-get install -y libopenblas-dev && rm -rf /var/lib/apt/lists/*
ENV CC=/usr/bin/gcc \
    CXX=/usr/bin/g++ \
    CMAKE_ARGS="-DLLAMA_METAL=off -DLLAMA_CUBLAS=off -DLLAMA_BLAS=on -DLLAMA_BLAS_VENDOR=OpenBLAS"

ENV PIP_PREFER_BINARY=1 PIP_DEFAULT_TIMEOUT=120
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# -----------------------------
# Final stage (select by target)
# -----------------------------
FROM ${PROFILE}
WORKDIR /app

# Copy application code
COPY . .
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/models /app/logs /app/backups /app/certs

# Set up model orchestrator plugin (if exists)
RUN mkdir -p /app/plugin_marketplace/ai/model-orchestrator

# Copy configuration files
COPY config/ /app/config/

# Set environment variables for plugin configuration
ENV PLUGIN_DIR="/app/plugin_marketplace" \
    MODELS_ROOT="/app/models" \
    CONFIG_PATH="/app/config"

# Expose ports
EXPOSE 8000 9090

# Health check with model orchestrator support
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health | grep -q '"status":"healthy"' || exit 1

# Start command with plugin initialization and uvloop/httptools
CMD ["bash", "-c", "python scripts/init_db_schema.py && uvicorn server.app:create_app --factory --host 0.0.0.0 --port 8000 --loop uvloop --http httptools"]
