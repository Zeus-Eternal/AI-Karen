# Environment Variables Configuration Guide

This document provides comprehensive documentation for all environment variables used in the AI Karen system, with a focus on backend connectivity configuration and standardized variable usage.

## Overview

The AI Karen system uses a standardized set of environment variables to ensure consistent configuration across all environments. This guide covers the migration from legacy variables to the new standardized format, configuration validation, and best practices.

## Standardized Environment Variables

### Backend Connectivity

#### Primary Backend URLs

**KAREN_BACKEND_URL** (Server-side)
- **Description**: Primary backend URL for server-side requests (Next.js API routes)
- **Format**: `http://hostname:port` (no trailing slash)
- **Example**: `http://localhost:8000`
- **Scope**: Server-side only
- **Required**: No (defaults to `http://localhost:8000`)

**NEXT_PUBLIC_KAREN_BACKEND_URL** (Client-side)
- **Description**: Primary backend URL for client-side requests (browser-based)
- **Format**: `http://hostname:port` (no trailing slash)
- **Example**: `http://localhost:8000`
- **Scope**: Client-side (accessible in browser)
- **Required**: No (defaults to `http://localhost:8000`)

#### Fallback and High Availability URLs

**KAREN_FALLBACK_BACKEND_URLS**
- **Description**: Comma-separated fallback backend URLs for automatic failover
- **Format**: `http://host1:port,http://host2:port,http://host3:port`
- **Example**: `http://127.0.0.1:8000,http://host.docker.internal:8000`
- **Scope**: Both server and client-side
- **Required**: No (automatically generated based on environment)

**KAREN_HA_BACKEND_URLS**
- **Description**: High availability backend URLs for production load balancing
- **Format**: `http://host1:port,http://host2:port`
- **Example**: `http://backend1.example.com:8000,http://backend2.example.com:8000`
- **Scope**: Both server and client-side
- **Required**: No (recommended for production)
- **Environment**: Production only

#### Container-Specific Configuration

**KAREN_CONTAINER_BACKEND_HOST**
- **Description**: Backend hostname for Docker container environments
- **Format**: `hostname`
- **Example**: `backend`, `api`, `ai-karen-api`
- **Default**: `backend`
- **Environment**: Docker containers

**KAREN_CONTAINER_BACKEND_PORT**
- **Description**: Backend port for Docker container environments
- **Format**: `port_number`
- **Example**: `8000`
- **Default**: `8000`
- **Environment**: Docker containers

#### External Access Configuration

**KAREN_EXTERNAL_HOST**
- **Description**: External hostname for external network access
- **Format**: `hostname` or `ip_address`
- **Example**: `your-domain.com`, `192.168.1.100`
- **Required**: No (auto-detected when possible)
- **Environment**: External access scenarios

**KAREN_EXTERNAL_BACKEND_PORT**
- **Description**: Backend port for external network access
- **Format**: `port_number`
- **Example**: `8000`, `443`
- **Default**: `8000`
- **Environment**: External access scenarios

#### Legacy Support

**KAREN_BACKEND_PORT**
- **Description**: Backend port (legacy support)
- **Format**: `port_number`
- **Example**: `8000`
- **Default**: `8000`
- **Note**: Maintained for backward compatibility

### Timeout Configuration

**AUTH_TIMEOUT_MS**
- **Description**: Authentication timeout in milliseconds
- **Format**: `number`
- **Example**: `45000`
- **Default**: `45000` (45 seconds)
- **Range**: 5000-120000ms
- **Note**: Increased from 15s to 45s for database operations

**CONNECTION_TIMEOUT_MS**
- **Description**: Network connection timeout in milliseconds
- **Format**: `number`
- **Example**: `30000`
- **Default**: `30000` (30 seconds)
- **Range**: 1000-60000ms

**SESSION_VALIDATION_TIMEOUT_MS**
- **Description**: Session validation timeout in milliseconds
- **Format**: `number`
- **Example**: `30000`
- **Default**: `30000` (30 seconds)
- **Range**: 5000-60000ms

**HEALTH_CHECK_TIMEOUT_MS**
- **Description**: Health check timeout in milliseconds
- **Format**: `number`
- **Example**: `10000`
- **Default**: `10000` (10 seconds)
- **Range**: 1000-30000ms

**HEALTH_CHECK_INTERVAL_MS**
- **Description**: Interval between health checks in milliseconds
- **Format**: `number`
- **Example**: `30000`
- **Default**: `30000` (30 seconds)

### Retry Configuration

**MAX_RETRY_ATTEMPTS**
- **Description**: Maximum number of retry attempts for failed requests
- **Format**: `number`
- **Example**: `3`
- **Default**: `3`
- **Range**: 1-10

**RETRY_BASE_DELAY_MS**
- **Description**: Base delay between retries in milliseconds
- **Format**: `number`
- **Example**: `1000`
- **Default**: `1000` (1 second)
- **Range**: 100-5000ms

**RETRY_MAX_DELAY_MS**
- **Description**: Maximum delay between retries in milliseconds
- **Format**: `number`
- **Example**: `10000`
- **Default**: `10000` (10 seconds)
- **Range**: 1000-30000ms

**RETRY_EXPONENTIAL_BASE**
- **Description**: Exponential backoff base multiplier
- **Format**: `number`
- **Example**: `2`
- **Default**: `2`

**ENABLE_EXPONENTIAL_BACKOFF**
- **Description**: Enable exponential backoff for retries
- **Format**: `boolean`
- **Example**: `true`
- **Default**: `true`

## Deprecated Environment Variables

The following environment variables are deprecated and should be migrated to their standardized equivalents:

### Migration Table

| Deprecated Variable | Standardized Variable | Description |
|--------------------|-----------------------|-------------|
| `API_BASE_URL` | `KAREN_BACKEND_URL` | Server-side backend URL |
| `NEXT_PUBLIC_API_BASE_URL` | `NEXT_PUBLIC_KAREN_BACKEND_URL` | Client-side backend URL |
| `BACKEND_PORT` | `KAREN_BACKEND_PORT` | Backend port configuration |

### Migration Process

1. **Identify deprecated variables** in your environment files
2. **Update configuration** to use standardized variables
3. **Test connectivity** with new configuration
4. **Remove deprecated variables** after successful migration

## Environment-Specific Configuration

### Development Environment

```bash
# Development configuration
KAREN_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_KAREN_BACKEND_URL=http://localhost:8000
KAREN_FALLBACK_BACKEND_URLS=http://127.0.0.1:8000,http://host.docker.internal:8000

# Timeout configuration (development)
AUTH_TIMEOUT_MS=45000
CONNECTION_TIMEOUT_MS=30000
MAX_RETRY_ATTEMPTS=3
```

### Docker Environment

```bash
# Docker container configuration
KAREN_BACKEND_URL=http://api:8000
NEXT_PUBLIC_KAREN_BACKEND_URL=http://localhost:8000
KAREN_CONTAINER_BACKEND_HOST=api
KAREN_CONTAINER_BACKEND_PORT=8000
KAREN_FALLBACK_BACKEND_URLS=http://backend:8000,http://host.docker.internal:8000

# Docker-specific settings
DOCKER_CONTAINER=true
KAREN_CONTAINER_MODE=true
```

### Production Environment

```bash
# Production configuration
KAREN_BACKEND_URL=https://api.yourdomain.com
NEXT_PUBLIC_KAREN_BACKEND_URL=https://api.yourdomain.com
KAREN_HA_BACKEND_URLS=https://api1.yourdomain.com,https://api2.yourdomain.com
KAREN_FALLBACK_BACKEND_URLS=https://backup-api.yourdomain.com

# Production timeout configuration
AUTH_TIMEOUT_MS=60000
CONNECTION_TIMEOUT_MS=45000
MAX_RETRY_ATTEMPTS=5
RETRY_MAX_DELAY_MS=15000

# Environment identification
NODE_ENV=production
```

## Configuration Validation

### Automatic Validation

The system automatically validates environment configuration on startup and provides:

- **URL format validation**
- **Timeout range validation**
- **Conflict detection**
- **Environment-specific warnings**
- **Migration recommendations**

### Manual Validation

Use the validation script to check your configuration:

```bash
# Basic validation
node scripts/validate-environment.js

# Environment-specific validation
node scripts/validate-environment.js --env=production

# Generate migration script
node scripts/validate-environment.js --fix

# Verbose output
node scripts/validate-environment.js --verbose
```

### Validation Warnings

Common validation warnings and their solutions:

**"Deprecated variable found"**
- **Solution**: Migrate to standardized variable names

**"Conflicting backend URLs"**
- **Solution**: Ensure consistent URL values across related variables

**"Docker environment with localhost URLs"**
- **Solution**: Use container networking hostnames in Docker

**"Production without high availability URLs"**
- **Solution**: Configure fallback or HA URLs for production

## Best Practices

### URL Configuration

1. **Use consistent URLs** across related variables
2. **Avoid trailing slashes** in URL values
3. **Use HTTPS** in production environments
4. **Configure fallback URLs** for high availability

### Timeout Configuration

1. **Set appropriate timeouts** based on network conditions
2. **Use longer timeouts** for database operations
3. **Configure retries** for transient failures
4. **Monitor timeout effectiveness** in production

### Environment Management

1. **Use environment-specific files** (`.env.development`, `.env.production`)
2. **Validate configuration** before deployment
3. **Document custom configurations** for your team
4. **Regularly review** and update configurations

### Security Considerations

1. **Use HTTPS** for production URLs
2. **Avoid exposing internal URLs** in client-side variables
3. **Validate URL formats** to prevent injection attacks
4. **Use secure defaults** for timeout values

## Troubleshooting

### Common Issues

**Connection Refused**
- Check if backend URL is accessible
- Verify port configuration
- Test with fallback URLs

**Timeout Errors**
- Increase timeout values
- Check network latency
- Verify backend performance

**Docker Connectivity Issues**
- Use container hostnames instead of localhost
- Check Docker network configuration
- Verify container-to-container communication

**Environment Variable Not Found**
- Check variable name spelling
- Verify environment file loading
- Use validation script to identify issues

### Debug Mode

Enable debug logging to troubleshoot configuration issues:

```bash
# Enable debug logging
KAREN_DEBUG_LOGGING=true

# Check configuration in browser console
# Look for "Environment Configuration Manager" logs
```

## Migration Guide

### Step 1: Identify Current Configuration

Run the validation script to identify deprecated variables:

```bash
node scripts/validate-environment.js
```

### Step 2: Update Environment Files

Replace deprecated variables with standardized ones:

```bash
# Before (deprecated)
API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# After (standardized)
KAREN_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_KAREN_BACKEND_URL=http://localhost:8000
```

### Step 3: Test Configuration

Validate the new configuration:

```bash
node scripts/validate-environment.js --env=development
```

### Step 4: Deploy and Monitor

Deploy with new configuration and monitor for issues:

- Check application logs for connectivity errors
- Monitor response times and retry rates
- Verify fallback URL functionality

### Step 5: Clean Up

Remove deprecated variables after successful migration:

```bash
# Remove deprecated variables from .env files
# Update documentation
# Notify team members
```

## Support

For additional help with environment configuration:

1. **Run validation script** with `--verbose` flag
2. **Check application logs** for configuration warnings
3. **Review network connectivity** between components
4. **Consult team documentation** for custom configurations

## Related Documentation

- [Backend Connectivity Guide](./backend-connectivity.md)
- [Docker Configuration Guide](./docker-configuration.md)
- [Production Deployment Guide](./production-deployment.md)
- [Troubleshooting Guide](../troubleshooting/connectivity-issues.md)