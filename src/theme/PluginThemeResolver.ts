import { ThemeManager, Theme, ThemeScope } from './ThemeManager';

interface ResolveContext {
  pluginName: string;
  promptTheme?: string;
  responseMetadata?: Record<string, any>;
}

/**
 * PluginThemeResolver decides which theme to use based on plugin name and
 * response metadata. Fallback order: plugin -> prompt -> app default.
 */
export class PluginThemeResolver {
  constructor(private manager: ThemeManager, private defaultAppTheme: string = 'default') {}

  resolve(ctx: ResolveContext): Theme | undefined {
    const { pluginName, promptTheme } = ctx;
    // Plugin level theme
    let theme = this.manager.getTheme('plugin', pluginName);
    if (theme) return theme;
    // Prompt level
    if (promptTheme) {
      theme = this.manager.getTheme('prompt', promptTheme);
      if (theme) return theme;
    }
    // App default
    return this.manager.getTheme('app', this.defaultAppTheme);
  }
}
