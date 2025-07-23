// Shared Advanced Settings Component
// Framework-agnostic advanced configuration interface

import { KarenSettings, Theme, TemperatureUnit, WeatherServiceOption } from '../../abstractions/types';

export interface AdvancedSettingsOptions {
  enableWeatherSettings?: boolean;
  enableApiSettings?: boolean;
  enableDebugMode?: boolean;
  enableExperimentalFeatures?: boolean;
}

export interface AdvancedSettingsState {
  temperatureUnit: TemperatureUnit;
  weatherService: WeatherServiceOption;
  weatherApiKey: string | null;
  defaultWeatherLocation: string | null;
  activeListenMode: boolean;
  debugMode: boolean;
  experimentalFeatures: Record<string, boolean>;
}

export class SharedAdvancedSettings {
  private state: AdvancedSettingsState;
  private options: AdvancedSettingsOptions;
  private theme: Theme;

  constructor(
    settings: KarenSettings,
    theme: Theme,
    options: AdvancedSettingsOptions = {}
  ) {
    this.theme = theme;
    this.options = {
      enableWeatherSettings: true,
      enableApiSettings: true,
      enableDebugMode: false,
      enableExperimentalFeatures: false,
      ...options
    };

    this.state = {
      temperatureUnit: settings.temperatureUnit,
      weatherService: settings.weatherService,
      weatherApiKey: settings.weatherApiKey,
      defaultWeatherLocation: settings.defaultWeatherLocation,
      activeListenMode: settings.activeListenMode,
      debugMode: false,
      experimentalFeatures: {}
    };
  }

  getRenderData() {
    return {
      state: this.state,
      options: this.options,
      theme: this.theme,
      handlers: {
        onTemperatureUnitChange: (unit: TemperatureUnit) => this.updateTemperatureUnit(unit),
        onWeatherServiceChange: (service: WeatherServiceOption) => this.updateWeatherService(service),
        onWeatherApiKeyChange: (key: string) => this.updateWeatherApiKey(key),
        onDefaultLocationChange: (location: string) => this.updateDefaultLocation(location),
        onActiveListenToggle: (enabled: boolean) => this.toggleActiveListen(enabled),
        onDebugModeToggle: (enabled: boolean) => this.toggleDebugMode(enabled),
        onExperimentalFeatureToggle: (feature: string, enabled: boolean) => 
          this.toggleExperimentalFeature(feature, enabled)
      }
    };
  }

  private updateTemperatureUnit(unit: TemperatureUnit): void {
    this.state.temperatureUnit = unit;
  }

  private updateWeatherService(service: WeatherServiceOption): void {
    this.state.weatherService = service;
  }

  private updateWeatherApiKey(key: string): void {
    this.state.weatherApiKey = key;
  }

  private updateDefaultLocation(location: string): void {
    this.state.defaultWeatherLocation = location;
  }

  private toggleActiveListen(enabled: boolean): void {
    this.state.activeListenMode = enabled;
  }

  private toggleDebugMode(enabled: boolean): void {
    this.state.debugMode = enabled;
  }

  private toggleExperimentalFeature(feature: string, enabled: boolean): void {
    this.state.experimentalFeatures[feature] = enabled;
  }
}