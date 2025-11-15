# Quick Start: Authentication Setup

This guide gets you up and running with AI Karen authentication in 5 minutes.

## Prerequisites

- PostgreSQL database running on `localhost:5432`
- Backend server accessible (we'll start it in Step 1)
- Frontend UI accessible (we'll start it in Step 2)

## Step-by-Step Setup

### Step 1: Start the Backend

```bash
# Navigate to project root
cd /home/user/AI-Karen

# Start the backend server
python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

**Verify it's running:**
```bash
# In another terminal
curl http://localhost:8000/api/auth/health
```

**Expected output:**
```json
{
  "status": "healthy",
  "service": "production-auth"
}
```

### Step 2: Create Admin User

```bash
# In another terminal
cd /home/user/AI-Karen
python3 scripts/operations/setup_admin_proper.py
```

**Expected output:**
```
✅ Admin user setup completed successfully!

👤 Default Admin Credentials:
   • Email: admin@kari.ai
   • Password: Password123!
   • Roles: admin, user
```

**IMPORTANT:** Write down these credentials!

### Step 3: Start the Frontend

```bash
# Navigate to frontend directory
cd /home/user/AI-Karen/ui_launchers/KAREN-Theme-Default

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Access the UI:**
Open your browser to: `http://localhost:8000` (or `http://localhost:8010`)

### Step 4: Login

1. Navigate to `http://localhost:8000` in your browser
2. You should see the login page
3. Enter credentials:
   - **Email:** `admin@kari.ai`
   - **Password:** `Password123!` (note the capital P and exclamation mark!)
4. Click **Sign In**

**Success!** You should now be logged in and see the dashboard.

## Troubleshooting

### Problem: "401 Unauthorized" Error

**Solution 1: Wrong Password**
- Make sure you're using `Password123!` NOT `password123`
- The password is case-sensitive
- Don't forget the exclamation mark!

**Solution 2: Admin User Not Created**
```bash
cd /home/user/AI-Karen
python3 scripts/operations/setup_admin_proper.py
```

**Solution 3: Account Locked**
```bash
cd /home/user/AI-Karen
python3 scripts/maintenance/unlock_admin_account.py
```

### Problem: "Cannot connect to server"

**Check if backend is running:**
```bash
curl http://localhost:8000/api/auth/health
```

If you get an error, start the backend:
```bash
cd /home/user/AI-Karen
python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

### Problem: Database connection failed

**Check PostgreSQL is running:**
```bash
pg_isready -h localhost -p 5432
```

**Start PostgreSQL if needed:**
```bash
sudo systemctl start postgresql
# or
sudo service postgresql start
```

## Next Steps

After successful login:

1. **Change Your Password**
   - Go to Profile Settings
   - Change from `Password123!` to a strong, unique password

2. **Create Additional Users**
   - Go to Admin Panel > User Management
   - Create user accounts for your team
   - Assign appropriate roles (user, admin, super_admin)

3. **Enable 2FA** (if available)
   - Go to Security Settings
   - Enable Two-Factor Authentication

4. **Explore Features**
   - Chat with AI Karen
   - Configure LLM providers
   - Manage extensions

## Environment Variables

If you encounter issues, check these environment variables in `/home/user/AI-Karen/ui_launchers/KAREN-Theme-Default/.env.local`:

```env
# Backend connection
KAREN_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_KAREN_BACKEND_URL=http://localhost:8000

# Database (for backend)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=karen_user
POSTGRES_PASSWORD=karen_secure_pass_change_me
POSTGRES_DB=ai_karen
```

## Common Errors and Fixes

| Error | Solution |
|-------|----------|
| 401 Unauthorized | Use `Password123!` (capital P + !) |
| Cannot connect to authentication server | Start backend: `uvicorn server.app:app` |
| Account locked | Run unlock script: `python3 scripts/maintenance/unlock_admin_account.py` |
| No admin user exists | Run setup script: `python3 scripts/operations/setup_admin_proper.py` |
| Database connection error | Check PostgreSQL is running: `pg_isready` |

## Advanced Configuration

### Change Backend URL

If your backend is on a different host/port:

1. Edit `.env.local`:
   ```env
   KAREN_BACKEND_URL=http://your-backend-host:port
   NEXT_PUBLIC_KAREN_BACKEND_URL=http://your-backend-host:port
   ```

2. Restart the frontend:
   ```bash
   npm run dev
   ```

### Use Different Database

Edit backend environment or `.env` file:
```env
POSTGRES_HOST=your-db-host
POSTGRES_PORT=5432
POSTGRES_USER=your-db-user
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=your-db-name
```

Restart the backend after changing these values.

## Security Checklist

Before deploying to production:

- [ ] Change default admin password
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Enable 2FA for admin accounts
- [ ] Set strong database passwords
- [ ] Configure rate limiting
- [ ] Enable audit logging
- [ ] Review and update CSP headers
- [ ] Set up proper backup strategy
- [ ] Configure session timeout

## Getting Help

If you still have issues:

1. **Check logs:**
   - Backend logs: `/home/user/AI-Karen/logs/`
   - Frontend console: Press F12 in browser

2. **Read troubleshooting guide:**
   - See `AUTH_TROUBLESHOOTING.md` for detailed diagnostics

3. **File an issue:**
   - Repository: https://github.com/Zeus-Eternal/AI-Karen/issues
   - Include error messages and logs

## Quick Reference Card

```
┌─────────────────────────────────────────────┐
│         AI KAREN - QUICK REFERENCE          │
├─────────────────────────────────────────────┤
│ Default Credentials:                        │
│   Email: admin@kari.ai                      │
│   Password: Password123!                    │
├─────────────────────────────────────────────┤
│ Start Backend:                              │
│   uvicorn server.app:app --port 8000        │
├─────────────────────────────────────────────┤
│ Start Frontend:                             │
│   cd ui_launchers/KAREN-Theme-Default       │
│   npm run dev                               │
├─────────────────────────────────────────────┤
│ Setup Admin:                                │
│   python3 scripts/operations/               │
│           setup_admin_proper.py             │
├─────────────────────────────────────────────┤
│ Unlock Account:                             │
│   python3 scripts/maintenance/              │
│           unlock_admin_account.py           │
├─────────────────────────────────────────────┤
│ URLs:                                       │
│   Frontend: http://localhost:8000           │
│   Backend: http://localhost:8000/api        │
│   Health: /api/auth/health                  │
└─────────────────────────────────────────────┘
```

**Print this card and keep it handy!**
