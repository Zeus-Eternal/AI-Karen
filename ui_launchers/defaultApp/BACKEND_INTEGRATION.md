# 🔌 Backend Integration Guide

## 📋 Overview

This guide covers connecting the new AI-Karen UI (frontend) to the AI-Karen backend server.

---

## 🏗️ Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Frontend      │         │    Backend      │
│   (Next.js)     │◄────────►│   (FastAPI)     │
│   Port: 3002    │         │   Port: 8000    │
└─────────────────┘         └─────────────────┘
        │                            │
        │                            │
    Browser                      Database
    (User Interface)           (PostgreSQL)
```

---

## 🚀 Step 1: Start Backend Server

### Prerequisites
- Python 3.11+
- Virtual environment (.env_karen/)
- Environment file (.env)

### Start Backend

```bash
cd /mnt/development/KIRO/AI-Karen

# Option 1: Using run script (recommended)
./run_karen.sh

# Option 2: Direct Python
.env_karen/bin/python3 start.py

# Option 3: Background mode
nohup ./run_karen.sh > /tmp/karen-backend.log 2>&1 &
```

### Verify Backend is Running

```bash
# Check if process is running
ps aux | grep -E "python.*start|uvicorn" | grep -v grep

# Check if port is listening
lsof -i:8000

# Test health endpoint
curl http://localhost:8000/api/health

# View logs
tail -f /tmp/karen-backend.log
```

### Expected Response

```bash
$ curl http://localhost:8000/api/health
{"status":"healthy","version":"1.0.0"}
```

---

## 🔧 Step 2: Configure Frontend

### Create Environment File

The frontend needs to know where the backend is located. Create `.env.local`:

```bash
cd ui_launchers/defaultApp
```

Create `.env.local` with:

```bash
# Backend API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Enable debug mode
NEXT_PUBLIC_DEBUG=true
```

**Important**: The `.env.local` file is git-ignored and must be created manually.

### Rebuild Frontend

After creating `.env.local`, rebuild the frontend to include environment variables:

```bash
cd ui_launchers/defaultApp

# Kill existing frontend server
pkill -f "next start"

# Rebuild
npm run build

# Restart
PORT=3002 npx next start -p 3002 &
```

---

## 🧪 Step 3: API Testing

### Test Connection

```bash
# Test backend is responding
curl http://localhost:8000/api/health

# Test frontend can reach backend
curl http://localhost:3002
```

### Test API Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/api/health
```

#### 2. List Conversations
```bash
curl http://localhost:8000/api/conversations \
  -H "Content-Type: application/json"
```

#### 3. Create Conversation
```bash
curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Conversation"}'
```

#### 4. Send Message
```bash
curl -X POST http://localhost:8000/api/conversations/{id}/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, AI-Karen!"}'
```

#### 5. Stream Message (SSE)
```bash
curl -N http://localhost:8000/api/conversations/{id}/stream \
  -H "Content-Type: application/json" \
  -d '{"content": "Tell me a joke"}'
```

---

## 🌐 Step 4: Frontend Integration Testing

### Open Browser

Navigate to: http://localhost:3002

### Test Flow

1. **Initial Load**
   - ✅ Page loads successfully
   - ✅ No console errors
   - ✅ UI components render

2. **Create Conversation**
   - Click "New Conversation" button
   - Conversation appears in sidebar (if implemented)
   - Message input becomes enabled

3. **Send Message**
   - Type message in input
   - Click "Send" button or press Enter
   - Message appears in chat
   - "Typing..." indicator shows

4. **Receive Response**
   - AI response appears
   - Streaming works (typewriter effect)
   - Markdown renders correctly
   - Code blocks highlight properly

5. **Multiple Messages**
   - Send several messages
   - Conversation history persists
   - Scroll to bottom works

---

## 🔍 Step 5: Troubleshooting

### Backend Not Starting

**Symptom**: Backend process exits immediately

**Solutions**:
```bash
# Check if port 8000 is already in use
lsof -i:8000

# Kill process using port 8000
kill -9 $(lsof -ti:8000)

# Check backend logs
tail -50 /tmp/karen-backend.log

# Verify .env file exists
ls -la .env

# Check virtual environment
ls -la .env_karen/bin/python3
```

### Frontend Can't Connect to Backend

**Symptom**: Network errors in browser console

**Solutions**:
```bash
# Verify backend is running
curl http://localhost:8000/api/health

# Check CORS configuration
# Look for CORS errors in browser console

# Verify NEXT_PUBLIC_API_URL
cat ui_launchers/defaultApp/.env.local

# Rebuild frontend after changing .env.local
cd ui_launchers/defaultApp
npm run build
```

### CORS Errors

**Symptom**: Browser shows CORS policy errors

**Solution**: Backend needs to allow frontend origin

Check backend CORS configuration in `server/app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Streaming Not Working

**Symptom**: Messages appear all at once instead of streaming

**Solutions**:
1. Check browser supports Server-Sent Events (SSE)
2. Verify backend streaming endpoint works
3. Check network tab in browser DevTools
4. Look for errors in console

### Messages Not Persisting

**Symptom**: Messages disappear on refresh

**Solutions**:
1. Check database connection
2. Verify backend is saving messages
3. Check browser local storage
4. Look for API errors in console

---

## 📊 Monitoring

### Backend Logs

```bash
# Follow backend logs in real-time
tail -f /tmp/karen-backend.log

# Search for errors
grep -i error /tmp/karen-backend.log

# Search for API requests
grep -i "POST /api" /tmp/karen-backend.log
```

### Frontend Logs

Open browser DevTools (F12):
- **Console Tab**: JavaScript errors and logs
- **Network Tab**: API requests and responses
- **Application Tab**: Local storage and cookies

---

## ✅ Integration Checklist

### Backend
- [ ] Server starts without errors
- [ ] Listening on port 8000
- [ ] Health endpoint responds
- [ ] CORS configured for frontend
- [ ] Database connected
- [ ] All API endpoints working

### Frontend
- [ ] .env.local configured
- [ ] Rebuilt with env vars
- [ ] Can reach backend
- [ ] No CORS errors
- [ ] Can create conversations
- [ ] Can send messages
- [ ] Streaming works
- [ ] Messages persist
- [ ] No console errors

### End-to-End
- [ ] Full message flow works
- [ ] Multiple conversations work
- [ ] Streaming displays correctly
- [ ] Error handling works
- [ ] Loading states show
- [ ] UI is responsive

---

## 🔧 Common Commands

### Backend

```bash
# Start backend
./run_karen.sh

# Stop backend
pkill -f "python.*start"

# Restart backend
pkill -f "python.*start" && sleep 2 && ./run_karen.sh &

# Check status
ps aux | grep -E "python.*start|uvicorn" | grep -v grep
curl http://localhost:8000/api/health
```

### Frontend

```bash
# Start frontend
cd ui_launchers/defaultApp
PORT=3002 npx next start -p 3002 &

# Stop frontend
pkill -f "next start"

# Restart frontend
pkill -f "next start" && sleep 2 && \
  cd ui_launchers/defaultApp && \
  PORT=3002 npx next start -p 3002 &
```

### Both

```bash
# Stop both
pkill -f "python.*start"
pkill -f "next start"

# Start both
./run_karen.sh > /tmp/karen-backend.log 2>&1 &
sleep 5
cd ui_launchers/defaultApp && \
  PORT=3002 npx next start -p 3002 &
```

---

## 📝 Notes

### Ports
- **Frontend**: 3002 (configurable)
- **Backend**: 8000 (default, set by KARI_SERVER_PORT)
- **Database**: 5432 (PostgreSQL default)

### URLs
- **Frontend**: http://localhost:3002
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (if Swagger enabled)

### Environment Files
- **Backend**: `.env` (in project root)
- **Frontend**: `.env.local` (in ui_launchers/defaultApp/)

### Logs
- **Backend**: `/tmp/karen-backend.log`
- **Frontend**: `/tmp/ui-server-3002.log`

---

## 🎯 Success Criteria

Integration is successful when:

1. ✅ Backend server running and healthy
2. ✅ Frontend can reach backend
3. ✅ No CORS errors
4. ✅ User can send messages
5. ✅ AI responses stream in real-time
6. ✅ Conversations persist
7. ✅ No console errors
8. ✅ UI is responsive

---

## 🚀 Next Steps

After successful integration:

1. **Build remaining Stage 1 features**
   - Conversation sidebar
   - Conversation management
   - Dark mode toggle

2. **Run comprehensive tests**
   - Unit tests
   - Integration tests
   - E2E tests

3. **Performance optimization**
   - Code splitting
   - Lazy loading
   - Caching

4. **Production preparation**
   - Security audit
   - Error tracking
   - Monitoring

---

**Last Updated**: 2026-01-22  
**Status**: Active Integration Phase
