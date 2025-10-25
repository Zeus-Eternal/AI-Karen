const { chromium } = require('playwright');

(async () => {
  console.log('🚀 Starting UI login test...');
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Monitor console messages
  page.on('console', msg => {
    console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
  });
  
  // Monitor network requests
  page.on('request', request => {
    if (request.url().includes('/auth/')) {
      console.log(`[REQUEST] ${request.method()} ${request.url()}`);
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('/auth/')) {
      console.log(`[RESPONSE] ${response.status()} ${response.url()}`);
    }
  });
  
  try {
    // Navigate to the app
    console.log('1. Navigating to app...');
    await page.goto('http://localhost:8010/', { waitUntil: 'networkidle' });
    
    // Take screenshot of initial state
    await page.screenshot({ path: 'ui-test-initial.png', fullPage: true });
    
    // Wait a bit for any loading states
    await page.waitForTimeout(3000);
    
    // Take screenshot after loading
    await page.screenshot({ path: 'ui-test-after-loading.png', fullPage: true });
    
    // Check current URL
    console.log('Current URL:', page.url());
    
    // Look for login form
    const emailInput = page.locator('input[type="email"], input[id="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[id="password"]').first();
    const submitButton = page.locator('button[type="submit"], button:has-text("Sign In")').first();
    
    const hasEmailInput = await emailInput.count() > 0;
    const hasPasswordInput = await passwordInput.count() > 0;
    const hasSubmitButton = await submitButton.count() > 0;
    
    console.log('Login form elements found:');
    console.log('- Email input:', hasEmailInput);
    console.log('- Password input:', hasPasswordInput);
    console.log('- Submit button:', hasSubmitButton);
    
    if (hasEmailInput && hasPasswordInput && hasSubmitButton) {
      console.log('2. Filling login form...');
      
      await emailInput.fill('admin@example.com');
      await passwordInput.fill('adminadmin');
      
      // Take screenshot before submit
      await page.screenshot({ path: 'ui-test-before-submit.png', fullPage: true });
      
      console.log('3. Submitting form...');
      await submitButton.click();
      
      // Wait for response
      await page.waitForTimeout(5000);
      
      // Take screenshot after submit
      await page.screenshot({ path: 'ui-test-after-submit.png', fullPage: true });
      
      console.log('Final URL:', page.url());
      
      // Check if we're now on the dashboard or main app
      const isDashboard = page.url().includes('dashboard') || 
                         await page.locator('text=Dashboard').count() > 0 ||
                         await page.locator('text=Karen AI').count() > 0;
      
      console.log('Login appears successful:', isDashboard);
      
    } else {
      console.log('❌ Login form not found');
      
      // Check if already logged in
      const loggedInIndicators = await page.locator('text=Dashboard, text=Logout, text=Sign Out').count();
      if (loggedInIndicators > 0) {
        console.log('✅ User appears to already be logged in');
      } else {
        console.log('❌ No login form and no logged-in indicators found');
        
        // Get page content for debugging
        const bodyText = await page.locator('body').textContent();
        console.log('Page content preview:', bodyText?.substring(0, 500));
      }
    }
    
  } catch (error) {
    console.error('Test failed:', error);
    await page.screenshot({ path: 'ui-test-error.png', fullPage: true });
  }
  
  console.log('🏁 Test complete. Check screenshots for visual debugging.');
  
  // Keep browser open for manual inspection
  console.log('Browser will stay open for 30 seconds for manual inspection...');
  await page.waitForTimeout(30000);
  
  await browser.close();
})();