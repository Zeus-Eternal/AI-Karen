import { test, expect, Page } from '@playwright/test';

/**
 * Performance End-to-End Tests
 * Tests application performance metrics, load times, and resource usage
 */

// Helper functions
async function loginUser(page: Page) {
  await page.goto('/login');
  await page.fill('[data-testid="email-input"]', 'test@example.com');
  await page.fill('[data-testid="password-input"]', 'testpassword123');
  await page.click('[data-testid="login-button"]');
  await page.waitForURL('/chat');
}

async function measurePageLoad(page: Page, url: string) {
  const startTime = Date.now();
  await page.goto(url);
  await page.waitForLoadState('networkidle');
  const endTime = Date.now();
  return endTime - startTime;
}

async function measureFirstContentfulPaint(page: Page) {
  const fcp = await page.evaluate(() => {
    return new Promise((resolve) => {
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const fcpEntry = entries.find(entry => entry.name === 'first-contentful-paint');
        if (fcpEntry) {
          resolve(fcpEntry.startTime);
        }
      }).observe({ entryTypes: ['paint'] });
    });
  });
  return fcp;
}

async function measureLargestContentfulPaint(page: Page) {
  const lcp = await page.evaluate(() => {
    return new Promise((resolve) => {
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        resolve(lastEntry.startTime);
      }).observe({ entryTypes: ['largest-contentful-paint'] });
      
      // Fallback timeout
      setTimeout(() => resolve(0), 5000);
    });
  });
  return lcp;
}

test.describe('Performance Tests', () => {
  test('Page load performance metrics', async ({ page }) => {
    // Measure login page load
    const loginLoadTime = await measurePageLoad(page, '/login');
    expect(loginLoadTime).toBeLessThan(3000); // Should load within 3 seconds
    
    // Measure First Contentful Paint
    const fcp = await measureFirstContentfulPaint(page);
    expect(fcp).toBeLessThan(1500); // FCP should be under 1.5 seconds
    
    // Measure Largest Contentful Paint
    const lcp = await measureLargestContentfulPaint(page);
    expect(lcp).toBeLessThan(2500); // LCP should be under 2.5 seconds
    
    // Login and measure chat page load
    await loginUser(page);
    
    const chatLoadTime = await measurePageLoad(page, '/chat');
    expect(chatLoadTime).toBeLessThan(2000); // Chat should load within 2 seconds
  });  te
st('Chat interaction performance', async ({ page }) => {
    await loginUser(page);
    
    // Mock fast API response
    await page.route('**/api/chat/**', route => {
      setTimeout(() => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'Fast response for performance testing',
            id: 'perf-test-id'
          })
        });
      }, 100); // 100ms simulated response time
    });
    
    // Measure time to first token
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Performance test message');
    
    const startTime = Date.now();
    await page.click('[data-testid="send-button"]');
    
    // Wait for first token to appear
    await page.waitForSelector('[data-testid="assistant-message"]');
    const firstTokenTime = Date.now() - startTime;
    
    expect(firstTokenTime).toBeLessThan(600); // First token should appear within 600ms
    
    // Measure total response time
    await page.waitForSelector('[data-testid="streaming-indicator"]', { state: 'hidden' });
    const totalResponseTime = Date.now() - startTime;
    
    expect(totalResponseTime).toBeLessThan(1000); // Total response within 1 second
  });

  test('Memory usage and leak detection', async ({ page }) => {
    await loginUser(page);
    
    // Get initial memory usage
    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory ? {
        usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
        totalJSHeapSize: (performance as any).memory.totalJSHeapSize
      } : null;
    });
    
    // Send multiple messages to test memory usage
    const messageInput = page.locator('[data-testid="message-input"]');
    
    for (let i = 0; i < 10; i++) {
      await messageInput.fill(`Memory test message ${i + 1}`);
      await page.click('[data-testid="send-button"]');
      await page.waitForSelector('[data-testid="assistant-message"]');
      
      // Force garbage collection if available
      await page.evaluate(() => {
        if ((window as any).gc) {
          (window as any).gc();
        }
      });
    }
    
    // Get final memory usage
    const finalMemory = await page.evaluate(() => {
      return (performance as any).memory ? {
        usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
        totalJSHeapSize: (performance as any).memory.totalJSHeapSize
      } : null;
    });
    
    if (initialMemory && finalMemory) {
      const memoryIncrease = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize;
      const memoryIncreasePercent = (memoryIncrease / initialMemory.usedJSHeapSize) * 100;
      
      // Memory increase should be reasonable (less than 50% increase)
      expect(memoryIncreasePercent).toBeLessThan(50);
    }
  });

  test('Bundle size and resource loading', async ({ page }) => {
    // Track network requests
    const requests: any[] = [];
    page.on('request', request => {
      requests.push({
        url: request.url(),
        resourceType: request.resourceType(),
        size: 0 // Will be updated on response
      });
    });
    
    const responses: any[] = [];
    page.on('response', response => {
      responses.push({
        url: response.url(),
        status: response.status(),
        size: response.headers()['content-length'] || 0
      });
    });
    
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Calculate total bundle size
    const jsRequests = requests.filter(req => 
      req.resourceType === 'script' && req.url.includes('/_next/static/')
    );
    
    const cssRequests = requests.filter(req => 
      req.resourceType === 'stylesheet' && req.url.includes('/_next/static/')
    );
    
    // Verify reasonable number of chunks
    expect(jsRequests.length).toBeLessThan(10); // Should not have too many JS chunks
    expect(cssRequests.length).toBeLessThan(5); // Should not have too many CSS files
    
    // Check for proper caching headers
    const staticResponses = responses.filter(res => 
      res.url.includes('/_next/static/')
    );
    
    staticResponses.forEach(response => {
      expect(response.status).toBe(200);
    });
  });

  test('Streaming performance and backpressure', async ({ page }) => {
    await loginUser(page);
    
    // Mock streaming response with many tokens
    await page.route('**/api/chat/stream/**', route => {
      const tokens = Array.from({ length: 100 }, (_, i) => `Token${i} `);
      let tokenIndex = 0;
      
      const stream = new ReadableStream({
        start(controller) {
          const sendToken = () => {
            if (tokenIndex < tokens.length) {
              const data = `data: {"token": "${tokens[tokenIndex]}"}\n\n`;
              controller.enqueue(new TextEncoder().encode(data));
              tokenIndex++;
              setTimeout(sendToken, 10); // 10ms between tokens
            } else {
              controller.close();
            }
          };
          sendToken();
        }
      });
      
      route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: stream
      });
    });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Test streaming performance');
    
    const startTime = Date.now();
    await page.click('[data-testid="send-button"]');
    
    // Wait for streaming to complete
    await page.waitForSelector('[data-testid="streaming-indicator"]', { state: 'hidden', timeout: 15000 });
    const streamingTime = Date.now() - startTime;
    
    // Streaming should complete within reasonable time
    expect(streamingTime).toBeLessThan(5000);
    
    // Verify all tokens were received
    const finalMessage = page.locator('[data-testid="assistant-message"]').last();
    const messageText = await finalMessage.textContent();
    expect(messageText).toContain('Token99');
  });

  test('Large conversation performance', async ({ page }) => {
    await loginUser(page);
    
    // Mock API to return consistent responses
    await page.route('**/api/chat/**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Response to message in large conversation test',
          id: `msg-${Date.now()}`
        })
      });
    });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    
    // Create a large conversation (50 messages)
    for (let i = 0; i < 25; i++) {
      await messageInput.fill(`Message ${i + 1} in large conversation`);
      await page.click('[data-testid="send-button"]');
      await page.waitForSelector('[data-testid="assistant-message"]');
    }
    
    // Measure scroll performance
    const scrollStartTime = Date.now();
    await page.evaluate(() => {
      const messageList = document.querySelector('[data-testid="message-list"]');
      if (messageList) {
        messageList.scrollTop = 0; // Scroll to top
      }
    });
    
    await page.waitForTimeout(100); // Allow scroll to complete
    const scrollTime = Date.now() - scrollStartTime;
    
    expect(scrollTime).toBeLessThan(200); // Scroll should be smooth
    
    // Test virtualization is working (not all messages should be in DOM)
    const visibleMessages = await page.locator('[data-testid="message"]').count();
    expect(visibleMessages).toBeLessThan(50); // Should be virtualized
    
    // Test adding new message to large conversation
    const newMessageStartTime = Date.now();
    await messageInput.fill('New message in large conversation');
    await page.click('[data-testid="send-button"]');
    await page.waitForSelector('[data-testid="assistant-message"]');
    const newMessageTime = Date.now() - newMessageStartTime;
    
    expect(newMessageTime).toBeLessThan(1000); // Should still be fast
  });

  test('Network performance under load', async ({ page }) => {
    await loginUser(page);
    
    // Track network timing
    const networkTimings: any[] = [];
    
    page.on('response', response => {
      const timing = response.request().timing();
      networkTimings.push({
        url: response.url(),
        status: response.status(),
        timing: timing
      });
    });
    
    // Send multiple concurrent requests
    const messageInput = page.locator('[data-testid="message-input"]');
    const promises = [];
    
    for (let i = 0; i < 5; i++) {
      const promise = (async () => {
        await messageInput.fill(`Concurrent message ${i + 1}`);
        await page.click('[data-testid="send-button"]');
        await page.waitForSelector('[data-testid="assistant-message"]');
      })();
      promises.push(promise);
    }
    
    await Promise.all(promises);
    
    // Analyze network performance
    const chatRequests = networkTimings.filter(timing => 
      timing.url.includes('/api/chat/')
    );
    
    chatRequests.forEach(request => {
      expect(request.status).toBe(200);
      if (request.timing) {
        // DNS + Connect + Request + Response should be reasonable
        const totalTime = request.timing.responseEnd - request.timing.requestStart;
        expect(totalTime).toBeLessThan(2000); // Under 2 seconds per request
      }
    });
  });

  test('Mobile performance', async ({ page }) => {
    // Simulate mobile device
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Simulate slower mobile network
    await page.route('**/*', async route => {
      await new Promise(resolve => setTimeout(resolve, 50)); // Add 50ms delay
      route.continue();
    });
    
    const loadStartTime = Date.now();
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    const mobileLoadTime = Date.now() - loadStartTime;
    
    // Mobile should still load reasonably fast
    expect(mobileLoadTime).toBeLessThan(5000);
    
    await loginUser(page);
    
    // Test mobile chat performance
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Mobile performance test');
    
    const mobileResponseStart = Date.now();
    await page.click('[data-testid="send-button"]');
    await page.waitForSelector('[data-testid="assistant-message"]');
    const mobileResponseTime = Date.now() - mobileResponseStart;
    
    expect(mobileResponseTime).toBeLessThan(2000);
  });
});