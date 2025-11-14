import { createContext } from 'react';
import { type FormatOptions, type InterpolationOptions, type PluralOptions } from '../lib/i18n';

type TranslationOptions = InterpolationOptions & Partial<PluralOptions> & { ns?: string };

export interface I18nContextValue {
  // Current locale
  locale: string;
  // Available locales
  locales: string[];
  // Locale info
  localeInfo: {
    code: string;
    name: string;
    nativeName: string;
    direction: 'ltr' | 'rtl';
  };
  // Translation function
  t: (key: string, options?: TranslationOptions) => string;
  // Formatting functions
  formatNumber: (value: number, options?: FormatOptions) => string;
  formatDate: (date: Date | string | number, options?: FormatOptions) => string;
  formatRelativeTime: (value: number, unit: Intl.RelativeTimeFormatUnit, options?: FormatOptions) => string;
  // Locale management
  changeLocale: (locale: string) => void;
  // Loading state
  isLoading: boolean;
}

export const I18nContext = createContext<I18nContextValue | undefined>(undefined);
