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

# Install Poetry
RUN pip install --no-cache-dir poetry

# -----------------------------
# Runtime stage (default: CPU-only, BLAS off)
# -----------------------------
FROM base AS runtime
ENV CC=/usr/bin/gcc \
    CXX=/usr/bin/g++ \
    CMAKE_ARGS="-DLLAMA_METAL=off -DLLAMA_CUBLAS=off -DLLAMA_BLAS=off"

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry config installer.max-workers 4
RUN poetry config installer.parallel true
# Install dependencies with retries and longer timeout
RUN poetry install --no-interaction --no-ansi --only main --no-root || \
    poetry install --no-interaction --no-ansi --only main --no-root || \
    poetry install --no-interaction --no-ansi --only main --no-root
# Ensure common spaCy model is available in the image to avoid runtime downloads
RUN python -m spacy download en_core_web_sm || true

# -----------------------------
# Runtime-perf stage (OpenBLAS enabled)
# -----------------------------
FROM base AS runtime-perf
RUN apt-get update && apt-get install -y libopenblas-dev && rm -rf /var/lib/apt/lists/*
ENV CC=/usr/bin/gcc \
    CXX=/usr/bin/g++ \
    CMAKE_ARGS="-DLLAMA_METAL=off -DLLAMA_CUBLAS=off -DLLAMA_BLAS=on -DLLAMA_BLAS_VENDOR=OpenBLAS"

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry config installer.max-workers 4
RUN poetry config installer.parallel true
# Install dependencies with retries and longer timeout
RUN poetry install --no-interaction --no-ansi --only main --no-root || \
    poetry install --no-interaction --no-ansi --only main --no-root || \
    poetry install --no-interaction --no-ansi --only main --no-root
# Ensure common spaCy model is available in the image to avoid runtime downloads
RUN python -m spacy download en_core_web_sm || true

# -----------------------------
# Final stage (select by target)
# -----------------------------
FROM ${PROFILE}
WORKDIR /app

# Set PYTHONPATH to include src directory
ENV PYTHONPATH=/app:/app/src:$PYTHONPATH

# Copy application code
COPY . .
RUN pip install -e .

# Make memory service initialization script executable
RUN chmod +x scripts/init_memory_service.py

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

# Health check: simple 200 from /health to avoid false negatives
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Start command with plugin initialization and uvloop/httptools
CMD ["bash", "-c", "python scripts/init_db_schema.py && uvicorn server.app:create_app --factory --host 0.0.0.0 --port 8000 --loop uvloop --http httptools"]
