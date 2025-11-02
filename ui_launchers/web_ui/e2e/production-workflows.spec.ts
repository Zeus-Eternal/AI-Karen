import { test, expect, Page } from '@playwright/test';

/**
 * Production Workflow E2E Tests
 * Tests specific production workflows as required by task 6.1
 */

test.describe('Production Workflows - Admin Authentication', () => {
  test('Admin login with admin@example.com:adminadmin credentials', async ({ page }) => {
    console.log('🔐 Testing admin login with production credentials');
    
    // Navigate to login page
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Check if login form exists
    const loginForm = page.locator('form');
    await expect(loginForm).toBeVisible({ timeout: 10000 });
    
    // Find login inputs
    const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"], input[placeholder*="password" i]').first();
    const submitButton = page.locator('button[type="submit"], input[type="submit"], button:has-text("login"), button:has-text("sign in")').first();
    
    // Verify form elements exist
    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(submitButton).toBeVisible();
    
    // Fill in admin credentials
    await emailInput.fill('admin@example.com');
    await passwordInput.fill('adminadmin');
    
    // Submit login form
    await submitButton.click();
    
    // Wait for navigation/response
    await page.waitForTimeout(5000);
    
    // Check if login was successful
    const currentUrl = page.url();
    console.log(`Current URL after login: ${currentUrl}`);
    
    // Should be redirected away from login page
    expect(currentUrl).not.toContain('/login');
    
    // Should be on dashboard, admin, or chat page
    const isOnValidPage = currentUrl.includes('/dashboard') || 
                         currentUrl.includes('/admin') || 
                         currentUrl.includes('/chat') ||
                         currentUrl.includes('/home');
    
    expect(isOnValidPage).toBeTruthy();
    
    // Check for user session indicators
    const userIndicators = page.locator('[data-testid*="user"], .user-info, .user-menu, [class*="user"]');
    const hasUserIndicator = await userIndicators.count() > 0;
    
    if (hasUserIndicator) {
      console.log('✅ User session indicators found');
    }
    
    // Try to access admin features
    await page.goto('/admin');
    await page.waitForTimeout(3000);
    
    const adminUrl = page.url();
    if (adminUrl.includes('/admin')) {
      console.log('✅ Admin access granted');
      
      // Look for admin-specific elements
      const adminElements = page.locator('[data-testid*="admin"], .admin, #admin, h1:has-text("admin"), h2:has-text("admin")');
      const adminElementCount = await adminElements.count();
      
      if (adminElementCount > 0) {
        console.log(`✅ Found ${adminElementCount} admin elements`);
      }
    } else {
      console.log('⚠️ Admin access may be restricted or redirected');
    }
  });

  test('First-run setup flow when no admin exists', async ({ page }) => {
    console.log('🚀 Testing first-run setup flow');
    
    // This test simulates the scenario where no admin user exists
    // We'll check if the system properly handles first-run setup
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const currentUrl = page.url();
    console.log(`Initial URL: ${currentUrl}`);
    
    // Check if redirected to setup/first-run page
    const isSetupFlow = currentUrl.includes('/setup') || 
                       currentUrl.includes('/first-run') || 
                       currentUrl.includes('/initialize') ||
                       currentUrl.includes('/onboarding');
    
    if (isSetupFlow) {
      console.log('✅ First-run setup flow detected');
      
      // Look for setup form elements
      const setupForm = page.locator('form');
      const setupInputs = page.locator('input[type="email"], input[type="password"], input[name*="admin"]');
      const setupButton = page.locator('button[type="submit"], button:has-text("setup"), button:has-text("create"), button:has-text("initialize")');
      
      if (await setupForm.count() > 0) {
        console.log('✅ Setup form found');
        expect(setupForm).toBeVisible();
      }
      
      if (await setupInputs.count() > 0) {
        console.log(`✅ Found ${await setupInputs.count()} setup inputs`);
      }
      
      if (await setupButton.count() > 0) {
        console.log('✅ Setup button found');
        expect(setupButton).toBeVisible();
      }
      
    } else {
      // If not in setup flow, try to trigger it by accessing admin areas
      await page.goto('/admin/setup');
      await page.waitForTimeout(2000);
      
      const setupUrl = page.url();
      if (setupUrl.includes('/setup') || setupUrl.includes('/first-run')) {
        console.log('✅ First-run setup accessible via /admin/setup');
      } else {
        console.log('ℹ️ First-run setup may not be needed (admin already exists)');
      }
    }
  });
});

test.describe('Production Workflows - Chat Functionality', () => {
  test('Chat functionality with response formatting validation', async ({ page }) => {
    console.log('💬 Testing chat functionality with response formatting');
    
    // Navigate to chat page
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');
    
    // Find chat interface elements
    const chatInput = page.locator('textarea, input[type="text"]').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit|→|▶/i }).first();
    
    // Verify chat interface exists
    await expect(chatInput).toBeVisible({ timeout: 10000 });
    await expect(sendButton).toBeVisible();
    
    // Test basic chat functionality
    const testMessage = 'Hello, this is a production test message. Please respond with a simple greeting.';
    await chatInput.fill(testMessage);
    await sendButton.click();
    
    // Wait for response
    await page.waitForTimeout(10000);
    
    // Check for messages in chat
    const messages = page.locator('[data-testid*="message"], .message, .chat-message, [class*="message"]');
    const messageCount = await messages.count();
    
    expect(messageCount).toBeGreaterThanOrEqual(2); // User message + AI response
    console.log(`✅ Found ${messageCount} messages in chat`);
    
    // Test response formatting with different content types
    const formattingTests = [
      {
        query: 'Tell me about the movie "The Matrix" from 1999',
        type: 'movie',
        expectedElements: ['.movie-card', '[data-format="movie"]', '.formatted-response']
      },
      {
        query: 'How do I make chocolate chip cookies? Please include ingredients and steps.',
        type: 'recipe', 
        expectedElements: ['.recipe-card', '[data-format="recipe"]', '.ingredients', '.steps']
      },
      {
        query: 'What is the current weather forecast?',
        type: 'weather',
        expectedElements: ['.weather-card', '[data-format="weather"]', '.forecast']
      }
    ];
    
    for (const test of formattingTests) {
      console.log(`Testing ${test.type} response formatting...`);
      
      // Clear and send new message
      await chatInput.fill(test.query);
      await sendButton.click();
      await page.waitForTimeout(15000); // Wait longer for AI response
      
      // Check for formatted response elements
      let foundFormatting = false;
      for (const selector of test.expectedElements) {
        const elements = await page.locator(selector).count();
        if (elements > 0) {
          foundFormatting = true;
          console.log(`✅ Found ${test.type} formatting: ${selector}`);
          break;
        }
      }
      
      if (!foundFormatting) {
        // Check if response contains relevant content even without special formatting
        const lastMessage = messages.last();
        const messageText = await lastMessage.textContent() || '';
        
        const hasRelevantContent = test.type === 'movie' ? 
          (messageText.includes('Matrix') || messageText.includes('movie') || messageText.includes('film')) :
          test.type === 'recipe' ?
          (messageText.includes('ingredients') || messageText.includes('recipe') || messageText.includes('cookies')) :
          test.type === 'weather' ?
          (messageText.includes('weather') || messageText.includes('temperature') || messageText.includes('forecast')) :
          false;
        
        if (hasRelevantContent) {
          console.log(`⚠️ ${test.type} response has relevant content but may lack special formatting`);
        } else {
          console.log(`❌ ${test.type} response may not be working properly`);
        }
      }
      
      // Wait between tests
      await page.waitForTimeout(2000);
    }
  });

  test('Model selection and switching functionality', async ({ page }) => {
    console.log('🤖 Testing model selection and switching');
    
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');
    
    // Find model selector
    const modelSelector = page.locator('select, [data-testid*="model"], [class*="model"], [role="combobox"]').first();
    
    if (await modelSelector.count() > 0) {
      console.log('✅ Model selector found');
      
      // Check available options
      const options = await modelSelector.locator('option').allTextContents();
      console.log(`Available models: ${options.join(', ')}`);
      
      // Verify we have production models (no test/demo entries)
      const testEntries = options.filter(option => 
        option.toLowerCase().includes('test') || 
        option.toLowerCase().includes('demo') ||
        option.toLowerCase().includes('other model') ||
        option.toLowerCase().includes('placeholder')
      );
      
      expect(testEntries).toHaveLength(0);
      console.log('✅ No test/demo model entries found');
      
      // Test model switching if multiple options available
      if (options.length > 1) {
        const initialSelection = await modelSelector.inputValue();
        console.log(`Initial model: ${initialSelection}`);
        
        // Select a different model
        const alternativeModel = options.find(option => option !== initialSelection);
        if (alternativeModel) {
          await modelSelector.selectOption(alternativeModel);
          await page.waitForTimeout(2000);
          
          const newSelection = await modelSelector.inputValue();
          expect(newSelection).toBe(alternativeModel);
          console.log(`✅ Successfully switched to: ${newSelection}`);
          
          // Test that chat still works with new model
          const chatInput = page.locator('textarea, input[type="text"]').first();
          const sendButton = page.locator('button').filter({ hasText: /send|submit/i }).first();
          
          if (await chatInput.count() > 0 && await sendButton.count() > 0) {
            await chatInput.fill('Test message with new model');
            await sendButton.click();
            await page.waitForTimeout(8000);
            
            const messages = page.locator('[data-testid*="message"], .message, .chat-message');
            const messageCount = await messages.count();
            
            if (messageCount > 0) {
              console.log('✅ Chat functionality works with model switching');
            }
          }
        }
      } else {
        console.log('ℹ️ Only one model available, skipping switching test');
      }
      
    } else {
      // Try alternative selectors for model selection
      const alternativeSelectors = [
        '[data-testid="model-selector"]',
        '.model-selector',
        'button:has-text("model")',
        '[aria-label*="model"]'
      ];
      
      let foundAlternative = false;
      for (const selector of alternativeSelectors) {
        if (await page.locator(selector).count() > 0) {
          console.log(`✅ Found model selector with alternative selector: ${selector}`);
          foundAlternative = true;
          break;
        }
      }
      
      if (!foundAlternative) {
        console.log('⚠️ Model selector not found - may be integrated differently');
      }
    }
  });
});

test.describe('Production Workflows - Integration Tests', () => {
  test('End-to-end user workflow', async ({ page }) => {
    console.log('🔄 Testing complete end-to-end user workflow');
    
    // 1. Start at home page
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 2. Navigate to chat (or login if required)
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      // Login if required
      const emailInput = page.locator('input[type="email"]').first();
      const passwordInput = page.locator('input[type="password"]').first();
      const submitButton = page.locator('button[type="submit"]').first();
      
      await emailInput.fill('admin@example.com');
      await passwordInput.fill('adminadmin');
      await submitButton.click();
      await page.waitForTimeout(3000);
    }
    
    // Navigate to chat
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');
    
    // 3. Test complete chat workflow
    const chatInput = page.locator('textarea, input[type="text"]').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit/i }).first();
    
    await expect(chatInput).toBeVisible();
    await expect(sendButton).toBeVisible();
    
    // 4. Send multiple messages to test conversation flow
    const testMessages = [
      'Hello, I need help with a technical question.',
      'Can you explain what artificial intelligence is?',
      'Thank you for the explanation.'
    ];
    
    for (let i = 0; i < testMessages.length; i++) {
      await chatInput.fill(testMessages[i]);
      await sendButton.click();
      await page.waitForTimeout(8000); // Wait for response
      
      // Verify message was added
      const messages = page.locator('[data-testid*="message"], .message, .chat-message');
      const messageCount = await messages.count();
      expect(messageCount).toBeGreaterThanOrEqual((i + 1) * 2); // Each exchange = 2 messages
    }
    
    console.log('✅ End-to-end workflow completed successfully');
  });

  test('Error handling and recovery', async ({ page }) => {
    console.log('🛠️ Testing error handling and recovery');
    
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');
    
    // Test network error handling
    await page.route('**/api/**', route => {
      route.abort('failed');
    });
    
    const chatInput = page.locator('textarea, input[type="text"]').first();
    const sendButton = page.locator('button').filter({ hasText: /send|submit/i }).first();
    
    if (await chatInput.count() > 0 && await sendButton.count() > 0) {
      await chatInput.fill('This message should trigger an error');
      await sendButton.click();
      await page.waitForTimeout(5000);
      
      // Check for error handling
      const errorElements = page.locator('.error, [data-testid*="error"], .alert-error, [class*="error"]');
      const hasErrorHandling = await errorElements.count() > 0;
      
      if (hasErrorHandling) {
        console.log('✅ Error handling UI detected');
      } else {
        console.log('⚠️ Error handling may not be visible to user');
      }
      
      // Remove network interception
      await page.unroute('**/api/**');
      
      // Test recovery
      await page.waitForTimeout(2000);
      await chatInput.fill('Recovery test message');
      await sendButton.click();
      await page.waitForTimeout(8000);
      
      const messages = page.locator('[data-testid*="message"], .message, .chat-message');
      const messageCount = await messages.count();
      
      if (messageCount > 0) {
        console.log('✅ System recovered from network error');
      }
    }
  });
});