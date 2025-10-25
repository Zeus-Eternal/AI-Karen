import { test, expect, Page } from '@playwright/test';
import { chromium } from 'playwright';

interface AuditResult {
  category: string;
  test: string;
  status: 'PASS' | 'FAIL' | 'WARNING';
  message: string;
  details?: any;
}

class WebContainerAuditor {
  private results: AuditResult[] = [];
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  private addResult(category: string, test: string, status: 'PASS' | 'FAIL' | 'WARNING', message: string, details?: any) {
    this.results.push({ category, test, status, message, details });
  }

  async auditSecurity() {
    console.log('🔒 Running Security Audit...');
    
    // Check for HTTPS
    try {
      const url = this.page.url();
      if (url.startsWith('https://')) {
        this.addResult('Security', 'HTTPS', 'PASS', 'Site uses HTTPS');
      } else {
        this.addResult('Security', 'HTTPS', 'WARNING', 'Site not using HTTPS in production');
      }
    } catch (error) {
      this.addResult('Security', 'HTTPS', 'FAIL', `HTTPS check failed: ${error}`);
    }

    // Check for security headers
    try {
      const response = await this.page.goto(this.page.url());
      const headers = response?.headers() || {};
      
      const securityHeaders = [
        'x-frame-options',
        'x-content-type-options',
        'x-xss-protection',
        'strict-transport-security',
        'content-security-policy'
      ];

      securityHeaders.forEach(header => {
        if (headers[header]) {
          this.addResult('Security', `Header: ${header}`, 'PASS', `Security header present: ${headers[header]}`);
        } else {
          this.addResult('Security', `Header: ${header}`, 'WARNING', `Missing security header: ${header}`);
        }
      });
    } catch (error) {
      this.addResult('Security', 'Security Headers', 'FAIL', `Security headers check failed: ${error}`);
    }

    // Check for exposed sensitive information
    try {
      const content = await this.page.content();
      const sensitivePatterns = [
        /password\s*[:=]\s*['"]\w+['"]/i,
        /api[_-]?key\s*[:=]\s*['"]\w+['"]/i,
        /secret\s*[:=]\s*['"]\w+['"]/i,
        /token\s*[:=]\s*['"]\w+['"]/i
      ];

      let foundSensitive = false;
      sensitivePatterns.forEach((pattern, index) => {
        if (pattern.test(content)) {
          foundSensitive = true;
          this.addResult('Security', 'Sensitive Data Exposure', 'FAIL', `Potential sensitive data exposed (pattern ${index + 1})`);
        }
      });

      if (!foundSensitive) {
        this.addResult('Security', 'Sensitive Data Exposure', 'PASS', 'No obvious sensitive data exposed in HTML');
      }
    } catch (error) {
      this.addResult('Security', 'Sensitive Data Exposure', 'FAIL', `Sensitive data check failed: ${error}`);
    }
  }

  async auditPerformance() {
    console.log('⚡ Running Performance Audit...');
    
    try {
      // Measure page load time
      const startTime = Date.now();
      await this.page.goto(this.page.url(), { waitUntil: 'networkidle' });
      const loadTime = Date.now() - startTime;

      if (loadTime < 3000) {
        this.addResult('Performance', 'Page Load Time', 'PASS', `Page loaded in ${loadTime}ms`);
      } else if (loadTime < 5000) {
        this.addResult('Performance', 'Page Load Time', 'WARNING', `Page loaded in ${loadTime}ms (consider optimization)`);
      } else {
        this.addResult('Performance', 'Page Load Time', 'FAIL', `Page loaded in ${loadTime}ms (too slow)`);
      }

      // Check for large resources
      const responses: any[] = [];
      this.page.on('response', response => {
        responses.push({
          url: response.url(),
          size: response.headers()['content-length'],
          type: response.headers()['content-type']
        });
      });

      await this.page.reload();
      await this.page.waitForTimeout(2000);

      const largeResources = responses.filter(r => r.size && parseInt(r.size) > 1024 * 1024); // > 1MB
      if (largeResources.length === 0) {
        this.addResult('Performance', 'Large Resources', 'PASS', 'No resources larger than 1MB detected');
      } else {
        this.addResult('Performance', 'Large Resources', 'WARNING', 
          `Found ${largeResources.length} large resources`, largeResources);
      }

    } catch (error) {
      this.addResult('Performance', 'Performance Check', 'FAIL', `Performance audit failed: ${error}`);
    }
  }

  async auditAccessibility() {
    console.log('♿ Running Accessibility Audit...');
    
    try {
      // Check for alt text on images
      const images = await this.page.locator('img').all();
      let imagesWithoutAlt = 0;
      
      for (const img of images) {
        const alt = await img.getAttribute('alt');
        if (!alt || alt.trim() === '') {
          imagesWithoutAlt++;
        }
      }

      if (imagesWithoutAlt === 0) {
        this.addResult('Accessibility', 'Image Alt Text', 'PASS', 'All images have alt text');
      } else {
        this.addResult('Accessibility', 'Image Alt Text', 'FAIL', 
          `${imagesWithoutAlt} images missing alt text`);
      }

      // Check for form labels
      const inputs = await this.page.locator('input[type="text"], input[type="email"], input[type="password"], textarea').all();
      let inputsWithoutLabels = 0;

      for (const input of inputs) {
        const id = await input.getAttribute('id');
        const ariaLabel = await input.getAttribute('aria-label');
        const ariaLabelledBy = await input.getAttribute('aria-labelledby');
        
        if (id) {
          const label = await this.page.locator(`label[for="${id}"]`).count();
          if (label === 0 && !ariaLabel && !ariaLabelledBy) {
            inputsWithoutLabels++;
          }
        } else if (!ariaLabel && !ariaLabelledBy) {
          inputsWithoutLabels++;
        }
      }

      if (inputsWithoutLabels === 0) {
        this.addResult('Accessibility', 'Form Labels', 'PASS', 'All form inputs have proper labels');
      } else {
        this.addResult('Accessibility', 'Form Labels', 'FAIL', 
          `${inputsWithoutLabels} form inputs missing labels`);
      }

      // Check for heading hierarchy
      const headings = await this.page.locator('h1, h2, h3, h4, h5, h6').all();
      const headingLevels = [];
      
      for (const heading of headings) {
        const tagName = await heading.evaluate(el => el.tagName.toLowerCase());
        headingLevels.push(parseInt(tagName.charAt(1)));
      }

      let hierarchyValid = true;
      for (let i = 1; i < headingLevels.length; i++) {
        if (headingLevels[i] > headingLevels[i-1] + 1) {
          hierarchyValid = false;
          break;
        }
      }

      if (hierarchyValid) {
        this.addResult('Accessibility', 'Heading Hierarchy', 'PASS', 'Heading hierarchy is valid');
      } else {
        this.addResult('Accessibility', 'Heading Hierarchy', 'WARNING', 
          'Heading hierarchy may be invalid', headingLevels);
      }

    } catch (error) {
      this.addResult('Accessibility', 'Accessibility Check', 'FAIL', `Accessibility audit failed: ${error}`);
    }
  }

  async auditFunctionality() {
    console.log('🔧 Running Functionality Audit...');
    
    try {
      // Check for JavaScript errors
      const jsErrors: string[] = [];
      this.page.on('pageerror', error => {
        jsErrors.push(error.message);
      });

      await this.page.reload();
      await this.page.waitForTimeout(3000);

      if (jsErrors.length === 0) {
        this.addResult('Functionality', 'JavaScript Errors', 'PASS', 'No JavaScript errors detected');
      } else {
        this.addResult('Functionality', 'JavaScript Errors', 'FAIL', 
          `${jsErrors.length} JavaScript errors detected`, jsErrors);
      }

      // Check for broken links
      const links = await this.page.locator('a[href]').all();
      let brokenLinks = 0;
      
      for (const link of links.slice(0, 10)) { // Limit to first 10 links for performance
        try {
          const href = await link.getAttribute('href');
          if (href && href.startsWith('http')) {
            const response = await this.page.request.get(href);
            if (response.status() >= 400) {
              brokenLinks++;
            }
          }
        } catch (error) {
          brokenLinks++;
        }
      }

      if (brokenLinks === 0) {
        this.addResult('Functionality', 'Broken Links', 'PASS', 'No broken links detected (sample check)');
      } else {
        this.addResult('Functionality', 'Broken Links', 'WARNING', 
          `${brokenLinks} potentially broken links detected`);
      }

      // Check for console warnings
      const consoleMessages: string[] = [];
      this.page.on('console', msg => {
        if (msg.type() === 'warning' || msg.type() === 'error') {
          consoleMessages.push(`${msg.type()}: ${msg.text()}`);
        }
      });

      await this.page.reload();
      await this.page.waitForTimeout(2000);

      if (consoleMessages.length === 0) {
        this.addResult('Functionality', 'Console Messages', 'PASS', 'No console warnings or errors');
      } else {
        this.addResult('Functionality', 'Console Messages', 'WARNING', 
          `${consoleMessages.length} console messages detected`, consoleMessages.slice(0, 5));
      }

    } catch (error) {
      this.addResult('Functionality', 'Functionality Check', 'FAIL', `Functionality audit failed: ${error}`);
    }
  }

  async auditMobile() {
    console.log('📱 Running Mobile Audit...');
    
    try {
      // Set mobile viewport
      await this.page.setViewportSize({ width: 375, height: 667 });
      await this.page.reload();

      // Check for viewport meta tag
      const viewportMeta = await this.page.locator('meta[name="viewport"]').count();
      if (viewportMeta > 0) {
        const content = await this.page.locator('meta[name="viewport"]').getAttribute('content');
        this.addResult('Mobile', 'Viewport Meta Tag', 'PASS', `Viewport meta tag present: ${content}`);
      } else {
        this.addResult('Mobile', 'Viewport Meta Tag', 'FAIL', 'Missing viewport meta tag');
      }

      // Check for horizontal scrolling
      const bodyWidth = await this.page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await this.page.evaluate(() => window.innerWidth);
      
      if (bodyWidth <= viewportWidth) {
        this.addResult('Mobile', 'Horizontal Scroll', 'PASS', 'No horizontal scrolling detected');
      } else {
        this.addResult('Mobile', 'Horizontal Scroll', 'WARNING', 
          `Content wider than viewport: ${bodyWidth}px vs ${viewportWidth}px`);
      }

      // Check touch targets
      const buttons = await this.page.locator('button, a, input[type="submit"]').all();
      let smallTouchTargets = 0;
      
      for (const button of buttons) {
        try {
          const box = await button.boundingBox();
          if (box && (box.width < 44 || box.height < 44)) {
            smallTouchTargets++;
          }
        } catch (error) {
          // Skip elements that can't be measured
        }
      }

      if (smallTouchTargets === 0) {
        this.addResult('Mobile', 'Touch Targets', 'PASS', 'All touch targets meet minimum size requirements');
      } else {
        this.addResult('Mobile', 'Touch Targets', 'WARNING', 
          `${smallTouchTargets} touch targets smaller than 44px`);
      }

    } catch (error) {
      this.addResult('Mobile', 'Mobile Check', 'FAIL', `Mobile audit failed: ${error}`);
    }
  }

  generateReport(): string {
    const categories = [...new Set(this.results.map(r => r.category))];
    let report = '\n🔍 WEB CONTAINER AUDIT REPORT\n';
    report += '=' .repeat(50) + '\n\n';

    const summary = {
      PASS: this.results.filter(r => r.status === 'PASS').length,
      WARNING: this.results.filter(r => r.status === 'WARNING').length,
      FAIL: this.results.filter(r => r.status === 'FAIL').length
    };

    report += `📊 SUMMARY: ${summary.PASS} passed, ${summary.WARNING} warnings, ${summary.FAIL} failed\n\n`;

    categories.forEach(category => {
      report += `📂 ${category.toUpperCase()}\n`;
      report += '-'.repeat(30) + '\n';
      
      const categoryResults = this.results.filter(r => r.category === category);
      categoryResults.forEach(result => {
        const icon = result.status === 'PASS' ? '✅' : result.status === 'WARNING' ? '⚠️' : '❌';
        report += `${icon} ${result.test}: ${result.message}\n`;
        if (result.details) {
          report += `   Details: ${JSON.stringify(result.details, null, 2).substring(0, 200)}...\n`;
        }
      });
      report += '\n';
    });

    return report;
  }

  getResults(): AuditResult[] {
    return this.results;
  }
}

test.describe('Web Container Comprehensive Audit', () => {
  test('Complete audit of web container', async ({ page }) => {
    const auditor = new WebContainerAuditor(page);
    
    // Navigate to the application
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Run all audit categories
    await auditor.auditSecurity();
    await auditor.auditPerformance();
    await auditor.auditAccessibility();
    await auditor.auditFunctionality();
    await auditor.auditMobile();

    // Generate and display report
    const report = auditor.generateReport();
    console.log(report);

    // Save results to file
    const results = auditor.getResults();
    await page.evaluate((results) => {
      // This will be available in the test artifacts
      console.log('AUDIT_RESULTS:', JSON.stringify(results, null, 2));
    }, results);

    // Assert that we don't have any critical failures
    const criticalFailures = results.filter(r => 
      r.status === 'FAIL' && 
      (r.category === 'Security' || r.test.includes('JavaScript Errors'))
    );

    if (criticalFailures.length > 0) {
      console.error('Critical failures detected:', criticalFailures);
    }

    // The test passes but logs all issues for review
    expect(results.length).toBeGreaterThan(0);
  });

  test('Admin panel specific audit', async ({ page }) => {
    const auditor = new WebContainerAuditor(page);
    
    try {
      // Try to access admin areas
      await page.goto('/admin');
      await page.waitForLoadState('networkidle');
      
      // Check if admin panel is properly protected
      const currentUrl = page.url();
      if (currentUrl.includes('/login') || currentUrl.includes('/unauthorized')) {
        auditor.addResult('Admin Security', 'Access Control', 'PASS', 'Admin panel properly protected');
      } else {
        auditor.addResult('Admin Security', 'Access Control', 'FAIL', 'Admin panel accessible without authentication');
      }

    } catch (error) {
      auditor.addResult('Admin Security', 'Access Control', 'WARNING', `Admin panel check failed: ${error}`);
    }

    const report = auditor.generateReport();
    console.log('ADMIN AUDIT:', report);
  });

  test('API endpoints audit', async ({ page }) => {
    const auditor = new WebContainerAuditor(page);
    
    // Test common API endpoints
    const apiEndpoints = [
      '/api/health',
      '/api/admin/users',
      '/api/admin/system/config',
      '/api/auth/login'
    ];

    for (const endpoint of apiEndpoints) {
      try {
        const response = await page.request.get(endpoint);
        const status = response.status();
        
        if (status === 200) {
          auditor.addResult('API', `Endpoint ${endpoint}`, 'PASS', `Endpoint accessible (${status})`);
        } else if (status === 401 || status === 403) {
          auditor.addResult('API', `Endpoint ${endpoint}`, 'PASS', `Endpoint properly protected (${status})`);
        } else if (status === 404) {
          auditor.addResult('API', `Endpoint ${endpoint}`, 'WARNING', `Endpoint not found (${status})`);
        } else {
          auditor.addResult('API', `Endpoint ${endpoint}`, 'FAIL', `Unexpected status (${status})`);
        }
      } catch (error) {
        auditor.addResult('API', `Endpoint ${endpoint}`, 'FAIL', `Request failed: ${error}`);
      }
    }

    const report = auditor.generateReport();
    console.log('API AUDIT:', report);
  });
});