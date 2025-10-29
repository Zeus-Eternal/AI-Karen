/**
 * Test script to verify the error response endpoint fix
 * Run this in the browser console after the fix is applied
 */

console.log('🔧 Testing Error Response Endpoint Fix...');

// Test the endpoint directly
async function testErrorResponseEndpoint() {
  try {
    const response = await fetch('http://localhost:8000/api/error-response/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        error_message: 'Test error from browser',
        error_type: 'TestError',
        status_code: 500,
        provider_name: 'test-provider',
        use_ai_analysis: false
      })
    });

    if (response.ok) {
      const data = await response.json();
      console.log('✅ Error response endpoint is working!');
      console.log('Response:', data);
      return true;
    } else {
      console.log('❌ Error response endpoint failed:', response.status, response.statusText);
      const errorText = await response.text();
      console.log('Error details:', errorText);
      return false;
    }
  } catch (error) {
    console.log('❌ Network error testing endpoint:', error);
    return false;
  }
}

// Test the frontend error panel functionality
async function testFrontendErrorPanel() {
  console.log('🔍 Testing frontend error panel...');
  
  // Look for any error panels on the page
  const errorPanels = document.querySelectorAll('[data-testid*="error"], .error-panel, .intelligent-error');
  
  if (errorPanels.length > 0) {
    console.log(`✅ Found ${errorPanels.length} error panel(s) on the page`);
    errorPanels.forEach((panel, index) => {
      console.log(`Panel ${index + 1}:`, panel);
    });
  } else {
    console.log('ℹ️ No error panels currently visible (this is normal if no errors are showing)');
  }
}

// Run the tests
async function runTests() {
  console.log('🚀 Starting Error Response Fix Tests...');
  console.log('');
  
  const endpointWorking = await testErrorResponseEndpoint();
  await testFrontendErrorPanel();
  
  console.log('');
  console.log('📋 Test Summary:');
  console.log(`   Backend endpoint: ${endpointWorking ? '✅ Working' : '❌ Failed'}`);
  console.log('   Frontend panels: ✅ Checked');
  
  if (endpointWorking) {
    console.log('');
    console.log('🎉 Error Response Fix Test Complete!');
    console.log('The HTTP 500 errors should no longer appear in the console.');
    console.log('Error analysis functionality is now working properly.');
  } else {
    console.log('');
    console.log('⚠️ Some issues remain - check the console for details.');
  }
}

// Auto-run the tests
runTests();