// Shared Settings Panel Component
// Framework-agnostic settings management interface

import { 
  ISettingsComponent,
  ComponentConfig
} from '../../abstractions/interfaces';
import { 
  KarenSettings, 
  SettingsState, 
  Theme 
} from '../../abstractions/types';
import { 
  validator, 
  errorHandler, 
  storageManager, 
  eventEmitter,
  debounce
} from '../../abstractions/utils';
import { DEFAULT_KAREN_SETTINGS, STORAGE_KEYS } from '../../abstractions/config';

export interface SettingsPanelOptions {
  enableSync?: boolean;
  autoSave?: boolean;
  showAdvanced?: boolean;
  enableImportExport?: boolean;
  enableReset?: boolean;
  sections?: SettingsSection[];
}

export interface SettingsSection {
  id: string;
  title: string;
  description?: string;
  icon?: string;
  enabled: boolean;
  component: string; // Component name to render
}

export interface SettingsPanelCallbacks {
  onSettingChange?: (key: keyof KarenSettings, value: any, oldValue: any) => void;
  onSettingsSave?: (settings: KarenSettings) => void;
  onSettingsReset?: () => void;
  onSettingsImport?: (settings: KarenSettings) => void;
  onSettingsExport?: (settings: KarenSettings) => void;
  onValidationError?: (errors: Record<string, string>) => void;
}

export class SharedSettingsPanel implements ISettingsComponent {
  public id: string;
  public isVisible: boolean = true;
  public isLoading: boolean = false;
  public theme: Theme;
  public state: SettingsState;

  private options: SettingsPanelOptions;
  private callbacks: SettingsPanelCallbacks;
  private config: ComponentConfig;
  private debouncedSave: () => void;
  private changeCallbacks: Array<(key: string, value: any) => void> = [];
  private saveCallbacks: Array<(settings: KarenSettings) => void> = [];

  constructor(
    containerId: string,
    theme: Theme,
    config: ComponentConfig,
    options: SettingsPanelOptions = {},
    callbacks: SettingsPanelCallbacks = {}
  ) {
    this.id = containerId;
    this.theme = theme;
    this.config = config;
    this.callbacks = callbacks;
    
    this.options = {
      enableSync: true,
      autoSave: config.autoSaveSettings,
      showAdvanced: false,
      enableImportExport: true,
      enableReset: true,
      sections: this.getDefaultSections(),
      ...options
    };

    // Initialize state
    this.state = {
      settings: { ...DEFAULT_KAREN_SETTINGS },
      isDirty: false,
      isLoading: false,
      errors: {}
    };

    // Create debounced save function
    this.debouncedSave = debounce(() => this.saveSettings(), 1000);

    // Load initial settings
    this.loadSettings();

    // Listen for external settings changes
    if (this.options.enableSync) {
      this.setupSyncListeners();
    }
  }

  async render(): Promise<void> {
    console.log('Rendering shared settings panel');
  }

  destroy(): void {
    eventEmitter.removeAllListeners(`settings-${this.id}`);
    console.log('Destroying shared settings panel');
  }

  updateTheme(theme: Theme): void {
    this.theme = theme;
    eventEmitter.emit(`settings-${this.id}-theme-changed`, theme);
  }

  async loadSettings(): Promise<KarenSettings> {
    this.updateState({ isLoading: true });

    try {
      const savedSettings = storageManager.get<KarenSettings>(STORAGE_KEYS.SETTINGS);
      
      if (savedSettings) {
        // Merge with defaults to ensure all properties exist
        const mergedSettings: KarenSettings = {
          ...DEFAULT_KAREN_SETTINGS,
          ...savedSettings,
          // Ensure nested objects are properly merged
          notifications: {
            ...DEFAULT_KAREN_SETTINGS.notifications,
            ...(savedSettings.notifications || {})
          }
        };

        this.updateState({
          settings: mergedSettings,
          isLoading: false,
          isDirty: false
        });

        return mergedSettings;
      } else {
        this.updateState({
          settings: { ...DEFAULT_KAREN_SETTINGS },
          isLoading: false,
          isDirty: false
        });

        return DEFAULT_KAREN_SETTINGS;
      }
    } catch (error) {
      errorHandler.handleError(error as Error, 'load settings');
      this.updateState({ isLoading: false });
      return DEFAULT_KAREN_SETTINGS;
    }
  }

  async saveSettings(settings?: KarenSettings): Promise<void> {
    const settingsToSave = settings || this.state.settings;
    
    // Validate settings
    const errors = this.validateSettings(settingsToSave);
    if (Object.keys(errors).length > 0) {
      this.updateState({ errors });
      if (this.callbacks.onValidationError) {
        this.callbacks.onValidationError(errors);
      }
      return;
    }

    this.updateState({ isLoading: true, errors: {} });

    try {
      // Save to storage
      storageManager.set(STORAGE_KEYS.SETTINGS, settingsToSave);
      
      this.updateState({
        settings: settingsToSave,
        isDirty: false,
        isLoading: false
      });

      // Notify callbacks
      this.saveCallbacks.forEach(callback => {
        try {
          callback(settingsToSave);
        } catch (error) {
          errorHandler.logError(error as Error, 'settings save callback');
        }
      });

      if (this.callbacks.onSettingsSave) {
        this.callbacks.onSettingsSave(settingsToSave);
      }

      // Emit event for other components
      eventEmitter.emit('settings-saved', settingsToSave);

    } catch (error) {
      errorHandler.handleError(error as Error, 'save settings');
      this.updateState({ isLoading: false });
    }
  }

  async resetSettings(): Promise<void> {
    this.updateState({
      settings: { ...DEFAULT_KAREN_SETTINGS },
      isDirty: true,
      errors: {}
    });

    if (this.options.autoSave) {
      await this.saveSettings();
    }

    if (this.callbacks.onSettingsReset) {
      this.callbacks.onSettingsReset();
    }

    eventEmitter.emit(`settings-${this.id}-reset`);
  }

  validateSettings(settings: Partial<KarenSettings>): Record<string, string> {
    return validator.validateSettings(settings);
  }

  updateSetting<K extends keyof KarenSettings>(key: K, value: KarenSettings[K]): void {
    const oldValue = this.state.settings[key];
    
    // Create new settings object
    const newSettings = {
      ...this.state.settings,
      [key]: value
    };

    // Special handling for nested objects
    if (key === 'notifications' && typeof value === 'object') {
      newSettings.notifications = {
        ...this.state.settings.notifications,
        ...(value as any)
      };
    }

    this.updateState({
      settings: newSettings,
      isDirty: true
    });

    // Notify callbacks
    this.changeCallbacks.forEach(callback => {
      try {
        callback(key, value);
      } catch (error) {
        errorHandler.logError(error as Error, 'settings change callback');
      }
    });

    if (this.callbacks.onSettingChange) {
      this.callbacks.onSettingChange(key, value, oldValue);
    }

    // Auto-save if enabled
    if (this.options.autoSave) {
      this.debouncedSave();
    }

    eventEmitter.emit(`settings-${this.id}-changed`, { key, value, oldValue });
  }

  getSetting<K extends keyof KarenSettings>(key: K): KarenSettings[K] {
    return this.state.settings[key];
  }

  onSettingChanged(callback: (key: string, value: any) => void): void {
    this.changeCallbacks.push(callback);
  }

  onSettingsSaved(callback: (settings: KarenSettings) => void): void {
    this.saveCallbacks.push(callback);
  }

  updateState(newState: Partial<SettingsState>): void {
    this.state = { ...this.state, ...newState };
    eventEmitter.emit(`settings-${this.id}-state-changed`, this.state);
  }

  getState(): SettingsState {
    return { ...this.state };
  }

  // Import settings from JSON
  async importSettings(settingsJson: string): Promise<void> {
    try {
      const importedSettings = JSON.parse(settingsJson) as Partial<KarenSettings>;
      
      // Validate imported settings
      const errors = this.validateSettings(importedSettings);
      if (Object.keys(errors).length > 0) {
        throw new Error(`Invalid settings: ${Object.values(errors).join(', ')}`);
      }

      // Merge with current settings
      const mergedSettings: KarenSettings = {
        ...this.state.settings,
        ...importedSettings,
        notifications: {
          ...this.state.settings.notifications,
          ...(importedSettings.notifications || {})
        }
      };

      this.updateState({
        settings: mergedSettings,
        isDirty: true,
        errors: {}
      });

      if (this.options.autoSave) {
        await this.saveSettings();
      }

      if (this.callbacks.onSettingsImport) {
        this.callbacks.onSettingsImport(mergedSettings);
      }

      eventEmitter.emit(`settings-${this.id}-imported`, mergedSettings);

    } catch (error) {
      errorHandler.handleError(error as Error, 'import settings');
      throw error;
    }
  }

  // Export settings to JSON
  exportSettings(): string {
    const exportData = {
      exportDate: new Date().toISOString(),
      version: '1.0',
      settings: this.state.settings
    };

    if (this.callbacks.onSettingsExport) {
      this.callbacks.onSettingsExport(this.state.settings);
    }

    return JSON.stringify(exportData, null, 2);
  }

  // Get available settings sections
  getAvailableSections(): SettingsSection[] {
    return this.options.sections || [];
  }

  // Update section visibility
  updateSectionVisibility(sectionId: string, visible: boolean): void {
    const sections = this.options.sections?.map(section => 
      section.id === sectionId ? { ...section, enabled: visible } : section
    );

    this.options = { ...this.options, sections };
    eventEmitter.emit(`settings-${this.id}-sections-changed`, sections);
  }

  // Get settings statistics
  getSettingsStats(): SettingsStats {
    const settings = this.state.settings;
    
    return {
      personalFactsCount: settings.personalFacts.length,
      customPersonaLength: settings.customPersonaInstructions.length,
      notificationsEnabled: settings.notifications.enabled,
      voiceEnabled: !!settings.ttsVoiceURI,
      weatherConfigured: !!settings.defaultWeatherLocation,
      lastModified: new Date() // Would be tracked in real implementation
    };
  }

  // Get CSS classes
  getCssClasses(): string[] {
    const classes = ['karen-settings-panel'];
    
    if (this.state.isLoading) {
      classes.push('karen-settings-panel-loading');
    }
    
    if (this.state.isDirty) {
      classes.push('karen-settings-panel-dirty');
    }
    
    if (Object.keys(this.state.errors).length > 0) {
      classes.push('karen-settings-panel-errors');
    }
    
    return classes;
  }

  // Get inline styles
  getInlineStyles(): Record<string, string> {
    return {
      backgroundColor: this.theme.colors.background,
      color: this.theme.colors.text,
      fontFamily: this.theme.typography.fontFamily,
      padding: this.theme.spacing.lg,
      borderRadius: this.theme.borderRadius,
      border: `1px solid ${this.theme.colors.border}`
    };
  }

  // Get render data
  getRenderData(): SettingsPanelRenderData {
    return {
      state: this.getState(),
      options: this.options,
      sections: this.getAvailableSections(),
      stats: this.getSettingsStats(),
      cssClasses: this.getCssClasses(),
      styles: this.getInlineStyles(),
      theme: this.theme,
      handlers: {
        onSettingChange: <K extends keyof KarenSettings>(key: K, value: KarenSettings[K]) => 
          this.updateSetting(key, value),
        onSave: () => this.saveSettings(),
        onReset: () => this.resetSettings(),
        onImport: (json: string) => this.importSettings(json),
        onExport: () => this.exportSettings(),
        onSectionToggle: (sectionId: string, visible: boolean) => 
          this.updateSectionVisibility(sectionId, visible)
      }
    };
  }

  // Private helper methods
  private getDefaultSections(): SettingsSection[] {
    return [
      {
        id: 'personality',
        title: 'Personality',
        description: 'Customize Karen\'s personality and behavior',
        icon: 'user',
        enabled: true,
        component: 'PersonalitySettings'
      },
      {
        id: 'memory',
        title: 'Memory',
        description: 'Configure memory depth and personal facts',
        icon: 'brain',
        enabled: true,
        component: 'MemorySettings'
      },
      {
        id: 'notifications',
        title: 'Notifications',
        description: 'Manage notification preferences',
        icon: 'bell',
        enabled: true,
        component: 'NotificationSettings'
      },
      {
        id: 'voice',
        title: 'Voice & Audio',
        description: 'Configure text-to-speech and voice settings',
        icon: 'volume',
        enabled: true,
        component: 'VoiceSettings'
      },
      {
        id: 'theme',
        title: 'Appearance',
        description: 'Customize the interface theme and appearance',
        icon: 'palette',
        enabled: true,
        component: 'ThemeSettings'
      },
      {
        id: 'advanced',
        title: 'Advanced',
        description: 'Advanced configuration options',
        icon: 'settings',
        enabled: this.options.showAdvanced || false,
        component: 'AdvancedSettings'
      }
    ];
  }

  private setupSyncListeners(): void {
    // Listen for storage changes from other tabs/windows
    if (typeof window !== 'undefined') {
      window.addEventListener('storage', (event) => {
        if (event.key === STORAGE_KEYS.SETTINGS && event.newValue) {
          try {
            const newSettings = JSON.parse(event.newValue) as KarenSettings;
            this.updateState({
              settings: newSettings,
              isDirty: false
            });
            eventEmitter.emit(`settings-${this.id}-synced`, newSettings);
          } catch (error) {
            errorHandler.logError(error as Error, 'settings sync');
          }
        }
      });
    }

    // Listen for settings changes from other components
    eventEmitter.on('settings-external-change', (data: { key: string; value: any }) => {
      if (data.key in this.state.settings) {
        this.updateSetting(data.key as keyof KarenSettings, data.value);
      }
    });
  }
}

// Supporting interfaces
export interface SettingsStats {
  personalFactsCount: number;
  customPersonaLength: number;
  notificationsEnabled: boolean;
  voiceEnabled: boolean;
  weatherConfigured: boolean;
  lastModified: Date;
}

export interface SettingsPanelRenderData {
  state: SettingsState;
  options: SettingsPanelOptions;
  sections: SettingsSection[];
  stats: SettingsStats;
  cssClasses: string[];
  styles: Record<string, string>;
  theme: Theme;
  handlers: {
    onSettingChange: <K extends keyof KarenSettings>(key: K, value: KarenSettings[K]) => void;
    onSave: () => Promise<void>;
    onReset: () => Promise<void>;
    onImport: (json: string) => Promise<void>;
    onExport: () => string;
    onSectionToggle: (sectionId: string, visible: boolean) => void;
  };
}

// Utility functions
export function createSettingsPanel(
  containerId: string,
  theme: Theme,
  config: ComponentConfig,
  options: SettingsPanelOptions = {},
  callbacks: SettingsPanelCallbacks = {}
): SharedSettingsPanel {
  return new SharedSettingsPanel(containerId, theme, config, options, callbacks);
}

export function validateSettingsImport(jsonString: string): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  try {
    const parsed = JSON.parse(jsonString);
    
    if (!parsed.settings) {
      errors.push('Missing settings object');
    }
    
    if (parsed.settings) {
      const validationErrors = validator.validateSettings(parsed.settings);
      errors.push(...Object.values(validationErrors));
    }
    
  } catch (error) {
    errors.push('Invalid JSON format');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

export function getSettingDisplayName(key: keyof KarenSettings): string {
  const displayNames: Record<keyof KarenSettings, string> = {
    memoryDepth: 'Memory Depth',
    personalityTone: 'Personality Tone',
    personalityVerbosity: 'Verbosity Level',
    personalFacts: 'Personal Facts',
    notifications: 'Notifications',
    ttsVoiceURI: 'Text-to-Speech Voice',
    customPersonaInstructions: 'Custom Persona Instructions',
    temperatureUnit: 'Temperature Unit',
    weatherService: 'Weather Service',
    weatherApiKey: 'Weather API Key',
    defaultWeatherLocation: 'Default Weather Location',
    activeListenMode: 'Active Listen Mode'
  };
  
  return displayNames[key] || key;
}

export function getSettingDescription(key: keyof KarenSettings): string {
  const descriptions: Record<keyof KarenSettings, string> = {
    memoryDepth: 'How much conversation history Karen should remember',
    personalityTone: 'The overall tone Karen uses in conversations',
    personalityVerbosity: 'How detailed Karen\'s responses should be',
    personalFacts: 'Personal information Karen should remember about you',
    notifications: 'When Karen should show notifications',
    ttsVoiceURI: 'The voice Karen uses for text-to-speech',
    customPersonaInstructions: 'Additional instructions for Karen\'s behavior',
    temperatureUnit: 'Temperature unit for weather information',
    weatherService: 'Which weather service to use',
    weatherApiKey: 'API key for weather service (if required)',
    defaultWeatherLocation: 'Your default location for weather queries',
    activeListenMode: 'Automatically start listening after Karen responds'
  };
  
  return descriptions[key] || '';
}