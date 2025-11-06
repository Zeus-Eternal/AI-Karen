/**
 * Internationalization Components
 *
 * Components for i18n support including language selection,
 * localized text, and formatted content.
 */

// Providers
export {
  default as I18nProvider,
  useI18n,
  useTranslation,
  useLocale,
  useFormatting,
} from "../../providers/i18n-provider";

// Components
export { default as LanguageSelector } from "./LanguageSelector";
export type { LanguageSelectorProps } from "./LanguageSelector";

export { default as LocalizedText, T, Plural } from "./LocalizedText";
export type { LocalizedTextProps } from "./LocalizedText";

export {
  FormattedNumber,
  FormattedDate,
  FormattedRelativeTime,
  TimeAgo,
  FormattedCurrency,
  FormattedPercent,
  FormattedFileSize,
} from "./FormattedText";
export type {
  FormattedNumberProps,
  FormattedDateProps,
  FormattedRelativeTimeProps,
  TimeAgoProps,
  FormattedCurrencyProps,
  FormattedPercentProps,
  FormattedFileSizeProps,
} from "./FormattedText";

// Core i18n
export {
  i18n,
  type I18nManager,
  type I18nConfig,
  type TranslationResources,
} from "../../lib/i18n";
export { defaultResources } from "../../lib/i18n/resources";
