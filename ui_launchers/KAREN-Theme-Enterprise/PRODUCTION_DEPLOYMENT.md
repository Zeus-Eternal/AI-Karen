# Production Deployment Guide

This guide covers the production-ready changes made to the AI Karen Web UI frontend to ensure security and proper functionality in production environments.

## Overview of Changes

### 1. Removed Hardcoded Credentials and Development Scripts

**LoginForm Component (`src/components/auth/LoginForm.tsx`)**
- Removed hardcoded credentials from error messages
- Removed development script references (`python3 scripts/...`)
- Replaced with generic user-friendly messages
- Made troubleshooting section development-only

### 2. Environment-Aware Logging

**New Environment Utilities (`src/lib/environment-utils.ts`)**
- Created centralized environment checking utilities
- Implemented conditional logging that only logs in development or when debug is enabled
- Added error message sanitization for production
- Created generic error messages for production use

**Updated Components**
- `AuthContext.tsx`: Updated to use environment-aware logging
- `app/error.tsx`: Updated error handling with production-safe messages
- `app/global-error.tsx`: Updated global error boundary
- `app/providers-inner.tsx`: Updated provider initialization logging
- `app/extensions/management/page.tsx`: Updated extension management logging

### 3. Mock Data and Development Features

**Extensions API (`src/app/api/extensions/route.ts`)**
- Modified to return empty response instead of sample data in production
- Added environment checks for fallback behavior
- Updated headers to indicate service availability

**Development Auth (`src/lib/auth/development-auth.ts`)**
- Updated to use centralized environment checking
- Ensured mock authentication is disabled in production
- Simplified environment detection logic

### 4. Production Configuration

**Updated Configuration (`src/lib/config.ts`)**
- Made debug logging disabled by default in production
- Disabled experimental features in production
- Disabled developer tools in production
- Disabled UI badges in production
- Updated CORS origins for production security
- Enhanced backend URL resolution for production environments
- Added HTTPS support for production backend connections

**Updated Environment Configuration Manager (`src/lib/config/environment-config-manager.ts`)**
- Enhanced primary URL determination with production HTTPS support
- Improved fallback URL generation for production environments
- Added production-specific endpoint alternatives
- Better protocol handling (HTTP vs HTTPS) based on environment

**Updated Authentication API Routes**
- Enhanced login route with production cookie domain settings
- Improved logout route with production security options
- Updated validate-session route for production backend URLs
- Added proper cookie domain configuration for production

**Production Environment File (`.env.production`)**
- Created comprehensive production-specific environment configuration
- Disabled all development features
- Configured secure CORS origins with multiple domains
- Set appropriate timeouts and retry limits
- Added high availability backend URL configuration
- Configured production backend URLs with HTTPS

## Deployment Instructions

### 1. Environment Setup

1. Copy `.env.production` to `.env.local` and update with your production values:
   ```bash
   # Use the deployment script for guided setup
   chmod +x ui_launchers/KAREN-Theme-Default/scripts/deploy-production.sh
   cd ui_launchers/KAREN-Theme-Default && ./scripts/deploy-production.sh
   
   # Or manually copy and configure
   # cp ui_launchers/KAREN-Theme-Default/.env.production ui_launchers/KAREN-Theme-Default/.env.local
   ```

2. Update the following values in `.env.local`:
   - `KAREN_EXTERNAL_HOST`: Your production API domain
   - `KARI_CORS_ORIGINS`: Your production frontend domain(s)
   - Any other production-specific settings

### 2. Build for Production

1. Set the environment variable:
   ```bash
   export NODE_ENV=production
   ```

2. Build the application:
   ```bash
   cd ui_launchers/KAREN-Theme-Default
   npm run build
   ```

### 3. Production Features

The following features are automatically disabled in production:
- Debug logging and console output
- Development tools and developer mode
- Experimental features
- Mock data and sample data fallbacks
- UI badges showing model/latency information
- Extension system (if not explicitly enabled)
- Voice features (if not explicitly enabled)

### 4. Security Considerations

1. **Error Messages**: All error messages are sanitized in production to prevent information disclosure
2. **Logging**: Sensitive information is not logged in production
3. **CORS**: Origins are restricted to production domains
4. **Authentication**: Mock authentication is completely disabled
5. **API Endpoints**: Development-only endpoints return appropriate responses

### 5. Verification

To verify production deployment:

1. Check that debug logging is disabled:
   - No console.log/debug/warn output in browser console
   - Network requests don't include debug headers

2. Verify error handling:
   - Error messages are user-friendly and generic
   - No stack traces or internal paths exposed

3. Check authentication:
   - Mock users are not available
   - Real authentication flow is working

4. Test features:
   - Development tools are hidden
   - Experimental features are disabled
   - Extension management works with real data

## Troubleshooting

### Issue: Development features appearing in production
**Solution**: Ensure `NODE_ENV=production` is set during build and deployment

### Issue: Error messages too verbose
**Solution**: Check that environment utilities are being used instead of direct console logging

### Issue: Mock data appearing in production
**Solution**: Verify all API routes have proper environment checks

## Post-Deployment Checklist

- [ ] Environment variables properly configured
- [ ] Debug logging disabled
- [ ] Error messages sanitized
- [ ] Development features disabled
- [ ] CORS properly configured with production domains
- [ ] Authentication flow working with production backend
- [ ] HTTPS URLs configured for production
- [ ] Cookie domains set for production
- [ ] High availability URLs configured (if needed)
- [ ] No hardcoded credentials in error messages
- [ ] Mock data disabled
- [ ] Console output minimal in production
- [ ] Deployment script executed successfully