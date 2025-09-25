# Port 8001 Connection Issue - Specific Fix

## Issue Description

You're experiencing connection errors where the frontend is trying to connect to `http://localhost:8001/health` instead of the correct `http://localhost:8000/health`.

**Error in Console:**
```
GET http://localhost:8001/health net::ERR_CONNECTION_REFUSED
```

## Root Cause

The issue is caused by a hardcoded default value in the compiled JavaScript that falls back to port 8001 when environment variables are not properly set.

## Immediate Fix

### Step 1: Set Environment Variables

Create or update `ui_launchers/web_ui/.env.local`:

```bash
# Backend API Configuration
KAREN_BACKEND_URL=http://127.0.0.1:8000
API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000

# Network Configuration
KAREN_ENVIRONMENT=local
KAREN_NETWORK_MODE=localhost
KAREN_USE_PROXY=false
NEXT_PUBLIC_USE_PROXY=false

# Development Settings
NODE_ENV=development
```

### Step 2: Restart Services

```bash
# Restart web UI to pick up new environment variables
docker compose restart web-ui

# Or restart everything
docker compose down
docker compose up -d
```

### Step 3: Clear Browser Cache

1. Open browser developer tools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"
4. Or use Ctrl+Shift+R (Cmd+Shift+R on Mac)

## Verification

### Check Environment Variables
```bash
# In the web UI container
docker compose exec web-ui env | grep -E "(KAREN|API)"
```

### Test Connectivity
```bash
# API should respond on port 8000
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

### Browser Console
1. Open developer tools (F12)
2. Go to Console tab
3. Look for configuration logs like:
   ```
   🔧 ConfigManager: Initial configuration loaded: {backendUrl: "http://localhost:8000", ...}
   ```

## Alternative Solutions

### Solution 1: Use the Fix Script

```bash
# Run the automated fix script
./fix-connection-issue.sh
```

### Solution 2: Manual Environment Setup

```bash
# Set environment variables in your shell
export KAREN_BACKEND_URL="http://127.0.0.1:8000"
export API_BASE_URL="http://127.0.0.1:8000"
export NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"

# Restart web UI
docker compose restart web-ui
```

### Solution 3: Rebuild Web UI

If environment variables don't take effect:

```bash
# Stop web UI
docker compose stop web-ui

# Remove the container
docker compose rm web-ui

# Rebuild and start
docker compose up -d web-ui
```

## Prevention

### 1. Always Set Environment Variables

Add to your main `.env` file:
```bash
KAREN_BACKEND_URL=http://127.0.0.1:8000
API_BASE_URL=http://127.0.0.1:8000
```

### 2. Use Consistent Ports

Ensure your `docker-compose.yml` uses consistent port mapping:
```yaml
services:
  api:
    ports:
      - "8000:8000"  # Always map to 8000
  web-ui:
    ports:
      - "8020:3000"  # Consistent web UI port
```

### 3. Verify Configuration

Add this to your startup routine:
```bash
# Check configuration before starting
echo "Backend URL: $KAREN_BACKEND_URL"
echo "API Base URL: $API_BASE_URL"

# Start services
docker compose up -d
```

## Debugging

### Check Compiled JavaScript

If the issue persists, check the compiled files:
```bash
# Search for 8001 in compiled files
grep -r "8001" ui_launchers/web_ui/.next/

# Should not return any results after fix
```

### Network Diagnostics

```bash
# Check what's actually listening
ss -ltnp | grep -E ':(8000|8001)'

# Test all possible endpoints
curl -v http://localhost:8000/health
curl -v http://127.0.0.1:8000/health
curl -v http://localhost:8001/health  # Should fail
```

### Browser Network Tab

1. Open developer tools (F12)
2. Go to Network tab
3. Reload page
4. Look for requests to port 8001
5. Check if they're now going to port 8000

## Related Issues

- [Network Connectivity Guide](NETWORK_CONNECTIVITY_GUIDE.md)
- [Connection Issues Checklist](../quick-fixes/CONNECTION_ISSUES_CHECKLIST.md)
- [Comprehensive Troubleshooting Guide](COMPREHENSIVE_TROUBLESHOOTING_GUIDE.md)

## Success Indicators

✅ **Fixed when you see:**
- No more `ERR_CONNECTION_REFUSED` errors in console
- Health checks going to `http://localhost:8000/health`
- Configuration logs showing correct backend URL
- Chat requests working properly

❌ **Still broken if you see:**
- Continued requests to port 8001
- Connection refused errors
- Health check failures

If the issue persists after following this guide, please check the comprehensive troubleshooting documentation or create an issue with your system details.