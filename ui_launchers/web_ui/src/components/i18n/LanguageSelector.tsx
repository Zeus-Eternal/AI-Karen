"use client";

import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Button } from '../ui/button';
import { Globe, Check } from 'lucide-react';
import { useLocale, useI18n } from '../../providers/i18n-provider';
import { cn } from '../../lib/utils';

interface LanguageSelectorProps {
  variant?: 'select' | 'dropdown' | 'inline';
  showFlag?: boolean;
  showNativeName?: boolean;
  className?: string;
}

export function LanguageSelector({
  variant = 'select',
  showFlag = true,
  showNativeName = true,
  className,
}: LanguageSelectorProps) {
  const { locale, locales, changeLocale } = useLocale();
  const { t } = useI18n();

  const getLocaleDisplayName = (localeCode: string) => {
    const localeNames: Record<string, { name: string; nativeName: string; flag: string }> = {
      en: { name: 'English', nativeName: 'English', flag: '🇺🇸' },
      es: { name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
      fr: { name: 'French', nativeName: 'Français', flag: '🇫🇷' },
      de: { name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
      ja: { name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
      zh: { name: 'Chinese', nativeName: '中文', flag: '🇨🇳' },
      ar: { name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦' },
      ru: { name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
    };

    return localeNames[localeCode] || { name: localeCode, nativeName: localeCode, flag: '🌐' };
  };

  const currentLocaleInfo = getLocaleDisplayName(locale);

  if (variant === 'select') {
    return (
      <div className={cn('w-full max-w-xs', className)}>
        <select value={locale} onValueChange={changeLocale} aria-label="Select option">
          <selectTrigger className="w-full" aria-label="Select option">
            <selectValue aria-label="Select option">
              <div className="flex items-center space-x-2">
                {showFlag && <span className="text-sm md:text-base lg:text-lg">{currentLocaleInfo.flag}</span>}
                <span>
                  {showNativeName ? currentLocaleInfo.nativeName : currentLocaleInfo.name}
                </span>
              </div>
            </SelectValue>
          </SelectTrigger>
          <selectContent aria-label="Select option">
            {locales.map((localeCode) => {
              const localeInfo = getLocaleDisplayName(localeCode);
              return (
                <selectItem key={localeCode} value={localeCode} aria-label="Select option">
                  <div className="flex items-center space-x-2">
                    {showFlag && <span className="text-sm md:text-base lg:text-lg">{localeInfo.flag}</span>}
                    <span>
                      {showNativeName ? localeInfo.nativeName : localeInfo.name}
                    </span>
                    {locale === localeCode && (
                      <Check className="h-4 w-4 ml-auto text-primary " />
                    )}
                  </div>
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
      </div>
    );
  }

  if (variant === 'inline') {
    return (
      <div className={cn('flex items-center space-x-1', className)}>
        {locales.map((localeCode) => {
          const localeInfo = getLocaleDisplayName(localeCode);
          const isActive = locale === localeCode;
          
          return (
            <button
              key={localeCode}
              variant={isActive ? 'default' : 'ghost'}
              size="sm"
              onClick={() => changeLocale(localeCode)}
              className={cn(
                'h-8 px-2 text-xs',
                isActive && 'bg-primary text-primary-foreground'
              )}
              aria-label={`Switch to ${localeInfo.name}`}
              aria-pressed={isActive}
            >
              {showFlag && <span className="mr-1">{localeInfo.flag}</span>}
              <span className="uppercase font-medium">
                {localeCode}
              </span>
            </Button>
          );
        })}
      </div>
    );
  }

  // Default dropdown variant
  return (
    <div className={cn('relative', className)}>
      <Button
        variant="ghost"
        size="sm"
        className="h-8 px-2"
        aria-label={t('settings.language')}
      >
        <Globe className="h-4 w-4 mr-1 " />
        {showFlag && <span className="mr-1">{currentLocaleInfo.flag}</span>}
        <span className="uppercase text-xs font-medium sm:text-sm md:text-base">
          {locale}
        </span>
      </Button>
    </div>
  );
}

export default LanguageSelector;