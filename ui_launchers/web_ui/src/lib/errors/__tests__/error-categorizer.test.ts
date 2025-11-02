/**
 * Tests for error categorization system
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */

import { ErrorCategorizer } from '../error-categorizer';
import { ErrorCategory, ErrorSeverity } from '../error-categories';

describe('ErrorCategorizer', () => {
  let categorizer: ErrorCategorizer;

  beforeEach(() => {
    categorizer = ErrorCategorizer.getInstance();

  describe('Network Error Categorization', () => {
    it('should categorize connection refused errors', () => {
      const error = new Error('ECONNREFUSED: Connection refused');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.NETWORK);
      expect(result.severity).toBe(ErrorSeverity.HIGH);
      expect(result.retryable).toBe(true);
      expect(result.maxRetries).toBe(3);
      expect(result.backoffStrategy).toBe('exponential');
      expect(result.userMessage).toContain('Unable to connect to server');

    it('should categorize network timeout errors', () => {
      const error = new Error('ETIMEDOUT: Network timeout');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.NETWORK);
      expect(result.retryable).toBe(true);
      expect(result.fallbackAction).toBe('USE_FALLBACK_BACKEND');

    it('should categorize fetch failures', () => {
      const error = new Error('fetch failed: NetworkError');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.NETWORK);
      expect(result.severity).toBe(ErrorSeverity.HIGH);
      expect(result.retryable).toBe(true);


  describe('Authentication Error Categorization', () => {
    it('should categorize unauthorized errors', () => {
      const error = new Error('401 Unauthorized');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.AUTHENTICATION);
      expect(result.severity).toBe(ErrorSeverity.MEDIUM);
      expect(result.retryable).toBe(false);
      expect(result.maxRetries).toBe(0);
      expect(result.userMessage).toContain('Invalid username or password');

    it('should categorize session expired errors', () => {
      const error = new Error('Session expired');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.AUTHENTICATION);
      expect(result.retryable).toBe(true);
      expect(result.maxRetries).toBe(1);
      expect(result.fallbackAction).toBe('REFRESH_SESSION');
      expect(result.userMessage).toContain('session has expired');

    it('should categorize authentication timeout errors', () => {
      const error = new Error('Authentication timeout');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.TIMEOUT);
      expect(result.retryable).toBe(true);
      expect(result.maxRetries).toBe(2);
      expect(result.userMessage).toContain('Request timed out');


  describe('Database Error Categorization', () => {
    it('should categorize database connection errors', () => {
      const error = new Error('Database connection failed');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.DATABASE);
      expect(result.severity).toBe(ErrorSeverity.CRITICAL);
      expect(result.retryable).toBe(true);
      expect(result.maxRetries).toBe(5);
      expect(result.backoffStrategy).toBe('linear');
      expect(result.fallbackAction).toBe('ENABLE_DEGRADED_MODE');

    it('should categorize constraint violation errors', () => {
      const error = new Error('Constraint violation: duplicate key');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.DATABASE);
      expect(result.severity).toBe(ErrorSeverity.MEDIUM);
      expect(result.retryable).toBe(false);
      expect(result.maxRetries).toBe(0);


  describe('Configuration Error Categorization', () => {
    it('should categorize invalid URL errors', () => {
      const error = new Error('Invalid URL provided');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.CONFIGURATION);
      expect(result.severity).toBe(ErrorSeverity.CRITICAL);
      expect(result.retryable).toBe(false);
      expect(result.userMessage).toContain('System configuration error');

    it('should categorize missing environment errors', () => {
      const error = new Error('Missing environment variable');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.CONFIGURATION);
      expect(result.retryable).toBe(false);


  describe('Timeout Error Categorization', () => {
    it('should categorize general timeout errors', () => {
      const error = new Error('Request timed out');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.TIMEOUT);
      expect(result.severity).toBe(ErrorSeverity.HIGH);
      expect(result.retryable).toBe(true);
      expect(result.maxRetries).toBe(3);
      expect(result.backoffStrategy).toBe('exponential');


  describe('Validation Error Categorization', () => {
    it('should categorize validation errors', () => {
      const error = new Error('Validation error: invalid input');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.VALIDATION);
      expect(result.severity).toBe(ErrorSeverity.LOW);
      expect(result.retryable).toBe(false);
      expect(result.userMessage).toContain('Invalid format detected');

    it('should categorize bad request errors', () => {
      const error = new Error('400 Bad Request');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.VALIDATION);
      expect(result.retryable).toBe(false);


  describe('Unknown Error Categorization', () => {
    it('should categorize unknown errors', () => {
      const error = new Error('Some unknown error');
      const result = categorizer.categorizeError(error);

      expect(result.category).toBe(ErrorCategory.UNKNOWN);
      expect(result.severity).toBe(ErrorSeverity.MEDIUM);
      expect(result.retryable).toBe(false);
      expect(result.userMessage).toContain('unexpected error occurred');


  describe('Error Code Generation', () => {
    it('should generate unique error codes', () => {
      const error1 = new Error('Test error 1');
      const error2 = new Error('Test error 2');
      
      const result1 = categorizer.categorizeError(error1);
      const result2 = categorizer.categorizeError(error2);

      expect(result1.code).toBeDefined();
      expect(result2.code).toBeDefined();
      expect(result1.code).not.toBe(result2.code);
      expect(result1.code).toMatch(/^[A-Z_0-9]+$/);


  describe('Correlation ID Generation', () => {
    it('should generate unique correlation IDs', () => {
      const error1 = new Error('Test error 1');
      const error2 = new Error('Test error 2');
      
      const result1 = categorizer.categorizeError(error1);
      const result2 = categorizer.categorizeError(error2);

      expect(result1.correlationId).toBeDefined();
      expect(result2.correlationId).toBeDefined();
      expect(result1.correlationId).not.toBe(result2.correlationId);
      expect(result1.correlationId).toMatch(/^corr_[a-z0-9_]+$/);


  describe('Context Handling', () => {
    it('should include context in categorized error', () => {
      const error = new Error('Test error');
      const context = { userId: '123', action: 'login' };
      
      const result = categorizer.categorizeError(error, context);

      expect(result.context).toMatchObject(context);
      expect(result.context?.originalError).toBe('Error');

    it('should handle string errors', () => {
      const error = 'String error message';
      const result = categorizer.categorizeError(error);

      expect(result.message).toBe(error);
      expect(result.context?.originalError).toBe('StringError');


  describe('Retry Logic', () => {
    it('should determine if error should be retried', () => {
      const retryableError = new Error('ECONNREFUSED');
      const nonRetryableError = new Error('401 Unauthorized');
      
      const retryableResult = categorizer.categorizeError(retryableError);
      const nonRetryableResult = categorizer.categorizeError(nonRetryableError);

      expect(categorizer.shouldRetry(retryableResult, 0)).toBe(true);
      expect(categorizer.shouldRetry(retryableResult, 3)).toBe(false); // Max retries reached
      expect(categorizer.shouldRetry(nonRetryableResult, 0)).toBe(false);


  describe('Retry Delay Calculation', () => {
    it('should calculate exponential backoff delay', () => {
      const error = new Error('ECONNREFUSED');
      const result = categorizer.categorizeError(error);
      
      const delay1 = categorizer.calculateRetryDelay(result, 0, 1000);
      const delay2 = categorizer.calculateRetryDelay(result, 1, 1000);
      const delay3 = categorizer.calculateRetryDelay(result, 2, 1000);

      expect(delay1).toBe(1000);
      expect(delay2).toBe(2000);
      expect(delay3).toBe(4000);

    it('should calculate linear backoff delay', () => {
      const error = new Error('Database connection failed');
      const result = categorizer.categorizeError(error);
      
      const delay1 = categorizer.calculateRetryDelay(result, 0, 1000);
      const delay2 = categorizer.calculateRetryDelay(result, 1, 1000);
      const delay3 = categorizer.calculateRetryDelay(result, 2, 1000);

      expect(delay1).toBe(1000);
      expect(delay2).toBe(2000);
      expect(delay3).toBe(3000);

    it('should calculate fixed delay', () => {
      const error = new Error('401 Unauthorized');
      const result = categorizer.categorizeError(error);
      
      const delay1 = categorizer.calculateRetryDelay(result, 0, 1000);
      const delay2 = categorizer.calculateRetryDelay(result, 1, 1000);

      expect(delay1).toBe(1000);
      expect(delay2).toBe(1000);

    it('should cap maximum delay', () => {
      const error = new Error('ECONNREFUSED');
      const result = categorizer.categorizeError(error);
      
      const delay = categorizer.calculateRetryDelay(result, 10, 1000);
      expect(delay).toBeLessThanOrEqual(30000); // Max 30 seconds for exponential


  describe('Severity Assessment', () => {
    it('should get correct severity levels', () => {
      expect(categorizer.getSeverityLevel(ErrorSeverity.LOW)).toBe(1);
      expect(categorizer.getSeverityLevel(ErrorSeverity.MEDIUM)).toBe(2);
      expect(categorizer.getSeverityLevel(ErrorSeverity.HIGH)).toBe(3);
      expect(categorizer.getSeverityLevel(ErrorSeverity.CRITICAL)).toBe(4);

    it('should identify errors requiring immediate attention', () => {
      const criticalError = new Error('Database connection failed');
      const configError = new Error('Invalid URL provided');
      const lowError = new Error('Validation error');
      
      const criticalResult = categorizer.categorizeError(criticalError);
      const configResult = categorizer.categorizeError(configError);
      const lowResult = categorizer.categorizeError(lowError);

      expect(categorizer.requiresImmediateAttention(criticalResult)).toBe(true);
      expect(categorizer.requiresImmediateAttention(configResult)).toBe(true);
      expect(categorizer.requiresImmediateAttention(lowResult)).toBe(false);


