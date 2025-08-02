/**
 * Test suite for AlertManager service
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { AlertManager } from '../alertManager';
import type { KarenAlert, AlertSettings } from '@/types/karen-alerts';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock toast
vi.mock('@/hooks/use-toast', () => ({
  toast: vi.fn(() => ({
    dismiss: vi.fn(),
  })),
}));

describe('AlertManager', () => {
  let alertManager: AlertManager;

  beforeEach(() => {
    alertManager = new AlertManager();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    vi.clearAllMocks();
  });

  describe('Initialization', () => {
    test('should initialize successfully', async () => {
      await expect(alertManager.initialize()).resolves.not.toThrow();
    });

    test('should load settings from localStorage', async () => {
      const mockSettings = {
        version: '1.0.0',
        settings: {
          durations: { success: 3000, info: 5000, warning: 7000, error: 9000, system: 5000 },
          maxConcurrentAlerts: 2,
          enableSounds: true,
          enableAnimations: false,
          position: 'top-left' as const,
          categories: { performance: false, health: true, system: true, validation: true },
          announceAlerts: false,
          highContrastMode: true,
          reducedMotion: true,
        },
        lastUpdated: Date.now(),
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockSettings));
      
      await alertManager.initialize();
      const settings = alertManager.getSettings();
      
      expect(settings.maxConcurrentAlerts).toBe(2);
      expect(settings.enableSounds).toBe(true);
      expect(settings.position).toBe('top-left');
    });

    test('should use default settings when localStorage is empty', async () => {
      localStorageMock.getItem.mockReturnValue(null);
      
      await alertManager.initialize();
      const settings = alertManager.getSettings();
      
      expect(settings.maxConcurrentAlerts).toBe(3);
      expect(settings.enableAnimations).toBe(true);
      expect(settings.position).toBe('top-right');
    });
  });

  describe('Alert Management', () => {
    beforeEach(async () => {
      await alertManager.initialize();
    });

    test('should show alert successfully', async () => {
      const alertData: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'info',
        variant: 'karen-info',
        title: 'Test Alert',
        message: 'This is a test message',
        priority: 'normal',
        source: 'test',
      };

      const result = await alertManager.showAlert(alertData);
      
      expect(result.success).toBe(true);
      expect(result.alertId).toBeDefined();
      expect(result.error).toBeUndefined();
    });

    test('should respect rate limiting', async () => {
      const alertData: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'info',
        variant: 'karen-info',
        title: 'Rate Limited Alert',
        message: 'This should be rate limited',
        priority: 'normal',
        source: 'test',
      };

      // Show 5 alerts (should all succeed)
      for (let i = 0; i < 5; i++) {
        const result = await alertManager.showAlert(alertData);
        expect(result.success).toBe(true);
      }

      // 6th alert should be rate limited
      const result = await alertManager.showAlert(alertData);
      expect(result.success).toBe(false);
      expect(result.error).toBe('Rate limit exceeded');
    });

    test('should respect category settings', async () => {
      // Disable performance alerts
      await alertManager.updateSettings({
        categories: { performance: false, health: true, system: true, validation: true },
      });

      const alertData: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'performance',
        variant: 'karen-warning',
        title: 'Performance Alert',
        message: 'This should be disabled',
        priority: 'normal',
        source: 'test',
      };

      const result = await alertManager.showAlert(alertData);
      expect(result.success).toBe(false);
      expect(result.error).toBe('Alert category disabled');
    });

    test('should prioritize alerts correctly', async () => {
      const lowPriorityAlert: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'info',
        variant: 'karen-info',
        title: 'Low Priority',
        message: 'Low priority message',
        priority: 'low',
        source: 'test',
      };

      const highPriorityAlert: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'validation',
        variant: 'karen-error',
        title: 'High Priority',
        message: 'High priority message',
        priority: 'high',
        source: 'test',
      };

      // Add low priority first, then high priority
      await alertManager.showAlert(lowPriorityAlert);
      await alertManager.showAlert(highPriorityAlert);

      const queuedAlerts = alertManager.getQueuedAlerts();
      
      // High priority should be first in queue
      if (queuedAlerts.length > 0) {
        expect(queuedAlerts[0].priority).toBe('high');
      }
    });

    test('should dismiss alert successfully', async () => {
      const alertData: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'info',
        variant: 'karen-info',
        title: 'Test Alert',
        message: 'This will be dismissed',
        priority: 'normal',
        source: 'test',
      };

      const showResult = await alertManager.showAlert(alertData);
      expect(showResult.success).toBe(true);

      const dismissResult = await alertManager.dismissAlert(showResult.alertId);
      expect(dismissResult.success).toBe(true);
      expect(dismissResult.alertId).toBe(showResult.alertId);
    });

    test('should handle dismiss of non-existent alert', async () => {
      const result = await alertManager.dismissAlert('non-existent-id');
      expect(result.success).toBe(false);
      expect(result.error).toBe('Alert not found');
    });
  });

  describe('Convenience Methods', () => {
    beforeEach(async () => {
      await alertManager.initialize();
    });

    test('should show success alert', async () => {
      const result = await alertManager.showSuccess('Success!', 'Operation completed');
      expect(result.success).toBe(true);
    });

    test('should show error alert', async () => {
      const result = await alertManager.showError('Error!', 'Something went wrong');
      expect(result.success).toBe(true);
    });

    test('should show warning alert', async () => {
      const result = await alertManager.showWarning('Warning!', 'Please be careful');
      expect(result.success).toBe(true);
    });

    test('should show info alert', async () => {
      const result = await alertManager.showInfo('Info', 'Here is some information');
      expect(result.success).toBe(true);
    });
  });

  describe('Settings Management', () => {
    beforeEach(async () => {
      await alertManager.initialize();
    });

    test('should update settings successfully', async () => {
      const newSettings: Partial<AlertSettings> = {
        maxConcurrentAlerts: 5,
        enableSounds: true,
        position: 'bottom-left',
      };

      const result = await alertManager.updateSettings(newSettings);
      expect(result.success).toBe(true);

      const settings = alertManager.getSettings();
      expect(settings.maxConcurrentAlerts).toBe(5);
      expect(settings.enableSounds).toBe(true);
      expect(settings.position).toBe('bottom-left');
    });

    test('should persist settings to localStorage', async () => {
      const newSettings: Partial<AlertSettings> = {
        maxConcurrentAlerts: 4,
      };

      await alertManager.updateSettings(newSettings);
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'karen-alert-settings',
        expect.stringContaining('"maxConcurrentAlerts":4')
      );
    });
  });

  describe('Event System', () => {
    beforeEach(async () => {
      await alertManager.initialize();
    });

    test('should emit alert-shown event', async () => {
      const eventListener = vi.fn();
      const unsubscribe = alertManager.addEventListener('alert-shown', eventListener);

      const alertData: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'info',
        variant: 'karen-info',
        title: 'Test Alert',
        message: 'Test message',
        priority: 'normal',
        source: 'test',
      };

      await alertManager.showAlert(alertData);
      
      expect(eventListener).toHaveBeenCalledWith(expect.objectContaining({
        title: 'Test Alert',
        message: 'Test message',
      }));

      unsubscribe();
    });

    test('should emit alert-dismissed event', async () => {
      const eventListener = vi.fn();
      const unsubscribe = alertManager.addEventListener('alert-dismissed', eventListener);

      const alertData: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'info',
        variant: 'karen-info',
        title: 'Test Alert',
        message: 'Test message',
        priority: 'normal',
        source: 'test',
      };

      const showResult = await alertManager.showAlert(alertData);
      await alertManager.dismissAlert(showResult.alertId);
      
      expect(eventListener).toHaveBeenCalledWith(expect.objectContaining({
        alertId: showResult.alertId,
      }));

      unsubscribe();
    });

    test('should unsubscribe event listeners', async () => {
      const eventListener = vi.fn();
      const unsubscribe = alertManager.addEventListener('alert-shown', eventListener);

      // Unsubscribe immediately
      unsubscribe();

      const alertData: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'info',
        variant: 'karen-info',
        title: 'Test Alert',
        message: 'Test message',
        priority: 'normal',
        source: 'test',
      };

      await alertManager.showAlert(alertData);
      
      // Event listener should not have been called
      expect(eventListener).not.toHaveBeenCalled();
    });
  });

  describe('Queue Management', () => {
    beforeEach(async () => {
      await alertManager.initialize();
    });

    test('should get queued alerts', async () => {
      const alertData: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'info',
        variant: 'karen-info',
        title: 'Queued Alert',
        message: 'This will be queued',
        priority: 'normal',
        source: 'test',
      };

      await alertManager.showAlert(alertData);
      const queuedAlerts = alertManager.getQueuedAlerts();
      
      expect(Array.isArray(queuedAlerts)).toBe(true);
    });

    test('should clear queue', async () => {
      const alertData: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'info',
        variant: 'karen-info',
        title: 'Queued Alert',
        message: 'This will be cleared',
        priority: 'normal',
        source: 'test',
      };

      await alertManager.showAlert(alertData);
      alertManager.clearQueue();
      
      const queuedAlerts = alertManager.getQueuedAlerts();
      expect(queuedAlerts).toHaveLength(0);
    });
  });

  describe('Metrics and History', () => {
    test('should track metrics', async () => {
      // Clear localStorage for this test
      localStorageMock.getItem.mockReturnValue(null);
      
      const freshAlertManager = new AlertManager();
      await freshAlertManager.initialize();
      
      const alertData: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'info',
        variant: 'karen-info',
        title: 'Metrics Test',
        message: 'Testing metrics',
        priority: 'normal',
        source: 'test',
      };

      // Get initial metrics
      const initialMetrics = freshAlertManager.getMetrics();
      const initialTotalShown = initialMetrics.totalShown;
      const initialInfoCount = initialMetrics.categoryBreakdown.info;
      
      // Show an alert
      await freshAlertManager.showAlert(alertData);
      
      // Wait a bit for processing
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // Check that metrics were updated
      const updatedMetrics = freshAlertManager.getMetrics();
      expect(updatedMetrics.totalShown).toBe(initialTotalShown + 1);
      expect(updatedMetrics.categoryBreakdown.info).toBe(initialInfoCount + 1);
    });

    test('should maintain history', async () => {
      // Clear localStorage for this test
      localStorageMock.getItem.mockReturnValue(null);
      
      const freshAlertManager = new AlertManager();
      await freshAlertManager.initialize();
      
      const alertData: Omit<KarenAlert, 'id' | 'timestamp'> = {
        type: 'info',
        variant: 'karen-info',
        title: 'History Test',
        message: 'Testing history',
        priority: 'normal',
        source: 'test',
      };

      // Get initial history length
      const initialHistoryLength = freshAlertManager.getHistory().alerts.length;

      const showResult = await freshAlertManager.showAlert(alertData);
      await freshAlertManager.dismissAlert(showResult.alertId);
      
      // Check that history was updated
      const updatedHistory = freshAlertManager.getHistory();
      expect(updatedHistory.alerts.length).toBeGreaterThan(initialHistoryLength);
    });
  });
});