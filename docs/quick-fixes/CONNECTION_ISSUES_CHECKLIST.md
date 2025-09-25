# AI-Karen Connection Issues - Quick Fix Checklist

## 🚨 Immediate Actions

Based on your console logs showing `ERR_CONNECTION_REFUSED` on `http://localhost:8001/health`, here's your quick fix checklist:

### ✅ Step 1: Check Service Status
```bash
# Check if services are running
docker compose ps

# Expected output should show all services as "Up"
# If any service is "Exit" or "Restarting", that's your problem
```

### ✅ Step 2: Verify Port Configuration
```bash
# Check what's actually listening
ss -ltnp | grep -E ':(8000|8001|3000|8020)'

# Your API should be on 8000, not 8001
# If nothing is on 8000, your API isn't running
```

### ✅ Step 3: Quick Service Restart
```bash
# Nuclear option - restart everything
docker compose down
docker compose up -d

# Wait 30 seconds for startup
sleep 30

# Test the correct endpoint
curl http://localhost:8000/health
```

## 🔧 Configuration Fixes

### Fix 1: Update Frontend Health Check URLs

The error shows health checks going to port 8001, but your API is on 8000.

**Update your frontend configuration:**
```typescript
// In ui_launchers/web_ui/src/lib/endpoint-config.ts or similar
const BACKEND_URLS = [
  'http://localhost:8000',  // NOT 8001
  'http://127.0.0.1:8000'
];
```

### Fix 2: Environment Variables Check
```bash
# Check your .env file
grep -E "(KAREN_BACKEND_URL|API_BASE_URL)" .env

# Should show:
# KAREN_BACKEND_URL=http://127.0.0.1:8000
# API_BASE_URL=http://127.0.0.1:8000
```

### Fix 3: Docker Compose Port Mapping
```yaml
# In docker-compose.yml, ensure:
services:
  api:
    ports:
      - "8000:8000"  # External:Internal
  web-ui:
    ports:
      - "8020:3000"  # Your UI should be on 8020
```

## 🎯 Specific Error Resolution

### Error: `GET http://localhost:8001/health net::ERR_CONNECTION_REFUSED`

**Root Cause:** Frontend is checking wrong port (8001 instead of 8000)

**Quick Fix:**
1. Find where port 8001 is configured in your frontend code
2. Change it to 8000
3. Restart the web UI

**Search for the misconfiguration:**
```bash
# Find where 8001 is referenced
grep -r "8001" ui_launchers/web_ui/src/
grep -r "localhost:8001" ui_launchers/web_ui/
```

### Error: Copilot requests timing out

**Quick Test:**
```bash
# Test copilot endpoint directly
curl -X POST http://localhost:8000/api/copilot/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer validated" \
  -d '{"session_id": "test"}'
```

**Expected Response:**
```json
{
  "status": "started",
  "session_id": "copilot_session_xxx",
  "message": "Copilot session initialized"
}
```

## 🚀 Verification Steps

### 1. API Health Check
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### 2. Detailed Health Summary
```bash
curl http://localhost:8000/api/health/summary
# Should return detailed service status
```

### 3. Web UI Access
```bash
# Your web UI should be accessible at:
open http://localhost:8020
# OR
open http://localhost:3000
```

### 4. API Documentation
```bash
# API docs should be available at:
open http://localhost:8000/docs
```

## 🔍 Diagnostic Commands

### Check All Ports
```bash
# See what's actually running
netstat -tlnp | grep -E ':(8000|8001|3000|8020|5433|6379)'
```

### Check Docker Logs
```bash
# API logs
docker compose logs api --tail=20

# Web UI logs
docker compose logs web-ui --tail=20

# All services
docker compose logs --tail=10
```

### Test Database Connections
```bash
# PostgreSQL
docker compose exec postgres pg_isready -U karen_user -d ai_karen

# Redis
docker compose exec redis redis-cli ping
```

## 🛠️ Emergency Recovery

If nothing else works:

### Nuclear Reset
```bash
# Stop everything
docker compose down

# Remove volumes (WARNING: This deletes data)
docker compose down -v

# Clean up
docker system prune -f

# Start fresh
docker compose up -d

# Initialize database
sleep 60
python create_tables.py
python create_admin_user.py
```

### Minimal Startup
```bash
# Start only essential services
docker compose up -d postgres redis api

# Test API
curl http://localhost:8000/health

# If API works, start web UI
docker compose up -d web-ui
```

## 📋 Prevention Checklist

- [ ] Always use consistent ports (8000 for API, 8020 for Web UI)
- [ ] Set proper environment variables
- [ ] Use health checks in docker-compose.yml
- [ ] Monitor logs during startup
- [ ] Test endpoints after changes

## 🆘 Still Having Issues?

If these quick fixes don't work:

1. **Check the full logs:**
   ```bash
   docker compose logs > debug-logs.txt
   ```

2. **Run the network diagnostics:**
   ```bash
   bash docs/troubleshooting/network-diagnostics.sh
   ```

3. **Check the comprehensive troubleshooting guide:**
   - [Network Connectivity Guide](NETWORK_CONNECTIVITY_GUIDE.md)
   - [Comprehensive Troubleshooting Guide](COMPREHENSIVE_TROUBLESHOOTING_GUIDE.md)

## 💡 Pro Tips

- **Always check ports first** - 90% of connection issues are port misconfigurations
- **Use 127.0.0.1 instead of localhost** - sometimes resolves DNS issues
- **Check firewall settings** - especially on Linux systems
- **Verify Docker network configuration** - services must be on same network

---

**Quick Reference:**
- API: `http://localhost:8000`
- Web UI: `http://localhost:8020`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`