/**
 * Integration tests for PreferencesService with the model selection system
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { PreferencesService } from '../preferences-service';
import { ModelSelectionPreferences } from '../types';

// Mock the karen-backend module
vi.mock('../../karen-backend', () => ({
  getKarenBackend: vi.fn(() => ({
    makeRequestPublic: vi.fn()
  }))
}));

// Mock the safe-console module
vi.mock('@/lib/safe-console', () => ({
  safeLog: vi.fn(),
  safeError: vi.fn()
}));

import { getKarenBackend } from '../../karen-backend';

describe('PreferencesService Integration', () => {
  let service: PreferencesService;
  let mockBackend: { makeRequestPublic: Mock };

  beforeEach(() => {
    vi.clearAllMocks();
    
    mockBackend = {
      makeRequestPublic: vi.fn()
    };
    (getKarenBackend as Mock).mockReturnValue(mockBackend);
    
    service = new PreferencesService();

  afterEach(async () => {
    if (service) {
      await service.shutdown();
    }

  describe('Real-world Usage Scenarios', () => {
    it('should handle complete user preference workflow', async () => {
      // Test individual operations work correctly
      
      // 1. Test getting initial preferences
      mockBackend.makeRequestPublic.mockResolvedValueOnce({});
      const initialPrefs = await service.getUserPreferences();
      expect(initialPrefs.autoSelectFallback).toBe(true);
      expect(initialPrefs.preferLocal).toBe(false);

      // 2. Test saving preferences
      const updatedPrefs: Partial<ModelSelectionPreferences> = {
        preferredProviders: ['openai', 'anthropic'],
        preferLocal: true
      };

      mockBackend.makeRequestPublic.mockResolvedValueOnce(undefined);
      await service.saveUserPreferences(updatedPrefs);

      // 3. Test validation works
      expect(service.validatePreferences(updatedPrefs)).toBe(true);
      expect(service.validatePreferences({ lastSelectedModel: 123 } as any)).toBe(false);

      // 4. Test updateLastSelectedModel works
      mockBackend.makeRequestPublic
        .mockResolvedValueOnce(initialPrefs) // getUserPreferences in updateLastSelectedModel
        .mockResolvedValueOnce(undefined); // saveUserPreferences

      await expect(service.updateLastSelectedModel('gpt-4')).resolves.not.toThrow();

    it('should handle system configuration integration', async () => {
      // Mock system config
      const systemConfig = { defaultModel: 'system-default-model' };
      mockBackend.makeRequestPublic.mockResolvedValue(systemConfig);

      const config = await service.getDefaultModelConfig();
      expect(config.defaultModel).toBe('system-default-model');

      // Verify caching works
      const cachedConfig = await service.getDefaultModelConfig();
      expect(cachedConfig).toEqual(config);
      expect(mockBackend.makeRequestPublic).toHaveBeenCalledTimes(1);

    it('should handle preference validation in real scenarios', async () => {
      // Test various invalid preference scenarios
      const invalidScenarios = [
        { lastSelectedModel: 123 },
        { preferredProviders: 'not-an-array' },
        { preferLocal: 'yes' },
        { autoSelectFallback: 1 }
      ];

      for (const invalidPrefs of invalidScenarios) {
        await expect(service.saveUserPreferences(invalidPrefs as any))
          .rejects.toThrow();
      }

      // Test valid preferences
      const validPrefs: Partial<ModelSelectionPreferences> = {
        lastSelectedModel: 'valid-model',
        preferredProviders: ['provider1', 'provider2'],
        preferLocal: false,
        autoSelectFallback: true
      };

      mockBackend.makeRequestPublic.mockResolvedValue(undefined);
      await expect(service.saveUserPreferences(validPrefs))
        .resolves.not.toThrow();

    it('should handle error recovery gracefully', async () => {
      // Simulate backend errors
      mockBackend.makeRequestPublic.mockRejectedValue(new Error('Backend down'));

      // Should return defaults instead of throwing
      const preferences = await service.getUserPreferences();
      expect(preferences).toBeDefined();
      expect(preferences.autoSelectFallback).toBe(true);

      const config = await service.getDefaultModelConfig();
      expect(config).toEqual({});

      // Save should throw since it's a critical operation
      await expect(service.saveUserPreferences({ preferLocal: true }))
        .rejects.toThrow();

    it('should handle concurrent operations correctly', async () => {
      const mockPrefs = {
        lastSelectedModel: 'concurrent-model',
        preferLocal: true
      };

      mockBackend.makeRequestPublic.mockResolvedValue(mockPrefs);

      // Make multiple concurrent calls
      const promises = [
        service.getUserPreferences(),
        service.getUserPreferences(),
        service.getUserPreferences()
      ];

      const results = await Promise.all(promises);

      // All should return the same result (merged with defaults)
      const expectedResult = service.mergeWithDefaults(mockPrefs);
      results.forEach(result => {
        expect(result).toEqual(expectedResult);

      // All calls should succeed
      expect(results).toHaveLength(3);
      results.forEach(result => {
        expect(result.lastSelectedModel).toBe('concurrent-model');
        expect(result.preferLocal).toBe(true);


    it('should handle preference merging correctly', async () => {
      // Test partial preferences are merged with defaults
      const partialPrefs = {
        lastSelectedModel: 'test-model'
        // Missing other fields
      };

      const merged = service.mergeWithDefaults(partialPrefs);

      expect(merged).toEqual({
        lastSelectedModel: 'test-model',
        defaultModel: undefined,
        preferredProviders: [],
        preferLocal: false,
        autoSelectFallback: true


    it('should provide useful service statistics', async () => {
      // Load some data
      mockBackend.makeRequestPublic
        .mockResolvedValueOnce({ lastSelectedModel: 'test' })
        .mockResolvedValueOnce({ defaultModel: 'default' });

      await service.getUserPreferences();
      await service.getDefaultModelConfig();

      const stats = service.getPreferencesStats();

      expect(stats.serviceName).toBe('PreferencesService');
      expect(stats.isInitialized).toBe(false); // Not explicitly initialized
      expect(stats.cacheSize).toBeGreaterThan(0);
      expect(stats.hasUserPreferences).toBe(true);
      expect(stats.hasDefaultConfig).toBe(true);
      expect(stats.config).toBeDefined();


  describe('Performance and Caching', () => {
    it('should cache preferences efficiently', async () => {
      // Create fresh service for clean test
      const freshService = new PreferencesService({ cacheTimeout: 30000 });
      vi.clearAllMocks();
      
      mockBackend.makeRequestPublic.mockResolvedValue({
        lastSelectedModel: 'cached-model'

      // First call - should hit backend
      await freshService.getUserPreferences();
      
      // Second call - should use cache
      await freshService.getUserPreferences();

      // Backend should only be called once due to caching
      expect(mockBackend.makeRequestPublic).toHaveBeenCalledTimes(1);
      
      await freshService.shutdown();

    it('should invalidate cache appropriately', async () => {
      // Load initial data
      mockBackend.makeRequestPublic.mockResolvedValueOnce({
        lastSelectedModel: 'initial'

      await service.getUserPreferences();

      // Clear cache
      service.clearCache();

      // Next call should hit backend again
      mockBackend.makeRequestPublic.mockResolvedValueOnce({
        lastSelectedModel: 'after-clear'

      const result = await service.getUserPreferences();
      expect(result.lastSelectedModel).toBe('after-clear');
      expect(mockBackend.makeRequestPublic).toHaveBeenCalledTimes(2);


