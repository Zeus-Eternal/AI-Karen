# AI Karen - Endpoint Connectivity Troubleshooting Guide

This guide helps diagnose and resolve common endpoint connectivity issues in AI Karen's backend routing system. Use this guide when experiencing connection problems between the Web UI and backend services.

## Quick Diagnostic Checklist

Before diving into specific issues, run through this quick checklist:

1. **Backend Status**: Is the backend service running?
   ```bash
   curl http://localhost:8000/health
   ```

2. **Web UI Status**: Is the Web UI accessible?
   ```bash
   curl http://localhost:9002
   ```

3. **Network Connectivity**: Can services reach each other?
   ```bash
   # From Web UI container/host
   curl http://backend-host:8000/health
   ```

4. **Configuration Check**: Are environment variables set correctly?
   ```bash
   echo $KAREN_BACKEND_URL
   echo $KAREN_ENVIRONMENT
   echo $KAREN_NETWORK_MODE
   ```

## Common Issues and Solutions

### 1. Connection Refused Errors

**Symptoms**:
- "Connection refused" errors in browser console
- Web UI cannot reach backend API
- Login page fails to load or authenticate

**Error Messages**:
```
Failed to fetch
TypeError: NetworkError when attempting to fetch resource
ERR_CONNECTION_REFUSED
```

**Diagnosis**:
```bash
# Test backend connectivity
curl -v http://localhost:8000/health

# Check if backend is listening on correct port
netstat -tlnp | grep :8000
ss -tlnp | grep :8000

# Check backend process
ps aux | grep python | grep main.py
```

**Solutions**:

1. **Backend Not Running**:
   ```bash
   # Start backend
   python main.py
   
   # Or with specific host/port
   python main.py --host 0.0.0.0 --port 8000
   ```

2. **Wrong Port Configuration**:
   ```bash
   # Check environment variables
   export KAREN_BACKEND_URL=http://localhost:8000
   
   # Update .env file
   echo "KAREN_BACKEND_URL=http://localhost:8000" >> .env
   ```

3. **Host Binding Issues**:
   ```bash
   # Backend binding to localhost only
   # Change to bind to all interfaces
   export HOST=0.0.0.0
   python main.py --host 0.0.0.0
   ```

4. **Docker Container Issues**:
   ```bash
   # Check container status
   docker-compose ps
   
   # Check container logs
   docker-compose logs api
   
   # Restart containers
   docker-compose restart api
   ```

### 2. CORS (Cross-Origin Resource Sharing) Errors

**Symptoms**:
- CORS policy errors in browser console
- Preflight request failures
- Authentication requests blocked

**Error Messages**:
```
Access to fetch at 'http://localhost:8000/api/auth/login' from origin 'http://localhost:9002' has been blocked by CORS policy
CORS preflight request failed
No 'Access-Control-Allow-Origin' header is present
```

**Diagnosis**:
```bash
# Test CORS preflight
curl -X OPTIONS \
  -H "Origin: http://localhost:9002" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v http://localhost:8000/api/auth/login

# Check backend CORS configuration
grep -r "CORS" main.py
grep -r "allow_origins" main.py
```

**Solutions**:

1. **Missing CORS Origins**:
   ```bash
   # Add Web UI origin to CORS configuration
   export KAREN_CORS_ORIGINS="http://localhost:9002,http://127.0.0.1:9002"
   
   # Update .env file
   echo "KAREN_CORS_ORIGINS=http://localhost:9002,http://127.0.0.1:9002" >> .env
   ```

2. **External IP CORS Issues**:
   ```bash
   # Add external IP to CORS origins
   export KAREN_CORS_ORIGINS="http://localhost:9002,http://10.105.235.209:9002"
   
   # For dynamic external IP detection
   export KAREN_EXTERNAL_HOST=10.105.235.209
   ```

3. **Docker CORS Configuration**:
   ```bash
   # Update docker-compose.yml environment
   environment:
     - KAREN_CORS_ORIGINS=http://localhost:9002,http://127.0.0.1:9002
   
   # Restart containers
   docker-compose restart api
   ```

4. **Backend CORS Middleware Check**:
   ```python
   # Verify in main.py
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:9002", "http://127.0.0.1:9002"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### 3. Network Timeout Issues

**Symptoms**:
- Requests timeout after long delays
- Intermittent connectivity issues
- Slow API responses

**Error Messages**:
```
Request timeout
Network timeout
ERR_NETWORK_TIMEOUT
```

**Diagnosis**:
```bash
# Test response time
time curl http://localhost:8000/health

# Check network latency
ping localhost
ping 10.105.235.209

# Monitor network connections
netstat -an | grep :8000
ss -an | grep :8000
```

**Solutions**:

1. **Increase Timeout Values**:
   ```bash
   # Update health check timeout
   export KAREN_HEALTH_CHECK_TIMEOUT=10000
   
   # Update API client timeout
   export KAREN_HTTP_TIMEOUT=30000
   ```

2. **Network Performance Issues**:
   ```bash
   # Check system resources
   top
   htop
   
   # Check disk I/O
   iostat -x 1
   
   # Check memory usage
   free -h
   ```

3. **Docker Network Issues**:
   ```bash
   # Check Docker network
   docker network ls
   docker network inspect ai-karen-net
   
   # Recreate network
   docker-compose down
   docker-compose up -d
   ```

### 4. Authentication Endpoint Issues

**Symptoms**:
- Login page cannot authenticate users
- Authentication requests fail
- Session management issues

**Error Messages**:
```
Authentication failed
Invalid credentials
Session expired
401 Unauthorized
```

**Diagnosis**:
```bash
# Test authentication endpoint
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Check authentication service
curl http://localhost:8000/api/auth/status

# Verify JWT configuration
echo $AUTH_SECRET_KEY
echo $AUTH_ALGORITHM
```

**Solutions**:

1. **Authentication Service Configuration**:
   ```bash
   # Set authentication secrets
   export AUTH_SECRET_KEY="your-super-secret-jwt-key"
   export AUTH_ALGORITHM="HS256"
   export AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

2. **Database Connection Issues**:
   ```bash
   # Test database connectivity
   python -c "
   import os
   from sqlalchemy import create_engine
   engine = create_engine(os.getenv('DATABASE_URL'))
   conn = engine.connect()
   print('Database connected successfully')
   conn.close()
   "
   ```

3. **User Database Setup**:
   ```bash
   # Initialize user database
   python scripts/init_db_schema.py
   
   # Create test user
   python -c "
   from src.ai_karen_engine.database.auth_models import create_user
   create_user('test', 'test@example.com', 'testpassword')
   "
   ```

### 5. Docker Container Networking Issues

**Symptoms**:
- Containers cannot communicate with each other
- Service discovery failures
- Port mapping issues

**Error Messages**:
```
Name resolution failure
Connection refused between containers
Service unavailable
```

**Diagnosis**:
```bash
# Check container network
docker-compose ps
docker network ls
docker network inspect ai-karen-net

# Test inter-container connectivity
docker-compose exec web-ui curl http://api:8000/health
docker-compose exec api curl http://postgres:5432

# Check port mappings
docker port ai-karen-api
docker port ai-karen-web-ui
```

**Solutions**:

1. **Service Name Resolution**:
   ```yaml
   # docker-compose.yml
   services:
     api:
       container_name: ai-karen-api
       networks:
         - ai-karen-net
     
     web-ui:
       environment:
         - KAREN_BACKEND_URL=http://api:8000  # Use service name
       depends_on:
         - api
       networks:
         - ai-karen-net
   ```

2. **Network Configuration**:
   ```bash
   # Recreate network
   docker-compose down
   docker network prune
   docker-compose up -d
   ```

3. **Port Mapping Issues**:
   ```yaml
   # Ensure correct port mapping
   services:
     api:
       ports:
         - "8000:8000"  # host:container
     web-ui:
       ports:
         - "9002:9002"
   ```

### 6. External IP Access Issues

**Symptoms**:
- Cannot access services from external networks
- Firewall blocking connections
- IP address resolution issues

**Error Messages**:
```
Connection timed out
No route to host
Connection refused from external IP
```

**Diagnosis**:
```bash
# Test external connectivity
curl http://10.105.235.209:8000/health

# Check firewall rules
sudo ufw status
sudo iptables -L

# Check service binding
netstat -tlnp | grep :8000
ss -tlnp | grep :8000

# Test from external network
nmap -p 8000 10.105.235.209
```

**Solutions**:

1. **Firewall Configuration**:
   ```bash
   # Allow backend port
   sudo ufw allow 8000/tcp
   
   # Allow Web UI port
   sudo ufw allow 9002/tcp
   
   # Check firewall status
   sudo ufw status verbose
   ```

2. **Service Binding**:
   ```bash
   # Bind to all interfaces
   export HOST=0.0.0.0
   python main.py --host 0.0.0.0 --port 8000
   ```

3. **External IP Configuration**:
   ```bash
   # Set external host
   export KAREN_EXTERNAL_HOST=10.105.235.209
   export KAREN_EXTERNAL_BACKEND_PORT=8000
   
   # Update CORS for external access
   export KAREN_CORS_ORIGINS="http://10.105.235.209:9002,http://localhost:9002"
   ```

## Advanced Diagnostics

### Network Traffic Analysis

```bash
# Monitor network traffic
sudo tcpdump -i any port 8000
sudo tcpdump -i any port 9002

# Monitor HTTP requests
sudo tcpdump -i any -A port 8000 | grep -E "(GET|POST|PUT|DELETE)"
```

### Application Logs Analysis

```bash
# Backend logs
tail -f backend.log
tail -f server.log

# Docker container logs
docker-compose logs -f api
docker-compose logs -f web-ui

# System logs
journalctl -u your-service-name -f
```

### Performance Monitoring

```bash
# Monitor system resources
htop
iotop
nethogs

# Monitor application performance
python -m cProfile main.py

# Monitor database performance
psql -c "SELECT * FROM pg_stat_activity;"
```

## Configuration Validation Tools

### Endpoint Validation Script

```bash
#!/bin/bash
# validate-endpoints.sh

echo "Validating AI Karen endpoint configuration..."

# Test backend health
echo "Testing backend health..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✓ Backend health check passed"
else
    echo "✗ Backend health check failed"
fi

# Test Web UI
echo "Testing Web UI..."
if curl -f -s http://localhost:9002 > /dev/null; then
    echo "✓ Web UI accessible"
else
    echo "✗ Web UI not accessible"
fi

# Test CORS
echo "Testing CORS configuration..."
CORS_RESPONSE=$(curl -s -X OPTIONS \
  -H "Origin: http://localhost:9002" \
  -H "Access-Control-Request-Method: GET" \
  -I http://localhost:8000/api/auth/login)

if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    echo "✓ CORS configuration valid"
else
    echo "✗ CORS configuration invalid"
fi

echo "Validation complete."
```

### Configuration Check Script

```python
#!/usr/bin/env python3
# check-config.py

import os
import requests
import sys

def check_environment_variables():
    """Check required environment variables"""
    required_vars = [
        'KAREN_BACKEND_URL',
        'KAREN_ENVIRONMENT',
        'KAREN_NETWORK_MODE'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"✗ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✓ All required environment variables set")
        return True

def check_backend_connectivity():
    """Check backend connectivity"""
    backend_url = os.getenv('KAREN_BACKEND_URL', 'http://localhost:8000')
    
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Backend connectivity successful ({backend_url})")
            return True
        else:
            print(f"✗ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Backend connectivity failed: {e}")
        return False

def check_cors_configuration():
    """Check CORS configuration"""
    backend_url = os.getenv('KAREN_BACKEND_URL', 'http://localhost:8000')
    web_ui_url = os.getenv('KAREN_WEB_UI_URL', 'http://localhost:9002')
    
    try:
        headers = {
            'Origin': web_ui_url,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(f"{backend_url}/api/auth/login", 
                                  headers=headers, timeout=5)
        
        if 'Access-Control-Allow-Origin' in response.headers:
            print("✓ CORS configuration valid")
            return True
        else:
            print("✗ CORS configuration invalid")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ CORS check failed: {e}")
        return False

def main():
    """Run all configuration checks"""
    print("AI Karen Configuration Validation")
    print("=" * 40)
    
    checks = [
        check_environment_variables,
        check_backend_connectivity,
        check_cors_configuration
    ]
    
    results = []
    for check in checks:
        results.append(check())
        print()
    
    if all(results):
        print("✓ All configuration checks passed!")
        sys.exit(0)
    else:
        print("✗ Some configuration checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Emergency Recovery Procedures

### Complete Service Reset

```bash
#!/bin/bash
# emergency-reset.sh

echo "Performing emergency service reset..."

# Stop all services
docker-compose down
pkill -f "python main.py"
pkill -f "npm run dev"

# Clear caches and temporary files
rm -rf __pycache__/
rm -rf ui_launchers/web_ui/node_modules/.cache/
rm -rf ui_launchers/web_ui/dist/

# Reset configuration
cp .env.example .env

# Restart services
docker-compose up -d
sleep 10

# Verify services
curl -f http://localhost:8000/health
curl -f http://localhost:9002

echo "Emergency reset complete."
```

### Database Connection Reset

```bash
#!/bin/bash
# reset-database.sh

echo "Resetting database connections..."

# Stop services
docker-compose stop api

# Reset database
docker-compose restart postgres
sleep 5

# Reinitialize schema
python scripts/init_db_schema.py

# Restart API
docker-compose start api

echo "Database reset complete."
```

## Getting Help

If you're still experiencing issues after following this guide:

1. **Check Logs**: Review application and system logs for specific error messages
2. **Verify Configuration**: Use the validation scripts provided above
3. **Test Incrementally**: Start with basic connectivity and add complexity
4. **Document Issues**: Note exact error messages and steps to reproduce
5. **Seek Support**: Contact the development team with detailed diagnostic information

## Related Documentation

- [Deployment Configuration Guide](./deployment-configuration-guide.md)
- [Developer Configuration Guide](./developer-configuration-guide.md)
- [API Reference](./api_reference.md)
- [Architecture Overview](./architecture.md)