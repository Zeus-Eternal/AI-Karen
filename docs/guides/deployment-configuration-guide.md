# AI Karen - Deployment Configuration Guide

This guide provides comprehensive instructions for configuring AI Karen's backend endpoint routing across different deployment scenarios. The system uses a centralized configuration approach to ensure consistent API communication between the Web UI and backend services.

## Overview

AI Karen's endpoint configuration system automatically detects the deployment environment and configures appropriate backend URLs. The system supports three primary deployment modes:

- **Local Development**: Backend and UI running on localhost
- **Docker Container**: Services running in Docker containers with container networking
- **External Access**: Services accessible via external IP addresses

## Environment Variables Reference

### Core Backend Configuration

```bash
# Primary backend URL (main API server)
KAREN_BACKEND_URL=http://localhost:8000

# Environment type detection
KAREN_ENVIRONMENT=local                    # Options: local, docker, production
KAREN_NETWORK_MODE=localhost              # Options: localhost, container, external

# Fallback endpoints (comma-separated)
KAREN_FALLBACK_BACKEND_URLS=http://127.0.0.1:8000,http://localhost:8000
```

### Container-Specific Configuration

```bash
# Docker container networking
KAREN_CONTAINER_BACKEND_HOST=api          # Container service name
KAREN_CONTAINER_BACKEND_PORT=8000         # Internal container port
KAREN_CONTAINER_MODE=true                 # Enable container detection

# Docker Compose service names
KAREN_POSTGRES_HOST=postgres              # Database container name
KAREN_REDIS_HOST=redis                    # Redis container name
KAREN_ELASTICSEARCH_HOST=elasticsearch    # Elasticsearch container name
```

### External Access Configuration

```bash
# External IP configuration
KAREN_EXTERNAL_HOST=10.105.235.209        # External server IP
KAREN_EXTERNAL_BACKEND_PORT=8000          # External backend port

# CORS origins for external access
KAREN_CORS_ORIGINS=http://localhost:9002,http://10.105.235.209:9002
```

### Health Check Configuration

```bash
# Health monitoring settings
KAREN_HEALTH_CHECK_ENABLED=true           # Enable periodic health checks
KAREN_HEALTH_CHECK_INTERVAL=30000         # Check interval in milliseconds
KAREN_HEALTH_CHECK_TIMEOUT=5000           # Request timeout in milliseconds
KAREN_HEALTH_CHECK_RETRIES=3              # Number of retry attempts
```

## Deployment Scenarios

### 1. Local Development Setup

**Use Case**: Development environment with backend and Web UI running on localhost.

**Configuration**:

```bash
# .env file
KAREN_BACKEND_URL=http://localhost:8000
KAREN_ENVIRONMENT=local
KAREN_NETWORK_MODE=localhost
KAREN_WEB_UI_URL=http://localhost:9002
KAREN_WEB_UI_PORT=9002

# Database connections (local)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# CORS configuration
KAREN_CORS_ORIGINS=http://localhost:9002,http://127.0.0.1:9002
```

**Setup Steps**:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   cd ui_launchers/web_ui && npm install
   ```

2. Start backend:
   ```bash
   python main.py
   ```

3. Start Web UI:
   ```bash
   cd ui_launchers/web_ui
   npm run dev
   ```

4. Access application:
   - Backend API: http://localhost:8000
   - Web UI: http://localhost:9002
   - API Documentation: http://localhost:8000/docs

**Verification**:
```bash
# Test backend connectivity
curl http://localhost:8000/health

# Test Web UI access
curl http://localhost:9002
```

### 2. Docker Container Deployment

**Use Case**: Full containerized deployment using Docker Compose.

**Configuration**:

```bash
# .env file for Docker
KAREN_BACKEND_URL=http://api:8000          # Use container service name
KAREN_ENVIRONMENT=docker
KAREN_NETWORK_MODE=container
KAREN_CONTAINER_BACKEND_HOST=api
KAREN_CONTAINER_BACKEND_PORT=8000

# Container networking
POSTGRES_HOST=postgres                     # Container service name
POSTGRES_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
ELASTICSEARCH_HOST=elasticsearch
ELASTICSEARCH_PORT=9200

# External access ports
KAREN_WEB_UI_PORT=9002
KAREN_EXTERNAL_BACKEND_PORT=8000

# CORS for container access
KAREN_CORS_ORIGINS=http://localhost:9002,http://127.0.0.1:9002
```

**Docker Compose Configuration**:

```yaml
# docker-compose.yml
services:
  api:
    build: .
    container_name: ai-karen-api
    ports:
      - "8000:8000"
    environment:
      - KAREN_BACKEND_URL=http://api:8000
      - KAREN_ENVIRONMENT=docker
      - KAREN_NETWORK_MODE=container
    depends_on:
      - postgres
      - redis
      - elasticsearch
    networks:
      - ai-karen-net

  web-ui:
    build: ./ui_launchers/web_ui
    container_name: ai-karen-web-ui
    ports:
      - "9002:9002"
    environment:
      - KAREN_BACKEND_URL=http://api:8000
      - KAREN_ENVIRONMENT=docker
    depends_on:
      - api
    networks:
      - ai-karen-net

networks:
  ai-karen-net:
    driver: bridge
```

**Setup Steps**:

1. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with container-specific settings
   ```

2. Build and start services:
   ```bash
   docker-compose up --build -d
   ```

3. Verify services:
   ```bash
   docker-compose ps
   docker-compose logs api
   docker-compose logs web-ui
   ```

4. Access application:
   - Backend API: http://localhost:8000
   - Web UI: http://localhost:9002

**Container Health Checks**:
```bash
# Check container status
docker-compose exec api curl http://localhost:8000/health

# Check inter-container communication
docker-compose exec web-ui curl http://api:8000/health
```

### 3. External IP Access

**Use Case**: Services accessible via external IP addresses (e.g., server deployment, remote access).

**Configuration**:

```bash
# .env file for external access
KAREN_BACKEND_URL=http://10.105.235.209:8000
KAREN_ENVIRONMENT=production
KAREN_NETWORK_MODE=external
KAREN_EXTERNAL_HOST=10.105.235.209
KAREN_EXTERNAL_BACKEND_PORT=8000

# Web UI configuration
KAREN_WEB_UI_URL=http://10.105.235.209:9002
KAREN_WEB_UI_PORT=9002

# CORS configuration for external access
KAREN_CORS_ORIGINS=http://10.105.235.209:9002,http://localhost:9002,http://127.0.0.1:9002

# Fallback endpoints
KAREN_FALLBACK_BACKEND_URLS=http://localhost:8000,http://127.0.0.1:8000
```

**Setup Steps**:

1. Configure firewall rules:
   ```bash
   # Allow backend port
   sudo ufw allow 8000/tcp
   
   # Allow Web UI port
   sudo ufw allow 9002/tcp
   ```

2. Update host configuration:
   ```bash
   # Ensure services bind to all interfaces
   export HOST=0.0.0.0
   ```

3. Start services:
   ```bash
   # Backend with external binding
   python main.py --host 0.0.0.0 --port 8000
   
   # Web UI with external binding
   cd ui_launchers/web_ui
   npm run dev -- --host 0.0.0.0 --port 9002
   ```

4. Access application:
   - Backend API: http://10.105.235.209:8000
   - Web UI: http://10.105.235.209:9002

**Network Verification**:
```bash
# Test external connectivity
curl http://10.105.235.209:8000/health

# Test from different network
curl -H "Origin: http://10.105.235.209:9002" http://10.105.235.209:8000/health
```

### 4. Hybrid Deployment

**Use Case**: Backend in Docker, Web UI on localhost (or vice versa).

**Configuration**:

```bash
# Backend in Docker, Web UI on localhost
KAREN_BACKEND_URL=http://localhost:8000    # Docker port mapping
KAREN_ENVIRONMENT=local
KAREN_NETWORK_MODE=localhost

# Docker backend with port mapping
# docker-compose.yml:
# services:
#   api:
#     ports:
#       - "8000:8000"

# Web UI on localhost
KAREN_WEB_UI_URL=http://localhost:9002
KAREN_WEB_UI_PORT=9002

# CORS for hybrid setup
KAREN_CORS_ORIGINS=http://localhost:9002,http://127.0.0.1:9002
```

**Setup Steps**:

1. Start backend in Docker:
   ```bash
   docker-compose up api -d
   ```

2. Start Web UI locally:
   ```bash
   cd ui_launchers/web_ui
   npm run dev
   ```

3. Verify connectivity:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:9002
   ```

## Configuration Validation

### Automatic Environment Detection

The system automatically detects the deployment environment:

```typescript
// Environment detection logic
const configManager = getConfigManager();
const envInfo = configManager.getEnvironmentInfo();

console.log('Environment:', envInfo.environment);
console.log('Network Mode:', envInfo.networkMode);
console.log('Backend URL:', envInfo.backendUrl);
console.log('Is Docker:', envInfo.isDocker);
console.log('Is External:', envInfo.isExternal);
```

### Manual Configuration Override

You can override automatic detection:

```bash
# Force specific configuration
KAREN_ENVIRONMENT=docker
KAREN_NETWORK_MODE=container
KAREN_BACKEND_URL=http://api:8000
```

### Configuration Testing

Test your configuration:

```bash
# Backend health check
curl -f http://your-backend-url:8000/health

# CORS preflight test
curl -X OPTIONS \
  -H "Origin: http://your-web-ui-url:9002" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  http://your-backend-url:8000/api/auth/login
```

## Common Configuration Patterns

### Development Team Setup

```bash
# .env.development
KAREN_BACKEND_URL=http://localhost:8000
KAREN_ENVIRONMENT=local
KAREN_NETWORK_MODE=localhost
KAREN_HEALTH_CHECK_ENABLED=true
KAREN_HEALTH_CHECK_INTERVAL=10000
DEBUG_LOGGING=true
```

### Staging Environment

```bash
# .env.staging
KAREN_BACKEND_URL=http://staging-api:8000
KAREN_ENVIRONMENT=docker
KAREN_NETWORK_MODE=container
KAREN_HEALTH_CHECK_ENABLED=true
KAREN_HEALTH_CHECK_INTERVAL=30000
KAREN_CORS_ORIGINS=http://staging-ui:9002
```

### Production Environment

```bash
# .env.production
KAREN_BACKEND_URL=https://api.yourdomain.com
KAREN_ENVIRONMENT=production
KAREN_NETWORK_MODE=external
KAREN_HEALTH_CHECK_ENABLED=true
KAREN_HEALTH_CHECK_INTERVAL=60000
KAREN_CORS_ORIGINS=https://app.yourdomain.com
PROD_SECURITY_ENABLED=true
PROD_SSL_ENABLED=true
```

## Security Considerations

### CORS Configuration

Always configure CORS origins appropriately:

```bash
# Development (permissive)
KAREN_CORS_ORIGINS=http://localhost:9002,http://127.0.0.1:9002

# Production (restrictive)
KAREN_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Network Security

- Use HTTPS in production
- Restrict firewall rules to necessary ports
- Use environment-specific secrets
- Enable authentication and authorization

### Container Security

```yaml
# docker-compose.yml security settings
services:
  api:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"
```

## Performance Optimization

### Health Check Tuning

```bash
# High-frequency monitoring (development)
KAREN_HEALTH_CHECK_INTERVAL=5000
KAREN_HEALTH_CHECK_TIMEOUT=2000

# Standard monitoring (production)
KAREN_HEALTH_CHECK_INTERVAL=30000
KAREN_HEALTH_CHECK_TIMEOUT=5000

# Low-frequency monitoring (resource-constrained)
KAREN_HEALTH_CHECK_INTERVAL=60000
KAREN_HEALTH_CHECK_TIMEOUT=10000
```

### Connection Pooling

```bash
# Database connection optimization
POSTGRES_MAX_CONNECTIONS=100
REDIS_MAX_CONNECTIONS=50

# HTTP client optimization
KAREN_HTTP_TIMEOUT=30000
KAREN_HTTP_RETRIES=3
```

## Next Steps

After configuring your deployment:

1. **Test Connectivity**: Verify all endpoints are accessible
2. **Monitor Health**: Check health check endpoints regularly
3. **Review Logs**: Monitor application logs for configuration issues
4. **Update Documentation**: Document your specific configuration
5. **Set Up Monitoring**: Implement proper monitoring and alerting

For troubleshooting common issues, see the [Troubleshooting Guide](./troubleshooting-guide.md).

For developer documentation on the configuration system, see the [Developer Configuration Guide](./developer-configuration-guide.md).