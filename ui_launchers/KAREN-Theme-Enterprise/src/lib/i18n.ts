// Re-export the i18n instance and types from the i18n directory
export { i18n, I18nManager } from './i18n/index';
export { defaultResources } from './i18n/resources';

// Import and re-export types to avoid circular import issues
import type {
  I18nConfig,
  TranslationResource,
  TranslationResources,
  FormatOptions,
  PluralOptions,
  InterpolationOptions,
} from './i18n/index';

export type {
  I18nConfig,
  TranslationResource,
  TranslationResources,
  FormatOptions,
  PluralOptions,
  InterpolationOptions,
};