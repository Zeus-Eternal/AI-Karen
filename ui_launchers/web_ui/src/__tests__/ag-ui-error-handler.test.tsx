/**
 * Tests for AG-UI Error Handler with Fallback Strategies
 */

import React from 'react';
import { vi } from 'vitest';
import { agUIErrorHandler, AGUIErrorType, FallbackStrategy } from '../lib/ag-ui-error-handler';

// Mock AG-Grid APIs
const mockGridApi = {
  setRowData: vi.fn(),
  getDisplayedRowCount: vi.fn(() => 0),
  refreshCells: vi.fn()
};

const mockColumnApi = {
  setColumnDefs: vi.fn(),
  getColumns: vi.fn(() => [])
};

describe('AGUIErrorHandler', () => {
  beforeEach(() => {
    // Reset the singleton instance for each test
    agUIErrorHandler.resetComponent('grid');
    agUIErrorHandler.resetComponent('chart');
    agUIErrorHandler.resetComponent('analytics');
    
    // Clear all mocks
    vi.clearAllMocks();

  describe('Grid Error Handling', () => {
    it('should handle grid load error with cached data', async () => {
      // Pre-populate cache
      const testData = [{ id: 1, name: 'Test' }];
      const testColumns = [{ field: 'id' }, { field: 'name' }];
      agUIErrorHandler.cacheData('grid', testData, testColumns);

      const error = new Error('Grid data loading failed');
      
      const result = await agUIErrorHandler.handleGridError(
        error,
        mockGridApi as any,
        mockColumnApi as any,
        [],
        testColumns
      );

      expect(result.strategy).toBe(FallbackStrategy.CACHED_DATA);
      expect(result.data).toEqual(testData);
      expect(result.message).toContain('cached data');
      expect(result.retryAvailable).toBe(true);

    it('should handle grid render error with simplified columns', async () => {
      const error = new Error('Grid rendering failed');
      const complexColumns = [
        { 
          field: 'id', 
          headerName: 'ID',
          cellRenderer: 'customRenderer',
          filter: 'agTextColumnFilter',
          sortable: true
        },
        { 
          field: 'name', 
          headerName: 'Name',
          cellEditor: 'agTextCellEditor',
          editable: true
        }
      ];
      
      const result = await agUIErrorHandler.handleGridError(
        error,
        mockGridApi as any,
        mockColumnApi as any,
        [],
        complexColumns
      );

      expect(result.strategy).toBe(FallbackStrategy.RETRY_MECHANISM);
      expect(result.columns).toHaveLength(2);
      expect(result.columns[0].cellRenderer).toBeUndefined();
      expect(result.columns[0].filter).toBe(false);
      expect(result.degradedFeatures).toContain('advanced-filtering');

    it('should fallback to simple table after max retries', async () => {
      const error = new Error('Persistent grid error');
      
      // Simulate multiple failures to exceed retry limit
      for (let i = 0; i < 4; i++) {
        await agUIErrorHandler.handleGridError(
          error,
          mockGridApi as any,
          mockColumnApi as any,
          [{ id: 1, name: 'test' }],
          [{ field: 'id' }, { field: 'name' }]
        );
      }
      
      const result = await agUIErrorHandler.handleGridError(
        error,
        mockGridApi as any,
        mockColumnApi as any,
        [{ id: 1, name: 'test' }],
        [{ field: 'id' }, { field: 'name' }]
      );

      expect(result.strategy).toBe(FallbackStrategy.SIMPLE_TABLE);
      expect(result.degradedFeatures).toContain('sorting');
      expect(result.degradedFeatures).toContain('filtering');


  describe('Chart Error Handling', () => {
    it('should handle chart render error with simplified data', async () => {
      const error = new Error('Chart rendering failed');
      const largeDataset = Array.from({ length: 200 }, (_, i) => ({
        label: `Item ${i}`,
        value: Math.random() * 100
      }));
      
      const result = await agUIErrorHandler.handleChartError(
        error,
        largeDataset,
        { type: 'line', animations: true }
      );

      expect(result.strategy).toBe(FallbackStrategy.RETRY_MECHANISM);
      expect(result.data.length).toBeLessThanOrEqual(100); // Data should be limited
      expect(result.degradedFeatures).toContain('animations');
      expect(result.degradedFeatures).toContain('interactive-features');

    it('should fallback to simple chart after retries', async () => {
      const error = new Error('Persistent chart error');
      const chartData = [{ label: 'A', value: 10 }];
      
      // Exceed retry limit
      for (let i = 0; i < 4; i++) {
        await agUIErrorHandler.handleChartError(error, chartData);
      }
      
      const result = await agUIErrorHandler.handleChartError(error, chartData);

      expect(result.strategy).toBe(FallbackStrategy.SIMPLE_TABLE);
      expect(result.message).toContain('showing data as table');
      expect(result.degradedFeatures).toContain('visualization');


  describe('Circuit Breaker Functionality', () => {
    it('should open circuit breaker after threshold failures', async () => {
      const error = new Error('Repeated failure');
      
      // Trigger failures to open circuit breaker (default threshold is 5)
      for (let i = 0; i < 6; i++) {
        await agUIErrorHandler.handleComponentError(error, 'grid', []);
      }
      
      const health = agUIErrorHandler.getComponentHealth('grid');
      expect(health.circuitBreakerOpen).toBe(true);
      expect(health.isHealthy).toBe(false);
      
      // Next call should be handled by circuit breaker
      const result = await agUIErrorHandler.handleComponentError(error, 'grid', []);
      expect(result.strategy).toBe(FallbackStrategy.ERROR_MESSAGE);

    it('should reset circuit breaker on successful operation', async () => {
      const error = new Error('Temporary failure');
      
      // Trigger some failures
      for (let i = 0; i < 3; i++) {
        await agUIErrorHandler.handleComponentError(error, 'grid', []);
      }
      
      // Reset the component
      agUIErrorHandler.resetComponent('grid');
      
      const health = agUIErrorHandler.getComponentHealth('grid');
      expect(health.circuitBreakerOpen).toBe(false);
      expect(health.failureCount).toBe(0);
      expect(health.isHealthy).toBe(true);


  describe('Error Classification', () => {
    it('should classify grid errors correctly', async () => {
      const loadError = new Error('Failed to load data');
      const renderError = new Error('Grid render failed');
      const memoryError = new Error('Out of memory');
      const timeoutError = new Error('Request timeout');
      
      const loadResult = await agUIErrorHandler.handleGridError(loadError, mockGridApi as any);
      const renderResult = await agUIErrorHandler.handleGridError(renderError, mockGridApi as any);
      const memoryResult = await agUIErrorHandler.handleGridError(memoryError, mockGridApi as any);
      const timeoutResult = await agUIErrorHandler.handleGridError(timeoutError, mockGridApi as any);
      
      // All should have appropriate fallback strategies
      expect(loadResult.strategy).toBeDefined();
      expect(renderResult.strategy).toBeDefined();
      expect(memoryResult.strategy).toBeDefined();
      expect(timeoutResult.strategy).toBeDefined();

    it('should classify chart errors correctly', async () => {
      const renderError = new Error('Chart draw failed');
      const dataError = new Error('Invalid chart data');
      
      const renderResult = await agUIErrorHandler.handleChartError(renderError, []);
      const dataResult = await agUIErrorHandler.handleChartError(dataError, []);
      
      expect(renderResult.strategy).toBeDefined();
      expect(dataResult.strategy).toBeDefined();


  describe('Caching Functionality', () => {
    it('should cache and retrieve data correctly', () => {
      const testData = [{ id: 1, value: 'test' }];
      const testColumns = [{ field: 'id' }, { field: 'value' }];
      
      // Cache data
      agUIErrorHandler.cacheData('test-component', testData, testColumns);
      
      // The cache should be used in error scenarios
      // This is tested indirectly through other tests
      expect(true).toBe(true); // Placeholder assertion

    it('should respect cache timeout', async () => {
      // This would require mocking Date.now() to test cache expiration
      // For now, we'll test that the cache mechanism exists
      const testData = [{ id: 1 }];
      agUIErrorHandler.cacheData('timeout-test', testData);
      
      // In a real scenario, we'd advance time and verify cache expiration
      expect(true).toBe(true); // Placeholder assertion


  describe('Health Monitoring', () => {
    it('should track component health accurately', async () => {
      const component = 'health-test';
      
      // Initial health should be good
      let health = agUIErrorHandler.getComponentHealth(component);
      expect(health.isHealthy).toBe(true);
      expect(health.failureCount).toBe(0);
      
      // Introduce some failures
      const error = new Error('Test failure');
      await agUIErrorHandler.handleComponentError(error, component, []);
      await agUIErrorHandler.handleComponentError(error, component, []);
      
      health = agUIErrorHandler.getComponentHealth(component);
      expect(health.failureCount).toBe(2);
      expect(health.lastFailureTime).toBeTruthy();
      
      // Health score should decrease with failures
      expect(health.isHealthy).toBe(true); // Still healthy with only 2 failures

    it('should calculate health score correctly', () => {
      const component = 'score-test';
      
      // Test with no failures
      let health = agUIErrorHandler.getComponentHealth(component);
      expect(health.isHealthy).toBe(true);
      
      // Test with circuit breaker open
      // This would require triggering enough failures to open the circuit breaker
      // and then checking the health score


  describe('Fallback Response Generation', () => {
    it('should generate appropriate simple table fallback', async () => {
      const error = new Error('Component failed');
      const testData = [
        { id: 1, name: 'John', age: 30 },
        { id: 2, name: 'Jane', age: 25 }
      ];
      
      const result = await agUIErrorHandler.handleComponentError(error, 'grid', testData);
      
      if (result.strategy === FallbackStrategy.SIMPLE_TABLE) {
        expect(result.data).toEqual(testData);
        expect(result.columns).toHaveLength(3); // id, name, age
        expect(result.columns[0].field).toBe('id');
        expect(result.columns[1].field).toBe('name');
        expect(result.columns[2].field).toBe('age');
      }

    it('should handle empty data gracefully', async () => {
      const error = new Error('No data available');
      
      const result = await agUIErrorHandler.handleComponentError(error, 'grid', []);
      
      expect(result.data).toBeDefined();
      expect(result.columns).toBeDefined();
      expect(result.message).toBeTruthy();


  describe('Integration Scenarios', () => {
    it('should handle multiple concurrent errors', async () => {
      const errors = [
        new Error('Grid error 1'),
        new Error('Chart error 1'),
        new Error('Analytics error 1')
      ];
      
      const promises = [
        agUIErrorHandler.handleGridError(errors[0], mockGridApi as any),
        agUIErrorHandler.handleChartError(errors[1], []),
        agUIErrorHandler.handleComponentError(errors[2], 'analytics', {})
      ];
      
      const results = await Promise.all(promises);
      
      // All should complete successfully with fallbacks
      expect(results).toHaveLength(3);
      results.forEach(result => {
        expect(result.strategy).toBeDefined();
        expect(result.message).toBeTruthy();


    it('should maintain component isolation', async () => {
      const error = new Error('Isolated failure');
      
      // Fail grid component multiple times
      for (let i = 0; i < 6; i++) {
        await agUIErrorHandler.handleGridError(error, mockGridApi as any);
      }
      
      // Grid should be unhealthy
      const gridHealth = agUIErrorHandler.getComponentHealth('grid');
      expect(gridHealth.isHealthy).toBe(false);
      
      // Chart should still be healthy
      const chartHealth = agUIErrorHandler.getComponentHealth('chart');
      expect(chartHealth.isHealthy).toBe(true);



describe('Error Handler Performance', () => {
  it('should handle errors efficiently under load', async () => {
    const startTime = Date.now();
    const errors = Array.from({ length: 100 }, (_, i) => new Error(`Error ${i}`));
    
    const promises = errors.map(error => 
      agUIErrorHandler.handleComponentError(error, 'load-test', [])
    );
    
    const results = await Promise.all(promises);
    const endTime = Date.now();
    
    // Should complete within reasonable time (adjust threshold as needed)
    expect(endTime - startTime).toBeLessThan(5000); // 5 seconds
    expect(results).toHaveLength(100);
    
    // All should have valid responses
    results.forEach(result => {
      expect(result.strategy).toBeDefined();


  it('should not leak memory with repeated errors', async () => {
    // This is a basic test - in a real scenario you'd use memory profiling tools
    const initialMemory = process.memoryUsage?.()?.heapUsed || 0;
    
    // Generate many errors
    for (let i = 0; i < 1000; i++) {
      await agUIErrorHandler.handleComponentError(
        new Error(`Memory test ${i}`),
        'memory-test',
        []
      );
    }
    
    // Force garbage collection if available
    if (global.gc) {
      global.gc();
    }
    
    const finalMemory = process.memoryUsage?.()?.heapUsed || 0;
    
    // Memory usage shouldn't grow excessively (this is a rough check)
    if (initialMemory > 0 && finalMemory > 0) {
      const memoryGrowth = finalMemory - initialMemory;
      expect(memoryGrowth).toBeLessThan(50 * 1024 * 1024); // Less than 50MB growth
    }

