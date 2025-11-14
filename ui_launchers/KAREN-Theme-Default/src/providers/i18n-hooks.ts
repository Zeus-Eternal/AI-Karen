"use client";

import { useContext } from 'react';
import { I18nContext, type I18nContextValue } from './i18n-context';
import { type InterpolationOptions, type PluralOptions } from '../lib/i18n';

export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}

// Convenience hooks
export function useTranslation(namespace?: string) {
  const { t } = useI18n();
  const translate = (key: string, options?: InterpolationOptions & Partial<PluralOptions>) => {
    const enrichedOptions =
      namespace !== undefined
        ? ({
            ...(options ?? {}),
            ns: namespace,
          } as InterpolationOptions & Partial<PluralOptions> & { ns: string })
        : options;
    return t(key, enrichedOptions);
  };
  return { t: translate };
}

export function useLocale() {
  const { locale, locales, localeInfo, changeLocale } = useI18n();
  return {
    locale,
    locales,
    localeInfo,
    changeLocale,
  };
}

export function useFormatting() {
  const { formatNumber, formatDate, formatRelativeTime } = useI18n();
  return {
    formatNumber,
    formatDate,
    formatRelativeTime,
  };
}
