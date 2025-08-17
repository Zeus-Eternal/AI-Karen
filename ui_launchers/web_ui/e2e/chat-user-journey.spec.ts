import { test, expect, Page } from '@playwright/test';

/**
 * End-to-End Tests for Complete Chat User Journeys
 * Tests the full user experience from login to conversation completion
 */

// Test data and utilities
const TEST_USER = {
  email: 'test@example.com',
  password: 'testpassword123'
};

const TEST_MESSAGES = {
  simple: 'Hello, how are you?',
  complex: 'Can you help me write a Python function to calculate fibonacci numbers?',
  withCode: 'Show me an example of a React component with hooks',
  longMessage: 'This is a very long message that should test the text area expansion and handling of lengthy user inputs. '.repeat(5)
};

// Helper functions
async function loginUser(page: Page) {
  await page.goto('/login');
  await page.fill('[data-testid="email-input"]', TEST_USER.email);
  await page.fill('[data-testid="password-input"]', TEST_USER.password);
  await page.click('[data-testid="login-button"]');
  await page.waitForURL('/chat');
}

async function waitForStreamingComplete(page: Page) {
  // Wait for streaming indicator to disappear
  await page.waitForSelector('[data-testid="streaming-indicator"]', { state: 'hidden', timeout: 30000 });
}

test.describe('Complete Chat User Journeys', () => {
  test.beforeEach(async ({ page }) => {
    // Set up test environment
    await page.goto('/');
  });

  test('Happy path: Login → Send message → Receive response → Continue conversation', async ({ page }) => {
    // Step 1: Login
    await loginUser(page);
    
    // Verify we're on the chat page
    await expect(page).toHaveURL('/chat');
    await expect(page.locator('[data-testid="chat-interface"]')).toBeVisible();
    
    // Step 2: Send first message
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill(TEST_MESSAGES.simple);
    await page.click('[data-testid="send-button"]');
    
    // Verify message appears in chat
    await expect(page.locator('[data-testid="user-message"]').last()).toContainText(TEST_MESSAGES.simple);
    
    // Step 3: Wait for AI response
    await waitForStreamingComplete(page);
    await expect(page.locator('[data-testid="assistant-message"]').last()).toBeVisible();
    
    // Step 4: Continue conversation
    await messageInput.fill(TEST_MESSAGES.complex);
    await page.click('[data-testid="send-button"]');
    
    // Verify conversation history is maintained
    const messages = page.locator('[data-testid="message"]');
    await expect(messages).toHaveCount(4); // 2 user + 2 assistant messages
    
    // Wait for second response
    await waitForStreamingComplete(page);
    
    // Verify final state
    await expect(page.locator('[data-testid="assistant-message"]')).toHaveCount(2);
  });

  test('Code interaction journey: Request code → Copy code → Edit message', async ({ page }) => {
    await loginUser(page);
    
    // Send message requesting code
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill(TEST_MESSAGES.withCode);
    await page.click('[data-testid="send-button"]');
    
    // Wait for response with code block
    await waitForStreamingComplete(page);
    
    // Verify code block is present
    const codeBlock = page.locator('[data-testid="code-block"]').first();
    await expect(codeBlock).toBeVisible();
    
    // Test copy functionality
    await codeBlock.locator('[data-testid="copy-button"]').click();
    await expect(page.locator('[data-testid="copy-success-toast"]')).toBeVisible();
    
    // Test message editing
    const lastUserMessage = page.locator('[data-testid="user-message"]').last();
    await lastUserMessage.hover();
    await lastUserMessage.locator('[data-testid="edit-button"]').click();
    
    // Edit the message
    const editInput = page.locator('[data-testid="edit-message-input"]');
    await editInput.fill('Show me a TypeScript version of that component');
    await page.click('[data-testid="save-edit-button"]');
    
    // Verify message was updated and new response generated
    await expect(lastUserMessage).toContainText('TypeScript version');
    await waitForStreamingComplete(page);
  });

  test('File upload journey: Upload file → Process → Continue conversation', async ({ page }) => {
    await loginUser(page);
    
    // Test file upload
    const fileInput = page.locator('[data-testid="file-input"]');
    
    // Create a test file
    const testFile = {
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('This is a test file content for processing.')
    };
    
    await fileInput.setInputFiles(testFile);
    
    // Verify file appears in upload area
    await expect(page.locator('[data-testid="uploaded-file"]')).toContainText('test.txt');
    
    // Send message with file
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Please analyze this file');
    await page.click('[data-testid="send-button"]');
    
    // Verify file is included in message
    const userMessage = page.locator('[data-testid="user-message"]').last();
    await expect(userMessage.locator('[data-testid="file-attachment"]')).toBeVisible();
    
    // Wait for AI response
    await waitForStreamingComplete(page);
    await expect(page.locator('[data-testid="assistant-message"]').last()).toBeVisible();
    
    // Continue conversation about the file
    await messageInput.fill('What are the key points from that file?');
    await page.click('[data-testid="send-button"]');
    await waitForStreamingComplete(page);
  });

  test('Voice input journey: Voice → Text → Send → Response', async ({ page }) => {
    await loginUser(page);
    
    // Mock getUserMedia for voice input
    await page.addInitScript(() => {
      // Mock MediaRecorder and getUserMedia
      (window as any).MediaRecorder = class MockMediaRecorder {
        constructor() {}
        start() {}
        stop() {}
        addEventListener() {}
      };
      
      (navigator as any).mediaDevices = {
        getUserMedia: () => Promise.resolve({
          getTracks: () => [{ stop: () => {} }]
        })
      };
    });
    
    // Start voice recording
    await page.click('[data-testid="voice-input-button"]');
    await expect(page.locator('[data-testid="recording-indicator"]')).toBeVisible();
    
    // Simulate voice input completion
    await page.click('[data-testid="stop-recording-button"]');
    
    // Mock transcription result
    await page.evaluate(() => {
      const event = new CustomEvent('transcription-complete', {
        detail: { text: 'This is a voice transcribed message' }
      });
      window.dispatchEvent(event);
    });
    
    // Verify transcribed text appears
    const messageInput = page.locator('[data-testid="message-input"]');
    await expect(messageInput).toHaveValue('This is a voice transcribed message');
    
    // Send the transcribed message
    await page.click('[data-testid="send-button"]');
    await waitForStreamingComplete(page);
  }); 
 test('Conversation management journey: Create → Rename → Delete → Restore', async ({ page }) => {
    await loginUser(page);
    
    // Start a conversation
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Start a new conversation about AI');
    await page.click('[data-testid="send-button"]');
    await waitForStreamingComplete(page);
    
    // Open conversation menu
    await page.click('[data-testid="conversation-menu-button"]');
    
    // Rename conversation
    await page.click('[data-testid="rename-conversation"]');
    const renameInput = page.locator('[data-testid="conversation-name-input"]');
    await renameInput.fill('AI Discussion');
    await page.click('[data-testid="save-name-button"]');
    
    // Verify name change
    await expect(page.locator('[data-testid="conversation-title"]')).toContainText('AI Discussion');
    
    // Create new conversation
    await page.click('[data-testid="new-conversation-button"]');
    await expect(page.locator('[data-testid="message-input"]')).toBeEmpty();
    
    // Verify conversation list
    await page.click('[data-testid="conversation-list-button"]');
    const conversationList = page.locator('[data-testid="conversation-list"]');
    await expect(conversationList.locator('[data-testid="conversation-item"]')).toHaveCount(2);
    
    // Switch back to first conversation
    await conversationList.locator('[data-testid="conversation-item"]').first().click();
    await expect(page.locator('[data-testid="conversation-title"]')).toContainText('AI Discussion');
    
    // Delete conversation
    await page.click('[data-testid="conversation-menu-button"]');
    await page.click('[data-testid="delete-conversation"]');
    await page.click('[data-testid="confirm-delete-button"]');
    
    // Verify deletion
    await expect(page.locator('[data-testid="conversation-title"]')).not.toContainText('AI Discussion');
  });

  test('Settings and preferences journey: Change theme → Update model → Save preferences', async ({ page }) => {
    await loginUser(page);
    
    // Open settings
    await page.click('[data-testid="settings-button"]');
    await expect(page.locator('[data-testid="settings-modal"]')).toBeVisible();
    
    // Change theme
    await page.click('[data-testid="theme-selector"]');
    await page.click('[data-testid="dark-theme-option"]');
    
    // Verify theme change
    await expect(page.locator('html')).toHaveClass(/dark/);
    
    // Change AI model
    await page.click('[data-testid="model-selector"]');
    await page.click('[data-testid="gpt-4-option"]');
    
    // Update other preferences
    await page.check('[data-testid="enable-streaming-checkbox"]');
    await page.fill('[data-testid="max-tokens-input"]', '2000');
    
    // Save settings
    await page.click('[data-testid="save-settings-button"]');
    await expect(page.locator('[data-testid="settings-saved-toast"]')).toBeVisible();
    
    // Close settings and verify persistence
    await page.click('[data-testid="close-settings-button"]');
    
    // Send a message to verify new settings are applied
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Test message with new settings');
    await page.click('[data-testid="send-button"]');
    
    // Verify model indicator shows correct model
    await expect(page.locator('[data-testid="current-model-indicator"]')).toContainText('GPT-4');
    
    await waitForStreamingComplete(page);
  });

  test('Error recovery journey: Network failure → Retry → Success', async ({ page }) => {
    await loginUser(page);
    
    // Intercept network requests to simulate failure
    await page.route('**/api/chat/**', route => {
      route.abort('failed');
    });
    
    // Send message that will fail
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('This message will fail initially');
    await page.click('[data-testid="send-button"]');
    
    // Verify error state
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    
    // Remove network interception to allow retry to succeed
    await page.unroute('**/api/chat/**');
    
    // Retry the message
    await page.click('[data-testid="retry-button"]');
    
    // Verify success after retry
    await waitForStreamingComplete(page);
    await expect(page.locator('[data-testid="assistant-message"]').last()).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible();
  });
});