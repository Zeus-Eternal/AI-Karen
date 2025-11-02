/**
 * Test file to verify all Karen Alert type definitions are properly implemented
 */

import {
  AlertType,
  AlertVariant,
  AlertPriority,
  AlertAction,
  KarenAlert,
  AlertSettings,
  AlertHistory,
  StoredAlert,
  AlertMetrics,
  AlertSettingsStorage,
  AlertResult,
  ErrorRecoveryConfig,
  DEFAULT_ALERT_SETTINGS,
  DEFAULT_ERROR_RECOVERY_CONFIG,
} from '../karen-alerts';

describe('Karen Alert Type Definitions', () => {
  test('AlertType union includes all required types', () => {
    const validTypes: AlertType[] = [
      'system',
      'performance',
      'health',
      'user-action',
      'validation',
      'success',
      'info'
    ];
    
    // This test passes if TypeScript compilation succeeds
    expect(validTypes).toHaveLength(7);
  });

  test('AlertVariant union includes all Karen variants', () => {
    const validVariants: AlertVariant[] = [
      'karen-success',
      'karen-info',
      'karen-warning',
      'karen-error',
      'karen-system'
    ];
    
    expect(validVariants).toHaveLength(5);
  });

  test('AlertPriority union includes all priority levels', () => {
    const validPriorities: AlertPriority[] = [
      'low',
      'normal',
      'high',
      'critical'
    ];
    
    expect(validPriorities).toHaveLength(4);
  });

  test('AlertAction interface has required properties', () => {
    const mockAction: AlertAction = {
      label: 'Test Action',
      action: () => {},
      variant: 'default',
      icon: null
    };
    
    expect(mockAction.label).toBe('Test Action');
    expect(typeof mockAction.action).toBe('function');
  });

  test('KarenAlert interface has all required properties', () => {
    const mockAlert: KarenAlert = {
      id: 'test-alert-1',
      type: 'info',
      variant: 'karen-info',
      title: 'Test Alert',
      message: 'This is a test alert message',
      emoji: '💡',
      priority: 'normal',
      duration: 5000,
      actions: [],
      expandableContent: null,
      metadata: { source: 'test' },
      timestamp: Date.now(),
      source: 'test-component'
    };
    
    expect(mockAlert.id).toBe('test-alert-1');
    expect(mockAlert.type).toBe('info');
    expect(mockAlert.variant).toBe('karen-info');
    expect(mockAlert.title).toBe('Test Alert');
    expect(mockAlert.message).toBe('This is a test alert message');
    expect(mockAlert.priority).toBe('normal');
    expect(mockAlert.source).toBe('test-component');
  });

  test('AlertSettings interface has all required configuration options', () => {
    const mockSettings: AlertSettings = {
      durations: {
        success: 4000,
        info: 6000,
        warning: 8000,
        error: 10000,
        system: 6000,
      },
      maxConcurrentAlerts: 3,
      enableSounds: false,
      enableAnimations: true,
      position: 'top-right',
      categories: {
        performance: true,
        health: true,
        system: true,
        validation: true,
      },
      announceAlerts: true,
      highContrastMode: false,
      reducedMotion: false,
    };
    
    expect(mockSettings.durations.success).toBe(4000);
    expect(mockSettings.maxConcurrentAlerts).toBe(3);
    expect(mockSettings.position).toBe('top-right');
    expect(mockSettings.categories.performance).toBe(true);
  });

  test('StoredAlert extends KarenAlert with tracking properties', () => {
    const mockStoredAlert: StoredAlert = {
      id: 'stored-alert-1',
      type: 'success',
      variant: 'karen-success',
      title: 'Success Alert',
      message: 'Operation completed successfully',
      priority: 'normal',
      timestamp: Date.now(),
      source: 'test-component',
      dismissed: true,
      dismissedAt: Date.now(),
      interactionCount: 2,
      lastInteraction: Date.now(),
    };
    
    expect(mockStoredAlert.dismissed).toBe(true);
    expect(typeof mockStoredAlert.dismissedAt).toBe('number');
    expect(mockStoredAlert.interactionCount).toBe(2);
  });

  test('AlertHistory interface has required properties', () => {
    const mockHistory: AlertHistory = {
      alerts: [],
      maxHistory: 100,
      retentionDays: 30,
    };
    
    expect(Array.isArray(mockHistory.alerts)).toBe(true);
    expect(mockHistory.maxHistory).toBe(100);
    expect(mockHistory.retentionDays).toBe(30);
  });

  test('AlertMetrics interface has all tracking properties', () => {
    const mockMetrics: AlertMetrics = {
      totalShown: 150,
      totalDismissed: 140,
      averageViewTime: 3500,
      actionClickRate: 0.25,
      categoryBreakdown: {
        system: 20,
        performance: 30,
        health: 15,
        'user-action': 40,
        validation: 25,
        success: 15,
        info: 5,
      },
      userSatisfactionScore: 4.2,
    };
    
    expect(mockMetrics.totalShown).toBe(150);
    expect(mockMetrics.actionClickRate).toBe(0.25);
    expect(mockMetrics.categoryBreakdown.system).toBe(20);
  });

  test('DEFAULT_ALERT_SETTINGS has proper default values', () => {
    expect(DEFAULT_ALERT_SETTINGS.durations.success).toBe(4000);
    expect(DEFAULT_ALERT_SETTINGS.maxConcurrentAlerts).toBe(3);
    expect(DEFAULT_ALERT_SETTINGS.enableAnimations).toBe(true);
    expect(DEFAULT_ALERT_SETTINGS.position).toBe('top-right');
    expect(DEFAULT_ALERT_SETTINGS.announceAlerts).toBe(true);
  });

  test('DEFAULT_ERROR_RECOVERY_CONFIG has proper default values', () => {
    expect(DEFAULT_ERROR_RECOVERY_CONFIG.maxRetries).toBe(3);
    expect(DEFAULT_ERROR_RECOVERY_CONFIG.retryDelay).toBe(1000);
    expect(DEFAULT_ERROR_RECOVERY_CONFIG.fallbackBehavior).toBe('console');
    expect(DEFAULT_ERROR_RECOVERY_CONFIG.errorReporting).toBe(true);
  });
});