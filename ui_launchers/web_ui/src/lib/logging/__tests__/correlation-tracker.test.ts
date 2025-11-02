/**
 * Tests for correlation tracking functionality
 */

import { correlationTracker } from '../correlation-tracker';

// Mock sessionStorage for testing
const mockSessionStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};

Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage

describe('CorrelationTracker', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Clear any existing correlation IDs
    correlationTracker.clearCorrelationId();

  describe('generateCorrelationId', () => {
    it('should generate unique correlation IDs', () => {
      const id1 = correlationTracker.generateCorrelationId();
      const id2 = correlationTracker.generateCorrelationId();
      
      expect(id1).toMatch(/^corr_[a-f0-9-]+$/);
      expect(id2).toMatch(/^corr_[a-f0-9-]+$/);
      expect(id1).not.toBe(id2);


  describe('setCorrelationId and getCurrentCorrelationId', () => {
    it('should set and retrieve correlation ID', () => {
      const testId = 'test-correlation-id';
      
      correlationTracker.setCorrelationId(testId);
      const retrieved = correlationTracker.getCurrentCorrelationId();
      
      expect(retrieved).toBe(testId);
      expect(mockSessionStorage.setItem).toHaveBeenCalledWith('currentCorrelationId', testId);

    it('should generate new ID if none exists', () => {
      mockSessionStorage.getItem.mockReturnValue(null);
      
      const id = correlationTracker.getCurrentCorrelationId();
      
      expect(id).toMatch(/^corr_[a-f0-9-]+$/);
      expect(mockSessionStorage.setItem).toHaveBeenCalledWith('currentCorrelationId', id);

    it('should retrieve from session storage if available', () => {
      const storedId = 'stored-correlation-id';
      mockSessionStorage.getItem.mockReturnValue(storedId);
      
      const id = correlationTracker.getCurrentCorrelationId();
      
      expect(id).toBe(storedId);


  describe('clearCorrelationId', () => {
    it('should clear correlation ID and remove from session storage', () => {
      correlationTracker.setCorrelationId('test-id');
      correlationTracker.clearCorrelationId();
      
      mockSessionStorage.getItem.mockReturnValue(null);
      const newId = correlationTracker.getCurrentCorrelationId();
      
      expect(newId).toMatch(/^corr_[a-f0-9-]+$/);
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('currentCorrelationId');


  describe('associateRequest and getCorrelationForRequest', () => {
    it('should associate request with correlation ID', () => {
      const requestId = 'test-request-id';
      const correlationId = 'test-correlation-id';
      
      correlationTracker.associateRequest(requestId, correlationId);
      const retrieved = correlationTracker.getCorrelationForRequest(requestId);
      
      expect(retrieved).toBe(correlationId);

    it('should use current correlation ID if none provided', () => {
      const requestId = 'test-request-id';
      correlationTracker.setCorrelationId('current-id');
      
      correlationTracker.associateRequest(requestId);
      const retrieved = correlationTracker.getCorrelationForRequest(requestId);
      
      expect(retrieved).toBe('current-id');


  describe('withCorrelation', () => {
    it('should execute function with correlation context', () => {
      const testId = 'test-correlation-id';
      const mockFn = jest.fn(() => 'result');
      
      const result = correlationTracker.withCorrelation(testId, mockFn);
      
      expect(result).toBe('result');
      expect(mockFn).toHaveBeenCalled();

    it('should clean up correlation ID after execution', () => {
      const testId = 'test-correlation-id';
      const originalId = correlationTracker.getCurrentCorrelationId();
      
      correlationTracker.withCorrelation(testId, () => {
        expect(correlationTracker.getCurrentCorrelationId()).toBe(testId);

      // Should restore original context
      expect(correlationTracker.getCurrentCorrelationId()).toBe(originalId);


  describe('withCorrelationAsync', () => {
    it('should execute async function with correlation context', async () => {
      const testId = 'test-correlation-id';
      const mockFn = jest.fn(async () => 'async-result');
      
      const result = await correlationTracker.withCorrelationAsync(testId, mockFn);
      
      expect(result).toBe('async-result');
      expect(mockFn).toHaveBeenCalled();

    it('should clean up correlation ID after async execution', async () => {
      const testId = 'test-correlation-id';
      const originalId = correlationTracker.getCurrentCorrelationId();
      
      await correlationTracker.withCorrelationAsync(testId, async () => {
        expect(correlationTracker.getCurrentCorrelationId()).toBe(testId);

      // Should restore original context
      expect(correlationTracker.getCurrentCorrelationId()).toBe(originalId);

    it('should clean up even if async function throws', async () => {
      const testId = 'test-correlation-id';
      const originalId = correlationTracker.getCurrentCorrelationId();
      
      try {
        await correlationTracker.withCorrelationAsync(testId, async () => {
          throw new Error('Test error');

      } catch (error) {
        // Expected
      }
      
      // Should restore original context even after error
      expect(correlationTracker.getCurrentCorrelationId()).toBe(originalId);


  describe('cleanup', () => {
    it('should limit the number of stored associations', () => {
      // Add many associations
      for (let i = 0; i < 1500; i++) {
        correlationTracker.associateRequest(`request-${i}`, `correlation-${i}`);
      }
      
      correlationTracker.cleanup();
      
      // Should keep only recent ones
      expect(correlationTracker.getCorrelationForRequest('request-0')).toBeUndefined();
      expect(correlationTracker.getCorrelationForRequest('request-1400')).toBeDefined();


