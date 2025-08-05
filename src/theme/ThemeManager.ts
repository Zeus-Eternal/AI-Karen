import fs from 'fs';
import path from 'path';
import Ajv, { JSONSchemaType } from 'ajv';

export type ThemeScope = 'app' | 'plugin' | 'prompt';

export interface ThemeStyle {
  colors?: Record<string, string>;
  typography?: Record<string, string>;
  icons?: Record<string, string>;
  widgets?: string[];
  [key: string]: any;
}

export interface Theme {
  name: string;
  version?: string;
  author?: string;
  license?: string;
  scope: ThemeScope;
  layout: string;
  style: ThemeStyle;
  metadata?: Record<string, any>;
}

/**
 * ThemeManager loads and validates theme definitions from the /themes directory.
 * Themes are grouped by scope: app-level, plugin-level, and prompt-level.
 */
export class ThemeManager {
  private themes: Map<string, Theme> = new Map();
  private ajv: Ajv;
  private validator: (data: Theme) => boolean;
  private baseDir: string;

  constructor(baseDir: string = path.resolve(process.cwd(), 'themes')) {
    this.baseDir = baseDir;
    const schemaPath = path.resolve(process.cwd(), 'src/theme/theme.schema.json');
    const schemaRaw = fs.readFileSync(schemaPath, 'utf-8');
    const schema = JSON.parse(schemaRaw) as JSONSchemaType<Theme>;
    this.ajv = new Ajv({ allErrors: true });
    this.validator = this.ajv.compile(schema);
  }

  /**
   * Load all theme files from the base directory into memory.
   */
  loadThemes(): void {
    const scopes: ThemeScope[] = ['app', 'plugin', 'prompt'];
    for (const scope of scopes) {
      const dir = path.join(this.baseDir, `${scope}_themes`);
      if (!fs.existsSync(dir)) continue;
      const files = fs.readdirSync(dir).filter(f => f.endsWith('.json'));
      for (const file of files) {
        const full = path.join(dir, file);
        try {
          const data = JSON.parse(fs.readFileSync(full, 'utf-8')) as Theme;
          if (this.validator(data)) {
            const key = `${scope}:${data.name}`;
            this.themes.set(key, data);
          } else {
            console.warn(`Theme validation failed for ${full}`, this.validator.errors);
          }
        } catch (err) {
          console.error(`Failed to load theme ${full}`, err);
        }
      }
    }
  }

  /**
   * Resolve a theme by scope and name.
   */
  getTheme(scope: ThemeScope, name: string): Theme | undefined {
    return this.themes.get(`${scope}:${name}`);
  }

  /**
   * Apply theme to document by dispatching a custom event. Consumers can listen
   * for `kari-theme-change` to update UI.
   */
  applyTheme(theme: Theme): void {
    if (typeof document !== 'undefined') {
      const event = new CustomEvent('kari-theme-change', { detail: theme });
      document.dispatchEvent(event);
    }
  }

  /**
   * Utility to list marketplace themes located in themes/marketplace.
   */
  listMarketplaceThemes(): Theme[] {
    const dir = path.join(this.baseDir, 'marketplace');
    if (!fs.existsSync(dir)) return [];
    const results: Theme[] = [];
    const walk = (current: string) => {
      const entries = fs.readdirSync(current, { withFileTypes: true });
      for (const entry of entries) {
        const full = path.join(current, entry.name);
        if (entry.isDirectory()) {
          walk(full);
        } else if (entry.isFile() && entry.name.endsWith('.json')) {
          try {
            const data = JSON.parse(fs.readFileSync(full, 'utf-8')) as Theme;
            if (this.validator(data)) {
              results.push(data);
            }
          } catch (err) {
            console.error(`Failed to load marketplace theme ${full}`, err);
          }
        }
      }
    };
    walk(dir);
    return results;
  }
}
