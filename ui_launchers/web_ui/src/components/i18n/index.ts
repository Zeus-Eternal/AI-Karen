/**
 * Internationalization Components
 * 
 * Components for i18n support including language selection,
 * localized text, and formatted content.
 */

// Providers
import { export { default as I18nProvider, useI18n, useTranslation, useLocale, useFormatting } from '../../providers/i18n-provider';

// Components
import { export { default as LanguageSelector } from './LanguageSelector';
import { export { default as LocalizedText, T, Plural } from './LocalizedText';
export {
import { } from './FormattedText';

// Core i18n
import { export { i18n, type I18nManager, type I18nConfig, type TranslationResources } from '../../lib/i18n';
import { export { defaultResources } from '../../lib/i18n/resources';