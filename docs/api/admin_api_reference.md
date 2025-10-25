# Admin Management System API Reference

This document provides comprehensive documentation for all admin management system API endpoints.

## Table of Contents

- [Authentication](#authentication)
- [Setup Endpoints](#setup-endpoints)
- [User Management](#user-management)
- [Admin Management](#admin-management)
- [System Configuration](#system-configuration)
- [Audit Logs](#audit-logs)
- [Security](#security)
- [Email Management](#email-management)
- [Performance Monitoring](#performance-monitoring)
- [Error Responses](#error-responses)

## Authentication

All admin API endpoints require authentication via session cookies. Additionally, most endpoints require specific role permissions:

- **Super Admin**: Full access to all endpoints
- **Admin**: Limited access to user management endpoints
- **User**: No access to admin endpoints

### Headers

```
Cookie: session=<session_token>
Content-Type: application/json
```

## Setup Endpoints

### Check First-Run Status

Checks if the system needs initial setup (no super admin exists).

**Endpoint:** `GET /api/admin/setup/check-first-run`

**Authentication:** None required

**Response:**
```json
{
  "needsSetup": boolean,
  "message": string
}
```

**Example:**
```bash
curl -X GET http://localhost:3000/api/admin/setup/check-first-run
```

### Create Super Admin

Creates the initial super admin account during first-run setup.

**Endpoint:** `POST /api/admin/setup/create-super-admin`

**Authentication:** None required (only works when no super admin exists)

**Request Body:**
```json
{
  "email": "admin@example.com",
  "username": "superadmin",
  "password": "SecurePassword123!",
  "confirmPassword": "SecurePassword123!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Super admin created successfully",
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "username": "superadmin",
    "role": "super_admin"
  }
}
```

## User Management

### List Users

Retrieves a paginated list of users with filtering and sorting options.

**Endpoint:** `GET /api/admin/users`

**Authentication:** Admin or Super Admin required

**Query Parameters:**
- `page` (number): Page number (default: 1)
- `limit` (number): Items per page (default: 20, max: 100)
- `search` (string): Search term for username/email
- `role` (string): Filter by role (user, admin, super_admin)
- `status` (string): Filter by status (active, inactive)
- `sortBy` (string): Sort field (username, email, createdAt, lastLogin)
- `sortOrder` (string): Sort direction (asc, desc)

**Response:**
```json
{
  "users": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "username": "username",
      "role": "user",
      "isActive": true,
      "emailVerified": true,
      "lastLogin": "2024-01-01T00:00:00Z",
      "createdAt": "2024-01-01T00:00:00Z",
      "createdBy": "uuid"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

### Create User

Creates a new user account.

**Endpoint:** `POST /api/admin/users`

**Authentication:** Admin or Super Admin required

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "username": "newuser",
  "password": "SecurePassword123!",
  "role": "user",
  "sendWelcomeEmail": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "User created successfully",
  "user": {
    "id": "uuid",
    "email": "newuser@example.com",
    "username": "newuser",
    "role": "user",
    "isActive": true
  }
}
```

### Get User Details

Retrieves detailed information about a specific user.

**Endpoint:** `GET /api/admin/users/{id}`

**Authentication:** Admin or Super Admin required

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "username",
    "role": "user",
    "isActive": true,
    "emailVerified": true,
    "lastLogin": "2024-01-01T00:00:00Z",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z",
    "createdBy": "uuid"
  }
}
```

### Update User

Updates user information.

**Endpoint:** `PUT /api/admin/users/{id}`

**Authentication:** Admin or Super Admin required

**Request Body:**
```json
{
  "email": "updated@example.com",
  "username": "updateduser",
  "isActive": true,
  "role": "user"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User updated successfully",
  "user": {
    "id": "uuid",
    "email": "updated@example.com",
    "username": "updateduser",
    "role": "user",
    "isActive": true
  }
}
```

### Delete User

Soft deletes a user account.

**Endpoint:** `DELETE /api/admin/users/{id}`

**Authentication:** Admin or Super Admin required

**Response:**
```json
{
  "success": true,
  "message": "User deleted successfully"
}
```

### Reset User Password

Resets a user's password and optionally sends them a notification.

**Endpoint:** `POST /api/admin/users/{id}/reset-password`

**Authentication:** Admin or Super Admin required

**Request Body:**
```json
{
  "newPassword": "NewSecurePassword123!",
  "sendNotification": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

### Bulk User Operations

Performs bulk operations on multiple users.

**Endpoint:** `POST /api/admin/users/bulk`

**Authentication:** Admin or Super Admin required

**Request Body:**
```json
{
  "operation": "activate|deactivate|delete|export",
  "userIds": ["uuid1", "uuid2", "uuid3"],
  "options": {
    "sendNotification": true,
    "format": "csv"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Bulk operation completed",
  "results": {
    "processed": 3,
    "successful": 2,
    "failed": 1,
    "errors": [
      {
        "userId": "uuid3",
        "error": "User not found"
      }
    ]
  }
}
```

### Import Users

Imports users from a CSV file.

**Endpoint:** `POST /api/admin/users/import`

**Authentication:** Admin or Super Admin required

**Content-Type:** `multipart/form-data`

**Request Body:**
- `file`: CSV file with user data
- `options`: JSON string with import options

**Response:**
```json
{
  "success": true,
  "message": "Users imported successfully",
  "results": {
    "total": 100,
    "imported": 95,
    "skipped": 3,
    "errors": 2,
    "details": [
      {
        "row": 5,
        "error": "Invalid email format"
      }
    ]
  }
}
```

### User Statistics

Retrieves user statistics and metrics.

**Endpoint:** `GET /api/admin/users/stats`

**Authentication:** Admin or Super Admin required

**Response:**
```json
{
  "totalUsers": 1000,
  "activeUsers": 950,
  "newUsersThisMonth": 50,
  "usersByRole": {
    "user": 980,
    "admin": 15,
    "super_admin": 5
  },
  "registrationTrend": [
    {
      "date": "2024-01-01",
      "count": 10
    }
  ]
}
```

## Admin Management

### List Admins

Retrieves a list of admin and super admin users.

**Endpoint:** `GET /api/admin/admins`

**Authentication:** Super Admin required

**Response:**
```json
{
  "admins": [
    {
      "id": "uuid",
      "email": "admin@example.com",
      "username": "admin",
      "role": "admin",
      "isActive": true,
      "lastLogin": "2024-01-01T00:00:00Z",
      "createdAt": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Promote User to Admin

Promotes a regular user to admin role.

**Endpoint:** `POST /api/admin/admins/promote/{id}`

**Authentication:** Super Admin required

**Request Body:**
```json
{
  "role": "admin",
  "sendNotification": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "User promoted to admin successfully"
}
```

### Demote Admin to User

Demotes an admin back to regular user role.

**Endpoint:** `POST /api/admin/admins/demote/{id}`

**Authentication:** Super Admin required

**Response:**
```json
{
  "success": true,
  "message": "Admin demoted to user successfully"
}
```

### Invite Admin

Sends an invitation to create an admin account.

**Endpoint:** `POST /api/admin/admins/invite`

**Authentication:** Super Admin required

**Request Body:**
```json
{
  "email": "newadmin@example.com",
  "role": "admin",
  "message": "Welcome to the admin team!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Admin invitation sent successfully",
  "invitationId": "uuid"
}
```

## System Configuration

### Get System Configuration

Retrieves system configuration settings.

**Endpoint:** `GET /api/admin/system/config`

**Authentication:** Super Admin required

**Query Parameters:**
- `category` (string): Filter by category (security, email, general)

**Response:**
```json
{
  "config": [
    {
      "id": "uuid",
      "key": "password_min_length",
      "value": "12",
      "category": "security",
      "updatedBy": "uuid",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Update System Configuration

Updates system configuration settings.

**Endpoint:** `PUT /api/admin/system/config`

**Authentication:** Super Admin required

**Request Body:**
```json
{
  "updates": [
    {
      "key": "password_min_length",
      "value": "14",
      "category": "security"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated successfully",
  "updated": 1
}
```

### System Activity Summary

Retrieves system activity summary and statistics.

**Endpoint:** `GET /api/admin/system/activity-summary`

**Authentication:** Super Admin required

**Response:**
```json
{
  "summary": {
    "totalUsers": 1000,
    "activeUsers": 950,
    "totalAdmins": 20,
    "recentLogins": 150,
    "auditEntries24h": 500,
    "systemHealth": "healthy"
  },
  "trends": {
    "userGrowth": 5.2,
    "loginActivity": 12.8,
    "adminActivity": 3.1
  }
}
```

## Audit Logs

### Get Audit Logs

Retrieves audit log entries with filtering and pagination.

**Endpoint:** `GET /api/admin/system/audit-logs`

**Authentication:** Super Admin required

**Query Parameters:**
- `page` (number): Page number
- `limit` (number): Items per page
- `userId` (string): Filter by user ID
- `action` (string): Filter by action type
- `resourceType` (string): Filter by resource type
- `startDate` (string): Start date filter (ISO format)
- `endDate` (string): End date filter (ISO format)

**Response:**
```json
{
  "logs": [
    {
      "id": "uuid",
      "userId": "uuid",
      "action": "user_created",
      "resourceType": "user",
      "resourceId": "uuid",
      "details": {
        "username": "newuser",
        "email": "newuser@example.com"
      },
      "ipAddress": "192.168.1.1",
      "userAgent": "Mozilla/5.0...",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1000,
    "totalPages": 20
  }
}
```

### Cleanup Audit Logs

Removes old audit log entries based on retention policy.

**Endpoint:** `POST /api/admin/system/audit-logs/cleanup`

**Authentication:** Super Admin required

**Request Body:**
```json
{
  "retentionMonths": 12,
  "dryRun": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Audit logs cleaned up successfully",
  "deletedCount": 5000,
  "retentionDate": "2023-01-01T00:00:00Z"
}
```

## Security

### Security Dashboard

Retrieves security metrics and alerts.

**Endpoint:** `GET /api/admin/security/dashboard`

**Authentication:** Super Admin required

**Response:**
```json
{
  "metrics": {
    "failedLogins24h": 25,
    "lockedAccounts": 3,
    "suspiciousActivity": 1,
    "mfaEnabled": 85.5
  },
  "alerts": [
    {
      "id": "uuid",
      "type": "multiple_failed_logins",
      "severity": "medium",
      "message": "Multiple failed login attempts detected",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Security Settings

Manages security configuration settings.

**Endpoint:** `GET /api/admin/security/settings`
**Endpoint:** `PUT /api/admin/security/settings`

**Authentication:** Super Admin required

**Response (GET):**
```json
{
  "settings": {
    "passwordPolicy": {
      "minLength": 12,
      "requireUppercase": true,
      "requireLowercase": true,
      "requireNumbers": true,
      "requireSpecialChars": true
    },
    "sessionSettings": {
      "adminTimeout": 1800,
      "userTimeout": 3600,
      "maxConcurrentSessions": 3
    },
    "loginSecurity": {
      "maxAttempts": 5,
      "lockoutDuration": 900,
      "progressiveDelay": true
    },
    "mfaSettings": {
      "requiredForAdmins": true,
      "requiredForUsers": false,
      "allowedMethods": ["totp", "sms"]
    }
  }
}
```

### Security Report

Generates a comprehensive security report.

**Endpoint:** `GET /api/admin/security/report`

**Authentication:** Super Admin required

**Query Parameters:**
- `startDate` (string): Report start date
- `endDate` (string): Report end date
- `format` (string): Report format (json, pdf, csv)

**Response:**
```json
{
  "report": {
    "period": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-31T23:59:59Z"
    },
    "summary": {
      "totalLogins": 10000,
      "failedLogins": 150,
      "accountLockouts": 12,
      "passwordResets": 45,
      "mfaActivations": 25
    },
    "threats": [
      {
        "type": "brute_force",
        "count": 5,
        "severity": "high"
      }
    ],
    "recommendations": [
      "Enable MFA for all admin accounts",
      "Review password policy settings"
    ]
  }
}
```

## Email Management

### Email Templates

Manages email templates for admin notifications.

**Endpoint:** `GET /api/admin/email/templates`
**Endpoint:** `POST /api/admin/email/templates`

**Authentication:** Super Admin required

### Email Queue

Manages the email delivery queue.

**Endpoint:** `GET /api/admin/email/queue`

**Authentication:** Super Admin required

### Email Statistics

Retrieves email delivery statistics.

**Endpoint:** `GET /api/admin/email/statistics`

**Authentication:** Super Admin required

## Performance Monitoring

### Performance Report

Retrieves system performance metrics.

**Endpoint:** `GET /api/admin/performance/report`

**Authentication:** Super Admin required

**Response:**
```json
{
  "metrics": {
    "responseTime": {
      "average": 150,
      "p95": 300,
      "p99": 500
    },
    "throughput": {
      "requestsPerSecond": 100,
      "peakRps": 250
    },
    "resources": {
      "cpuUsage": 45.2,
      "memoryUsage": 68.5,
      "diskUsage": 32.1
    },
    "database": {
      "connectionPool": 85,
      "queryTime": 25,
      "slowQueries": 3
    }
  }
}
```

## Error Responses

All endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid request parameters",
  "details": {
    "field": "email",
    "issue": "Invalid email format"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "Insufficient permissions",
  "requiredRole": "super_admin"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded",
  "retryAfter": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "requestId": "uuid"
}
```

## Rate Limiting

Admin API endpoints have the following rate limits:

- **Setup endpoints**: 5 requests per minute
- **User management**: 100 requests per minute
- **Admin management**: 50 requests per minute
- **System configuration**: 20 requests per minute
- **Audit logs**: 200 requests per minute
- **Security endpoints**: 30 requests per minute

Rate limits are enforced per IP address and authenticated user.

## Webhooks

Some admin operations support webhook notifications:

- User created/updated/deleted
- Admin role changes
- Security events
- System configuration changes

Configure webhooks in the system configuration panel.