/**
 * Test Endpoint Configuration
 * This script tests the current endpoint configuration to debug connectivity issues
 */

// Test environment variables
console.log('🧪 Testing Endpoint Configuration');
console.log('================================');

// Check if we're in browser environment
if (typeof window !== 'undefined') {
  console.log('🌐 Browser Environment Detected');
  console.log('Current URL:', window.location.href);
  console.log('Current Hostname:', window.location.hostname);
  console.log('Current Port:', window.location.port);
} else {
  console.log('🖥️ Node.js Environment Detected');
}

// Check process.env availability
if (typeof process !== 'undefined' && process.env) {
  console.log('📋 Environment Variables Available');
  
  // Check specific variables
  const envVars = [
    'NODE_ENV',
    'KAREN_BACKEND_URL',
    'NEXT_PUBLIC_KAREN_BACKEND_URL',
    'KAREN_ENVIRONMENT',
    'NEXT_PUBLIC_KAREN_ENVIRONMENT',
    'KAREN_NETWORK_MODE',
    'NEXT_PUBLIC_KAREN_NETWORK_MODE',
    'KAREN_EXTERNAL_HOST',
    'NEXT_PUBLIC_KAREN_EXTERNAL_HOST'
  ];
  
  envVars.forEach(varName => {
    const value = process.env[varName];
    console.log(`${varName}:`, value || 'undefined');
  });
} else {
  console.log('❌ No process.env available');
}

// Test configuration manager if available
try {
  // This will only work in the browser with the actual modules
  if (typeof window !== 'undefined' && window.location.hostname) {
    console.log('🔧 Testing Configuration Manager...');
    
    // Try to import and test the configuration manager
    // Note: This is just for testing - actual import would be different
    console.log('Configuration test would go here in actual browser environment');
  }
} catch (error) {
  console.log('❌ Configuration Manager Test Failed:', error.message);
}

console.log('✅ Endpoint Configuration Test Complete');