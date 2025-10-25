import { test, expect } from '@playwright/test';

const TEST_CREDENTIALS = {
  email: process.env.NEXT_PUBLIC_DEV_ADMIN_EMAIL || 'admin@example.com',
  password: process.env.NEXT_PUBLIC_DEV_ADMIN_PASSWORD || 'adminadmin'
};

test('Login system diagnosis', async ({ page }) => {
  console.log('🚀 Starting login system diagnosis...');
  
  // Step 1: Load the application
  console.log('1. Loading application...');
  await page.goto('/', { waitUntil: 'networkidle', timeout: 30000 });
  console.log('✅ App loaded successfully');
  console.log('Current URL:', page.url());
  console.log('Page title:', await page.title());
  
  // Take initial screenshot
  await page.screenshot({ path: 'login-diagnosis-initial.png', fullPage: true });
  
  // Step 2: Look for login form elements
  console.log('2. Searching for login form elements...');
  
  const emailSelectors = [
    'input[type="email"]',
    'input[id="email"]',
    'input[name="email"]',
    '[data-testid*="email"]'
  ];
  
  const passwordSelectors = [
    'input[type="password"]',
    'input[id="password"]',
    'input[name="password"]',
    '[data-testid*="password"]'
  ];
  
  const submitSelectors = [
    'button[type="submit"]',
    'button:has-text("Sign In")',
    'button:has-text("Login")',
    '[data-testid*="submit"]',
    '[data-testid*="login"]'
  ];
  
  let emailInput = null;
  let passwordInput = null;
  let submitButton = null;
  
  // Find email input
  for (const selector of emailSelectors) {
    const element = page.locator(selector).first();
    if (await element.count() > 0) {
      emailInput = element;
      console.log(`✅ Found email input with selector: ${selector}`);
      break;
    }
  }
  
  // Find password input
  for (const selector of passwordSelectors) {
    const element = page.locator(selector).first();
    if (await element.count() > 0) {
      passwordInput = element;
      console.log(`✅ Found password input with selector: ${selector}`);
      break;
    }
  }
  
  // Find submit button
  for (const selector of submitSelectors) {
    const element = page.locator(selector).first();
    if (await element.count() > 0) {
      submitButton = element;
      console.log(`✅ Found submit button with selector: ${selector}`);
      break;
    }
  }
  
  if (!emailInput || !passwordInput || !submitButton) {
    console.log('❌ Login form elements not found');
    console.log('Email input found:', !!emailInput);
    console.log('Password input found:', !!passwordInput);
    console.log('Submit button found:', !!submitButton);
    
    // Check if user is already logged in
    const logoutElements = page.locator('button:has-text("Logout"), button:has-text("Sign Out"), a:has-text("Logout")');
    if (await logoutElements.count() > 0) {
      console.log('ℹ️  User appears to be already logged in');
      return;
    }
    
    // Check page content for debugging
    const bodyText = await page.locator('body').textContent();
    console.log('Page content preview:', bodyText?.substring(0, 500));
    
    return;
  }
  
  // Step 3: Test form interaction
  console.log('3. Testing form interaction...');
  
  try {
    await emailInput.fill(TEST_CREDENTIALS.email);
    console.log('✅ Email field filled');
    
    await passwordInput.fill(TEST_CREDENTIALS.password);
    console.log('✅ Password field filled');
    
    // Take screenshot before submit
    await page.screenshot({ path: 'login-diagnosis-before-submit.png', fullPage: true });
    
  } catch (error) {
    console.log('❌ Failed to fill form fields:', error);
    return;
  }
  
  // Step 4: Monitor network and submit
  console.log('4. Submitting form and monitoring network...');
  
  const responses: any[] = [];
  const consoleMessages: string[] = [];
  
  page.on('response', response => {
    if (response.url().includes('/auth/') || response.url().includes('/login') || response.url().includes('/api/auth/')) {
      responses.push({
        url: response.url(),
        status: response.status(),
        statusText: response.statusText()
      });
    }
  });
  
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
  
  // Take screenshot after submit
  await page.screenshot({ path: 'login-diagnosis-after-submit.png', fullPage: true });
  
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
  const errorSelectors = [
    '[role="alert"]',
    '.alert-error',
    '.error',
    '[data-testid*="error"]',
    '.text-red-500',
    '.text-destructive'
  ];
  
  for (const selector of errorSelectors) {
    const errorElements = page.locator(selector);
    const errorCount = await errorElements.count();
    
    if (errorCount > 0) {
      console.log(`🚨 Found ${errorCount} error elements with selector: ${selector}`);
      for (let i = 0; i < errorCount; i++) {
        const errorText = await errorElements.nth(i).textContent();
        console.log(`  Error ${i + 1}: ${errorText}`);
      }
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
  
  if (!loginSuccessful) {
    console.log('❌ Login appears to have failed - no success indicators found');
  }
  
  console.log('🏁 Login diagnosis complete');
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