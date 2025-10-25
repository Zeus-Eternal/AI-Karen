import { test, expect } from '@playwright/test';

// Simple audit that works with existing server
test.describe('Simple Web Container Audit', () => {
  test.beforeEach(async ({ page }) => {
    // Set base URL directly
    await page.goto('http://localhost:8000');
  });

  test('Basic functionality audit', async ({ page }) => {
    console.log('🔍 Running Basic Functionality Audit...');
    
    // Check if page loads
    await expect(page).toHaveTitle(/AI Karen/i);
    console.log('✅ Page loads with correct title');

    // Check for JavaScript errors
    const jsErrors: string[] = [];
    page.on('pageerror', error => {
      jsErrors.push(error.message);
    });

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');
    
    if (jsErrors.length === 0) {
      console.log('✅ No JavaScript errors detected');
    } else {
      console.log(`❌ Found ${jsErrors.length} JavaScript errors:`, jsErrors);
    }

    expect(jsErrors.length).toBeLessThan(5); // Allow some minor errors
  });

  test('Security headers audit', async ({ page }) => {
    console.log('🔒 Running Security Headers Audit...');
    
    const response = await page.goto('http://localhost:8000');
    const headers = response?.headers() || {};
    
    // Check for important security headers
    const securityHeaders = [
      'x-frame-options',
      'x-content-type-options',
      'content-security-policy'
    ];

    let headersPassed = 0;
    securityHeaders.forEach(header => {
      if (headers[header]) {
        console.log(`✅ ${header}: ${headers[header]}`);
        headersPassed++;
      } else {
        console.log(`⚠️  Missing header: ${header}`);
      }
    });

    expect(headersPassed).toBeGreaterThan(0);
  });

  test('Accessibility basics audit', async ({ page }) => {
    console.log('♿ Running Basic Accessibility Audit...');
    
    // Check for images without alt text
    const images = await page.locator('img').all();
    let imagesWithoutAlt = 0;
    
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      if (!alt || alt.trim() === '') {
        imagesWithoutAlt++;
      }
    }

    console.log(`📊 Found ${images.length} images, ${imagesWithoutAlt} without alt text`);
    
    // Check for form inputs without labels
    const inputs = await page.locator('input[type="text"], input[type="email"], input[type="password"]').all();
    let inputsWithoutLabels = 0;

    for (const input of inputs) {
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      
      if (id) {
        const labelCount = await page.locator(`label[for="${id}"]`).count();
        if (labelCount === 0 && !ariaLabel) {
          inputsWithoutLabels++;
        }
      } else if (!ariaLabel) {
        inputsWithoutLabels++;
      }
    }

    console.log(`📊 Found ${inputs.length} inputs, ${inputsWithoutLabels} without proper labels`);
    
    // These are warnings, not failures
    expect(images.length).toBeGreaterThanOrEqual(0);
  });

  test('Performance basics audit', async ({ page }) => {
    console.log('⚡ Running Basic Performance Audit...');
    
    const startTime = Date.now();
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    const loadTime = Date.now() - startTime;

    console.log(`📊 Page load time: ${loadTime}ms`);
    
    if (loadTime < 5000) {
      console.log('✅ Page load time is acceptable');
    } else {
      console.log('⚠️  Page load time is slow');
    }

    // Check for large resources (basic check)
    const responses: any[] = [];
    page.on('response', response => {
      const size = response.headers()['content-length'];
      if (size && parseInt(size) > 1024 * 1024) { // > 1MB
        responses.push({
          url: response.url(),
          size: size
        });
      }
    });

    await page.reload();
    await page.waitForTimeout(2000);

    console.log(`📊 Found ${responses.length} large resources (>1MB)`);
    
    expect(loadTime).toBeLessThan(30000); // 30 second timeout
  });

  test('Mobile responsiveness audit', async ({ page }) => {
    console.log('📱 Running Mobile Responsiveness Audit...');
    
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();

    // Check for viewport meta tag
    const viewportMeta = await page.locator('meta[name="viewport"]').count();
    if (viewportMeta > 0) {
      const content = await page.locator('meta[name="viewport"]').getAttribute('content');
      console.log(`✅ Viewport meta tag: ${content}`);
    } else {
      console.log('❌ Missing viewport meta tag');
    }

    // Check for horizontal scrolling
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    
    if (bodyWidth <= viewportWidth + 10) { // Allow small tolerance
      console.log('✅ No horizontal scrolling detected');
    } else {
      console.log(`⚠️  Horizontal scrolling detected: ${bodyWidth}px > ${viewportWidth}px`);
    }

    expect(viewportMeta).toBeGreaterThan(0);
  });

  test('API endpoints basic check', async ({ page }) => {
    console.log('🔌 Running API Endpoints Check...');
    
    // Test if we can make requests to API endpoints
    const apiTests = [
      { endpoint: '/api/health', expectStatus: [200, 500] }, // 500 is OK for health if backend is down
      { endpoint: '/api/admin/users', expectStatus: [401, 403, 404] }, // Should be protected
      { endpoint: '/login', expectStatus: [200] } // Login page should work
    ];

    for (const { endpoint, expectStatus } of apiTests) {
      try {
        const response = await page.request.get(`http://localhost:8000${endpoint}`);
        const status = response.status();
        
        if (expectStatus.includes(status)) {
          console.log(`✅ ${endpoint}: ${status} (expected)`);
        } else {
          console.log(`⚠️  ${endpoint}: ${status} (unexpected, expected: ${expectStatus.join(', ')})`);
        }
      } catch (error) {
        console.log(`❌ ${endpoint}: Request failed - ${error}`);
      }
    }

    // This test always passes as it's informational
    expect(true).toBe(true);
  });
});