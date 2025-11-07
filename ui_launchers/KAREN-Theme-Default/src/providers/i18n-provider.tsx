"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';
import { i18n, type I18nManager, type FormatOptions, type InterpolationOptions, type PluralOptions } from '../lib/i18n';
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
  formatDate: (date: Date, options?: FormatOptions) => string;
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
  const [mounted, setMounted] = useState(false);
  // Initialize i18n system
  useEffect(() => {
    const initI18n = async () => {
      try {
        // Configure i18n with provided options
        i18n.config = {
          ...i18n.config,
          defaultLocale,
          locales,
        };
        // Initialize with default resources
        await i18n.init(defaultResources);
        // Set initial locale
        setLocale(i18n.getCurrentLocale());
        // Listen for locale changes
        const unsubscribe = i18n.onLocaleChange((newLocale) => {
          setLocale(newLocale);
          // Update document attributes
          if (typeof document !== 'undefined') {
            document.documentElement.lang = newLocale;
            document.documentElement.dir = i18n.getTextDirection();
          }
        });
        setIsLoading(false);
        setMounted(true);
        return unsubscribe;
      } catch (error) {
        console.error('[I18nProvider] Failed to initialize i18n:', error);
        setIsLoading(false);
        setMounted(true);
        // Return a no-op unsubscribe function
        return () => {};
      }
    };
    const cleanup = initI18n();
    return () => {
      cleanup?.then(unsubscribe => unsubscribe?.());
    };
  }, [defaultLocale, locales]);
  // Update document attributes when locale changes
  useEffect(() => {
    if (!mounted) return;
    if (typeof document !== 'undefined') {
      document.documentElement.lang = locale;
      document.documentElement.dir = i18n.getTextDirection();
    }
  }, [locale, mounted]);
  const contextValue: I18nContextValue = {
    locale,
    locales: i18n.getAvailableLocales(),
    localeInfo: i18n.getLocaleInfo(),
    t: i18n.t.bind(i18n),
    formatNumber: i18n.formatNumber.bind(i18n),
    formatDate: i18n.formatDate.bind(i18n),
    formatRelativeTime: i18n.formatRelativeTime.bind(i18n),
    changeLocale: i18n.changeLocale.bind(i18n),
    isLoading,
  };
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
    return t(key, { ...options, ns: namespace });
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
