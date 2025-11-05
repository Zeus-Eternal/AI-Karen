# Admin Management System Database Utilities

This directory contains database utilities and interfaces for the admin management system, providing role-based access control, audit logging, and system configuration management.

## Overview

The admin management system extends the existing authentication infrastructure with:

- **Role-based Access Control**: Three-tier hierarchy (Super Admin > Admin > User)
- **Audit Logging**: Comprehensive tracking of administrative actions
- **System Configuration**: Centralized application settings management
- **Permission System**: Fine-grained access control

## Database Schema

### New Tables Added

1. **Role Column in auth_users**: Added `role` field with values `super_admin`, `admin`, `user`
2. **audit_logs**: Tracks all administrative actions
3. **system_config**: Stores application configuration settings
4. **permissions**: Defines available permissions
5. **role_permissions**: Maps roles to permissions

### Database Functions

- `log_audit_event()`: Creates audit log entries
- `user_has_permission()`: Checks if user has specific permission
- `get_user_permissions()`: Returns all permissions for a user

## TypeScript Interfaces

### Core Models

- `User`: Enhanced user model with role information
- `AuditLog`: Audit trail entries
- `SystemConfig`: Configuration settings
- `Permission`: Permission definitions

### Utility Types

- `UserListFilter`: Filtering options for user queries
- `AuditLogFilter`: Filtering options for audit logs
- `PaginationParams`: Pagination configuration
- `PaginatedResponse<T>`: Paginated API responses

## Database Utilities

### AdminDatabaseUtils Class

Main utility class providing methods for:

- **User Management**: CRUD operations with role-based filtering
- **Audit Logging**: Creating and querying audit entries
- **Permission Checking**: Role and permission validation
- **System Configuration**: Managing application settings

### Key Methods

```typescript
// Get user with role information
async getUserWithRole(userId: string): Promise<User | null>

// Get filtered and paginated users
async getUsersWithRoleFilter(
  filter: UserListFilter,
  pagination: PaginationParams
): Promise<PaginatedResponse<User>>

// Check user permissions
async userHasPermission(userId: string, permissionName: string): Promise<boolean>

// Create audit log entry
async createAuditLog(entry: AuditLogEntry): Promise<string>

// Get system configuration
async getSystemConfig(category?: string): Promise<SystemConfig[]>
```

## Database Client Interface

### DatabaseClient Interface

Abstraction layer for database operations:

```typescript
interface DatabaseClient {
  query(sql: string, params?: any[]): Promise<QueryResult>;
  transaction<T>(callback: (client: DatabaseClient) => Promise<T>): Promise<T>;
}
```

### Implementations

- **MockDatabaseClient**: For testing and development
- **PostgreSQLClient**: For production (to be implemented)

## Usage Examples

### Basic Setup

```typescript
import { getAdminDatabaseUtils } from '@/lib/database';

const adminUtils = getAdminDatabaseUtils();
```

### User Management

```typescript
// Get user with role
const user = await adminUtils.getUserWithRole(userId);

// Filter users by role
const adminUsers = await adminUtils.getUsersWithRoleFilter({
  role: 'admin',
  is_active: true
});

// Check permissions
const canCreateUsers = await adminUtils.userHasPermission(userId, 'user.create');
```

### Audit Logging

```typescript
// Create audit log entry
await adminUtils.createAuditLog({
  user_id: adminUserId,
  action: 'user.create',
  resource_type: 'user',
  resource_id: newUserId,
  details: { email: 'new@example.com' },
  ip_address: '192.168.1.1'
});

// Query audit logs
const auditLogs = await adminUtils.getAuditLogs({
  user_id: userId,
  start_date: new Date('2024-01-01'),
  end_date: new Date('2024-12-31')
});
```

### System Configuration

```typescript
// Get security configuration
const securityConfig = await adminUtils.getSystemConfig('security');

// Update configuration
await adminUtils.updateSystemConfig(
  'password_min_length',
  12,
  adminUserId,
  'Updated minimum password length'
);
```

## Migration

The database migration `018_admin_management_system.sql` includes:

1. Adding role column to existing auth_users table
2. Creating new tables for audit logs, system config, and permissions
3. Setting up default permissions and role mappings
4. Creating database functions for common operations
5. Adding proper indexes for performance

## Testing

Tests are provided in `__tests__/admin-utils.test.ts` covering:

- User role management
- Permission checking
- Audit logging
- System configuration
- Database utility functions

Run tests with:
```bash
npm test -- --run src/lib/database/__tests__/admin-utils.test.ts
```

## Security Considerations

- All administrative actions are logged
- Role-based access control prevents privilege escalation
- Database functions validate permissions
- Audit logs are immutable once created
- System configuration changes are tracked

## Performance

- Indexes on frequently queried columns
- Pagination for large result sets
- Efficient role-based queries
- Connection pooling support (when implemented)

## Future Enhancements

- Real PostgreSQL client implementation
- Connection pooling
- Query optimization
- Backup and recovery procedures
- Performance monitoring