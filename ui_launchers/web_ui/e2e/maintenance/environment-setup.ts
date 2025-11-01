import { Page, Browser } from '@playwright/test';

export class EnvironmentSetup {
  private static instance: EnvironmentSetup;
  private environments: Map<string, any> = new Map();

  static getInstance(): EnvironmentSetup {
    if (!EnvironmentSetup.instance) {
      EnvironmentSetup.instance = new EnvironmentSetup();
    }
    return EnvironmentSetup.instance;
  }

  async setupTestEnvironment(browser: Browser, environmentType: 'development' | 'staging' | 'production'): Promise<Page> {
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
      locale: 'en-US',
      timezoneId: 'America/New_York',
      permissions: ['clipboard-read', 'clipboard-write'],
      recordVideo: process.env.CI ? { dir: 'test-results/videos' } : undefined,
      recordHar: process.env.CI ? { path: 'test-results/network.har' } : undefined
    });

    const page = await context.newPage();

    // Setup environment-specific configurations
    await this.configureEnvironment(page, environmentType);
    
    // Setup request/response interceptors
    await this.setupInterceptors(page);
    
    // Setup error handling
    await this.setupErrorHandling(page);
    
    return page;
  }

  private async configureEnvironment(page: Page, environmentType: string): Promise<void> {
    const configs = {
      development: {
        baseURL: 'http://localhost:8010',
        apiURL: 'http://localhost:8000',
        wsURL: 'ws://localhost:8010',
        timeout: 30000,
        retries: 2
      },
      staging: {
        baseURL: 'https://staging.kari.ai',
        apiURL: 'https://api-staging.kari.ai',
        wsURL: 'wss://staging.kari.ai',
        timeout: 60000,
        retries: 3
      },
      production: {
        baseURL: 'https://kari.ai',
        apiURL: 'https://api.kari.ai',
        wsURL: 'wss://kari.ai',
        timeout: 60000,
        retries: 3
      }
    };

    const config = configs[environmentType];
    this.environments.set('current', config);

    // Set environment variables in page context
    await page.addInitScript((config) => {
      window.__TEST_CONFIG__ = config;
    }, config);
  }

  private async setupInterceptors(page: Page): Promise<void> {
    // Intercept and log all network requests
    page.on('request', request => {
      if (process.env.DEBUG_NETWORK) {
        console.log(`→ ${request.method()} ${request.url()}`);
      }
    });

    page.on('response', response => {
      if (process.env.DEBUG_NETWORK) {
        console.log(`← ${response.status()} ${response.url()}`);
      }
      
      // Log failed requests
      if (response.status() >= 400) {
        console.error(`Failed request: ${response.status()} ${response.url()}`);
      }
    });

    // Setup common route mocks for testing
    await this.setupCommonMocks(page);
  }

  private async setupCommonMocks(page: Page): Promise<void> {
    // Mock external services in test environment
    if (process.env.NODE_ENV === 'test') {
      // Mock analytics service
      await page.route('**/api/analytics/**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, data: {} })
        });
      });

      // Mock external model providers
      await page.route('**/api/providers/external/**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ 
            status: 'connected',
            models: ['test-model-1', 'test-model-2']
          })
        });
      });
    }
  }

  private async setupErrorHandling(page: Page): Promise<void> {
    // Handle uncaught exceptions
    page.on('pageerror', error => {
      console.error('Page error:', error.message);
    });

    // Handle console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('Console error:', msg.text());
      }
    });

    // Handle failed requests
    page.on('requestfailed', request => {
      console.error('Request failed:', request.url(), request.failure()?.errorText);
    });
  }

  async setupDatabaseState(page: Page, state: 'clean' | 'seeded' | 'production-like'): Promise<void> {
    const stateConfigs = {
      clean: {
        users: [],
        plugins: [],
        memories: [],
        settings: {}
      },
      seeded: {
        users: [
          { username: 'admin@test.com', role: 'admin' },
          { username: 'user@test.com', role: 'user' }
        ],
        plugins: [
          { id: 'test-plugin', status: 'active' }
        ],
        memories: [
          { content: 'Test memory 1', type: 'knowledge' },
          { content: 'Test memory 2', type: 'conversation' }
        ],
        settings: {
          theme: 'light',
          language: 'en'
        }
      },
      'production-like': {
        users: Array(100).fill(null).map((_, i) => ({
          username: `user${i}@test.com`,
          role: i < 5 ? 'admin' : 'user'
        })),
        plugins: Array(20).fill(null).map((_, i) => ({
          id: `plugin-${i}`,
          status: Math.random() > 0.3 ? 'active' : 'inactive'
        })),
        memories: Array(1000).fill(null).map((_, i) => ({
          content: `Memory content ${i}`,
          type: ['knowledge', 'conversation', 'document'][i % 3]
        })),
        settings: {
          theme: 'dark',
          language: 'en'
        }
      }
    };

    const config = stateConfigs[state];
    
    await page.request.post('/api/test/setup-database', {
      data: config
    });
  }

  async setupPerformanceMonitoring(page: Page): Promise<void> {
    // Setup performance monitoring
    await page.addInitScript(() => {
      // Track page load performance
      window.addEventListener('load', () => {
        const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        console.log('Page Load Performance:', {
          domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
          loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
          totalTime: perfData.loadEventEnd - perfData.fetchStart
        });
      });

      // Track resource loading
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.duration > 1000) { // Log slow resources
            console.warn('Slow resource:', entry.name, entry.duration + 'ms');
          }
        }
      });
      observer.observe({ entryTypes: ['resource'] });
    });
  }

  async setupAccessibilityTesting(page: Page): Promise<void> {
    // Inject axe-core for accessibility testing
    await page.addScriptTag({
      url: 'https://unpkg.com/axe-core@4.7.0/axe.min.js'
    });

    // Setup accessibility monitoring
    await page.addInitScript(() => {
      // Auto-run accessibility checks on page changes
      let lastUrl = location.href;
      new MutationObserver(() => {
        if (location.href !== lastUrl) {
          lastUrl = location.href;
          setTimeout(() => {
            if (window.axe) {
              window.axe.run().then((results: any) => {
                if (results.violations.length > 0) {
                  console.warn('Accessibility violations found:', results.violations);
                }
              });
            }
          }, 1000);
        }
      }).observe(document, { subtree: true, childList: true });
    });
  }

  async setupVisualTesting(page: Page): Promise<void> {
    // Setup visual regression testing
    await page.addInitScript(() => {
      // Disable animations for consistent screenshots
      const style = document.createElement('style');
      style.textContent = `
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
        }
      `;
      document.head.appendChild(style);
    });

    // Wait for fonts to load
    await page.waitForFunction(() => document.fonts.ready);
  }

  async teardownEnvironment(page: Page): Promise<void> {
    // Cleanup test data
    await page.request.post('/api/test/cleanup');
    
    // Close page and context
    await page.context().close();
  }

  getEnvironmentConfig(key?: string): any {
    const config = this.environments.get('current');
    return key ? config?.[key] : config;
  }

  async waitForEnvironmentReady(page: Page): Promise<void> {
    // Wait for application to be fully loaded
    await page.waitForFunction(() => {
      return window.__APP_READY__ === true;
    }, { timeout: 30000 });

    // Wait for critical resources
    await page.waitForLoadState('networkidle');
    
    // Wait for any pending API calls
    await page.waitForFunction(() => {
      return window.__PENDING_REQUESTS__ === 0;
    }, { timeout: 10000 }).catch(() => {
      // Ignore timeout - some requests might be ongoing
    });
  }
}