# Network Connectivity Troubleshooting Guide

## Overview

This guide addresses common network connectivity issues in AI-Karen, particularly focusing on the connection problems shown in your browser console logs.

## Common Connection Issues

### Issue: ERR_CONNECTION_REFUSED on Health Checks

**Symptoms:**
```javascript
GET http://localhost:8001/health net::ERR_CONNECTION_REFUSED
```

**Root Causes:**
1. Backend service not running on expected port
2. Port configuration mismatch
3. Service startup order issues
4. Firewall blocking connections

### Diagnostic Steps

#### 1. Check Service Status
```bash
# Check if AI-Karen services are running
docker compose ps

# Check specific port bindings
docker compose port api 8000
docker compose port web-ui 3000

# Check what's listening on ports
ss -ltnp | grep -E ':(8000|8001|3000|8020)'
lsof -i :8000
lsof -i :8001
```

#### 2. Verify Configuration
```bash
# Check environment variables
echo $KAREN_BACKEND_URL
echo $API_BASE_URL
echo $NEXT_PUBLIC_API_URL

# Check docker-compose configuration
grep -A 5 -B 5 "ports:" docker-compose.yml
```

#### 3. Test Direct Connectivity
```bash
# Test API health endpoint
curl -v http://localhost:8000/health
curl -v http://localhost:8000/api/health/summary

# Test copilot endpoint
curl -X POST http://localhost:8000/api/copilot/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{}'
```

## Quick Fixes

### 1. Restart Services
```bash
# Full restart
docker compose down
docker compose up -d

# Wait for services to be ready
sleep 30

# Check health
curl http://localhost:8000/health
```

### 2. Fix Port Configuration

**Update docker-compose.yml:**
```yaml
services:
  api:
    ports:
      - "8000:8000"  # Ensure correct port mapping
    environment:
      - PORT=8000
  
  web-ui:
    ports:
      - "8020:3000"  # Map to port 8020 as expected
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Update Frontend Configuration

**Fix API client configuration:**
```typescript
// ui_launchers/web_ui/src/lib/api-client.ts
const DEFAULT_BASE_URLS = [
  'http://127.0.0.1:8000',  // Primary backend
  'http://localhost:8000',   // Fallback
].filter(Boolean) as string[];
```

**Update environment variables:**
```bash
# In .env file
KAREN_BACKEND_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
API_BASE_URL=http://127.0.0.1:8000
```

## Specific Issue Resolution

### Health Check Port Mismatch

The error shows health checks going to port 8001, but your API is likely on port 8000.

**Fix in frontend code:**
```typescript
// Update health check configuration
const HEALTH_CHECK_ENDPOINTS = [
  'http://localhost:8000/health',  // Correct port
  'http://127.0.0.1:8000/health'   // Alternative
];
```

### Copilot Endpoint Issues

**Verify copilot route is working:**
```bash
# Test copilot start endpoint
curl -X POST http://localhost:8000/api/copilot/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer validated" \
  -d '{
    "session_id": "test-session",
    "model": "local:tinyllama-1.1b"
  }'
```

## Advanced Troubleshooting

### Network Diagnostics Script

Create a diagnostic script to check all connections:

```bash
#!/bin/bash
# network-diagnostics.sh

echo "=== AI-Karen Network Diagnostics ==="

# Check Docker services
echo "1. Docker Services Status:"
docker compose ps

# Check port bindings
echo -e "\n2. Port Bindings:"
ss -ltnp | grep -E ':(8000|8001|3000|8020|5433|6379)'

# Test API endpoints
echo -e "\n3. API Endpoint Tests:"
endpoints=(
  "http://localhost:8000/health"
  "http://localhost:8000/api/health/summary"
  "http://localhost:8000/docs"
)

for endpoint in "${endpoints[@]}"; do
  echo -n "Testing $endpoint: "
  if curl -s -f "$endpoint" > /dev/null; then
    echo "✅ OK"
  else
    echo "❌ FAILED"
  fi
done

# Check environment variables
echo -e "\n4. Environment Configuration:"
echo "KAREN_BACKEND_URL: ${KAREN_BACKEND_URL:-'Not set'}"
echo "API_BASE_URL: ${API_BASE_URL:-'Not set'}"
echo "NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-'Not set'}"

# Check logs for errors
echo -e "\n5. Recent Error Logs:"
docker compose logs api --tail=10 | grep -i error || echo "No recent errors"
```

### Frontend Network Debugging

Add network debugging to your frontend:

```typescript
// ui_launchers/web_ui/src/lib/network-debug.ts
export class NetworkDebugger {
  static async diagnoseConnectivity() {
    const endpoints = [
      'http://localhost:8000/health',
      'http://127.0.0.1:8000/health',
      'http://localhost:8001/health'  // Check if this is misconfigured
    ];

    const results = await Promise.allSettled(
      endpoints.map(async (url) => {
        try {
          const response = await fetch(url, { 
            method: 'GET',
            timeout: 5000 
          });
          return { url, status: response.status, ok: response.ok };
        } catch (error) {
          return { url, error: error.message };
        }
      })
    );

    console.log('Network Connectivity Results:', results);
    return results;
  }
}
```

## Prevention Strategies

### 1. Health Check Configuration

**Proper health check setup:**
```yaml
# docker-compose.yml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 2. Service Dependencies

**Ensure proper startup order:**
```yaml
services:
  api:
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```

### 3. Environment Validation

**Add environment validation:**
```python
# src/ai_karen_engine/config/validation.py
import os
from typing import List

def validate_environment() -> List[str]:
    """Validate required environment variables."""
    errors = []
    
    required_vars = [
        'KAREN_BACKEND_URL',
        'POSTGRES_HOST',
        'REDIS_URL'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    return errors
```

## Monitoring and Alerts

### Set up Connection Monitoring

```bash
# Create monitoring script
cat > monitor-connections.sh << 'EOF'
#!/bin/bash
while true; do
  if ! curl -s -f http://localhost:8000/health > /dev/null; then
    echo "$(date): API health check failed" >> connection-errors.log
    # Send alert (email, Slack, etc.)
  fi
  sleep 60
done
EOF

chmod +x monitor-connections.sh
```

### Browser Console Monitoring

```javascript
// Add to your frontend for automatic error reporting
window.addEventListener('unhandledrejection', (event) => {
  if (event.reason?.message?.includes('ERR_CONNECTION_REFUSED')) {
    console.error('Connection refused detected:', event.reason);
    // Report to monitoring service
  }
});
```

## Recovery Procedures

### Automatic Recovery

```bash
#!/bin/bash
# auto-recovery.sh
echo "Starting AI-Karen recovery procedure..."

# Stop all services
docker compose down

# Clean up networks
docker network prune -f

# Restart services
docker compose up -d

# Wait for services
sleep 60

# Verify health
if curl -s -f http://localhost:8000/health; then
  echo "✅ Recovery successful"
else
  echo "❌ Recovery failed - manual intervention required"
  exit 1
fi
```

This guide should help you resolve the connection issues you're experiencing. The key is ensuring all services are running on the correct ports and that your frontend configuration matches your backend setup.