# AI Karen Database Migrations

## Overview

This directory contains the database migration files for AI Karen. The migrations have been completely reorganized and consolidated to provide a clean, production-ready database schema.

## Migration Structure

### Current Clean Organization

```
data/migrations/postgres/
├── 000_cleanup_redundant_migrations.sql    # Cleanup old redundant tables
├── 001_consolidated_production_schema.sql # Single source of truth for schema
└── [future migrations start from 002+]    # Incremental changes only
```

### Migration History

The previous 23 migration files have been **consolidated and removed** to eliminate confusion and maintain a clean, single source of truth. All redundant auth tables, overlapping schemas, and messy migrations have been cleaned up into the two essential migration files above.

## Key Changes

### ✅ **Consolidated Auth System**
- **Before**: 4+ separate auth migrations creating conflicting tables
- **After**: Single `users` table with all required fields (email, username, password, full_name, etc.)

### ✅ **Streamlined Schema**
- **Before**: 23 migration files with redundant and overlapping functionality
- **After**: 2 clean migrations providing complete production schema

### ✅ **Production Features**
- Multi-tenant architecture
- Comprehensive audit logging
- Rate limiting
- Security features (2FA, account locking)
- Plugin management
- System configuration
- Full conversation and messaging system

### ✅ **Required User Profile Fields**
All user profile requirements are now included:
- `email` (required, unique)
- `username` (optional, unique)
- `password_hash` (required, bcrypt)
- `full_name`, `first_name`, `last_name` (profile info)
- `display_name` (user-facing name)
- `is_active`, `is_verified` (account status)
- `roles` (JSONB array of permissions)
- `preferences` (JSONB user settings)
- Security fields (2FA, failed attempts, etc.)
- Social/profile fields (avatar, bio, location, etc.)

## Migration Execution Order

1. **Run the cleanup migration first:**
   ```sql
   \i data/migrations/postgres/000_cleanup_redundant_migrations.sql
   ```

2. **Then run the consolidated schema:**
   ```sql
   \i data/migrations/postgres/001_consolidated_production_schema.sql
   ```

## Default Accounts

The consolidated migration creates two default accounts:

- **Admin**: `admin@karen.ai` / `admin123`
  - Roles: `["super_admin", "admin", "user"]`
  - **⚠️ CHANGE PASSWORD IMMEDIATELY AFTER FIRST LOGIN**
- **Demo**: `demo@karen.ai` / `demo123`
  - Roles: `["user"]`

## Troubleshooting Login Issues

If you encounter login timeouts or "Request timed out" errors:

1. **Verify backend is running**: The API server should be accessible at `http://localhost:8000`
2. **Use correct credentials**: Only the accounts listed above exist in the database
3. **Check database connection**: Ensure the backend can connect to the PostgreSQL database
4. **Verify migration applied**: Confirm the consolidated schema has been applied to your database

**Test login with curl:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"email":"admin@karen.ai","password":"admin123"}' \
  http://localhost:8000/api/auth/login
```

**Run the database verification script:**
```bash
./scripts/verify_database_setup.sh
```
This script will check that all required tables exist, default accounts are created, and the backend API is responding.
  - For testing and demonstrations

## Database Tables Overview

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `tenants` | Multi-tenancy support | Domain-based tenant isolation |
| `users` | User accounts & profiles | Complete user management |
| `user_sessions` | Session management | Security monitoring, risk scoring |
| `conversations` | Chat conversations | AI context, tagging, archiving |
| `messages` | Individual messages | AI metadata, attachments, reactions |
| `plugins` | Plugin management | Installation, configuration, dependencies |
| `plugin_settings` | User plugin settings | Per-user plugin configuration |
| `audit_logs` | Comprehensive audit | Event logging, security monitoring |
| `password_reset_tokens` | Password reset | Secure token management |
| `email_verification_tokens` | Email verification | Account verification |
| `rate_limits` | Rate limiting | API and user action limits |
| `system_config` | Configuration | Key-value system settings |

## Utility Functions

The schema includes several utility functions for maintenance:

- `cleanup_expired_sessions()` - Remove expired sessions
- `cleanup_expired_tokens()` - Remove expired reset/verification tokens
- `cleanup_old_audit_logs(days)` - Archive old audit logs
- `get_system_stats()` - System statistics overview
- `lock_user_account(email, minutes)` - Security account locking

## Views

- `active_sessions` - Currently active user sessions
- `recent_user_activity` - Recent user activity summary

## Security Features

- **Password Security**: bcrypt hashing (12 rounds)
- **Session Security**: Risk scoring, suspicious activity detection
- **Account Protection**: Failed attempt tracking, automatic locking
- **Audit Logging**: Comprehensive event logging with security flags
- **Rate Limiting**: Configurable limits on API calls and user actions

## Performance Optimizations

- Comprehensive indexing strategy
- JSONB indexes for complex queries
- GIN indexes for array and text search
- Partitioning-ready structure for large datasets

## Migration from Old Schema

If you have an existing database with the old migration structure:

1. **Backup your data** (important!)
2. Run the cleanup migration to remove redundant tables
3. Run the consolidated schema migration
4. **Manually migrate** any critical data from old tables to new schema
5. Update your application code to use the new table structure

## Future Migrations

All future database changes should be incremental migrations starting from `002_*.sql`. These should only add new features or modify existing tables - never recreate the entire schema.

## Support

For migration issues or questions about the new schema, refer to the consolidated migration file comments or check the audit logs for any issues during migration execution.