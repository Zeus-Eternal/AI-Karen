/**
 * Internationalization (i18n) System
 * 
 * Comprehensive i18n support with dynamic language switching,
 * locale-aware formatting, and cultural adaptation.
 */
export interface I18nConfig {
  defaultLocale: string;
  locales: string[];
  fallbackLocale: string;
  interpolation: {
    prefix: string;
    suffix: string;
  };
  pluralization: boolean;
  contextSeparator: string;
  namespaceSeparator: string;
}
export interface TranslationResource {
  [key: string]: string | TranslationResource;
}
export interface TranslationResources {
  [locale: string]: {
    [namespace: string]: TranslationResource;
  };
}
export interface FormatOptions {
  locale?: string;
  currency?: string;
  timeZone?: string;
  dateStyle?: 'full' | 'long' | 'medium' | 'short';
  timeStyle?: 'full' | 'long' | 'medium' | 'short';
  numberStyle?: 'decimal' | 'currency' | 'percent';
}
export interface PluralOptions {
  count: number;
  [key: string]: any;
}
export interface InterpolationOptions {
  [key: string]: string | number | boolean;
}
export const DEFAULT_CONFIG: I18nConfig = {
  defaultLocale: 'en',
  locales: ['en', 'es', 'fr', 'de', 'ja', 'zh', 'ar', 'ru'],
  fallbackLocale: 'en',
  interpolation: {
    prefix: '{{',
    suffix: '}}',
  },
  pluralization: true,
  contextSeparator: '_',
  namespaceSeparator: ':',
};
export class I18nManager {
  private config: I18nConfig;
  private resources: TranslationResources = {};
  private currentLocale: string;
  private listeners: Set<(locale: string) => void> = new Set();
  constructor(config: Partial<I18nConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.currentLocale = this.config.defaultLocale;
  }
  /**
   * Initialize the i18n system with resources
   */
  async init(resources: TranslationResources): Promise<void> {
    this.resources = resources;
    // Detect browser locale if available
    if (typeof window !== 'undefined') {
      const browserLocale = this.detectBrowserLocale();
      if (browserLocale && this.config.locales.includes(browserLocale)) {
        this.currentLocale = browserLocale;
      }
    }
    // Load saved locale from storage
    const savedLocale = this.getStoredLocale();
    if (savedLocale && this.config.locales.includes(savedLocale)) {
      this.currentLocale = savedLocale;
    }
  }
  /**
   * Change the current locale
   */
  changeLocale(locale: string): void {
    if (!this.config.locales.includes(locale)) {
      return;
    }
    this.currentLocale = locale;
    this.storeLocale(locale);
    this.notifyListeners(locale);
  }
  /**
   * Get the current locale
   */
  getCurrentLocale(): string {
    return this.currentLocale;
  }
  /**
   * Get available locales
   */
  getAvailableLocales(): string[] {
    return [...this.config.locales];
  }
  /**
   * Translate a key
   */
  t(key: string, options: InterpolationOptions & PluralOptions & { ns?: string } = {}): string {
    const { ns = 'common', count, ...interpolationOptions } = options;
    // Handle pluralization
    if (this.config.pluralization && typeof count === 'number') {
      const pluralKey = this.getPluralKey(key, count);
      const translation = this.getTranslation(pluralKey, ns);
      if (translation) {
        return this.interpolate(translation, { ...interpolationOptions, count });
      }
    }
    // Get regular translation
    const translation = this.getTranslation(key, ns);
    if (translation) {
      return this.interpolate(translation, interpolationOptions);
    }
    // Fallback to key if no translation found
    console.warn(`Translation missing for key: ${key} (locale: ${this.currentLocale})`);
    return key;
  }
  /**
   * Format numbers according to locale
   */
  formatNumber(value: number, options: FormatOptions = {}): string {
    const locale = options.locale || this.currentLocale;
    const style = options.numberStyle || 'decimal';
    const formatOptions: Intl.NumberFormatOptions = {
      style,
    };
    if (style === 'currency' && options.currency) {
      formatOptions.currency = options.currency;
    }
    try {
      return new Intl.NumberFormat(locale, formatOptions).format(value);
    } catch (error) {
      return value.toString();
    }
  }
  /**
   * Format dates according to locale
   */
  formatDate(date: Date, options: FormatOptions = {}): string {
    const locale = options.locale || this.currentLocale;
    const formatOptions: Intl.DateTimeFormatOptions = {};
    if (options.dateStyle) {
      formatOptions.dateStyle = options.dateStyle;
    }
    if (options.timeStyle) {
      formatOptions.timeStyle = options.timeStyle;
    }
    if (options.timeZone) {
      formatOptions.timeZone = options.timeZone;
    }
    try {
      return new Intl.DateTimeFormat(locale, formatOptions).format(date);
    } catch (error) {
      return date.toISOString();
    }
  }
  /**
   * Format relative time (e.g., "2 hours ago")
   */
  formatRelativeTime(value: number, unit: Intl.RelativeTimeFormatUnit, options: FormatOptions = {}): string {
    const locale = options.locale || this.currentLocale;
    try {
      return new Intl.RelativeTimeFormat(locale, { numeric: 'auto' }).format(value, unit);
    } catch (error) {
      return `${value} ${unit}`;
    }
  }
  /**
   * Get text direction for current locale
   */
  getTextDirection(): 'ltr' | 'rtl' {
    const rtlLocales = ['ar', 'he', 'fa', 'ur'];
    return rtlLocales.includes(this.currentLocale) ? 'rtl' : 'ltr';
  }
  /**
   * Get locale info
   */
  getLocaleInfo(locale?: string): {
    code: string;
    name: string;
    nativeName: string;
    direction: 'ltr' | 'rtl';
  } {
    const targetLocale = locale || this.currentLocale;
    const localeNames: Record<string, { name: string; nativeName: string }> = {
      en: { name: 'English', nativeName: 'English' },
      es: { name: 'Spanish', nativeName: 'Español' },
      fr: { name: 'French', nativeName: 'Français' },
      de: { name: 'German', nativeName: 'Deutsch' },
      ja: { name: 'Japanese', nativeName: '日本語' },
      zh: { name: 'Chinese', nativeName: '中文' },
      ar: { name: 'Arabic', nativeName: 'العربية' },
      ru: { name: 'Russian', nativeName: 'Русский' },
    };
    const info = localeNames[targetLocale] || { name: targetLocale, nativeName: targetLocale };
    return {
      code: targetLocale,
      name: info.name,
      nativeName: info.nativeName,
      direction: this.getTextDirection(),
    };
  }
  /**
   * Add a locale change listener
   */
  onLocaleChange(callback: (locale: string) => void): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }
  /**
   * Load additional translation resources
   */
  addResources(locale: string, namespace: string, resources: TranslationResource): void {
    if (!this.resources[locale]) {
      this.resources[locale] = {};
    }
    if (!this.resources[locale][namespace]) {
      this.resources[locale][namespace] = {};
    }
    this.resources[locale][namespace] = {
      ...this.resources[locale][namespace],
      ...resources,
    };
  }
  // Private methods
  private getTranslation(key: string, namespace: string): string | null {
    const keys = key.split('.');
    let current: any = this.resources[this.currentLocale]?.[namespace];
    // Try current locale first
    for (const k of keys) {
      if (current && typeof current === 'object' && k in current) {
        current = current[k];
      } else {
        current = null;
        break;
      }
    }
    if (typeof current === 'string') {
      return current;
    }
    // Fallback to fallback locale
    if (this.currentLocale !== this.config.fallbackLocale) {
      current = this.resources[this.config.fallbackLocale]?.[namespace];
      for (const k of keys) {
        if (current && typeof current === 'object' && k in current) {
          current = current[k];
        } else {
          current = null;
          break;
        }
      }
      if (typeof current === 'string') {
        return current;
      }
    }
    return null;
  }
  private interpolate(template: string, options: InterpolationOptions): string {
    const { prefix, suffix } = this.config.interpolation;
    return template.replace(
      new RegExp(`${this.escapeRegex(prefix)}([^${this.escapeRegex(suffix)}]+)${this.escapeRegex(suffix)}`, 'g'),
      (match, key) => {
        const value = options[key.trim()];
        return value !== undefined ? String(value) : match;
      }
    );
  }
  private getPluralKey(key: string, count: number): string {
    // Special case for zero - check if zero form exists first
    if (count === 0) {
      const zeroKey = `${key}.zero`;
      const zeroTranslation = this.getTranslation(zeroKey, 'common');
      if (zeroTranslation) {
        return zeroKey;
      }
    }
    const pluralRules = new Intl.PluralRules(this.currentLocale);
    const rule = pluralRules.select(count);
    // Map plural rules to our key format
    const ruleMap: Record<string, string> = {
      'zero': 'zero',
      'one': 'one',
      'two': 'two',
      'few': 'few',
      'many': 'many',
      'other': 'other',
    };
    const pluralSuffix = ruleMap[rule] || 'other';
    return `${key}.${pluralSuffix}`;
  }
  private escapeRegex(string: string): string {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
  private detectBrowserLocale(): string | null {
    if (typeof window === 'undefined' || !window.navigator) {
      return null;
    }
    const language = window.navigator.language;
    const shortLocale = language.split('-')[0];
    return this.config.locales.includes(shortLocale) ? shortLocale : null;
  }
  private getStoredLocale(): string | null {
    if (typeof window === 'undefined' || !window.localStorage) {
      return null;
    }
    try {
      return localStorage.getItem('i18n-locale');
    } catch {
      return null;
    }
  }
  private storeLocale(locale: string): void {
    if (typeof window === 'undefined' || !window.localStorage) {
      return;
    }
    try {
      localStorage.setItem('i18n-locale', locale);
    } catch (error) {
    }
  }
  private notifyListeners(locale: string): void {
    this.listeners.forEach(callback => {
      try {
        callback(locale);
      } catch (error) {
      }

  }
}
// Global instance
export const i18n = new I18nManager();
export default i18n;
