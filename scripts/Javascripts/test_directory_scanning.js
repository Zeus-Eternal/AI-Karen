/**
 * Test script to verify directory scanning functionality
 */

async function testDirectoryScanning() {
  console.log('🧪 Testing Directory Scanning Implementation');
  
  const baseUrl = 'http://localhost:3000';
  
  // Test each scanning endpoint
  const endpoints = [
    '/api/models/scan/llama-cpp',
    '/api/models/scan/transformers', 
    '/api/models/scan/stable-diffusion',
    '/api/models/scan/flux'
  ];
  
  for (const endpoint of endpoints) {
    try {
      console.log(`\n📡 Testing ${endpoint}...`);
      
      const response = await fetch(`${baseUrl}${endpoint}`);
      const data = await response.json();
      
      console.log(`✅ ${endpoint} - Status: ${response.status}`);
      console.log(`   Models found: ${data.models?.length || 0}`);
      console.log(`   Directory: ${data.directory}`);
      console.log(`   Scan time: ${data.scan_time}`);
      
      if (data.models?.length > 0) {
        console.log(`   Sample model: ${data.models[0].filename || data.models[0].name || data.models[0].dirname}`);
      }
      
    } catch (error) {
      console.error(`❌ ${endpoint} - Error:`, error.message);
    }
  }
  
  // Test the enhanced model library endpoint with scanning
  try {
    console.log('\n📡 Testing enhanced model library with scanning...');
    
    const response = await fetch(`${baseUrl}/api/models/library?scan=true&includeHealth=true`);
    const data = await response.json();
    
    console.log(`✅ Enhanced library - Status: ${response.status}`);
    console.log(`   Total models: ${data.total_count}`);
    console.log(`   Local models: ${data.local_count}`);
    console.log(`   Source: ${data.source}`);
    
    if (data.models?.length > 0) {
      const modelTypes = [...new Set(data.models.map(m => m.type))];
      console.log(`   Model types found: ${modelTypes.join(', ')}`);
      
      const subtypes = [...new Set(data.models.map(m => m.subtype))];
      console.log(`   Model subtypes: ${subtypes.join(', ')}`);
    }
    
  } catch (error) {
    console.error('❌ Enhanced library - Error:', error.message);
  }
  
  console.log('\n🎉 Directory scanning test completed!');
}

// Run the test if this script is executed directly
if (typeof window === 'undefined') {
  testDirectoryScanning().catch(console.error);
}

module.exports = { testDirectoryScanning };