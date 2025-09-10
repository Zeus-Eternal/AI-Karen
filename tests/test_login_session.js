#!/usr/bin/env node

/**
 * Test script to verify login and session management
 */

const fetch = require('node-fetch');

const BASE_URL = 'http://localhost:8010';

async function testLogin() {
  console.log('🔐 Testing login and session management...\n');
  
  try {
    // Step 1: Login
    console.log('1. Attempting login...');
    const loginResponse = await fetch(`${BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'admin@example.com',
        password: 'admin123'
      })
    });
    
    if (!loginResponse.ok) {
      const errorText = await loginResponse.text();
      console.error('❌ Login failed:', loginResponse.status, errorText);
      return;
    }
    
    const loginData = await loginResponse.json();
    console.log('✅ Login successful!');
    console.log('   User ID:', loginData.user?.user_id);
    console.log('   Email:', loginData.user?.email);
    console.log('   Token Type:', loginData.token_type);
    console.log('   Expires In:', loginData.expires_in, 'seconds');
    
    // Extract cookies from response
    const cookies = loginResponse.headers.get('set-cookie');
    console.log('   Cookies:', cookies ? 'Present' : 'None');
    
    // Step 2: Test authenticated endpoint with token
    console.log('\n2. Testing authenticated endpoint with Bearer token...');
    const authHeader = `Bearer ${loginData.access_token}`;
    
    const meResponse = await fetch(`${BASE_URL}/api/auth/me`, {
      headers: {
        'Authorization': authHeader,
        'Cookie': cookies || ''
      }
    });
    
    if (meResponse.ok) {
      const meData = await meResponse.json();
      console.log('✅ Authenticated request successful!');
      console.log('   Current user:', meData.email);
    } else {
      const errorText = await meResponse.text();
      console.log('❌ Authenticated request failed:', meResponse.status, errorText);
    }
    
    // Step 3: Test model library endpoint
    console.log('\n3. Testing model library endpoint...');
    const modelsResponse = await fetch(`${BASE_URL}/api/models/library`, {
      headers: {
        'Authorization': authHeader,
        'Cookie': cookies || ''
      }
    });
    
    if (modelsResponse.ok) {
      const modelsData = await modelsResponse.json();
      console.log('✅ Model library request successful!');
      console.log('   Models available:', Array.isArray(modelsData) ? modelsData.length : 'Unknown');
    } else {
      const errorText = await modelsResponse.text();
      console.log('❌ Model library request failed:', modelsResponse.status, errorText);
    }
    
    console.log('\n🎉 Authentication test completed!');
    
  } catch (error) {
    console.error('❌ Test failed with error:', error.message);
  }
}

// Run the test
testLogin();