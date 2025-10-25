import { test, expect, Page } from '@playwright/test';

/**
 * Quick Login Debug Test
 * 
 * A focused test to quickly identify the most common login issues
 */

const TEST_CREDENTIALS = {
  email: process.env.NEXT_PUBLIC_DEV_ADMIN_EMAIL || 'admin@example.com',
  password: process.env.NEXT_PUBLIC_DEV_ADMIN_PASSWORD || 'adminadmin'
};

test.describe('Quick Login Debug', () => {
  
  test('Quick login issue diagnosis', async ({ page }) => {
    console.log('🚀 Starting quick login diagnosis...');
    
    // Step 1: Check if app loads
    console.log('1. Loading application...');
    try {
      await page.goto('/', { waitUntil: 'networkidle', timeout: 30000 });
      console.log('✅ App loaded successfully');
    } catch (error) {
      console.log('❌ App failed to load:', error);
      return;
    }
    
    // Step 2: Check for login form
    console.log('2. Looking for login form...');
    const loginForm = page.locator('form').first();
    const emailInput = page.locator('input[type="email"], input[id="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[id="password"]').first();
    const submitButton = page.locator('button[type="submit"], button:has-text("Sign In"), button:has-text("Login")').first();
    
    if (await emailInput.count() === 0) {
      console.log('❌ No email input found');
      console.log('Current page URL:', page.url());
      console.log('Page title:', await page.title());
      
      // Check if already logged in
      const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign Out"), a:has-text("Logout")');
      if (await logoutButton.count() > 0) {
        console.log('ℹ️  User appears to be already logged in');
        return;
      }
      
      // Take screenshot for debugging
      await page.screenshot({ path: 'quick-debug-no-login-form.png', fullPage: true });
      return;
    }
    
    console.log('✅ Login form found');
    
    // Step 3: Test form interaction
    console.log('3. Testing form interaction...');
    try {
      await emailInput.fill(TEST_CREDENTIALS.email);
      await passwordInput.fill(TEST_CREDENTIALS.password);
      console.log('✅ Form fields filled successfully');
    } catch (error) {
      console.log('❌ Failed to fill form fields:', error);
      return;
    }
    
    // Step 4: Submit form and monitor
    console.log('4. Submitting login form...');
    
    // Set up response monitoring
    const responses: any[] = [];
    page.on('response', response => {
      if (response.url().includes('/auth/') || response.url().includes('/login')) {
        responses.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText()
        });
      }
    });
    
    // Set up console monitoring
    const consoleMessages: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error' || msg.text().toLowerCase().includes('error')) {
        consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
      }
    });
    
    try {
      await submitButton.click();
      console.log('✅ Form submitted');
      
      // Wait for response
      await page.waitForTimeout(5000);
      
    } catch (error) {
      console.log('❌ Failed to submit form:', error);
    }
    
    // Step 5: Analyze results
    console.log('5. Analyzing results...');
    
    // Check responses
    if (responses.length > 0) {
      console.log('📡 Auth responses received:');
      responses.forEach(res => {
        console.log(`  ${res.status} ${res.statusText} - ${res.url}`);
      });
    } else {
      console.log('❌ No auth responses received - possible network issue');
    }
    
    // Check console errors
    if (consoleMessages.length > 0) {
      console.log('🚨 Console errors:');
      consoleMessages.forEach(msg => console.log(`  ${msg}`));
    }
    
    // Check current page state
    const currentUrl = page.url();
    console.log(`📍 Current URL: ${currentUrl}`);
    
    // Look for error messages
    const errorMessages = page.locator('[role="alert"], .alert-error, .error, [data-testid*="error"]');
    const errorCount = await errorMessages.count();
    
    if (errorCount > 0) {
      console.log('🚨 Error messages on page:');
      for (let i = 0; i < errorCount; i++) {
        const errorText = await errorMessages.nth(i).textContent();
        console.log(`  ${errorText}`);
      }
    }
    
    // Check if login was successful
    const successIndicators = [
      'dashboard', 'welcome', 'logout', 'sign out', 'profile'
    ];
    
    let loginSuccessful = false;
    for (const indicator of successIndicators) {
      const elements = page.locator(`:has-text("${indicator}")`);
      if (await elements.count() > 0) {
        console.log(`✅ Login appears successful - found "${indicator}"`);
        loginSuccessful = true;
        break;
      }
    }
    
    if (!loginSuccessful && currentUrl === page.url()) {
      console.log('❌ Login appears to have failed - still on same page');
    }
    
    // Take final screenshot
    await page.screenshot({ path: 'quick-debug-final-state.png', fullPage: true });
    
    console.log('🏁 Quick diagnosis complete');
  });

  test('Backend connectivity check', async ({ page }) => {
    console.log('🔍 Checking backend connectivity...');
    
    const backendUrls = [
      'http://localhost:8000',
      'http://localhost:8001', 
      'http://127.0.0.1:8000',
      'http://127.0.0.1:8001'
    ];
    
    for (const url of backendUrls) {
      console.log(`Testing ${url}...`);
      
      try {
        const response = await page.request.get(`${url}/health`, { timeout: 3000 });
        console.log(`  ✅ ${url} - Status: ${response.status()}`);
      } catch (error) {
        console.log(`  ❌ ${url} - Error: ${error}`);
      }
      
      try {
        const authResponse = await page.request.post(`${url}/api/auth/login`, {
          data: TEST_CREDENTIALS,
          timeout: 3000
        });
        console.log(`  ✅ ${url}/api/auth/login - Status: ${authResponse.status()}`);
      } catch (error) {
        console.log(`  ❌ ${url}/api/auth/login - Error: ${error}`);
      }
    }
  });

  test('Direct API login test', async ({ page }) => {
    console.log('🔍 Testing direct API login...');
    
    await page.goto('/');
    
    const result = await page.evaluate(async (credentials) => {
      try {
        console.log('Making direct login request...');
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(credentials),
          credentials: 'include'
        });
        
        const text = await response.text();
        console.log('Login response received:', response.status, text);
        
        return {
          success: true,
          status: response.status,
          statusText: response.statusText,
          body: text,
          headers: Object.fromEntries(response.headers.entries())
        };
      } catch (error) {
        console.error('Login request failed:', error);
        return {
          success: false,
          error: error.message
        };
      }
    }, TEST_CREDENTIALS);
    
    console.log('📊 Direct API login result:');
    console.log(JSON.stringify(result, null, 2));
    
    if (result.success && result.status === 200) {
      console.log('✅ Direct API login successful');
      
      // Test session validation
      const sessionResult = await page.evaluate(async () => {
        try {
          const response = await fetch('/api/auth/validate-session', {
            credentials: 'include'
          });
          const text = await response.text();
          return {
            status: response.status,
            body: text
          };
        } catch (error) {
          return {
            error: error.message
          };
        }
      });
      
      console.log('📊 Session validation result:');
      console.log(JSON.stringify(sessionResult, null, 2));
    } else {
      console.log('❌ Direct API login failed');
    }
  });
});