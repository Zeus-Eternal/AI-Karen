#!/usr/bin/env node

/**
 * Debug Configuration Script
 * This script helps debug what environment variables are being loaded
 */

console.log('🔍 AI Karen Web UI Configuration Debug');
console.log('=====================================');

// Check Node.js environment variables
console.log('\n📋 Node.js Environment Variables:');
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('PORT:', process.env.PORT);

// Check Karen-specific environment variables
console.log('\n🔧 Karen Configuration Variables:');
console.log('KAREN_BACKEND_URL:', process.env.KAREN_BACKEND_URL);
console.log('KAREN_ENVIRONMENT:', process.env.KAREN_ENVIRONMENT);
console.log('KAREN_NETWORK_MODE:', process.env.KAREN_NETWORK_MODE);
console.log('KAREN_EXTERNAL_HOST:', process.env.KAREN_EXTERNAL_HOST);
console.log('KAREN_FALLBACK_BACKEND_URLS:', process.env.KAREN_FALLBACK_BACKEND_URLS);

// Check Next.js public environment variables
console.log('\n🌐 Next.js Public Environment Variables:');
console.log('NEXT_PUBLIC_KAREN_BACKEND_URL:', process.env.NEXT_PUBLIC_KAREN_BACKEND_URL);
console.log('NEXT_PUBLIC_KAREN_ENVIRONMENT:', process.env.NEXT_PUBLIC_KAREN_ENVIRONMENT);
console.log('NEXT_PUBLIC_KAREN_NETWORK_MODE:', process.env.NEXT_PUBLIC_KAREN_NETWORK_MODE);
console.log('NEXT_PUBLIC_KAREN_EXTERNAL_HOST:', process.env.NEXT_PUBLIC_KAREN_EXTERNAL_HOST);
console.log('NEXT_PUBLIC_KAREN_FALLBACK_BACKEND_URLS:', process.env.NEXT_PUBLIC_KAREN_FALLBACK_BACKEND_URLS);

// Check API URL variables
console.log('\n🔗 API Configuration:');
console.log('NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);

console.log('\n✅ Configuration debug complete!');
console.log('\nTo run this script:');
console.log('cd ui_launchers/KAREN-Theme-Default && node debug-config.js');