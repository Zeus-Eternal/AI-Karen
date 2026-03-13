// This script uses Node.js built-in fetch (available in Node 18+)
// If running on older Node versions, install and use node-fetch

/**
 * Test script for chat API endpoints
 * Verifies that the chat API is properly connected and functional
 */

async function testChatAPI() {
  const baseUrl = process.env.API_BASE_URL || 'http://localhost:3000';
  
  console.log('Testing Chat API endpoints...');
  console.log(`Base URL: ${baseUrl}`);
  
  try {
    // Test GET /api/chat
    console.log('\n1. Testing GET /api/chat...');
    const getResponse = await fetch(`${baseUrl}/api/chat`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    console.log(`Status: ${getResponse.status}`);
    console.log(`Content-Type: ${getResponse.headers.get('content-type')}`);
    
    if (getResponse.ok) {
      const getData = await getResponse.json();
      console.log('GET /api/chat: ✅ SUCCESS');
      console.log('Response:', JSON.stringify(getData, null, 2));
    } else {
      console.log('GET /api/chat: ❌ FAILED');
      const errorText = await getResponse.text();
      console.log('Error:', errorText);
    }
    
    // Test POST /api/chat
    console.log('\n2. Testing POST /api/chat...');
    const postResponse = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'test-model',
        messages: [
          { role: 'user', content: 'Hello, test message' }
        ],
        stream: false
      }),
    });
    
    console.log(`Status: ${postResponse.status}`);
    console.log(`Content-Type: ${postResponse.headers.get('content-type')}`);
    
    if (postResponse.ok) {
      const postData = await postResponse.json();
      console.log('POST /api/chat: ✅ SUCCESS');
      console.log('Response:', JSON.stringify(postData, null, 2));
    } else {
      console.log('POST /api/chat: ❌ FAILED');
      const errorText = await postResponse.text();
      console.log('Error:', errorText);
    }
    
    // Test POST /api/chat with streaming
    console.log('\n3. Testing POST /api/chat with streaming...');
    const streamResponse = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        model: 'test-model',
        messages: [
          { role: 'user', content: 'Hello, streaming test' }
        ],
        stream: true
      }),
    });
    
    console.log(`Status: ${streamResponse.status}`);
    console.log(`Content-Type: ${streamResponse.headers.get('content-type')}`);
    
    if (streamResponse.ok) {
      console.log('POST /api/chat (streaming): ✅ SUCCESS');
      // For streaming, we'll just read the first chunk to verify it's working
      const reader = streamResponse.body.getReader();
      const { done, value } = await reader.read();
      if (!done) {
        console.log('First chunk:', new TextDecoder().decode(value));
      }
    } else {
      console.log('POST /api/chat (streaming): ❌ FAILED');
      const errorText = await streamResponse.text();
      console.log('Error:', errorText);
    }
    
    // Test GET /api/conversations
    console.log('\n4. Testing GET /api/conversations...');
    const convResponse = await fetch(`${baseUrl}/api/conversations`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    console.log(`Status: ${convResponse.status}`);
    console.log(`Content-Type: ${convResponse.headers.get('content-type')}`);
    
    if (convResponse.ok) {
      const convData = await convResponse.json();
      console.log('GET /api/conversations: ✅ SUCCESS');
      console.log('Response:', JSON.stringify(convData, null, 2));
    } else {
      console.log('GET /api/conversations: ❌ FAILED');
      const errorText = await convResponse.text();
      console.log('Error:', errorText);
    }
    
    console.log('\n✅ All tests completed!');
    
  } catch (error) {
    console.error('\n❌ Test failed with error:', error.message);
    process.exit(1);
  }
}

// Run the tests
testChatAPI();