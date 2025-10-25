import { test, expect, Page, BrowserContext } from '@playwright/test';
import { chromium } from 'playwright';

/**
 * Comprehensive Login Audit and Debug Test Suite
 * 
 * This test suite performs a thorough audit of the login system to identify
 * why users can't login. It tests all aspects of the authentication flow.
 */

const TEST_CREDENTIALS = {
  email: process.env.NEXT_PUBLIC_DEV_ADMIN_EMAIL || 'admin@example.com',
  password: process.env.NEXT_PUBLIC_DEV_ADMIN_PASSWORD || 'adminadmin'
};

const BACKEND_URLS = [
  'http://localhost:8000',
  'http://localhost:8001', 
  'http://localhost:8002',
  'http://127.0.0.1:8000',
  'http://127.0.0.1:8001',
  'http://127.0.0.1:8002'
];

// Helper function to capture detailed network information
async function captureNetworkDetails(page: Page) {
  const networkLogs: any[] = [];
  const consoleLogs: any[] = [];
  
  page.on('request', request => {
    networkLogs.push({
      type: 'request',
      url: request.url(),
      method: request.method(),
      headers: request.headers(),
      postData: request.postData()
    });
  });
  
  page.on('response', response => {
    networkLogs.push({
      type: 'response',
      url: response.url(),
      status: response.status(),
      headers: response.headers()
    });
  });
  
  page.on('console', msg => {
    consoleLogs.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
  });
  
  page.on('pageerror', error => {
    consoleLogs.push({
      type: 'pageerror',
      text: error.message,
      stack: error.stack
    });
  });
  
  return { networkLogs, consoleLogs };
}

test.describe('Login System Audit & Debug', () => {
  
  test('1. Frontend Login Form Audit', async ({ page }) => {
    console.log('🔍 AUDIT: Testing frontend login form...');
    
    const { networkLogs, consoleLogs } = await captureNetworkDetails(page);
    
    // Navigate to the app
    await page.goto('/');
    
    // Check if we're redirected to login or if login form is visible
    await page.waitForLoadState('networkidle');
    
    // Look for login form elements
    const emailInput = page.locator('input[type="email"], input[id="email"]');
    const passwordInput = page.locator('input[type="password"], input[id="password"]');
    const submitButton = page.locator('button[type="submit"], button[data-testid="submit-button"]');
    
    console.log('📋 Login form elements check:');
    console.log('- Email input exists:', await emailInput.count() > 0);
    console.log('- Password input exists:', await passwordInput.count() > 0);
    console.log('- Submit button exists:', await submitButton.count() > 0);
    
    // Check if form is actually visible and functional
    if (await emailInput.count() > 0) {
      await expect(emailInput).toBeVisible();
      await expect(passwordInput).toBeVisible();
      await expect(submitButton).toBeVisible();
      
      // Test form interaction
      await emailInput.fill('test@example.com');
      await passwordInput.fill('testpassword');
      
      console.log('✅ Login form is present and interactive');
    } else {
      console.log('❌ Login form not found - checking current page state');
      console.log('Current URL:', page.url());
      console.log('Page title:', await page.title());
      
      // Take screenshot for debugging
      await page.screenshot({ path: 'login-audit-no-form.png', fullPage: true });
    }
    
    // Log any console errors
    if (consoleLogs.length > 0) {
      console.log('🚨 Console logs detected:');
      consoleLogs.forEach(log => console.log(`  ${log.type}: ${log.text}`));
    }
  });

  test('2. Backend API Connectivity Audit', async ({ page }) => {
    console.log('🔍 AUDIT: Testing backend API connectivity...');
    
    // Test each potential backend URL
    for (const backendUrl of BACKEND_URLS) {
      console.log(`Testing backend: ${backendUrl}`);
      
      try {
        // Test health/status endpoint
        const healthResponse = await page.request.get(`${backendUrl}/health`, {
          timeout: 5000
        });
        console.log(`  Health check: ${healthResponse.status()}`);
      } catch (error) {
        console.log(`  Health check failed: ${error}`);
      }
      
      try {
        // Test auth login endpoint
        const loginResponse = await page.request.post(`${backendUrl}/api/auth/login`, {
          data: TEST_CREDENTIALS,
          timeout: 5000
        });
        console.log(`  Login endpoint: ${loginResponse.status()}`);
        
        if (loginResponse.ok()) {
          const responseBody = await loginResponse.text();
          console.log(`  Login response: ${responseBody.substring(0, 200)}...`);
        }
      } catch (error) {
        console.log(`  Login endpoint failed: ${error}`);
      }
      
      try {
        // Test simple auth endpoint (fallback)
        const simpleAuthResponse = await page.request.post(`${backendUrl}/auth/login`, {
          data: TEST_CREDENTIALS,
          timeout: 5000
        });
        console.log(`  Simple auth endpoint: ${simpleAuthResponse.status()}`);
      } catch (error) {
        console.log(`  Simple auth endpoint failed: ${error}`);
      }
    }
  });

  test('3. Frontend-Backend Integration Audit', async ({ page }) => {
    console.log('🔍 AUDIT: Testing frontend-backend integration...');
    
    const { networkLogs, consoleLogs } = await captureNetworkDetails(page);
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Find and fill login form
    const emailInput = page.locator('input[type="email"], input[id="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[id="password"]').first();
    const submitButton = page.locator('button[type="submit"], button[data-testid="submit-button"]').first();
    
    if (await emailInput.count() > 0) {
      console.log('📝 Filling login form...');
      await emailInput.fill(TEST_CREDENTIALS.email);
      await passwordInput.fill(TEST_CREDENTIALS.password);
      
      console.log('🚀 Submitting login form...');
      await submitButton.click();
      
      // Wait for network activity
      await page.waitForTimeout(3000);
      
      // Analyze network requests
      const loginRequests = networkLogs.filter(log => 
        log.type === 'request' && log.url.includes('/api/auth/login')
      );
      
      const loginResponses = networkLogs.filter(log => 
        log.type === 'response' && log.url.includes('/api/auth/login')
      );
      
      console.log('🌐 Network Analysis:');
      console.log(`- Login requests made: ${loginRequests.length}`);
      console.log(`- Login responses received: ${loginResponses.length}`);
      
      if (loginRequests.length > 0) {
        loginRequests.forEach((req, i) => {
          console.log(`  Request ${i + 1}:`);
          console.log(`    URL: ${req.url}`);
          console.log(`    Method: ${req.method}`);
          console.log(`    Headers: ${JSON.stringify(req.headers, null, 2)}`);
          if (req.postData) {
            console.log(`    Body: ${req.postData}`);
          }
        });
      }
      
      if (loginResponses.length > 0) {
        loginResponses.forEach((res, i) => {
          console.log(`  Response ${i + 1}:`);
          console.log(`    URL: ${res.url}`);
          console.log(`    Status: ${res.status}`);
          console.log(`    Headers: ${JSON.stringify(res.headers, null, 2)}`);
        });
      }
      
      // Check for error messages on page
      const errorElements = page.locator('[role="alert"], .alert, .error, [data-testid*="error"]');
      const errorCount = await errorElements.count();
      
      if (errorCount > 0) {
        console.log('🚨 Error messages found on page:');
        for (let i = 0; i < errorCount; i++) {
          const errorText = await errorElements.nth(i).textContent();
          console.log(`  Error ${i + 1}: ${errorText}`);
        }
      }
      
      // Check current page state
      console.log('📍 Post-login page state:');
      console.log(`  Current URL: ${page.url()}`);
      console.log(`  Page title: ${await page.title()}`);
      
      // Check for authentication indicators
      const authIndicators = [
        'logout', 'sign out', 'profile', 'dashboard', 'welcome',
        '[data-testid*="user"]', '[data-testid*="auth"]'
      ];
      
      for (const indicator of authIndicators) {
        const elements = page.locator(indicator);
        const count = await elements.count();
        if (count > 0) {
          console.log(`  Found auth indicator "${indicator}": ${count} elements`);
        }
      }
      
    } else {
      console.log('❌ No login form found for integration test');
    }
    
    // Log console messages
    if (consoleLogs.length > 0) {
      console.log('📝 Console logs during login:');
      consoleLogs.forEach(log => {
        console.log(`  ${log.type}: ${log.text}`);
        if (log.location) {
          console.log(`    Location: ${JSON.stringify(log.location)}`);
        }
      });
    }
  });

  test('4. Cookie and Session Management Audit', async ({ page, context }) => {
    console.log('🔍 AUDIT: Testing cookie and session management...');
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check initial cookies
    const initialCookies = await context.cookies();
    console.log('🍪 Initial cookies:', initialCookies.length);
    initialCookies.forEach(cookie => {
      console.log(`  ${cookie.name}: ${cookie.value.substring(0, 50)}... (domain: ${cookie.domain})`);
    });
    
    // Attempt login via JavaScript (similar to the HAR test)
    const loginResult = await page.evaluate(async (credentials) => {
      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(credentials),
          credentials: 'include'
        });
        
        const responseText = await response.text();
        
        return {
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries()),
          body: responseText,
          ok: response.ok
        };
      } catch (error) {
        return {
          error: error.message,
          status: 0
        };
      }
    }, TEST_CREDENTIALS);
    
    console.log('🔐 Direct login API call result:');
    console.log(`  Status: ${loginResult.status}`);
    console.log(`  OK: ${loginResult.ok}`);
    console.log(`  Body: ${loginResult.body?.substring(0, 200)}...`);
    
    if (loginResult.headers) {
      console.log('  Response headers:');
      Object.entries(loginResult.headers).forEach(([key, value]) => {
        console.log(`    ${key}: ${value}`);
      });
    }
    
    // Check cookies after login attempt
    const postLoginCookies = await context.cookies();
    console.log('🍪 Post-login cookies:', postLoginCookies.length);
    postLoginCookies.forEach(cookie => {
      console.log(`  ${cookie.name}: ${cookie.value.substring(0, 50)}... (domain: ${cookie.domain}, httpOnly: ${cookie.httpOnly})`);
    });
    
    // Test session validation
    const sessionResult = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/auth/validate-session', {
          method: 'GET',
          credentials: 'include'
        });
        
        const responseText = await response.text();
        
        return {
          status: response.status,
          statusText: response.statusText,
          body: responseText,
          ok: response.ok
        };
      } catch (error) {
        return {
          error: error.message,
          status: 0
        };
      }
    });
    
    console.log('✅ Session validation result:');
    console.log(`  Status: ${sessionResult.status}`);
    console.log(`  OK: ${sessionResult.ok}`);
    console.log(`  Body: ${sessionResult.body}`);
  });

  test('5. Environment and Configuration Audit', async ({ page }) => {
    console.log('🔍 AUDIT: Testing environment and configuration...');
    
    // Check environment variables that might affect login
    const envVars = await page.evaluate(() => {
      return {
        NODE_ENV: process.env.NODE_ENV,
        NEXT_PUBLIC_DEV_ADMIN_EMAIL: process.env.NEXT_PUBLIC_DEV_ADMIN_EMAIL,
        NEXT_PUBLIC_DEV_ADMIN_PASSWORD: process.env.NEXT_PUBLIC_DEV_ADMIN_PASSWORD,
        NEXT_PUBLIC_DEBUG_AUTH: process.env.NEXT_PUBLIC_DEBUG_AUTH,
        // Don't expose sensitive vars, just check if they exist
        hasApiUrl: !!process.env.NEXT_PUBLIC_API_URL,
        hasBackendUrl: !!process.env.NEXT_PUBLIC_BACKEND_URL
      };
    });
    
    console.log('🌍 Environment configuration:');
    Object.entries(envVars).forEach(([key, value]) => {
      console.log(`  ${key}: ${value}`);
    });
    
    // Test API client configuration
    await page.goto('/');
    
    const apiClientTest = await page.evaluate(async () => {
      try {
        // Test if API client is properly configured
        const testResponse = await fetch('/api/health', {
          method: 'GET',
          credentials: 'include'
        });
        
        return {
          status: testResponse.status,
          ok: testResponse.ok,
          url: testResponse.url
        };
      } catch (error) {
        return {
          error: error.message
        };
      }
    });
    
    console.log('🔧 API client test:');
    console.log(`  Health endpoint: ${JSON.stringify(apiClientTest)}`);
  });

  test('6. Complete Login Flow Debug', async ({ page }) => {
    console.log('🔍 AUDIT: Complete login flow debug with detailed logging...');
    
    const { networkLogs, consoleLogs } = await captureNetworkDetails(page);
    
    // Enable verbose logging
    await page.addInitScript(() => {
      // Override console methods to capture more details
      const originalLog = console.log;
      const originalError = console.error;
      const originalWarn = console.warn;
      
      console.log = (...args) => {
        originalLog('[PLAYWRIGHT-LOG]', ...args);
      };
      
      console.error = (...args) => {
        originalError('[PLAYWRIGHT-ERROR]', ...args);
      };
      
      console.warn = (...args) => {
        originalWarn('[PLAYWRIGHT-WARN]', ...args);
      };
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Take initial screenshot
    await page.screenshot({ path: 'login-debug-initial.png', fullPage: true });
    
    // Find login form
    const emailInput = page.locator('input[type="email"], input[id="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[id="password"]').first();
    const submitButton = page.locator('button[type="submit"], button[data-testid="submit-button"]').first();
    
    if (await emailInput.count() > 0) {
      console.log('📝 Starting complete login flow...');
      
      // Fill form step by step
      console.log('  Step 1: Filling email...');
      await emailInput.fill(TEST_CREDENTIALS.email);
      await page.waitForTimeout(500);
      
      console.log('  Step 2: Filling password...');
      await passwordInput.fill(TEST_CREDENTIALS.password);
      await page.waitForTimeout(500);
      
      // Take screenshot before submit
      await page.screenshot({ path: 'login-debug-before-submit.png', fullPage: true });
      
      console.log('  Step 3: Submitting form...');
      await submitButton.click();
      
      // Wait and observe
      console.log('  Step 4: Waiting for response...');
      await page.waitForTimeout(5000);
      
      // Take screenshot after submit
      await page.screenshot({ path: 'login-debug-after-submit.png', fullPage: true });
      
      // Check final state
      console.log('  Step 5: Analyzing final state...');
      console.log(`    Final URL: ${page.url()}`);
      console.log(`    Page title: ${await page.title()}`);
      
      // Look for success/error indicators
      const successIndicators = page.locator('[data-testid*="success"], .success, [role="status"]');
      const errorIndicators = page.locator('[data-testid*="error"], .error, [role="alert"]');
      
      console.log(`    Success indicators: ${await successIndicators.count()}`);
      console.log(`    Error indicators: ${await errorIndicators.count()}`);
      
      if (await errorIndicators.count() > 0) {
        for (let i = 0; i < await errorIndicators.count(); i++) {
          const errorText = await errorIndicators.nth(i).textContent();
          console.log(`      Error ${i + 1}: ${errorText}`);
        }
      }
      
      // Final network analysis
      console.log('🌐 Final network analysis:');
      const authRequests = networkLogs.filter(log => 
        log.url.includes('/auth/') || log.url.includes('/api/auth/')
      );
      
      console.log(`  Total auth-related requests: ${authRequests.length}`);
      authRequests.forEach((req, i) => {
        console.log(`    ${i + 1}. ${req.type.toUpperCase()} ${req.url} - Status: ${req.status || 'pending'}`);
      });
      
    } else {
      console.log('❌ No login form found for complete flow test');
      await page.screenshot({ path: 'login-debug-no-form.png', fullPage: true });
    }
    
    // Final console log analysis
    console.log('📝 All console messages:');
    consoleLogs.forEach((log, i) => {
      console.log(`  ${i + 1}. [${log.type}] ${log.text}`);
    });
  });
});