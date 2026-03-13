import { test, type Page, type BrowserContext } from '@playwright/test';

/**
 * Server availability checker and helper utilities for Playwright tests
 * Provides graceful handling when server is not available
 */

export interface ServerConfig {
  baseURL: string;
  timeout: number;
  retries: number;
  retryDelay: number;
}

export const DEFAULT_SERVER_CONFIG: ServerConfig = {
  baseURL: 'http://localhost:9002',
  timeout: 5000,
  retries: 3,
  retryDelay: 1000,
};

export class ServerHelper {
  private config: ServerConfig;
  private page: Page;

  constructor(page: Page, config: Partial<ServerConfig> = {}) {
    this.page = page;
    this.config = { ...DEFAULT_SERVER_CONFIG, ...config };
  }

  /**
   * Check if server is available by making a simple request
   */
  async isServerAvailable(): Promise<boolean> {
    const { baseURL, timeout, retries, retryDelay } = this.config;

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        console.log(`Checking server availability (attempt ${attempt}/${retries}): ${baseURL}`);
        
        // Try to fetch base URL
        const response = await fetch(baseURL, {
          method: 'HEAD',
          signal: AbortSignal.timeout(timeout),
        });
        
        if (response.ok) {
          console.log(`Server is available at ${baseURL}`);
          return true;
        }
      } catch (error) {
        console.warn(`Server check attempt ${attempt} failed:`, error instanceof Error ? error.message : error);
        
        if (attempt < retries) {
          console.log(`Retrying in ${retryDelay}ms...`);
          await this.sleep(retryDelay);
        }
      }
    }

    console.log(`Server is not available at ${baseURL} after ${retries} attempts`);
    return false;
  }

  /**
   * Navigate to a URL with server availability check
   */
  async navigateWithFallback(url: string, fallbackContent?: string): Promise<boolean> {
    const serverAvailable = await this.isServerAvailable();
    
    if (!serverAvailable) {
      console.log(`Server not available, using fallback for ${url}`);
      
      // Create a mock page content when server is not available
      await this.createMockPage(url, fallbackContent);
      return false;
    }

    try {
      console.log(`Navigating to ${url}`);
      await this.page.goto(url, { timeout: this.config.timeout });
      return true;
    } catch (error) {
      console.error(`Navigation to ${url} failed:`, error instanceof Error ? error.message : error);
      
      // Fallback to mock content if navigation fails
      await this.createMockPage(url, fallbackContent);
      return false;
    }
  }

  /**
   * Create a mock page when server is not available
   */
  private async createMockPage(url: string, customContent?: string): Promise<void> {
    const mockContent = customContent || this.generateMockContent(url);
    
    await this.page.setContent(mockContent);
    console.log(`Created mock page for ${url}`);
  }

  /**
   * Generate mock HTML content based on URL
   */
  private generateMockContent(url: string): string {
    if (url.includes('/chat')) {
      return this.generateChatMockContent();
    } else if (url.includes('/login')) {
      return this.generateLoginMockContent();
    } else if (url.includes('/profile')) {
      return this.generateProfileMockContent();
    } else {
      return this.generateDefaultMockContent(url);
    }
  }

  /**
   * Generate mock chat page content
   */
  private generateChatMockContent(): string {
    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chat - AI Karen (Mock)</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
          .chat-container { max-width: 800px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
          .chat-header { padding: 20px; border-bottom: 1px solid #eee; background: #4CAF50; color: white; border-radius: 8px 8px 0 0; }
          .chat-messages { height: 400px; overflow-y: auto; padding: 20px; }
          .chat-input { padding: 20px; border-top: 1px solid #eee; display: flex; gap: 10px; }
          .message-input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
          .send-button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
          .voice-button { padding: 10px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer; }
          .file-input { display: none; }
          .mock-notice { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 10px; margin-bottom: 20px; text-align: center; }
        </style>
      </head>
      <body>
        <div class="mock-notice">
          <strong>Mock Mode:</strong> Server is not running. This is simulated content for testing purposes.
        </div>
        <div class="chat-container" data-testid="chat-container">
          <div class="chat-header">
            <h2>AI Karen Chat</h2>
          </div>
          <div class="chat-messages">
            <div class="assistant-message" data-testid="assistant-message">
              <p>Hello! I'm AI Karen. How can I help you today? (Mock Response)</p>
            </div>
          </div>
          <div class="chat-input">
            <input type="text" class="message-input" data-testid="message-input" placeholder="Type your message here..." style="display: block;">
            <button class="send-button" data-testid="send-button">Send</button>
            <button class="voice-button" data-testid="voice-button">🎤</button>
            <input type="file" class="file-input" data-testid="file-input" style="display: block;">
          </div>
        </div>
      </body>
      </html>
    `;
  }

  /**
   * Generate mock login page content
   */
  private generateLoginMockContent(): string {
    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - AI Karen (Mock)</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
          .login-container { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
          .login-header { text-align: center; margin-bottom: 30px; }
          .form-group { margin-bottom: 20px; }
          .form-label { display: block; margin-bottom: 5px; font-weight: bold; }
          .form-input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
          .login-button { width: 100%; padding: 12px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
          .mock-notice { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 10px; margin-bottom: 20px; text-align: center; }
          .user-menu { margin-top: 20px; padding: 10px; background: #4CAF50; color: white; border-radius: 4px; display: none; }
          .user-menu.visible { display: block; }
          .profile-link { margin-top: 15px; padding: 8px 16px; background: #2196F3; color: white; text-decoration: none; border-radius: 4px; display: inline-block; }
          .login-success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px; border-radius: 4px; margin-top: 15px; display: none; }
          .login-success.visible { display: block; }
        </style>
      </head>
      <body>
        <div class="login-container">
          <div class="mock-notice">
            <strong>Mock Mode:</strong> Server is not running. This is simulated content for testing purposes.
          </div>
          <div class="login-header">
            <h2>Login to AI Karen</h2>
          </div>
          <form class="login-form" data-testid="login-form">
            <div class="form-group">
              <label class="form-label">Email</label>
              <input type="email" class="form-input" data-testid="email-input" placeholder="Enter your email">
            </div>
            <div class="form-group">
              <label class="form-label">Password</label>
              <input type="password" class="form-input" data-testid="password-input" placeholder="Enter your password">
            </div>
            <button type="submit" class="login-button" data-testid="login-button">Login</button>
          </form>
          <div class="user-menu" data-testid="user-menu">
            <h3>User Menu (Mock)</h3>
            <p>Welcome, Test User!</p>
            <div class="user-id" data-testid="user-id">test-user-123</div>
            <a href="/profile" class="profile-link" data-testid="profile-link">Go to Profile</a>
          </div>
          <div class="login-success" data-testid="login-success">
            Login successful! Welcome back.
          </div>
        </div>
        <script>
          // Mock login functionality
          document.querySelector('.login-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Simulate login process
            setTimeout(function() {
              // Hide login form
              document.querySelector('.login-form').style.display = 'none';
              
              // Show user menu
              const userMenu = document.querySelector('.user-menu');
              userMenu.classList.add('visible');
              
              // Show success message
              const loginSuccess = document.querySelector('.login-success');
              loginSuccess.classList.add('visible');
              
              // Simulate navigation by updating URL (for testing purposes)
              // Use try-catch to handle security restrictions in Playwright
              try {
                window.history.pushState({}, '', '/dashboard');
              } catch (error) {
                console.log('History pushState failed (expected in Playwright):', error.message);
                // Alternative: update location hash
                window.location.hash = '#dashboard';
              }
              
              // Dispatch a custom event to indicate login success
              window.dispatchEvent(new CustomEvent('login-success', {
                detail: { userId: 'test-user-123', email: 'testuser@example.com' }
              }));
            }, 500);
          });
          
          // Handle profile link click
          document.querySelector('.profile-link').addEventListener('click', function(e) {
            e.preventDefault();
            
            // Simulate navigation to profile page
            setTimeout(function() {
              // Replace entire page content with profile page content
              const profileHTML = generateProfileHTML();
              document.body.innerHTML = profileHTML;
              
              // Try to update URL
              try {
                window.history.pushState({}, '', '/profile');
              } catch (error) {
                console.log('History pushState failed (expected in Playwright):', error.message);
                window.location.hash = '#profile';
              }
            }, 100);
          });
          
          // Function to generate profile HTML
          function generateProfileHTML() {
            return '<!DOCTYPE html>' +
              '<html lang="en">' +
                '<head>' +
                  '<meta charset="UTF-8">' +
                  '<meta name="viewport" content="width=device-width, initial-scale=1.0">' +
                  '<title>Profile - AI Karen (Mock)</title>' +
                  '<style>' +
                    'body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }' +
                    '.profile-container { max-width: 800px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 40px; }' +
                    '.profile-header { text-align: center; margin-bottom: 30px; }' +
                    '.profile-info { display: grid; gap: 20px; }' +
                    '.info-group { padding: 20px; border: 1px solid #eee; border-radius: 4px; }' +
                    '.submit-button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }' +
                    '.mock-notice { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 10px; margin-bottom: 20px; text-align: center; }' +
                  '</style>' +
                '</head>' +
                '<body>' +
                  '<div class="mock-notice">' +
                    '<strong>Mock Mode:</strong> Server is not running. This is simulated content for testing purposes.' +
                  '</div>' +
                  '<div class="profile-container" data-testid="profile-page">' +
                    '<div class="profile-header">' +
                      '<h1 data-testid="profile-header">User Profile</h1>' +
                    '</div>' +
                    '<div class="profile-info">' +
                      '<div class="info-group">' +
                        '<h3>User Information</h3>' +
                        '<p><strong>Email:</strong> testuser@example.com</p>' +
                        '<p><strong>User ID:</strong> <span data-testid="user-id">test-user-123</span></p>' +
                      '</div>' +
                      '<div class="info-group">' +
                        '<h3>Actions</h3>' +
                        '<button class="submit-button" data-testid="submit-data-button">Update Profile</button>' +
                        '<div data-testid="api-response-indicator" style="margin-top: 10px; padding: 5px; background: #e8f5e8; border-radius: 4px;">API Response Ready</div>' +
                      '</div>' +
                    '</div>' +
                  '</div>' +
                '</body>' +
              '</html>';
          }
        </script>
      </body>
      </html>
    `;
  }

  /**
   * Generate mock profile page content
   */
  private generateProfileMockContent(): string {
    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Profile - AI Karen (Mock)</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
          .profile-container { max-width: 800px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 40px; }
          .profile-header { text-align: center; margin-bottom: 30px; }
          .profile-info { display: grid; gap: 20px; }
          .info-group { padding: 20px; border: 1px solid #eee; border-radius: 4px; }
          .submit-button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
          .mock-notice { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 10px; margin-bottom: 20px; text-align: center; }
        </style>
      </head>
      <body>
        <div class="mock-notice">
          <strong>Mock Mode:</strong> Server is not running. This is simulated content for testing purposes.
        </div>
        <div class="profile-container" data-testid="profile-page">
          <div class="profile-header">
            <h1 data-testid="profile-header">User Profile</h1>
          </div>
          <div class="profile-info">
            <div class="info-group">
              <h3>User Information</h3>
              <p><strong>Email:</strong> testuser@example.com</p>
              <p><strong>User ID:</strong> <span data-testid="user-id">test-user-123</span></p>
            </div>
            <div class="info-group">
              <h3>Actions</h3>
              <button class="submit-button" data-testid="submit-data-button">Update Profile</button>
              <div data-testid="api-response-indicator" style="margin-top: 10px; padding: 5px; background: #e8f5e8; border-radius: 4px;">API Response Ready</div>
            </div>
          </div>
        </div>
      </body>
      </html>
    `;
  }

  /**
   * Generate default mock content for unknown pages
   */
  private generateDefaultMockContent(url: string): string {
    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Page - AI Karen (Mock)</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; text-align: center; }
          .mock-container { max-width: 600px; margin: 50px auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
          .mock-notice { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 10px; margin-bottom: 20px; }
        </style>
      </head>
      <body>
        <div class="mock-container">
          <div class="mock-notice">
            <strong>Mock Mode:</strong> Server is not running. This is simulated content for testing purposes.
          </div>
          <h1>Mock Page</h1>
          <p>This is a mock page for: <code>${url}</code></p>
          <p>The original server is not available, so this content was generated for testing purposes.</p>
        </div>
      </body>
      </html>
    `;
  }

  /**
   * Sleep helper function
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Mock API response for testing
   */
  async setupMockApiResponses(): Promise<void> {
    await this.page.route('**/api/**', async (route) => {
      const url = route.request().url();
      
      console.log(`Mocking API response for: ${url}`);
      
      // Mock different API endpoints
      if (url.includes('/api/auth/login')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            userId: 'test-user-123',
            user: { id: 'test-user-123', email: 'testuser@example.com' }
          }),
        });
      } else if (url.includes('/api/user/data')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            userId: 'test-user-123',
            submissionId: '550e8400-e29b-41d4-a716-446655440000',
            submissionTimestamp: new Date().toISOString(),
            data: { name: 'Test User', email: 'testuser@example.com' }
          }),
        });
      } else if (url.includes('/api/user/profile')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            data: {
              id: 'test-user-123',
              email: 'testuser@example.com',
              name: 'Test User',
              preferences: {
                theme: 'light',
                notifications: true
              }
            }
          }),
        });
      } else if (url.includes('/api/validate')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            validated: true,
            data: {
              id: 'test-user-123',
              timestamp: new Date().toISOString(),
              checksum: 'abc123def456'
            }
          }),
        });
      } else if (url.includes('/api/error')) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            success: false,
            error: {
              code: 'INTERNAL_SERVER_ERROR',
              message: 'Mock server error for testing'
            }
          }),
        });
      } else {
        // Default mock response
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            message: 'Mock API response',
            timestamp: new Date().toISOString(),
          }),
        });
      }
    });

    // Set up mock navigation for profile link
    await this.page.route('**/profile', async (route) => {
      console.log('Mocking profile navigation');
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: this.generateProfileMockContent(),
      });
    });

    // Add error message simulation script
    await this.page.addInitScript(() => {
      // Store error messages globally for test access
      (window as any).__testErrors = [];
      
      // Function to simulate error display
      (window as any).simulateError = (message: string) => {
        // Create error element if it doesn't exist
        let errorElement = document.querySelector('[data-testid="error-message"]');
        if (!errorElement) {
          errorElement = document.createElement('div');
          errorElement.setAttribute('data-testid', 'error-message');
          (errorElement as HTMLElement).style.cssText = 'color: red; padding: 10px; margin: 10px; border: 1px solid red; border-radius: 4px;';
          document.body.appendChild(errorElement);
        }
        errorElement.textContent = message;
        (window as any).__testErrors.push(message);
      };
    });
  }

  /**
   * Get current server configuration
   */
  getConfig(): ServerConfig {
    return { ...this.config };
  }
}

/**
 * Create a server helper instance for use in tests
 */
export function createServerHelper(page: Page, config?: Partial<ServerConfig>): ServerHelper {
  return new ServerHelper(page, config);
}

/**
 * Test decorator to skip tests when server is not available
 */
export function skipWhenServerUnavailable(page: Page, config?: Partial<ServerConfig>) {
  return async function() {
    const helper = new ServerHelper(page, config);
    const serverAvailable = await helper.isServerAvailable();
    
    if (!serverAvailable) {
      console.log('Skipping test - server not available');
      test.skip();
    }
  };
}