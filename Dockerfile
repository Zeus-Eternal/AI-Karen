FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/models /app/logs /app/backups /app/certs

# Set up model orchestrator plugin
RUN mkdir -p /app/plugin_marketplace/ai/model-orchestrator
COPY plugin_marketplace/ai/model-orchestrator/ /app/plugin_marketplace/ai/model-orchestrator/

# Copy configuration files
COPY config/ /app/config/

# Set environment variables for plugin configuration
ENV PLUGIN_DIR="/app/plugin_marketplace"
ENV MODELS_ROOT="/app/models"
ENV CONFIG_PATH="/app/config"

# Expose ports
EXPOSE 8000 9090

# Health check with model orchestrator support
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health | grep -q '"status":"healthy"' || exit 1

# Start command with plugin initialization
CMD ["bash", "-c", "python scripts/init_db_schema.py && uvicorn main:create_app --factory --host 0.0.0.0 --port 8000"]
