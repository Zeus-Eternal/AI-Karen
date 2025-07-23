// Shared Theme Settings Component
// Framework-agnostic theme and appearance configuration interface

import { Theme } from '../../abstractions/types';
import { themeManager } from '../../abstractions/theme';

export interface ThemeSettingsOptions {
  enableCustomThemes?: boolean;
  enableColorPicker?: boolean;
  showPreview?: boolean;
}

export interface ThemeSettingsState {
  selectedTheme: string;
  availableThemes: Theme[];
  customColors: Record<string, string>;
  previewMode: boolean;
}

export class SharedThemeSettings {
  private state: ThemeSettingsState;
  private options: ThemeSettingsOptions;
  private theme: Theme;

  constructor(
    theme: Theme,
    options: ThemeSettingsOptions = {}
  ) {
    this.theme = theme;
    this.options = {
      enableCustomThemes: true,
      enableColorPicker: true,
      showPreview: true,
      ...options
    };

    this.state = {
      selectedTheme: theme.name,
      availableThemes: themeManager.availableThemes,
      customColors: {},
      previewMode: false
    };
  }

  getRenderData() {
    return {
      state: this.state,
      options: this.options,
      theme: this.theme,
      handlers: {
        onThemeChange: (themeName: string) => this.updateTheme(themeName),
        onColorChange: (colorKey: string, color: string) => this.updateColor(colorKey, color),
        onPreviewToggle: () => this.togglePreview(),
        onResetTheme: () => this.resetTheme()
      }
    };
  }

  private updateTheme(themeName: string): void {
    this.state.selectedTheme = themeName;
    themeManager.setTheme(themeName);
  }

  private updateColor(colorKey: string, color: string): void {
    this.state.customColors[colorKey] = color;
  }

  private togglePreview(): void {
    this.state.previewMode = !this.state.previewMode;
  }

  private resetTheme(): void {
    this.state.customColors = {};
    themeManager.setTheme('light');
  }
}