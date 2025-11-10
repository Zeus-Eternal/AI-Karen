"use client";

import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { i18n, type FormatOptions, type InterpolationOptions, type PluralOptions } from '../lib/i18n';
import { defaultResources } from '../lib/i18n/resources';
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
  t: (key: string, options?: InterpolationOptions & PluralOptions & { ns?: string }) => string;
  // Formatting functions
  formatNumber: (value: number, options?: FormatOptions) => string;
  formatDate: (date: Date | string | number, options?: FormatOptions) => string;
  formatRelativeTime: (value: number, unit: Intl.RelativeTimeFormatUnit, options?: FormatOptions) => string;
  // Locale management
  changeLocale: (locale: string) => void;
  // Loading state
  isLoading: boolean;
}
const I18nContext = createContext<I18nContextValue | undefined>(undefined);
export interface I18nProviderProps {
  children: React.ReactNode;
  defaultLocale?: string;
  locales?: string[];
}
export function I18nProvider({
  children,
  defaultLocale = 'en',
  locales = ['en', 'es', 'fr', 'de'],
}: I18nProviderProps) {
  const [locale, setLocale] = useState(defaultLocale);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    let active = true;
    let unsubscribe: (() => void) | undefined;

    const initI18n = async () => {
      try {
        i18n.configure({
          defaultLocale,
          locales,
        });

        await i18n.init(defaultResources);

        if (!active) {
          return;
        }

        setLocale(i18n.getCurrentLocale());
        unsubscribe = i18n.onLocaleChange((newLocale) => {
          if (!active) {
            return;
          }

          setLocale(newLocale);

          if (typeof document !== 'undefined') {
            document.documentElement.lang = newLocale;
            document.documentElement.dir = i18n.getTextDirection();
          }
        });
      } catch (error) {
        console.error('[I18nProvider] Failed to initialize i18n:', error);
      } finally {
        if (active) {
          setIsInitialized(true);
          setIsLoading(false);
        }
      }
    };

    setIsLoading(true);
    setIsInitialized(false);
    void initI18n();

    return () => {
      active = false;
      unsubscribe?.();
    };
  }, [defaultLocale, locales]);

  useEffect(() => {
    if (!isInitialized) {
      return;
    }

    if (typeof document !== 'undefined') {
      document.documentElement.lang = locale;
      document.documentElement.dir = i18n.getTextDirection();
    }
  }, [locale, isInitialized]);

  const contextValue: I18nContextValue = useMemo(() => ({
    locale,
    locales: i18n.getAvailableLocales(),
    localeInfo: i18n.getLocaleInfo(),
    t: i18n.t.bind(i18n),
    formatNumber: i18n.formatNumber.bind(i18n),
    formatDate: i18n.formatDate.bind(i18n),
    formatRelativeTime: i18n.formatRelativeTime.bind(i18n),
    changeLocale: i18n.changeLocale.bind(i18n),
    isLoading,
  }), [locale, isLoading]);
  return (
    <I18nContext.Provider value={contextValue}>
      {children}
    </I18nContext.Provider>
  );
}
export function useI18n() {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}
// Convenience hooks
export function useTranslation(namespace?: string) {
  const { t } = useI18n();
  const translate = (key: string, options?: InterpolationOptions & PluralOptions) => {
    const enrichedOptions =
      namespace !== undefined
        ? ({ ...(options ?? {}), ns: namespace } as InterpolationOptions &
            PluralOptions & { ns: string })
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
export default I18nProvider;
