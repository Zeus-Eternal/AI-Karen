import { vi } from 'vitest';
import {
  validateFeatureFlagConfig,
  mergeWithEnvironmentDefaults,
  loadConfigFromEnvironment,
  saveConfigToStorage,
  loadConfigFromStorage,
  createConfigUpdater,
  SECURITY_CRITICAL_FLAGS,
  PERFORMANCE_CRITICAL_FLAGS
} from '../featureFlagConfig';
import { FeatureFlag } from '@/hooks/use-feature';

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

// Mock console methods
const consoleSpy = {
  error: vi.spyOn(console, 'error').mockImplementation(() => {}),
  warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
};

describe('featureFlagConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    consoleSpy.error.mockClear();
    consoleSpy.warn.mockClear();
  });

  afterAll(() => {
    consoleSpy.error.mockRestore();
    consoleSpy.warn.mockRestore();
  });

  describe('validateFeatureFlagConfig', () => {
    it('should validate security-critical flags', () => {
      const config = { 'security.sanitization': false };
      const result = validateFeatureFlagConfig(config);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain("Security-critical flag 'security.sanitization' cannot be disabled");
    });

    it('should warn about performance implications in production', () => {
      const config = { 'analytics.detailed': true };
      const result = validateFeatureFlagConfig(config, 'production');

      expect(result.isValid).toBe(true);
      expect(result.warnings).toContain('Detailed analytics may impact performance in production');
    });

    it('should warn about debug mode in production', () => {
      const config = { 'debug.mode': true };
      const result = validateFeatureFlagConfig(config, 'production');

      expect(result.isValid).toBe(true);
      expect(result.warnings).toContain('Debug mode should not be enabled in production');
    });

    it('should warn about privacy implications for voice features', () => {
      const config = { 'voice.input': true };
      const result = validateFeatureFlagConfig(config);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toContain('Voice features may have privacy implications');
    });

    it('should pass validation for valid configuration', () => {
      const config = { 
        'chat.streaming': true,
        'security.sanitization': true 
      };
      const result = validateFeatureFlagConfig(config);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
  });

  describe('mergeWithEnvironmentDefaults', () => {
    it('should merge with development defaults', () => {
      const config = { 'chat.streaming': false };
      const result = mergeWithEnvironmentDefaults(config, 'development');

      expect(result['chat.streaming']).toBe(false); // user override
      expect(result['debug.mode']).toBe(true); // development default
      expect(result['security.sanitization']).toBe(true); // base default
    });

    it('should merge with production defaults', () => {
      const config = { 'chat.streaming': false };
      const result = mergeWithEnvironmentDefaults(config, 'production');

      expect(result['chat.streaming']).toBe(false); // user override
      expect(result['debug.mode']).toBe(false); // production default
      expect(result['security.sanitization']).toBe(true); // base default
    });

    it('should use production defaults for unknown environment', () => {
      const config = { 'chat.streaming': false };
      const result = mergeWithEnvironmentDefaults(config, 'unknown');

      expect(result['debug.mode']).toBe(false); // production default
    });
  });

  describe('loadConfigFromEnvironment', () => {
    const originalEnv = process.env;

    beforeEach(() => {
      process.env = { ...originalEnv };
    });

    afterEach(() => {
      process.env = originalEnv;
    });

    it('should load configuration from environment variables', () => {
      process.env.NEXT_PUBLIC_FEATURE_CHAT_STREAMING = 'false';
      process.env.NEXT_PUBLIC_FEATURE_DEBUG_MODE = 'true';

      const result = loadConfigFromEnvironment();

      expect(result['chat.streaming']).toBe(false);
      expect(result['debug.mode']).toBe(true);
    });

    it('should handle missing environment variables', () => {
      const result = loadConfigFromEnvironment();

      expect(Object.keys(result)).toHaveLength(0);
    });
  });

  describe('saveConfigToStorage', () => {
    it('should save valid configuration to localStorage', () => {
      const config = { 'chat.streaming': true };
      const result = saveConfigToStorage(config);

      expect(result).toBe(true);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'feature_flags',
        expect.stringContaining('"chat.streaming":true')
      );
    });

    it('should reject invalid configuration', () => {
      const config = { 'security.sanitization': false };
      const result = saveConfigToStorage(config);

      expect(result).toBe(false);
      expect(consoleSpy.error).toHaveBeenCalledWith(
        'Invalid feature flag configuration:',
        expect.arrayContaining([expect.stringContaining('security.sanitization')])
      );
    });

    it('should handle localStorage errors', () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('Storage error');
      });

      const config = { 'chat.streaming': true };
      const result = saveConfigToStorage(config);

      expect(result).toBe(false);
      expect(consoleSpy.error).toHaveBeenCalledWith(
        'Failed to save feature flag configuration:',
        expect.any(Error)
      );
    });
  });

  describe('loadConfigFromStorage', () => {
    it('should load valid configuration from localStorage', () => {
      const storedConfig = {
        flags: { 'chat.streaming': false },
        environment: 'production',
        version: '1.0.0',
        lastUpdated: '2023-01-01T00:00:00.000Z'
      };
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(storedConfig));

      const result = loadConfigFromStorage();

      expect(result).toEqual({ 'chat.streaming': false });
    });

    it('should return null for missing storage', () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      const result = loadConfigFromStorage();

      expect(result).toBeNull();
    });

    it('should handle invalid stored configuration', () => {
      const invalidConfig = {
        flags: { 'security.sanitization': false },
        environment: 'production',
        version: '1.0.0',
        lastUpdated: '2023-01-01T00:00:00.000Z'
      };
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(invalidConfig));

      const result = loadConfigFromStorage();

      expect(result).toBeNull();
      expect(consoleSpy.error).toHaveBeenCalledWith(
        'Invalid stored feature flag configuration:',
        expect.arrayContaining([expect.stringContaining('security.sanitization')])
      );
    });

    it('should handle JSON parsing errors', () => {
      mockLocalStorage.getItem.mockReturnValue('invalid json');

      const result = loadConfigFromStorage();

      expect(result).toBeNull();
      expect(consoleSpy.error).toHaveBeenCalledWith(
        'Failed to load feature flag configuration:',
        expect.any(Error)
      );
    });
  });

  describe('createConfigUpdater', () => {
    it('should update single flag with validation', () => {
      const onUpdate = vi.fn();
      const updater = createConfigUpdater(onUpdate);

      updater.updateFlag('chat.streaming', true);

      expect(onUpdate).toHaveBeenCalledWith({ 'chat.streaming': true });
    });

    it('should reject invalid single flag update', () => {
      const onUpdate = vi.fn();
      const updater = createConfigUpdater(onUpdate);

      expect(() => {
        updater.updateFlag('security.sanitization', false);
      }).toThrow("Cannot update flag 'security.sanitization'");

      expect(onUpdate).not.toHaveBeenCalled();
    });

    it('should update multiple flags with validation', () => {
      const onUpdate = vi.fn();
      const updater = createConfigUpdater(onUpdate);

      const flags = { 'chat.streaming': true, 'chat.tools': false };
      updater.updateFlags(flags);

      expect(onUpdate).toHaveBeenCalledWith(flags);
    });

    it('should reject invalid multiple flags update', () => {
      const onUpdate = vi.fn();
      const updater = createConfigUpdater(onUpdate);

      const flags = { 'security.sanitization': false };

      expect(() => {
        updater.updateFlags(flags);
      }).toThrow('Cannot update flags');

      expect(onUpdate).not.toHaveBeenCalled();
    });

    it('should reset to defaults', () => {
      const onUpdate = vi.fn();
      const updater = createConfigUpdater(onUpdate);

      updater.resetToDefaults('development');

      expect(onUpdate).toHaveBeenCalledWith(
        expect.objectContaining({
          'debug.mode': true, // development default
          'security.sanitization': true // base default
        })
      );
    });
  });

  describe('constants', () => {
    it('should define security critical flags', () => {
      expect(SECURITY_CRITICAL_FLAGS).toContain('security.sanitization');
      expect(SECURITY_CRITICAL_FLAGS).toContain('security.rbac');
    });

    it('should define performance critical flags', () => {
      expect(PERFORMANCE_CRITICAL_FLAGS).toContain('performance.virtualization');
      expect(PERFORMANCE_CRITICAL_FLAGS).toContain('analytics.detailed');
    });
  });
});