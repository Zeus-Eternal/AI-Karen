// Shared Notification Settings Component
// Framework-agnostic notification configuration interface

import { 
  KarenSettings, 
  NotificationPreferences, 
  Theme 
} from '../../abstractions/types';

export interface NotificationSettingsOptions {
  enableBrowserNotifications?: boolean;
  enableSoundNotifications?: boolean;
  showNotificationPreview?: boolean;
  enableScheduling?: boolean;
}

export interface NotificationSettingsState {
  preferences: NotificationPreferences;
  browserPermission: NotificationPermission | null;
  soundEnabled: boolean;
  quietHours: {
    enabled: boolean;
    start: string;
    end: string;
  };
  errors: Record<string, string>;
}

export interface NotificationSettingsCallbacks {
  onPreferencesChange?: (preferences: NotificationPreferences) => void;
  onBrowserPermissionRequest?: () => void;
  onSoundToggle?: (enabled: boolean) => void;
  onQuietHoursChange?: (quietHours: { enabled: boolean; start: string; end: string }) => void;
}

export class SharedNotificationSettings {
  private state: NotificationSettingsState;
  private options: NotificationSettingsOptions;
  private callbacks: NotificationSettingsCallbacks;
  private theme: Theme;

  constructor(
    settings: KarenSettings,
    theme: Theme,
    options: NotificationSettingsOptions = {},
    callbacks: NotificationSettingsCallbacks = {}
  ) {
    this.theme = theme;
    this.options = {
      enableBrowserNotifications: true,
      enableSoundNotifications: true,
      showNotificationPreview: true,
      enableScheduling: true,
      ...options
    };
    this.callbacks = callbacks;

    this.state = {
      preferences: settings.notifications,
      browserPermission: this.getBrowserPermission(),
      soundEnabled: false,
      quietHours: {
        enabled: false,
        start: '22:00',
        end: '08:00'
      },
      errors: {}
    };
  }

  // Get current state
  getState(): NotificationSettingsState {
    return { ...this.state };
  }

  // Update state
  updateState(newState: Partial<NotificationSettingsState>): void {
    this.state = { ...this.state, ...newState };
  }

  // Update notification preferences
  updatePreferences(preferences: Partial<NotificationPreferences>): void {
    const newPreferences = { ...this.state.preferences, ...preferences };
    this.updateState({ preferences: newPreferences });

    if (this.callbacks.onPreferencesChange) {
      this.callbacks.onPreferencesChange(newPreferences);
    }
  }

  // Toggle main notifications
  toggleNotifications(enabled: boolean): void {
    this.updatePreferences({ enabled });
  }

  // Toggle insight alerts
  toggleInsightAlerts(enabled: boolean): void {
    this.updatePreferences({ alertOnNewInsights: enabled });
  }

  // Toggle summary alerts
  toggleSummaryAlerts(enabled: boolean): void {
    this.updatePreferences({ alertOnSummaryReady: enabled });
  }

  // Request browser notification permission
  async requestBrowserPermission(): Promise<void> {
    if (!this.options.enableBrowserNotifications || !('Notification' in window)) {
      return;
    }

    try {
      const permission = await Notification.requestPermission();
      this.updateState({ browserPermission: permission });

      if (this.callbacks.onBrowserPermissionRequest) {
        this.callbacks.onBrowserPermissionRequest();
      }
    } catch (error) {
      console.error('Failed to request notification permission:', error);
    }
  }

  // Toggle sound notifications
  toggleSound(enabled: boolean): void {
    this.updateState({ soundEnabled: enabled });

    if (this.callbacks.onSoundToggle) {
      this.callbacks.onSoundToggle(enabled);
    }
  }

  // Update quiet hours
  updateQuietHours(quietHours: Partial<{ enabled: boolean; start: string; end: string }>): void {
    const newQuietHours = { ...this.state.quietHours, ...quietHours };
    
    // Validate time format
    if (quietHours.start && !this.isValidTimeFormat(quietHours.start)) {
      this.updateState({
        errors: { ...this.state.errors, quietHoursStart: 'Invalid time format' }
      });
      return;
    }

    if (quietHours.end && !this.isValidTimeFormat(quietHours.end)) {
      this.updateState({
        errors: { ...this.state.errors, quietHoursEnd: 'Invalid time format' }
      });
      return;
    }

    this.updateState({ 
      quietHours: newQuietHours,
      errors: { 
        ...this.state.errors, 
        quietHoursStart: '', 
        quietHoursEnd: '' 
      }
    });

    if (this.callbacks.onQuietHoursChange) {
      this.callbacks.onQuietHoursChange(newQuietHours);
    }
  }

  // Test notification
  async testNotification(): Promise<void> {
    if (!this.canShowNotifications()) {
      return;
    }

    try {
      if (this.options.enableBrowserNotifications && this.state.browserPermission === 'granted') {
        new Notification('Karen AI Test', {
          body: 'This is a test notification from Karen AI',
          icon: '/favicon.ico',
          tag: 'karen-test'
        });
      }

      if (this.options.enableSoundNotifications && this.state.soundEnabled) {
        this.playNotificationSound();
      }
    } catch (error) {
      console.error('Failed to show test notification:', error);
    }
  }

  // Check if notifications can be shown
  canShowNotifications(): boolean {
    if (!this.state.preferences.enabled) return false;
    
    if (this.state.quietHours.enabled && this.isInQuietHours()) {
      return false;
    }

    return true;
  }

  // Check if currently in quiet hours
  isInQuietHours(): boolean {
    if (!this.state.quietHours.enabled) return false;

    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();
    
    const startTime = this.parseTime(this.state.quietHours.start);
    const endTime = this.parseTime(this.state.quietHours.end);

    if (startTime <= endTime) {
      // Same day range (e.g., 09:00 to 17:00)
      return currentTime >= startTime && currentTime <= endTime;
    } else {
      // Overnight range (e.g., 22:00 to 08:00)
      return currentTime >= startTime || currentTime <= endTime;
    }
  }

  // Get browser notification permission status
  private getBrowserPermission(): NotificationPermission | null {
    if (!('Notification' in window)) return null;
    return Notification.permission;
  }

  // Validate time format (HH:MM)
  private isValidTimeFormat(time: string): boolean {
    const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
    return timeRegex.test(time);
  }

  // Parse time string to minutes
  private parseTime(time: string): number {
    const [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
  }

  // Play notification sound
  private playNotificationSound(): void {
    try {
      const audio = new Audio('/notification-sound.mp3');
      audio.volume = 0.5;
      audio.play().catch(error => {
        console.warn('Failed to play notification sound:', error);
      });
    } catch (error) {
      console.warn('Notification sound not available:', error);
    }
  }

  // Get notification types
  getNotificationTypes(): Array<{
    key: keyof NotificationPreferences;
    label: string;
    description: string;
    enabled: boolean;
  }> {
    return [
      {
        key: 'enabled',
        label: 'Enable Notifications',
        description: 'Allow Karen to show notifications',
        enabled: this.state.preferences.enabled
      },
      {
        key: 'alertOnNewInsights',
        label: 'New Insights',
        description: 'Notify when Karen discovers new insights',
        enabled: this.state.preferences.alertOnNewInsights
      },
      {
        key: 'alertOnSummaryReady',
        label: 'Summary Ready',
        description: 'Notify when conversation summaries are generated',
        enabled: this.state.preferences.alertOnSummaryReady
      }
    ];
  }

  // Get notification preview
  getNotificationPreview(): { title: string; body: string; icon?: string } {
    return {
      title: 'Karen AI',
      body: 'This is how notifications will appear',
      icon: '/favicon.ico'
    };
  }

  // Get CSS classes
  getCssClasses(): string[] {
    const classes = ['karen-notification-settings'];
    
    if (!this.state.preferences.enabled) {
      classes.push('karen-notification-settings-disabled');
    }
    
    if (this.state.browserPermission === 'denied') {
      classes.push('karen-notification-settings-blocked');
    }
    
    if (Object.keys(this.state.errors).length > 0) {
      classes.push('karen-notification-settings-errors');
    }
    
    return classes;
  }

  // Get inline styles
  getInlineStyles(): Record<string, string> {
    return {
      backgroundColor: this.theme.colors.surface,
      color: this.theme.colors.text,
      padding: this.theme.spacing.md,
      borderRadius: this.theme.borderRadius,
      border: `1px solid ${this.theme.colors.border}`,
      fontFamily: this.theme.typography.fontFamily
    };
  }

  // Get render data
  getRenderData(): NotificationSettingsRenderData {
    return {
      state: this.getState(),
      options: this.options,
      notificationTypes: this.getNotificationTypes(),
      preview: this.options.showNotificationPreview ? this.getNotificationPreview() : null,
      canShowBrowserNotifications: this.options.enableBrowserNotifications && ('Notification' in window),
      canPlaySounds: this.options.enableSoundNotifications,
      cssClasses: this.getCssClasses(),
      styles: this.getInlineStyles(),
      theme: this.theme,
      handlers: {
        onToggleNotifications: (enabled: boolean) => this.toggleNotifications(enabled),
        onToggleInsightAlerts: (enabled: boolean) => this.toggleInsightAlerts(enabled),
        onToggleSummaryAlerts: (enabled: boolean) => this.toggleSummaryAlerts(enabled),
        onRequestBrowserPermission: () => this.requestBrowserPermission(),
        onToggleSound: (enabled: boolean) => this.toggleSound(enabled),
        onUpdateQuietHours: (quietHours: Partial<{ enabled: boolean; start: string; end: string }>) => 
          this.updateQuietHours(quietHours),
        onTestNotification: () => this.testNotification()
      }
    };
  }

  // Update theme
  updateTheme(theme: Theme): void {
    this.theme = theme;
  }

  // Update from settings
  updateFromSettings(settings: KarenSettings): void {
    this.updateState({
      preferences: settings.notifications
    });
  }
}

// Supporting interfaces
export interface NotificationSettingsRenderData {
  state: NotificationSettingsState;
  options: NotificationSettingsOptions;
  notificationTypes: Array<{
    key: keyof NotificationPreferences;
    label: string;
    description: string;
    enabled: boolean;
  }>;
  preview: { title: string; body: string; icon?: string } | null;
  canShowBrowserNotifications: boolean;
  canPlaySounds: boolean;
  cssClasses: string[];
  styles: Record<string, string>;
  theme: Theme;
  handlers: {
    onToggleNotifications: (enabled: boolean) => void;
    onToggleInsightAlerts: (enabled: boolean) => void;
    onToggleSummaryAlerts: (enabled: boolean) => void;
    onRequestBrowserPermission: () => Promise<void>;
    onToggleSound: (enabled: boolean) => void;
    onUpdateQuietHours: (quietHours: Partial<{ enabled: boolean; start: string; end: string }>) => void;
    onTestNotification: () => Promise<void>;
  };
}

// Utility functions
export function createNotificationSettings(
  settings: KarenSettings,
  theme: Theme,
  options: NotificationSettingsOptions = {},
  callbacks: NotificationSettingsCallbacks = {}
): SharedNotificationSettings {
  return new SharedNotificationSettings(settings, theme, options, callbacks);
}

export function checkNotificationSupport(): {
  browserNotifications: boolean;
  soundNotifications: boolean;
  permission: NotificationPermission | null;
} {
  return {
    browserNotifications: 'Notification' in window,
    soundNotifications: 'Audio' in window,
    permission: 'Notification' in window ? Notification.permission : null
  };
}

export function formatQuietHoursDisplay(start: string, end: string): string {
  const formatTime = (time: string) => {
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  return `${formatTime(start)} - ${formatTime(end)}`;
}