/**
 * Comprehensive backend connectivity test for port 8000
 * This script will help ensure the backend is reachable
 */

const { spawn } = require('child_process');

console.log('🔍 Testing Backend Connectivity on Port 8000...\n');

// Test 1: Check if port 8000 is open
console.log('Test 1: Port 8000 Availability Check');
async function testPortAvailability() {
  return new Promise((resolve) => {
    const net = require('net');
    const socket = new net.Socket();
    
    const timeout = setTimeout(() => {
      socket.destroy();
      console.log('  ❌ Port 8000: Connection timeout (port likely closed)');
      resolve(false);
    }, 3000);
    
    socket.connect(8000, 'localhost', () => {
      clearTimeout(timeout);
      console.log('  ✅ Port 8000: Open and accepting connections');
      socket.destroy();
      resolve(true);
    });
    
    socket.on('error', (err) => {
      clearTimeout(timeout);
      console.log(`  ❌ Port 8000: ${err.message}`);
      resolve(false);
    });
  });
}

// Test 2: Check what's running on port 8000
console.log('\nTest 2: Process Check on Port 8000');
function checkPortProcess() {
  return new Promise((resolve) => {
    const lsof = spawn('lsof', ['-i', ':8000']);
    let output = '';
    
    lsof.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    lsof.on('close', (code) => {
      if (output.trim()) {
        console.log('  ✅ Process found on port 8000:');
        console.log(output);
      } else {
        console.log('  ❌ No process found running on port 8000');
      }
      resolve(output.trim() !== '');
    });
    
    lsof.on('error', (err) => {
      console.log('  ⚠️ Could not check port process (lsof not available)');
      resolve(false);
    });
  });
}

// Test 3: Try to reach common backend endpoints
console.log('\nTest 3: Backend Endpoint Connectivity');
async function testBackendEndpoints() {
  const endpoints = [
    { path: '/', description: 'Root endpoint' },
    { path: '/health', description: 'Health check' },
    { path: '/docs', description: 'API documentation' },
    { path: '/api', description: 'API root' },
    { path: '/api/auth', description: 'Auth endpoints' },
  ];
  
  for (const endpoint of endpoints) {
    try {
      const url = `http://localhost:8000${endpoint.path}`;
      console.log(`  Testing: ${url}`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch(url, {
        method: 'GET',
        signal: controller.signal,
        headers: { 'Accept': 'application/json' }
      });
      
      clearTimeout(timeoutId);
      
      console.log(`    ✅ ${endpoint.description}: ${response.status} ${response.statusText}`);
      
      // Try to get response body for successful requests
      if (response.ok) {
        try {
          const text = await response.text();
          if (text.length > 0) {
            console.log(`    📄 Response: ${text.substring(0, 100)}${text.length > 100 ? '...' : ''}`);
          }
        } catch (e) {
          console.log(`    📄 Response: [Binary or non-text content]`);
        }
      }
      
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log(`    ❌ ${endpoint.description}: Timeout (>5s)`);
      } else {
        console.log(`    ❌ ${endpoint.description}: ${error.message}`);
      }
    }
  }
}

// Test 4: Check network configuration
console.log('\nTest 4: Network Configuration Check');
function checkNetworkConfig() {
  console.log('Network Interface Check:');
  
  const os = require('os');
  const interfaces = os.networkInterfaces();
  
  Object.keys(interfaces).forEach(name => {
    const iface = interfaces[name];
    iface.forEach(details => {
      if (details.family === 'IPv4' && !details.internal) {
        console.log(`  🌐 ${name}: ${details.address}`);
      }
    });
  });
  
  console.log('\nLocalhost Variants:');
  const localhostVariants = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0'
  ];
  
  localhostVariants.forEach(host => {
    console.log(`  📍 ${host}:8000`);
  });
}

// Test 5: Test with curl if available
console.log('\nTest 5: Curl Test (if available)');
function testWithCurl() {
  return new Promise((resolve) => {
    const curl = spawn('curl', ['-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:8000/health']);
    let output = '';
    
    curl.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    curl.on('close', (code) => {
      if (code === 0) {
        const httpCode = output.trim();
        if (httpCode === '200') {
          console.log('  ✅ Curl test: Backend responding (HTTP 200)');
        } else if (httpCode === '000') {
          console.log('  ❌ Curl test: Connection failed');
        } else {
          console.log(`  ⚠️ Curl test: HTTP ${httpCode}`);
        }
      } else {
        console.log('  ❌ Curl test: Command failed');
      }
      resolve();
    });
    
    curl.on('error', (err) => {
      console.log('  ⚠️ Curl not available for testing');
      resolve();
    });
  });
}

// Test 6: Firewall and security check
console.log('\nTest 6: Security and Firewall Check');
function checkSecurity() {
  console.log('Common Issues That Block Port 8000:');
  console.log('  🔥 Firewall blocking the port');
  console.log('  🛡️ Security software blocking connections');
  console.log('  🚫 Port already in use by another service');
  console.log('  🌐 Backend bound to 127.0.0.1 instead of 0.0.0.0');
  console.log('  ⚙️ Backend not started or crashed');
  
  console.log('\nTo check firewall (Ubuntu/Debian):');
  console.log('  sudo ufw status');
  console.log('  sudo ufw allow 8000');
  
  console.log('\nTo check what\'s using port 8000:');
  console.log('  sudo netstat -tlnp | grep :8000');
  console.log('  sudo ss -tlnp | grep :8000');
}

// Test 7: Backend startup verification
console.log('\nTest 7: Backend Startup Verification');
function verifyBackendStartup() {
  console.log('Steps to ensure backend is running:');
  console.log('1. Navigate to project root directory');
  console.log('2. Activate virtual environment: source .env_ai/bin/activate');
  console.log('3. Check if main.py exists: ls -la main.py');
  console.log('4. Start backend: python main.py');
  console.log('5. Alternative: uvicorn main:app --reload --host 0.0.0.0 --port 8000');
  
  console.log('\nBackend should show output like:');
  console.log('  INFO:     Uvicorn running on http://0.0.0.0:8000');
  console.log('  INFO:     Application startup complete');
  
  console.log('\nIf backend fails to start, check:');
  console.log('  📦 Dependencies installed: pip install -r requirements.txt');
  console.log('  🐍 Python version compatibility');
  console.log('  📁 Working directory is correct');
  console.log('  🔧 Configuration files present');
}

// Run all tests
async function runAllTests() {
  try {
    const portOpen = await testPortAvailability();
    
    if (portOpen) {
      console.log('\n🎉 Port 8000 is open! Testing endpoints...');
      await testBackendEndpoints();
    } else {
      console.log('\n⚠️ Port 8000 is not accessible. Checking for processes...');
      await checkPortProcess();
    }
    
    checkNetworkConfig();
    await testWithCurl();
    checkSecurity();
    verifyBackendStartup();
    
  } catch (error) {
    console.error('Test execution error:', error);
  }
}

// Execute all tests
runAllTests().then(() => {
  console.log('\n🎯 Backend Connectivity Test Complete!');
  
  console.log('\n📋 Summary:');
  console.log('If port 8000 is NOT accessible:');
  console.log('  1. ❌ Backend is not running');
  console.log('  2. 🔧 Start the FastAPI backend server');
  console.log('  3. 🌐 Ensure it binds to 0.0.0.0:8000 (not just 127.0.0.1)');
  console.log('  4. 🔥 Check firewall settings');
  
  console.log('\nIf port 8000 IS accessible but login fails:');
  console.log('  1. ✅ Backend is running');
  console.log('  2. 🔍 Check authentication endpoints');
  console.log('  3. 🔐 Verify login credentials');
  console.log('  4. 🌐 Check CORS configuration');
  
  console.log('\n🚀 Next Steps:');
  console.log('1. Run this test to see current status');
  console.log('2. If backend not running: Start it with proper host binding');
  console.log('3. If backend running: Test login flow in browser');
  console.log('4. Check browser dev tools for network errors');
  
  console.log('\n💡 Quick Backend Start Command:');
  console.log('cd /media/zeus/Development3/KIRO/AI-Karen');
  console.log('source .env_ai/bin/activate');
  console.log('uvicorn main:app --reload --host 0.0.0.0 --port 8000');
});