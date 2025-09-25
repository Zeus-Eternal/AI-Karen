# Environment Setup Fix - Resolve Docker Compose Warnings

## Issue Description

You're seeing warnings when running `docker compose up`:

```
WARN[0000] The "REDIS_PASSWORD" variable is not set. Defaulting to a blank string.
WARN[0000] The "POSTGRES_PASSWORD" variable is not set. Defaulting to a blank string.
WARN[0000] The "POSTGRES_DB" variable is not set. Defaulting to a blank string.
```

## Root Cause

The Docker Compose file expects environment variables that aren't set in your `.env` file.

## Quick Fix

### Step 1: Create/Update .env File

The `.env` file has been created for you with proper defaults. Verify it exists:

```bash
ls -la .env
```

If it doesn't exist, create it:

```bash
cp .env.example .env
```

### Step 2: Verify Environment Variables

Check that key variables are set:

```bash
grep -E "(POSTGRES_|REDIS_|MINIO_)" .env
```

Should show:
```
POSTGRES_USER=karen_user
POSTGRES_PASSWORD=karen_secure_pass_change_me
POSTGRES_DB=ai_karen
REDIS_PASSWORD=karen_redis_pass
MINIO_ACCESS_KEY=ai-karen-minio
MINIO_SECRET_KEY=ai-karen-minio-secret
```

### Step 3: Restart Services

```bash
# Stop any running services
docker compose down

# Start with proper environment
docker compose up -d

# Check status
docker compose ps
```

## Verification

### Check No More Warnings

When you run `docker compose up`, you should see:
- ✅ No WARN messages about missing variables
- ✅ Services starting successfully
- ✅ Health checks passing

### Test Database Connection

```bash
# Test PostgreSQL
docker compose exec postgres psql -U karen_user -d ai_karen -c "SELECT version();"

# Test Redis
docker compose exec redis redis-cli -a karen_redis_pass ping
```

### Test API Health

```bash
# Wait for services to be ready
sleep 30

# Test API
curl http://localhost:8000/health
```

## Environment Variables Explained

### Database Variables
```bash
POSTGRES_USER=karen_user          # Database username
POSTGRES_PASSWORD=karen_secure_pass_change_me  # Database password
POSTGRES_DB=ai_karen             # Database name
POSTGRES_HOST=localhost          # Database host
POSTGRES_PORT=5433              # External port mapping
```

### Redis Variables
```bash
REDIS_PASSWORD=karen_redis_pass  # Redis authentication password
REDIS_PORT=6380                 # External port mapping (avoids conflicts)
REDIS_URL=redis://:karen_redis_pass@redis:6379/0  # Full connection string
```

### MinIO Variables (for Milvus)
```bash
MINIO_ACCESS_KEY=ai-karen-minio     # MinIO access key
MINIO_SECRET_KEY=ai-karen-minio-secret  # MinIO secret key
MINIO_ROOT_USER=ai-karen-minio      # MinIO root user
MINIO_ROOT_PASSWORD=ai-karen-minio-secret  # MinIO root password
```

### Backend API Variables
```bash
KAREN_BACKEND_URL=http://127.0.0.1:8000  # Backend API URL
AUTH_SECRET_KEY=dev-secret-key-change-in-production  # JWT secret
AUTH_DEV_MODE=true                       # Enable development mode
```

## Security Notes

### Development vs Production

**Development (current setup):**
- Simple passwords for easy setup
- Development mode enabled
- Permissive CORS settings
- Security features disabled

**Production (change these):**
- Strong, unique passwords
- Disable development mode
- Restrict CORS origins
- Enable security features

### Change for Production

```bash
# Generate secure passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
AUTH_SECRET_KEY=$(openssl rand -base64 32)

# Update security settings
AUTH_DEV_MODE=false
AUTH_ENABLE_SECURITY_FEATURES=true
AUTH_ENABLE_RATE_LIMITING=true
```

## Troubleshooting

### Still Getting Warnings?

1. **Check .env file location:**
   ```bash
   pwd  # Should be in AI-Karen root directory
   ls -la .env  # File should exist
   ```

2. **Check .env file format:**
   ```bash
   head -10 .env  # Should show variable assignments
   ```

3. **Reload environment:**
   ```bash
   docker compose down
   docker compose up -d
   ```

### Services Not Starting?

1. **Check logs:**
   ```bash
   docker compose logs postgres
   docker compose logs redis
   ```

2. **Check ports:**
   ```bash
   ss -ltnp | grep -E ':(5433|6380|8000)'
   ```

3. **Clean restart:**
   ```bash
   docker compose down -v  # WARNING: Removes data
   docker compose up -d
   ```

### Database Connection Issues?

1. **Wait for services:**
   ```bash
   # Services need time to initialize
   sleep 60
   ```

2. **Check health:**
   ```bash
   docker compose exec postgres pg_isready -U karen_user -d ai_karen
   docker compose exec redis redis-cli -a karen_redis_pass ping
   ```

3. **Initialize database:**
   ```bash
   python create_tables.py
   python create_admin_user.py
   ```

## Success Indicators

✅ **Environment properly configured when:**
- No WARN messages during `docker compose up`
- All services show "Up" status in `docker compose ps`
- Health checks pass
- API responds on http://localhost:8000/health
- Database connections work

❌ **Still needs fixing if:**
- WARN messages about missing variables
- Services showing "Exit" status
- Connection refused errors
- Health checks failing

## Next Steps

After fixing the environment:

1. **Initialize the system:**
   ```bash
   python create_tables.py
   python create_admin_user.py
   ```

2. **Test the web UI:**
   ```bash
   # Should be accessible at:
   open http://localhost:8020
   ```

3. **Check API documentation:**
   ```bash
   open http://localhost:8000/docs
   ```

This should resolve all the environment variable warnings and get your AI-Karen system running properly.