/**
 * Tests for Error Recovery Manager
 * 
 * Comprehensive test suite for error recovery strategies,
 * automatic retry logic, and intelligent recovery mechanisms.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ErrorRecoveryManager, RecoveryConfig } from '../../lib/error-handling/error-recovery-manager';

describe('ErrorRecoveryManager', () => {
  let recoveryManager: ErrorRecoveryManager;
  let mockConfig: RecoveryConfig;

  beforeEach(() => {
    mockConfig = {
      maxAttempts: 3,
      retryDelay: 1000,
      exponentialBackoff: true,
      section: 'test-section',
      enableSmartRecovery: true
    };

    recoveryManager = new ErrorRecoveryManager(mockConfig);

  describe('Initialization', () => {
    it('should initialize with provided config', () => {
      expect(recoveryManager).toBeInstanceOf(ErrorRecoveryManager);

    it('should use default values for optional config', () => {
      const minimalConfig: RecoveryConfig = {
        maxAttempts: 2,
        retryDelay: 500,
        exponentialBackoff: false,
        section: 'minimal'
      };

      const manager = new ErrorRecoveryManager(minimalConfig);
      expect(manager).toBeInstanceOf(ErrorRecoveryManager);


  describe('Error Pattern Recognition', () => {
    it('should recognize network errors', async () => {
      const networkError = new Error('Network request failed');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await recoveryManager.getRecoveryStrategy(networkError, errorInfo, 1);

      expect(strategy.type).toBe('retry');
      expect(strategy.confidence).toBeGreaterThan(0.7);
      expect(strategy.description).toContain('Network connectivity');

    it('should recognize chunk loading errors', async () => {
      const chunkError = new Error('Loading chunk 123 failed');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await recoveryManager.getRecoveryStrategy(chunkError, errorInfo, 1);

      expect(strategy.type).toBe('reload');
      expect(strategy.confidence).toBeGreaterThan(0.8);
      expect(strategy.description).toContain('Application update');

    it('should recognize authentication errors', async () => {
      const authError = new Error('Authentication failed - token expired');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await recoveryManager.getRecoveryStrategy(authError, errorInfo, 1);

      expect(strategy.type).toBe('redirect');
      expect(strategy.confidence).toBeGreaterThan(0.9);
      expect(strategy.description).toContain('Authentication issue');

    it('should recognize memory/performance errors', async () => {
      const memoryError = new Error('Maximum call stack size exceeded');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await recoveryManager.getRecoveryStrategy(memoryError, errorInfo, 1);

      expect(strategy.type).toBe('degraded');
      expect(strategy.confidence).toBeGreaterThan(0.6);
      expect(strategy.description).toContain('Performance issue');

    it('should recognize component rendering errors', async () => {
      const renderError = new Error('Cannot read property of undefined');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await recoveryManager.getRecoveryStrategy(renderError, errorInfo, 1);

      expect(strategy.type).toBe('fallback');
      expect(strategy.confidence).toBeGreaterThan(0.5);
      expect(strategy.description).toContain('Component error');


  describe('Recovery Strategy Adaptation', () => {
    it('should apply exponential backoff when enabled', async () => {
      const error = new Error('Network timeout');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy1 = await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);
      const strategy2 = await recoveryManager.getRecoveryStrategy(error, errorInfo, 2);
      const strategy3 = await recoveryManager.getRecoveryStrategy(error, errorInfo, 3);

      expect(strategy2.delay).toBeGreaterThan(strategy1.delay);
      expect(strategy3.delay).toBeGreaterThan(strategy2.delay);

    it('should reduce confidence with each attempt', async () => {
      const error = new Error('Test error');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy1 = await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);
      const strategy2 = await recoveryManager.getRecoveryStrategy(error, errorInfo, 2);
      const strategy3 = await recoveryManager.getRecoveryStrategy(error, errorInfo, 3);

      expect(strategy2.confidence).toBeLessThan(strategy1.confidence);
      expect(strategy3.confidence).toBeLessThan(strategy2.confidence);

    it('should add more aggressive actions for repeated failures', async () => {
      const error = new Error('Persistent error');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy1 = await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);
      const strategy3 = await recoveryManager.getRecoveryStrategy(error, errorInfo, 3);

      expect(strategy3.actions.length).toBeGreaterThan(strategy1.actions.length);
      expect(strategy3.type).toBe('degraded');

    it('should switch to fallback mode after max attempts', async () => {
      const error = new Error('Unrecoverable error');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await recoveryManager.getRecoveryStrategy(error, errorInfo, 4);

      expect(strategy.type).toBe('fallback');
      expect(strategy.confidence).toBeLessThan(0.2);
      expect(strategy.description).toContain('Maximum recovery attempts');


  describe('Custom Fallback Strategies', () => {
    it('should use custom strategies when provided', async () => {
      const customConfig: RecoveryConfig = {
        ...mockConfig,
        fallbackStrategies: [
          {
            errorPattern: /custom.*error/i,
            strategy: {
              type: 'cache',
              delay: 500,
              confidence: 0.95,
              description: 'Custom recovery strategy',
              actions: [{ type: 'clear_cache' }]
            },
            priority: 1
          }
        ]
      };

      const customManager = new ErrorRecoveryManager(customConfig);
      const error = new Error('Custom error occurred');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await customManager.getRecoveryStrategy(error, errorInfo, 1);

      expect(strategy.type).toBe('cache');
      expect(strategy.description).toBe('Custom recovery strategy');
      expect(strategy.confidence).toBe(0.95);

    it('should prioritize custom strategies over pattern-based ones', async () => {
      const customConfig: RecoveryConfig = {
        ...mockConfig,
        fallbackStrategies: [
          {
            errorPattern: /network/i,
            strategy: {
              type: 'cache',
              delay: 100,
              confidence: 1.0,
              description: 'Custom network strategy',
              actions: []
            },
            priority: 1
          }
        ]
      };

      const customManager = new ErrorRecoveryManager(customConfig);
      const error = new Error('Network error');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await customManager.getRecoveryStrategy(error, errorInfo, 1);

      expect(strategy.description).toBe('Custom network strategy');
      expect(strategy.type).toBe('cache');


  describe('Smart Recovery', () => {
    it('should learn from successful recoveries', async () => {
      const error = new Error('Learning test error');
      const errorInfo = { componentStack: 'TestComponent' };

      // First attempt
      await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);
      
      // Mark as successful
      recoveryManager.markRecoverySuccess(error, errorInfo);

      // Second attempt should use learned strategy
      const strategy = await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);

      expect(strategy.description).toContain('learned recovery pattern');

    it('should try alternative approaches when previous attempts failed', async () => {
      const error = new Error('Failing test error');
      const errorInfo = { componentStack: 'TestComponent' };

      // Multiple failed attempts
      await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);
      await recoveryManager.getRecoveryStrategy(error, errorInfo, 2);
      await recoveryManager.getRecoveryStrategy(error, errorInfo, 3);

      // Next attempt should try alternative approach
      const strategy = await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);

      expect(strategy.description).toContain('alternative approach');
      expect(strategy.confidence).toBeLessThan(0.5);

    it('should disable smart recovery when configured', async () => {
      const configWithoutSmart: RecoveryConfig = {
        ...mockConfig,
        enableSmartRecovery: false
      };

      const manager = new ErrorRecoveryManager(configWithoutSmart);
      const error = new Error('No smart recovery');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await manager.getRecoveryStrategy(error, errorInfo, 1);

      expect(strategy.description).not.toContain('learned');
      expect(strategy.description).not.toContain('alternative approach');


  describe('Recovery History and Statistics', () => {
    it('should track recovery attempts', async () => {
      const error = new Error('Tracked error');
      const errorInfo = { componentStack: 'TestComponent' };

      await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);
      await recoveryManager.getRecoveryStrategy(error, errorInfo, 2);

      const stats = recoveryManager.getRecoveryStats();

      expect(stats.totalAttempts).toBe(2);
      expect(stats.section).toBe('test-section');

    it('should calculate success rates correctly', async () => {
      const error1 = new Error('Success error');
      const error2 = new Error('Failure error');
      const errorInfo = { componentStack: 'TestComponent' };

      // Successful recovery
      await recoveryManager.getRecoveryStrategy(error1, errorInfo, 1);
      recoveryManager.markRecoverySuccess(error1, errorInfo);

      // Failed recovery
      await recoveryManager.getRecoveryStrategy(error2, errorInfo, 1);

      const stats = recoveryManager.getRecoveryStats();

      expect(stats.totalAttempts).toBe(2);
      expect(stats.successfulAttempts).toBe(1);
      expect(stats.successRate).toBe(0.5);

    it('should categorize errors by type', async () => {
      const networkError = new Error('Network failed');
      const renderError = new Error('Cannot read property');
      const errorInfo = { componentStack: 'TestComponent' };

      await recoveryManager.getRecoveryStrategy(networkError, errorInfo, 1);
      await recoveryManager.getRecoveryStrategy(renderError, errorInfo, 1);

      const stats = recoveryManager.getRecoveryStats();

      expect(stats.errorTypes).toHaveProperty('network');
      expect(stats.errorTypes).toHaveProperty('cannot');

    it('should clear history when requested', async () => {
      const error = new Error('Clear test error');
      const errorInfo = { componentStack: 'TestComponent' };

      await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);

      let stats = recoveryManager.getRecoveryStats();
      expect(stats.totalAttempts).toBe(1);

      recoveryManager.clearHistory();

      stats = recoveryManager.getRecoveryStats();
      expect(stats.totalAttempts).toBe(0);


  describe('Recovery Actions', () => {
    it('should include appropriate actions for network errors', async () => {
      const error = new Error('Network connection failed');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);

      const actionTypes = strategy.actions.map(action => action.type);
      expect(actionTypes).toContain('clear_cache');
      expect(actionTypes).toContain('notify_user');

    it('should include fallback UI actions for rendering errors', async () => {
      const error = new Error('Cannot read property of undefined');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);

      const actionTypes = strategy.actions.map(action => action.type);
      expect(actionTypes).toContain('reset_state');
      expect(actionTypes).toContain('fallback_ui');

    it('should include auth-specific actions for authentication errors', async () => {
      const error = new Error('401 Unauthorized');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);

      const actionTypes = strategy.actions.map(action => action.type);
      expect(actionTypes).toContain('clear_cache');
      expect(actionTypes).toContain('notify_user');

      const clearCacheAction = strategy.actions.find(action => action.type === 'clear_cache');
      expect(clearCacheAction?.params?.type).toBe('auth');


  describe('Edge Cases', () => {
    it('should handle errors with no message', async () => {
      const error = new Error('');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);

      expect(strategy).toBeDefined();
      expect(strategy.type).toBeDefined();

    it('should handle errors with no stack trace', async () => {
      const error = new Error('No stack error');
      error.stack = undefined;
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await recoveryManager.getRecoveryStrategy(error, errorInfo, 1);

      expect(strategy).toBeDefined();
      expect(strategy.type).toBeDefined();

    it('should handle very high attempt counts', async () => {
      const error = new Error('High attempt error');
      const errorInfo = { componentStack: 'TestComponent' };

      const strategy = await recoveryManager.getRecoveryStrategy(error, errorInfo, 100);

      expect(strategy.type).toBe('fallback');
      expect(strategy.confidence).toBeLessThan(0.2);

    it('should handle concurrent recovery attempts', async () => {
      const error = new Error('Concurrent error');
      const errorInfo = { componentStack: 'TestComponent' };

      const promises = [
        recoveryManager.getRecoveryStrategy(error, errorInfo, 1),
        recoveryManager.getRecoveryStrategy(error, errorInfo, 1),
        recoveryManager.getRecoveryStrategy(error, errorInfo, 1)
      ];

      const strategies = await Promise.all(promises);

      strategies.forEach(strategy => {
        expect(strategy).toBeDefined();
        expect(strategy.type).toBeDefined();



  describe('Configuration Validation', () => {
    it('should handle invalid max attempts', () => {
      const invalidConfig: RecoveryConfig = {
        maxAttempts: -1,
        retryDelay: 1000,
        exponentialBackoff: true,
        section: 'test'
      };

      expect(() => new ErrorRecoveryManager(invalidConfig)).not.toThrow();

    it('should handle invalid retry delay', () => {
      const invalidConfig: RecoveryConfig = {
        maxAttempts: 3,
        retryDelay: -1000,
        exponentialBackoff: true,
        section: 'test'
      };

      expect(() => new ErrorRecoveryManager(invalidConfig)).not.toThrow();

    it('should handle missing section', () => {
      const invalidConfig: RecoveryConfig = {
        maxAttempts: 3,
        retryDelay: 1000,
        exponentialBackoff: true,
        section: ''
      };

      expect(() => new ErrorRecoveryManager(invalidConfig)).not.toThrow();


