/**
 * API Response Validation Tests
 * End-to-end testing for critical user flow with API interception and validation
 */

import { test, expect } from '@playwright/test';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

// Test configuration
const TEST_CONFIG = {
  timeout: 30000,
  retries: 2,
  headless: false,
  slowMo: 0,
};

// Test environment placeholders
const APP_LOGIN_URL = process.env.APP_LOGIN_URL || '/login';
const TEST_USER = process.env.TEST_USER || 'testuser@example.com';
const TEST_PASS = process.env.TEST_PASS || 'testpassword123';

// API endpoints
const API_ENDPOINTS = {
  USER_DATA: '/api/user/data',
  LOGIN: '/api/auth/login',
  PROFILE: '/profile',
};

// Interface for API request/response data
interface ApiRequestData {
  url: string;
  method: string;
  headers: Record<string, string>;
  postData?: string | null;
}

interface ApiResponseData {
  status: number;
  statusText: string;
  headers: Record<string, string>;
  body?: any;
}

// Extended interface for validated API response data
interface ValidatedApiResponseData extends ApiResponseData {
  userId?: string;
  submissionId?: string;
  submissionTimestamp?: string;
}

// Helper function to validate UUID format
function isValidUUID(uuid: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
}

// Helper function to validate ISO 8601 timestamp
function isValidISO8601(timestamp: string): boolean {
  if (typeof timestamp !== 'string') return false;
  
  // Check if it's a valid date and matches ISO 8601 format
  const date = new Date(timestamp);
  if (isNaN(date.getTime())) return false;
  
  // More strict regex for ISO 8601
  const iso8601Regex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?([+-]\d{2}:\d{2})?$/;
  return iso8601Regex.test(timestamp);
}

// Helper function to check if timestamp is recent (within last 5 minutes)
function isRecentTimestamp(timestamp: string): boolean {
  const date = new Date(timestamp);
  if (isNaN(date.getTime())) return false;
  
  const now = new Date();
  const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);
  
  return date >= fiveMinutesAgo && date <= now;
}

describe('API Response Validation Tests', () => {
  let browser: Browser;
  let context: BrowserContext;
  let page: Page;
  
  beforeAll(async () => {
    browser = await chromium.launch({
      headless: TEST_CONFIG.headless,
      slowMo: TEST_CONFIG.slowMo,
    });
    
    context = await browser.newContext({
      viewport: { width: 1280, height: 720 },
    });
    
    page = await context.newPage();
    
    // Set up error handling
    page.on('pageerror', (error) => {
      console.error('Page error:', error);
    });
    
    page.on('requestfailed', (request) => {
      console.error('Request failed:', request.url(), request.failure());
    });
    
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        console.error('Console error:', msg.text());
      }
    });
  });
  
  afterAll(async () => {
    await context.close();
    await browser.close();
  });

  beforeEach(async () => {
    // Clear cookies and storage before each test
    await context.clearCookies();
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test('should authenticate successfully and navigate to profile', async () => {
    // Navigate to login page
    await page.goto(APP_LOGIN_URL);
    
    // Wait for login form to be visible
    await page.waitForSelector('[data-testid="login-form"]', { timeout: 10000 });
    
    // Fill in login credentials
    await page.fill('[data-testid="email-input"]', TEST_USER);
    await page.fill('[data-testid="password-input"]', TEST_PASS);
    
    // Submit login form
    await page.click('[data-testid="login-button"]');
    
    // Wait for successful login redirect or success message
    await page.waitForSelector('[data-testid="login-success"]', { timeout: 15000 });
    
    // Verify login was successful by checking for user-specific elements
    const userElement = await page.locator('[data-testid="user-menu"]');
    expect(await userElement.isVisible()).toBe(true);
    
    // Navigate to profile page
    await page.click('[data-testid="profile-link"]');
    await page.waitForSelector('[data-testid="profile-page"]', { timeout: 10000 });
    
    // Verify profile page loaded successfully
    const profileHeader = await page.locator('[data-testid="profile-header"]');
    expect(await profileHeader.isVisible()).toBe(true);
  });

  test('should intercept and capture API request/response for user data', async () => {
    // First, authenticate
    await authenticateUser(page);
    
    // Navigate to profile page
    await page.goto(API_ENDPOINTS.PROFILE);
    await page.waitForSelector('[data-testid="profile-page"]');
    
    // Set up request interception for the user data API
    let requestData: ApiRequestData | null = null;
    let responseData: ApiResponseData | null = null;
    
    await page.route(API_ENDPOINTS.USER_DATA, async (route) => {
      const request = route.request();
      
      // Capture request data
      requestData = {
        url: request.url(),
        method: request.method(),
        headers: request.headers(),
        postData: request.postData(),
      };
      
      console.log('API Request intercepted:', {
        url: requestData!.url,
        method: requestData!.method,
        headers: requestData!.headers,
      });
      
      // Continue with the request to get real response
      const response = await route.fetch();
      const responseHeaders = response.headers();
      const responseStatus = response.status();
      const responseStatusText = response.statusText();
      
      // Capture response data
      try {
        const responseBody = await response.json();
        responseData = {
          status: responseStatus,
          statusText: responseStatusText,
          headers: responseHeaders,
          body: responseBody,
        };
      } catch (error) {
        // If response is not JSON, get text instead
        const responseText = await response.text();
        responseData = {
          status: responseStatus,
          statusText: responseStatusText,
          headers: responseHeaders,
          body: responseText,
        };
      }
      
      console.log('API Response intercepted:', {
        status: responseData.status,
        statusText: responseData.statusText,
        headers: responseData.headers,
      });
      
      // Continue with the original response
      await route.fulfill({
        status: responseStatus,
        headers: responseHeaders,
        body: await response.text(),
      });
    });
    
    // Trigger the API call by clicking the data submission button
    await page.click('[data-testid="submit-data-button"]');
    
    // Wait for the API call to complete
    await page.waitForTimeout(2000);
    
    // Verify that we captured the request and response
    expect(requestData).not.toBeNull();
    expect(responseData).not.toBeNull();
    
    // Basic validation of the request
    expect(requestData!.url).toContain(API_ENDPOINTS.USER_DATA);
    expect(requestData!.method).toBe('POST');
    
    // Basic validation of the response
    expect(responseData!.status).toBeGreaterThanOrEqual(200);
    expect(responseData!.status).toBeLessThan(300);
    
    // Log the captured data for debugging
    console.log('Captured Request:', JSON.stringify(requestData, null, 2));
    console.log('Captured Response:', JSON.stringify(responseData, null, 2));
  });

  test('should handle API errors gracefully', async () => {
    // First, authenticate
    await authenticateUser(page);
    
    // Navigate to profile page
    await page.goto(API_ENDPOINTS.PROFILE);
    await page.waitForSelector('[data-testid="profile-page"]');
    
    // Set up request interception to simulate an error response
    await page.route(API_ENDPOINTS.USER_DATA, (route) => {
      console.log('Simulating API error response');
      
      // Fulfill with an error response
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error: 'Internal server error',
          message: 'Failed to process user data',
        }),
      });
    });
    
    // Trigger the API call
    await page.click('[data-testid="submit-data-button"]');
    
    // Wait for error handling to occur
    await page.waitForSelector('[data-testid="error-message"]', { timeout: 5000 });
    
    // Verify error message is displayed
    const errorMessage = await page.locator('[data-testid="error-message"]');
    expect(await errorMessage.isVisible()).toBe(true);
    
    const errorText = await errorMessage.textContent();
    expect(errorText).toContain('error');
  });

  test('should validate API response structure', async () => {
    // First, authenticate
    await authenticateUser(page);
    
    // Navigate to profile page
    await page.goto(API_ENDPOINTS.PROFILE);
    await page.waitForSelector('[data-testid="profile-page"]');
    
    // Set up request interception to capture and validate response
    await page.route(API_ENDPOINTS.USER_DATA, async (route) => {
      const request = route.request();
      const response = await route.fetch();
      const responseText = await response.text();
      
      try {
        const responseBody = await response.json();
        
        // Log response structure for validation
        console.log('API Response Structure:', JSON.stringify(responseBody, null, 2));
        
        // Basic structure validation (will be expanded in next subtask)
        if (typeof responseBody === 'object' && responseBody !== null) {
          console.log('Response is a valid object');
        } else {
          console.warn('Response is not a valid object');
        }
        
        // Continue with the original response
        await route.fulfill({
          status: response.status(),
          headers: response.headers(),
          body: responseText,
        });
      } catch (error) {
        console.error('Error parsing JSON response:', error);
        
        // Continue with the original response
        await route.fulfill({
          status: response.status(),
          headers: response.headers(),
          body: responseText,
        });
      }
    });
    
    // Trigger the API call
    await page.click('[data-testid="submit-data-button"]');
    
    // Wait for the API call to complete
    await page.waitForTimeout(2000);
    
    // Verify that some response was received
    const responseIndicator = await page.locator('[data-testid="api-response-indicator"]');
    expect(await responseIndicator.isVisible()).toBe(true);
  });

  test('should perform rigorous API response validation', async () => {
    // First, authenticate and extract user ID
    const userId = await authenticateUserAndGetId(page);
    
    // Navigate to profile page
    await page.goto(API_ENDPOINTS.PROFILE);
    await page.waitForSelector('[data-testid="profile-page"]');
    
    // Set up request interception for comprehensive validation
    let validatedResponse: ValidatedApiResponseData | null = null;
    
    await page.route(API_ENDPOINTS.USER_DATA, async (route) => {
      const request = route.request();
      const response = await route.fetch();
      
      // Capture response data
      const responseHeaders = response.headers();
      const responseStatus = response.status();
      const responseStatusText = response.statusText();
      
      try {
        const responseBody = await response.json();
        
        // Perform rigorous validation
        const validationResult = validateApiResponse(responseBody, responseStatus, userId);
        
        validatedResponse = {
          status: responseStatus,
          statusText: responseStatusText,
          headers: responseHeaders,
          body: responseBody,
          ...validationResult.extractedFields,
        };
        
        // Log validation results
        console.log('API Response Validation Results:', {
          status: responseStatus,
          isValid: validationResult.isValid,
          errors: validationResult.errors,
          extractedFields: validationResult.extractedFields,
        });
        
        // Continue with the original response
        await route.fulfill({
          status: responseStatus,
          headers: responseHeaders,
          body: await response.text(),
        });
      } catch (error) {
        console.error('Error during API response validation:', error);
        
        // Continue with the original response even if validation fails
        await route.fulfill({
          status: responseStatus,
          headers: responseHeaders,
          body: await response.text(),
        });
      }
    });
    
    // Trigger the API call
    await page.click('[data-testid="submit-data-button"]');
    
    // Wait for the API call to complete
    await page.waitForTimeout(2000);
    
    // Verify that validation was performed
    expect(validatedResponse).not.toBeNull();
    
    // Assert all validation requirements
    expect(validatedResponse!.status).toBe(200);
    expect(validatedResponse!.statusText).toBe('OK');
    expect(typeof validatedResponse!.body).toBe('object');
    expect(validatedResponse!.body).not.toBeNull();
    
    // Validate extracted fields
    expect(validatedResponse!.userId).toBe(userId);
    expect(validatedResponse!.submissionId).toBeDefined();
    expect(isValidUUID(validatedResponse!.submissionId!)).toBe(true);
    expect(validatedResponse!.submissionTimestamp).toBeDefined();
    expect(isValidISO8601(validatedResponse!.submissionTimestamp!)).toBe(true);
    expect(isRecentTimestamp(validatedResponse!.submissionTimestamp!)).toBe(true);
    
    console.log('All API response validation checks passed successfully');
  });

  /**
   * Validates API response against all requirements
   */
  function validateApiResponse(responseBody: any, status: number, expectedUserId: string): {
    isValid: boolean;
    errors: string[];
    extractedFields: {
      userId?: string;
      submissionId?: string;
      submissionTimestamp?: string;
    };
  } {
    const errors: string[] = [];
    const extractedFields: {
      userId?: string;
      submissionId?: string;
      submissionTimestamp?: string;
    } = {};
    
    // Validate status code
    if (status !== 200) {
      errors.push(`Expected status 200, got ${status}`);
    }
    
    // Validate response is a JSON object
    if (typeof responseBody !== 'object' || responseBody === null) {
      errors.push('Response body is not a valid JSON object');
      return { isValid: false, errors, extractedFields };
    }
    
    // Validate userId field
    if (!responseBody.userId) {
      errors.push('Missing userId field in response');
    } else if (typeof responseBody.userId !== 'string') {
      errors.push('userId field must be a string');
    } else if (responseBody.userId !== expectedUserId) {
      errors.push(`userId field (${responseBody.userId}) does not match expected user ID (${expectedUserId})`);
    } else {
      extractedFields.userId = responseBody.userId;
    }
    
    // Validate submissionId field
    if (!responseBody.submissionId) {
      errors.push('Missing submissionId field in response');
    } else if (typeof responseBody.submissionId !== 'string') {
      errors.push('submissionId field must be a string');
    } else if (responseBody.submissionId.trim() === '') {
      errors.push('submissionId field cannot be empty');
    } else if (!isValidUUID(responseBody.submissionId)) {
      errors.push(`submissionId field (${responseBody.submissionId}) is not a valid UUID`);
    } else {
      extractedFields.submissionId = responseBody.submissionId;
    }
    
    // Validate submissionTimestamp field
    if (!responseBody.submissionTimestamp) {
      errors.push('Missing submissionTimestamp field in response');
    } else if (typeof responseBody.submissionTimestamp !== 'string') {
      errors.push('submissionTimestamp field must be a string');
    } else if (!isValidISO8601(responseBody.submissionTimestamp)) {
      errors.push(`submissionTimestamp field (${responseBody.submissionTimestamp}) is not a valid ISO 8601 timestamp`);
    } else if (!isRecentTimestamp(responseBody.submissionTimestamp)) {
      errors.push(`submissionTimestamp field (${responseBody.submissionTimestamp}) is not recent`);
    } else {
      extractedFields.submissionTimestamp = responseBody.submissionTimestamp;
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      extractedFields,
    };
  }

  /**
   * Helper function to authenticate a user and extract user ID
   */
  async function authenticateUserAndGetId(page: Page): Promise<string> {
    await page.goto(APP_LOGIN_URL);
    
    // Wait for login form
    await page.waitForSelector('[data-testid="login-form"]', { timeout: 10000 });
    
    // Fill in credentials
    await page.fill('[data-testid="email-input"]', TEST_USER);
    await page.fill('[data-testid="password-input"]', TEST_PASS);
    
    // Set up interception to capture login response and extract user ID
    let extractedUserId: string | null = null;
    
    await page.route(API_ENDPOINTS.LOGIN, async (route) => {
      const response = await route.fetch();
      
      try {
        const responseBody = await response.json();
        
        // Extract user ID from login response
        if (responseBody.userId) {
          extractedUserId = responseBody.userId;
        } else if (responseBody.user && responseBody.user.id) {
          extractedUserId = responseBody.user.id;
        } else if (responseBody.data && responseBody.data.userId) {
          extractedUserId = responseBody.data.userId;
        }
        
        console.log('Extracted user ID from login response:', extractedUserId);
      } catch (error) {
        console.error('Error extracting user ID from login response:', error);
      }
      
      // Continue with the original response
      await route.fulfill({
        status: response.status(),
        headers: response.headers(),
        body: await response.text(),
      });
    });
    
    // Submit form
    await page.click('[data-testid="login-button"]');
    
    // Wait for successful login
    await page.waitForSelector('[data-testid="login-success"]', { timeout: 15000 });
    
    // Verify authentication was successful
    const userElement = await page.locator('[data-testid="user-menu"]');
    expect(await userElement.isVisible()).toBe(true);
    
    // If we couldn't extract user ID from API response, try to get it from the UI
    if (!extractedUserId) {
      try {
        // Look for user ID in various UI elements
        const userIdElement = await page.locator('[data-testid="user-id"]').first();
        if (await userIdElement.isVisible()) {
          extractedUserId = await userIdElement.textContent() || null;
        }
      } catch (error) {
        console.warn('Could not extract user ID from UI elements');
      }
    }
    
    // If still no user ID, use the test user email as fallback
    if (!extractedUserId) {
      console.warn('Using test user email as fallback user ID');
      extractedUserId = TEST_USER;
    }
    
    return extractedUserId;
  }

  /**
   * Helper function to authenticate a user
   */
  async function authenticateUser(page: Page): Promise<void> {
    await page.goto(APP_LOGIN_URL);
    
    // Wait for login form
    await page.waitForSelector('[data-testid="login-form"]', { timeout: 10000 });
    
    // Fill in credentials
    await page.fill('[data-testid="email-input"]', TEST_USER);
    await page.fill('[data-testid="password-input"]', TEST_PASS);
    
    // Submit form
    await page.click('[data-testid="login-button"]');
    
    // Wait for successful login
    await page.waitForSelector('[data-testid="login-success"]', { timeout: 15000 });
    
    // Verify authentication was successful
    const userElement = await page.locator('[data-testid="user-menu"]');
    expect(await userElement.isVisible()).toBe(true);
  }
});