# Authentication Troubleshooting Guide

This guide helps you diagnose and fix authentication issues in AI Karen.

## Quick Diagnosis

### Issue: 401 Unauthorized Error on Login

**Error Message:**
```
[ERROR] Request failed for /api/auth/login after 1 attempts: HTTP 401: Unauthorized
[ERROR] [authentication:login] Authentication attempt failed
Login failed: ConnectionError: HTTP 401: Unauthorized
```

**Root Causes:**

#### 1. **Wrong Credentials** (Most Common)
The default admin credentials are:
- **Email:** `admin@kari.ai`
- **Password:** `Password123!` (NOTE: Capital 'P' and exclamation mark!)

**Common Mistakes:**
- ❌ Using `password123` (lowercase, no special char)
- ❌ Using `password123!` (lowercase P)
- ❌ Using `Password123` (no exclamation mark)
- ✅ Correct: `Password123!`

#### 2. **Admin User Not Created**
The system requires first-run setup to create the admin user.

**Check if admin user exists:**
```bash
cd /home/user/AI-Karen
python3 scripts/operations/setup_admin_proper.py
```

This script will:
- Create the admin user if it doesn't exist
- Set up the password if it's missing
- Verify the setup

**Output if successful:**
```
✅ Admin user setup completed successfully!

👤 Default Admin Credentials:
   • Email: admin@kari.ai
   • Password: Password123!
   • Roles: admin, user
```

#### 3. **Account Locked Due to Failed Attempts**
After 5 failed login attempts, the account gets locked for security.

**Unlock the admin account:**
```bash
cd /home/user/AI-Karen
python3 scripts/maintenance/unlock_admin_account.py
```

This script will:
- Clear failed login attempts
- Remove account lock
- Clear rate limiting
- Clear old sessions

#### 4. **Backend Not Running**
The backend authentication service must be running on port 8000.

**Check if backend is running:**
```bash
# Check if the backend is responding
curl http://localhost:8000/api/auth/status

# Expected output:
{
  "status": "healthy",
  "service": "production-auth",
  "mode": "jwt-authentication"
}
```

**Start the backend if not running:**
```bash
cd /home/user/AI-Karen
# Start the backend server
python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

#### 5. **Database Connection Issues**
The backend needs access to PostgreSQL database.

**Check database connection:**
```bash
# Verify PostgreSQL is running
pg_isready -h localhost -p 5432

# Connect to database and check admin user
psql -h localhost -U karen_user -d ai_karen -c "SELECT user_id, email, is_active FROM auth_users WHERE email='admin@kari.ai';"
```

**Environment Variables:**
Ensure these are set in your `.env` file:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=karen_user
POSTGRES_PASSWORD=karen_secure_pass_change_me
POSTGRES_DB=ai_karen
```

## Step-by-Step Fix Procedure

### Step 1: Verify Backend is Running
```bash
# Terminal 1: Start backend if not running
cd /home/user/AI-Karen
python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Check health
curl http://localhost:8000/api/auth/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "service": "production-auth"
}
```

### Step 2: Setup Admin User
```bash
cd /home/user/AI-Karen
python3 scripts/operations/setup_admin_proper.py
```

**Expected Output:**
```
✅ Admin user setup completed successfully!

👤 Default Admin Credentials:
   • Email: admin@kari.ai
   • Password: Password123!
   • Roles: admin, user
```

###Step 3: Unlock Account (if needed)
```bash
cd /home/user/AI-Karen
python3 scripts/maintenance/unlock_admin_account.py
```

### Step 4: Test Login
Try logging in with the correct credentials:
- **Email:** `admin@kari.ai`
- **Password:** `Password123!`

### Step 5: Check Frontend Connection
```bash
# Terminal 3: Start frontend if not running
cd /home/user/AI-Karen/ui_launchers/KAREN-Theme-Default
npm run dev

# Access at: http://localhost:8000
```

## Advanced Troubleshooting

### Check Backend Logs
```bash
# Follow backend logs for detailed error messages
tail -f /home/user/AI-Karen/logs/app.log
```

### Check Database State
```bash
# Connect to database
psql -h localhost -U karen_user -d ai_karen

# Check admin user
SELECT user_id, email, roles, is_active, failed_login_attempts, locked_until
FROM auth_users
WHERE email='admin@kari.ai';

# Check password hash exists
SELECT user_id, created_at, updated_at
FROM auth_password_hashes
WHERE user_id = (SELECT user_id FROM auth_users WHERE email='admin@kari.ai');

# Check recent auth events
SELECT event_type, email, success, timestamp, error_message
FROM auth_events
WHERE email='admin@kari.ai'
ORDER BY timestamp DESC
LIMIT 10;
```

### Clear All Rate Limiting
```bash
cd /home/user/AI-Karen
python3 scripts/maintenance/clear_all_rate_limits.py
```

### Disable Rate Limiting (for testing)
```bash
cd /home/user/AI-Karen
python3 scripts/maintenance/disable_rate_limiting.py
```

## Common Configuration Issues

### Backend URL Mismatch
The frontend expects the backend at `http://localhost:8000`.

**Check environment variables:**
```bash
cd /home/user/AI-Karen/ui_launchers/KAREN-Theme-Default
cat .env.local | grep BACKEND_URL
```

**Expected:**
```env
NEXT_PUBLIC_KAREN_BACKEND_URL=http://localhost:8000
KAREN_BACKEND_URL=http://localhost:8000
```

### CORS Issues
If you see CORS errors in the browser console:

**Check backend CORS settings:**
```python
# In server/app.py or similar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:8010"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Security Best Practices

### Change Default Password
After first login, **immediately change the default password**:

1. Log in with `admin@kari.ai` / `Password123!`
2. Navigate to Profile Settings
3. Change password to a strong, unique password
4. Enable 2FA if available

### Create Additional Users
Don't share the admin account:

```bash
# Create a new user via API or admin panel
# Use the admin panel at: http://localhost:8000/admin/users
```

## Still Having Issues?

### Check Recent Commits
Recent fixes for authentication issues:
- Session timeout causing immediate re-login
- Extension API returning 401 during grace period
- Grace period mechanism to prevent race conditions

### Review Logs
1. **Backend logs:** `/home/user/AI-Karen/logs/`
2. **Frontend console:** Browser DevTools (F12)
3. **Network tab:** Check API request/response details

### Contact Support
If none of the above fixes work:

1. **Gather information:**
   - Backend logs
   - Browser console errors
   - Network request details
   - Database user state

2. **File an issue:**
   - Repository: https://github.com/Zeus-Eternal/AI-Karen/issues
   - Include all gathered information
   - Mention this troubleshooting guide was consulted

## Quick Reference

### Default Credentials
```
Email: admin@kari.ai
Password: Password123!
```

### Key Scripts
```bash
# Setup admin user
python3 scripts/operations/setup_admin_proper.py

# Unlock account
python3 scripts/maintenance/unlock_admin_account.py

# Clear rate limits
python3 scripts/maintenance/clear_all_rate_limits.py

# Disable rate limiting
python3 scripts/maintenance/disable_rate_limiting.py
```

### Key URLs
```
Frontend: http://localhost:8000 (or 8010)
Backend: http://localhost:8000
Auth Status: http://localhost:8000/api/auth/status
Auth Health: http://localhost:8000/api/auth/health
First-Run Check: http://localhost:8000/api/auth/first-run
```

### Environment Variables
```env
KAREN_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_KAREN_BACKEND_URL=http://localhost:8000
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=karen_user
POSTGRES_PASSWORD=karen_secure_pass_change_me
POSTGRES_DB=ai_karen
```
