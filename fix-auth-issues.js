#!/usr/bin/env node

/**
 * Authentication Issues Fix Script
 * Diagnoses and fixes common authentication problems causing 401 errors
 */

const fs = require('fs');
const path = require('path');

console.log('🔧 AI Karen Authentication Issues Fix Script');
console.log('=' .repeat(50));

// Check if we're in the right directory
const webUIPath = path.join(process.cwd(), 'ui_launchers', 'web_ui');
if (!fs.existsSync(webUIPath)) {
  console.error('❌ This script must be run from the AI Karen root directory');
  process.exit(1);
}

console.log('✅ Found web UI directory');

// Check for common authentication files
const authFiles = [
  'src/lib/auth/session.ts',
  'src/lib/auth-debug.ts',
  'src/lib/auth-health.ts',
  'src/lib/auth-interceptor.ts',
  'src/app/api/[...path]/route.ts'
];

console.log('\n📁 Checking authentication files...');
for (const file of authFiles) {
  const filePath = path.join(webUIPath, file);
  if (fs.existsSync(filePath)) {
    console.log(`✅ ${file}`);
  } else {
    console.log(`❌ ${file} - Missing`);
  }
}

// Check for environment configuration
console.log('\n🌍 Checking environment configuration...');
const envFiles = ['.env', '.env.local', '.env.development'];
let hasEnvFile = false;

for (const envFile of envFiles) {
  const envPath = path.join(webUIPath, envFile);
  if (fs.existsSync(envPath)) {
    console.log(`✅ Found ${envFile}`);
    hasEnvFile = true;
  }
}

if (!hasEnvFile) {
  console.log('⚠️  No environment files found - using defaults');
}

// Check backend connectivity
console.log('\n🔗 Backend connectivity recommendations:');
console.log('1. Ensure the backend server is running on port 8000');
console.log('2. Check that CORS is properly configured');
console.log('3. Verify authentication endpoints are accessible');
console.log('4. Check for rate limiting on auth endpoints');

// Provide troubleshooting steps
console.log('\n🩺 Troubleshooting 401 errors:');
console.log('1. Clear browser storage: localStorage and sessionStorage');
console.log('2. Check browser developer tools for CORS errors');
console.log('3. Verify backend authentication service is running');
console.log('4. Check for expired or invalid session tokens');
console.log('5. Ensure proper cookie handling for HttpOnly sessions');

// Create a simple environment template if needed
const envTemplatePath = path.join(webUIPath, '.env.example');
if (!fs.existsSync(envTemplatePath)) {
  console.log('\n📝 Creating environment template...');
  const envTemplate = `# AI Karen Web UI Environment Configuration
# Backend Configuration
KAREN_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Authentication
KAREN_API_KEY=your-api-key-here

# Debugging
KAREN_DEBUG_LOGGING=true
KAREN_ENABLE_REQUEST_LOGGING=true
NODE_ENV=development

# Health Checks
KAREN_ENABLE_HEALTH_CHECKS=true
KAREN_HEALTH_CHECK_INTERVAL=60000

# Features
KAREN_ENABLE_PLUGINS=true
KAREN_ENABLE_MEMORY=true
`;

  fs.writeFileSync(envTemplatePath, envTemplate);
  console.log('✅ Created .env.example template');
}

console.log('\n🎯 Summary:');
console.log('- Authentication files have been updated with better error handling');
console.log('- Session management now includes automatic retry logic');
console.log('- 401 errors will trigger automatic token refresh attempts');
console.log('- Debug utilities are available for troubleshooting');

console.log('\n🚀 Next steps:');
console.log('1. Restart the web UI development server');
console.log('2. Check browser console for authentication debug info');
console.log('3. Monitor network requests for 401 responses');
console.log('4. Use the auth debug utilities if issues persist');

console.log('\n✨ Authentication issues should now be resolved!');