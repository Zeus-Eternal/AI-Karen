# CORS Issues Fix - Cross-Origin Request Blocked

## Issue Description

You're seeing CORS (Cross-Origin Resource Sharing) errors in the browser console:

```
Access to fetch at 'http://localhost:8000/copilot/assist' from origin 'http://10.96.136.74:8020' 
has been blocked by CORS policy: Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause

The frontend is running on `http://10.96.136.74:8020` but trying to access the backend on `http://localhost:8000`. The backend's CORS configuration doesn't include the frontend's IP address in the allowed origins.

## Immediate Fix

### Step 1: Update CORS Configuration

Update your `.env` file to include the frontend's IP address:

```bash
# Add your frontend IP to CORS origins
KARI_CORS_ORIGINS=http://localhost:3000,http://localhost:8020,http://127.0.0.1:3000,http://127.0.0.1:8020,http://10.96.136.74:8020,http://10.96.136.74:3000
```

### Step 2: Restart Backend Services

```bash
# Restart the API to pick up new CORS settings
docker compose restart api

# Or restart all services
docker compose down
docker compose up -d
```

### Step 3: Verify CORS Headers

Test that CORS headers are now present:

```bash
# Test CORS preflight request
curl -H "Origin: http://10.96.136.74:8020" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type,Authorization" \
     -X OPTIONS \
     http://localhost:8000/api/copilot/assist

# Should return CORS headers like:
# Access-Control-Allow-Origin: http://10.96.136.74:8020
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
# Access-Control-Allow-Headers: Content-Type, Authorization
```

## Alternative Solutions

### Solution 1: Use Wildcard CORS (Development Only)

For development, you can allow all origins:

```bash
# In .env file - ONLY FOR DEVELOPMENT
KARI_CORS_ORIGINS=*
KARI_CORS_METHODS=*
KARI_CORS_HEADERS=*
KARI_CORS_CREDENTIALS=true
```

**⚠️ Warning:** Never use `*` for CORS origins in production!

### Solution 2: Use Next.js Proxy

Enable the Next.js proxy to avoid CORS issues:

```bash
# In ui_launchers/web_ui/.env.local
NEXT_PUBLIC_USE_PROXY=true
KAREN_USE_PROXY=true
```

This routes API calls through the Next.js server, avoiding CORS entirely.

### Solution 3: Access Frontend via Localhost

Instead of using the IP address, access the frontend via localhost:

```bash
# Access via localhost instead of IP
open http://localhost:8020
```

## Backend CORS Configuration

### Check Current CORS Settings

```bash
# Check what CORS origins are configured
grep KARI_CORS .env

# Should show your IP address in the list
```

### FastAPI CORS Configuration

The backend CORS is configured in the FastAPI application. Check if it's properly set:

```python
# In the FastAPI app configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://10.96.136.74:8020", "http://localhost:8020"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Network Configuration Issues

### Check Network Setup

Your frontend is running on `10.96.136.74:8020`, which suggests:

1. **Docker network configuration**
2. **VM or container networking**
3. **Port forwarding setup**

### Verify Network Connectivity

```bash
# From the frontend container/host, test backend connectivity
curl -v http://localhost:8000/health

# Check if backend is accessible from frontend IP
ping localhost
nslookup localhost
```

### Docker Network Issues

If running in Docker, ensure services are on the same network:

```yaml
# docker-compose.yml
services:
  api:
    networks:
      - ai-karen-net
  web-ui:
    networks:
      - ai-karen-net

networks:
  ai-karen-net:
    driver: bridge
```

## Authentication Issues

The logs also show authentication problems:

```
POST http://10.96.136.74:8020/api/auth/login 404 (Not Found)
POST http://10.96.136.74:8020/api/auth/login-simple 404 (Not Found)
```

### Fix Authentication Routes

Ensure authentication routes exist in your Next.js API:

```bash
# Check if auth routes exist
ls -la ui_launchers/web_ui/src/app/api/auth/

# Should show:
# login/
# login-simple/
# validate-session/
```

### Test Authentication Endpoints

```bash
# Test backend auth directly
curl -X POST http://localhost:8000/api/auth/dev-login \
     -H "Content-Type: application/json" \
     -d '{}'

# Should return a token
```

## Complete Fix Script

Create a comprehensive fix:

```bash
#!/bin/bash
echo "🔧 Fixing CORS and Authentication Issues"

# 1. Update CORS configuration
echo "1. Updating CORS configuration..."
if grep -q "KARI_CORS_ORIGINS" .env; then
    # Update existing CORS origins
    sed -i 's/KARI_CORS_ORIGINS=.*/KARI_CORS_ORIGINS=http:\/\/localhost:3000,http:\/\/localhost:8020,http:\/\/127.0.0.1:3000,http:\/\/127.0.0.1:8020,http:\/\/10.96.136.74:8020,http:\/\/10.96.136.74:3000/' .env
else
    # Add CORS origins
    echo "KARI_CORS_ORIGINS=http://localhost:3000,http://localhost:8020,http://127.0.0.1:3000,http://127.0.0.1:8020,http://10.96.136.74:8020,http://10.96.136.74:3000" >> .env
fi

# 2. Ensure other CORS settings
grep -q "KARI_CORS_METHODS" .env || echo "KARI_CORS_METHODS=*" >> .env
grep -q "KARI_CORS_HEADERS" .env || echo "KARI_CORS_HEADERS=*" >> .env
grep -q "KARI_CORS_CREDENTIALS" .env || echo "KARI_CORS_CREDENTIALS=true" >> .env

# 3. Restart services
echo "2. Restarting services..."
docker compose restart api web-ui

# 4. Wait for services
echo "3. Waiting for services to restart..."
sleep 30

# 5. Test CORS
echo "4. Testing CORS configuration..."
curl -H "Origin: http://10.96.136.74:8020" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8000/api/health

echo "✅ CORS fix applied!"
```

## Verification Steps

### 1. Check Browser Console

After applying the fix:
- ✅ No more CORS errors
- ✅ Requests to backend succeed
- ✅ Authentication works

### 2. Test API Endpoints

```bash
# Test health endpoint with CORS
curl -H "Origin: http://10.96.136.74:8020" \
     http://localhost:8000/health

# Test authentication
curl -X POST http://localhost:8000/api/auth/dev-login \
     -H "Content-Type: application/json" \
     -H "Origin: http://10.96.136.74:8020" \
     -d '{}'
```

### 3. Check Network Connectivity

```bash
# Verify backend is accessible
curl http://localhost:8000/health

# Check frontend is accessible
curl http://10.96.136.74:8020
```

## Prevention

### 1. Always Include Frontend Origins

When deploying, always add your frontend URLs to CORS origins:

```bash
# Development
KARI_CORS_ORIGINS=http://localhost:8020,http://127.0.0.1:8020

# Production
KARI_CORS_ORIGINS=https://app.yourdomain.com,https://yourdomain.com
```

### 2. Use Environment-Specific Configuration

```bash
# Development .env
KARI_CORS_ORIGINS=http://localhost:8020,http://10.96.136.74:8020

# Production .env
KARI_CORS_ORIGINS=https://app.yourdomain.com
```

### 3. Test CORS During Development

Always test cross-origin requests during development:

```bash
# Test from different origins
curl -H "Origin: http://localhost:8020" http://localhost:8000/health
curl -H "Origin: http://10.96.136.74:8020" http://localhost:8000/health
```

This should resolve your CORS issues and allow the frontend to communicate with the backend properly.