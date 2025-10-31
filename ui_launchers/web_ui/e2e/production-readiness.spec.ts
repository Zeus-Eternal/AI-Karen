import { test, expect, Page } from '@playwright/test';

interface ProductionCheck {
  category: string;
  test: string;
  status: 'PASS' | 'FAIL' | 'WARNING' | 'SKIP';
  message: string;
  details?: any;
}

class ProductionReadinessValidator {
  private checks: ProductionCheck[] = [];
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  private addCheck(category: string, test: string, status: 'PASS' | 'FAIL' | 'WARNING' | 'SKIP', message: string, details?: any) {
    this.checks.push({ category, test, status, message, details });
    const icon = { 'PASS': '✅', 'FAIL': '❌', 'WARNING': '⚠️', 'SKIP': '⏭️' }[status];
    console.log(`${icon} [${category}] ${test}: ${message}`);
  }

  async validateAuthentication() {
    console.log('🔐 Validating Authentication System...');
    
    try {
      // Test admin login with production credentials
      await this.page.goto('/login');
      await this.page.waitForLoadState('networkidle');

      // Check if login form exists
      const loginForm = this.page.locator('form');
      const emailInput = this.page.locator('input[type="email"], input[name="email"]');
      const passwordInput = this.page.locator('input[type="password"], input[name="password"]');
      const submitButton = this.page.locator('button[type="submit"], input[type="submit"]');

      if (await loginForm.count() > 0) {
        this.addCheck('Authentication', 'Login Form Present', 'PASS', 'Login form is available');
        
        // Test with admin credentials
        if (await emailInput.count() > 0 && await passwordInput.count() > 0) {
          await emailInput.fill('admin@example.com');
          await passwordInput.fill('adminadmin');
          
          if (await submitButton.count() > 0) {
            await submitButton.click();
            await this.page.waitForTimeout(3000);
            
            const currentUrl = this.page.url();
            if (currentUrl.includes('/dashboard') || currentUrl.includes('/admin') || currentUrl.includes('/chat')) {
              this.addCheck('Authentication', 'Admin Login', 'PASS', 'Admin login successful');
              
              // Check for admin features
              const adminElements = await this.page.locator('[data-testid*="admin"], .admin, #admin').count();
              if (adminElements > 0) {
                this.addCheck('Authentication', 'Admin Features', 'PASS', 'Admin features accessible after login');
              } else {
                this.addCheck('Authentication', 'Admin Features', 'WARNING', 'Admin features not clearly visible');
              }
            } else if (currentUrl.includes('/setup') || currentUrl.includes('/first-run')) {
              this.addCheck('Authentication', 'First Run Setup', 'PASS', 'First-run setup flow detected');
            } else {
              this.addCheck('Authentication', 'Admin Login', 'FAIL', 'Admin login failed or redirected unexpectedly');
            }
          } else {
            this.addCheck('Authentication', 'Login Form', 'FAIL', 'Submit button not found');
          }
        } else {
          this.addCheck('Authentication', 'Login Form', 'FAIL', 'Email or password input not found');
        }
      } else {
        this.addCheck('Authentication', 'Login Form Present', 'FAIL', 'Login form not found');
      }

      // Test unauthorized access protection
      await this.page.goto('/admin/users');
      await this.page.waitForTimeout(2000);
      
      const adminUrl = this.page.url();
      if (adminUrl.includes('/login') || adminUrl.includes('/unauthorized')) {
        this.addCheck('Authentication', 'Admin Protection', 'PASS', 'Admin routes properly protected');
      } else if (adminUrl.includes('/admin')) {
        // Check if we're actually logged in
        const userInfo = await this.page.locator('[data-testid="user-info"], .user-info').count();
        if (userInfo > 0) {
          this.addCheck('Authentication', 'Admin Protection', 'PASS', 'Admin access granted to authenticated user');
        } else {
          this.addCheck('Authentication', 'Admin Protection', 'FAIL', 'Admin routes accessible without authentication');
        }
      }

    } catch (error) {
      this.addCheck('Authentication', 'Authentication Test', 'FAIL', `Authentication test failed: ${error}`);
    }
  }

  async validateChatFunctionality() {
    console.log('💬 Validating Chat Functionality...');
    
    try {
      await this.page.goto('/chat');
      await this.page.waitForLoadState('networkidle');

      // Check for chat interface elements
      const chatInput = this.page.locator('textarea, input[type="text"]').first();
      const sendButton = this.page.locator('button').filter({ hasText: /send|submit/i });
      const modelSelector = this.page.locator('select, [data-testid*="model"], [class*="model"]');

      if (await chatInput.count() > 0) {
        this.addCheck('Chat', 'Chat Input', 'PASS', 'Chat input field present');
        
        // Test sending a message
        await chatInput.fill('Hello, this is a production test message.');
        
        if (await sendButton.count() > 0) {
          await sendButton.click();
          await this.page.waitForTimeout(5000); // Wait for response
          
          // Check for response
          const messages = await this.page.locator('[data-testid*="message"], .message, .chat-message').count();
          if (messages >= 2) { // User message + AI response
            this.addCheck('Chat', 'Message Exchange', 'PASS', 'Chat message exchange working');
            
            // Check for response formatting
            const formattedElements = await this.page.locator('.formatted-response, [data-formatted="true"]').count();
            if (formattedElements > 0) {
              this.addCheck('Chat', 'Response Formatting', 'PASS', 'Response formatting detected');
            } else {
              this.addCheck('Chat', 'Response Formatting', 'WARNING', 'No formatted responses detected');
            }
          } else {
            this.addCheck('Chat', 'Message Exchange', 'FAIL', 'No AI response received');
          }
        } else {
          this.addCheck('Chat', 'Send Button', 'FAIL', 'Send button not found');
        }
      } else {
        this.addCheck('Chat', 'Chat Input', 'FAIL', 'Chat input field not found');
      }

      // Test model selection
      if (await modelSelector.count() > 0) {
        const options = await modelSelector.locator('option').count();
        if (options > 1) {
          this.addCheck('Chat', 'Model Selection', 'PASS', `${options} model options available`);
          
          // Check for production models (no test/demo entries)
          const optionTexts = await modelSelector.locator('option').allTextContents();
          const testEntries = optionTexts.filter(text => 
            text.toLowerCase().includes('test') || 
            text.toLowerCase().includes('demo') || 
            text.toLowerCase().includes('other model')
          );
          
          if (testEntries.length === 0) {
            this.addCheck('Chat', 'Production Models', 'PASS', 'No test/demo model entries found');
          } else {
            this.addCheck('Chat', 'Production Models', 'FAIL', 
              `Found test/demo entries: ${testEntries.join(', ')}`);
          }
        } else {
          this.addCheck('Chat', 'Model Selection', 'WARNING', 'Limited model options available');
        }
      } else {
        this.addCheck('Chat', 'Model Selection', 'WARNING', 'Model selector not found');
      }

    } catch (error) {
      this.addCheck('Chat', 'Chat Functionality', 'FAIL', `Chat test failed: ${error}`);
    }
  }

  async validateResponseFormatting() {
    console.log('🎨 Validating Response Formatting...');
    
    const testQueries = [
      { query: 'Tell me about the movie Inception', type: 'movie', keywords: ['movie', 'film', 'director'] },
      { query: 'How do I make chocolate chip cookies?', type: 'recipe', keywords: ['ingredients', 'recipe', 'cooking'] },
      { query: 'What is the weather like today?', type: 'weather', keywords: ['weather', 'temperature', 'forecast'] },
      { query: 'Latest news about artificial intelligence', type: 'news', keywords: ['news', 'article', 'headline'] }
    ];

    try {
      await this.page.goto('/chat');
      await this.page.waitForLoadState('networkidle');

      for (const testQuery of testQueries) {
        const chatInput = this.page.locator('textarea, input[type="text"]').first();
        const sendButton = this.page.locator('button').filter({ hasText: /send|submit/i });

        if (await chatInput.count() > 0 && await sendButton.count() > 0) {
          await chatInput.fill(testQuery.query);
          await sendButton.click();
          await this.page.waitForTimeout(10000); // Wait longer for AI response

          // Check for formatted response
          const responseElements = await this.page.locator('[data-testid*="message"], .message, .chat-message').last();
          const responseText = await responseElements.textContent() || '';
          
          // Check for formatting indicators
          const hasFormatting = await this.page.locator(
            '.formatted-response, [data-formatted="true"], .card, .recipe-card, .movie-card, .weather-card, .news-card'
          ).count() > 0;

          if (hasFormatting) {
            this.addCheck('Response Formatting', `${testQuery.type} Formatting`, 'PASS', 
              `${testQuery.type} response appears to be formatted`);
          } else {
            // Check if response contains expected keywords
            const hasKeywords = testQuery.keywords.some(keyword => 
              responseText.toLowerCase().includes(keyword.toLowerCase())
            );
            
            if (hasKeywords) {
              this.addCheck('Response Formatting', `${testQuery.type} Formatting`, 'WARNING', 
                `${testQuery.type} response contains relevant content but may not be formatted`);
            } else {
              this.addCheck('Response Formatting', `${testQuery.type} Formatting`, 'FAIL', 
                `${testQuery.type} response does not appear relevant or formatted`);
            }
          }

          // Clear chat for next test
          await this.page.waitForTimeout(1000);
        } else {
          this.addCheck('Response Formatting', `${testQuery.type} Formatting`, 'SKIP', 
            'Chat interface not available for formatting test');
          break;
        }
      }

    } catch (error) {
      this.addCheck('Response Formatting', 'Formatting Tests', 'FAIL', 
        `Response formatting test failed: ${error}`);
    }
  }

  async validateUIProduction() {
    console.log('🎨 Validating UI Production Readiness...');
    
    try {
      await this.page.goto('/');
      await this.page.waitForLoadState('networkidle');

      // Check for development artifacts
      const pageContent = await this.page.content();
      const devArtifacts = [
        'TODO',
        'FIXME',
        'DEBUG',
        'console.log',
        'localhost:3000',
        'development mode',
        'test data',
        'placeholder'
      ];

      const foundArtifacts = devArtifacts.filter(artifact => 
        pageContent.toLowerCase().includes(artifact.toLowerCase())
      );

      if (foundArtifacts.length === 0) {
        this.addCheck('UI Production', 'Development Artifacts', 'PASS', 
          'No obvious development artifacts found in HTML');
      } else {
        this.addCheck('UI Production', 'Development Artifacts', 'WARNING', 
          `Found potential development artifacts: ${foundArtifacts.join(', ')}`);
      }

      // Check for proper meta tags
      const title = await this.page.title();
      const metaDescription = await this.page.locator('meta[name="description"]').getAttribute('content');
      const viewport = await this.page.locator('meta[name="viewport"]').getAttribute('content');

      if (title && title.length > 0 && !title.includes('localhost')) {
        this.addCheck('UI Production', 'Page Title', 'PASS', `Page title: ${title}`);
      } else {
        this.addCheck('UI Production', 'Page Title', 'WARNING', 'Page title missing or contains localhost');
      }

      if (metaDescription) {
        this.addCheck('UI Production', 'Meta Description', 'PASS', 'Meta description present');
      } else {
        this.addCheck('UI Production', 'Meta Description', 'WARNING', 'Meta description missing');
      }

      if (viewport) {
        this.addCheck('UI Production', 'Viewport Meta', 'PASS', 'Viewport meta tag present');
      } else {
        this.addCheck('UI Production', 'Viewport Meta', 'FAIL', 'Viewport meta tag missing');
      }

      // Check for console errors
      const consoleErrors: string[] = [];
      this.page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      await this.page.reload();
      await this.page.waitForTimeout(3000);

      if (consoleErrors.length === 0) {
        this.addCheck('UI Production', 'Console Errors', 'PASS', 'No console errors detected');
      } else {
        this.addCheck('UI Production', 'Console Errors', 'FAIL', 
          `${consoleErrors.length} console errors detected`, { errors: consoleErrors.slice(0, 3) });
      }

      // Check responsive design
      await this.page.setViewportSize({ width: 375, height: 667 }); // Mobile
      await this.page.waitForTimeout(1000);
      
      const bodyWidth = await this.page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await this.page.evaluate(() => window.innerWidth);
      
      if (bodyWidth <= viewportWidth + 10) { // Allow small margin
        this.addCheck('UI Production', 'Mobile Responsive', 'PASS', 'No horizontal scrolling on mobile');
      } else {
        this.addCheck('UI Production', 'Mobile Responsive', 'WARNING', 
          `Horizontal scrolling detected: ${bodyWidth}px > ${viewportWidth}px`);
      }

      // Reset viewport
      await this.page.setViewportSize({ width: 1280, height: 720 });

    } catch (error) {
      this.addCheck('UI Production', 'UI Validation', 'FAIL', `UI validation failed: ${error}`);
    }
  }

  async validatePerformance() {
    console.log('⚡ Validating Performance...');
    
    try {
      // Measure page load time
      const startTime = Date.now();
      await this.page.goto('/', { waitUntil: 'networkidle' });
      const loadTime = Date.now() - startTime;

      if (loadTime < 3000) {
        this.addCheck('Performance', 'Page Load Time', 'PASS', `Page loaded in ${loadTime}ms`);
      } else if (loadTime < 5000) {
        this.addCheck('Performance', 'Page Load Time', 'WARNING', `Page loaded in ${loadTime}ms`);
      } else {
        this.addCheck('Performance', 'Page Load Time', 'FAIL', `Page loaded in ${loadTime}ms (too slow)`);
      }

      // Check for large resources
      const responses: any[] = [];
      this.page.on('response', response => {
        const contentLength = response.headers()['content-length'];
        if (contentLength) {
          responses.push({
            url: response.url(),
            size: parseInt(contentLength),
            type: response.headers()['content-type']
          });
        }
      });

      await this.page.reload();
      await this.page.waitForTimeout(2000);

      const largeResources = responses.filter(r => r.size > 1024 * 1024); // > 1MB
      if (largeResources.length === 0) {
        this.addCheck('Performance', 'Resource Sizes', 'PASS', 'No resources larger than 1MB');
      } else {
        this.addCheck('Performance', 'Resource Sizes', 'WARNING', 
          `${largeResources.length} large resources found`, 
          { resources: largeResources.slice(0, 3) });
      }

    } catch (error) {
      this.addCheck('Performance', 'Performance Check', 'FAIL', `Performance check failed: ${error}`);
    }
  }

  generateReport(): any {
    const summary = {
      PASS: this.checks.filter(c => c.status === 'PASS').length,
      FAIL: this.checks.filter(c => c.status === 'FAIL').length,
      WARNING: this.checks.filter(c => c.status === 'WARNING').length,
      SKIP: this.checks.filter(c => c.status === 'SKIP').length
    };

    const overallStatus = summary.FAIL > 0 ? 'NOT_READY' : 
                         summary.WARNING > 3 ? 'NEEDS_ATTENTION' : 'READY';

    return {
      timestamp: new Date().toISOString(),
      overall_status: overallStatus,
      summary,
      checks: this.checks
    };
  }

  getChecks(): ProductionCheck[] {
    return this.checks;
  }
}

test.describe('Production Readiness E2E Validation', () => {
  test('Complete production readiness validation', async ({ page }) => {
    const validator = new ProductionReadinessValidator(page);
    
    console.log('🚀 Starting Production Readiness E2E Validation');
    
    // Run all validation checks
    await validator.validateAuthentication();
    await validator.validateChatFunctionality();
    await validator.validateResponseFormatting();
    await validator.validateUIProduction();
    await validator.validatePerformance();
    
    // Generate report
    const report = validator.generateReport();
    console.log('\n📊 PRODUCTION READINESS REPORT');
    console.log('================================');
    console.log(`Overall Status: ${report.overall_status}`);
    console.log(`Summary: ${report.summary.PASS} passed, ${report.summary.WARNING} warnings, ${report.summary.FAIL} failed, ${report.summary.SKIP} skipped`);
    
    // Log detailed results
    const checks = validator.getChecks();
    const failedChecks = checks.filter(c => c.status === 'FAIL');
    const warningChecks = checks.filter(c => c.status === 'WARNING');
    
    if (failedChecks.length > 0) {
      console.log('\n❌ Failed Checks:');
      failedChecks.forEach(check => {
        console.log(`  • [${check.category}] ${check.test}: ${check.message}`);
      });
    }
    
    if (warningChecks.length > 0) {
      console.log('\n⚠️  Warning Checks:');
      warningChecks.forEach(check => {
        console.log(`  • [${check.category}] ${check.test}: ${check.message}`);
      });
    }
    
    // Save report for CI/CD
    await page.evaluate((reportData) => {
      console.log('PRODUCTION_READINESS_REPORT:', JSON.stringify(reportData, null, 2));
    }, report);
    
    // Assert based on overall status
    expect(report.overall_status).not.toBe('NOT_READY');
    expect(report.summary.PASS).toBeGreaterThan(0);
    
    console.log('\n✅ Production readiness validation completed');
  });

  test('Admin workflow validation', async ({ page }) => {
    console.log('👑 Validating Admin Workflow');
    
    // Test admin login and access
    await page.goto('/login');
    
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    const submitButton = page.locator('button[type="submit"], input[type="submit"]');
    
    if (await emailInput.count() > 0) {
      await emailInput.fill('admin@example.com');
      await passwordInput.fill('adminadmin');
      await submitButton.click();
      
      await page.waitForTimeout(3000);
      
      // Should be redirected to dashboard or admin area
      const currentUrl = page.url();
      expect(currentUrl).not.toContain('/login');
      
      // Try to access admin features
      await page.goto('/admin');
      await page.waitForTimeout(2000);
      
      // Should have access to admin features
      const adminUrl = page.url();
      expect(adminUrl).toContain('/admin');
      
      console.log('✅ Admin workflow validation passed');
    } else {
      console.log('⏭️  Admin workflow validation skipped - no login form found');
    }
  });

  test('Model selection validation', async ({ page }) => {
    console.log('🤖 Validating Model Selection');
    
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');
    
    const modelSelector = page.locator('select, [data-testid*="model"], [class*="model"]');
    
    if (await modelSelector.count() > 0) {
      const options = await modelSelector.locator('option').allTextContents();
      
      // Should have production models
      expect(options.length).toBeGreaterThan(0);
      
      // Should not have test entries
      const testEntries = options.filter(option => 
        option.toLowerCase().includes('test') || 
        option.toLowerCase().includes('demo') ||
        option.toLowerCase().includes('other model')
      );
      
      expect(testEntries).toHaveLength(0);
      
      console.log(`✅ Model selection validation passed - ${options.length} production models available`);
    } else {
      console.log('⚠️  Model selector not found');
    }
  });
});