"use client";

import React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Button } from "../ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { Globe, Check } from "lucide-react";
import { useLocale, useI18n } from "../../providers/i18n-provider";
import { cn } from "../../lib/utils";

export interface LanguageSelectorProps {
  variant?: "select" | "dropdown" | "inline";
  showFlag?: boolean;
  showNativeName?: boolean;
  className?: string;
}

type LocaleInfo = {
  name: string;
  nativeName: string;
  flag: string;
};

const LOCALE_MAP: Record<string, LocaleInfo> = {
  en: { name: "English", nativeName: "English", flag: "🇺🇸" },
  es: { name: "Spanish", nativeName: "Español", flag: "🇪🇸" },
  fr: { name: "French", nativeName: "Français", flag: "🇫🇷" },
  de: { name: "German", nativeName: "Deutsch", flag: "🇩🇪" },
  ja: { name: "Japanese", nativeName: "日本語", flag: "🇯🇵" },
  zh: { name: "Chinese", nativeName: "中文", flag: "🇨🇳" },
  ar: { name: "Arabic", nativeName: "العربية", flag: "🇸🇦" },
  ru: { name: "Russian", nativeName: "Русский", flag: "🇷🇺" },
};

function getLocaleDisplayName(localeCode: string): LocaleInfo {
  return (
    LOCALE_MAP[localeCode] ?? {
      name: localeCode,
      nativeName: localeCode,
      flag: "🌐",
    }
  );
}

export function LanguageSelector({
  variant = "select",
  showFlag = true,
  showNativeName = true,
  className,
}: LanguageSelectorProps) {
  const { locale, locales, changeLocale } = useLocale();
  const { t } = useI18n();

  const currentLocaleInfo = getLocaleDisplayName(locale);

  /* Variant: Select (Shadcn Select) */
  if (variant === "select") {
    return (
      <div className={cn("w-full max-w-xs", className)}>
        <Select value={locale} onValueChange={changeLocale}>
          <SelectTrigger className="w-full" aria-label={t("settings.language")}>
            <SelectValue
              aria-label={t("settings.language")}
              placeholder={t("settings.language")}
            >
              <div className="flex items-center gap-2">
                {showFlag && (
                  <span className="text-sm md:text-base lg:text-lg">
                    {currentLocaleInfo.flag}
                  </span>
                )}
                <span>
                  {showNativeName
                    ? currentLocaleInfo.nativeName
                    : currentLocaleInfo.name}
                </span>
              </div>
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {locales.map((code) => {
              const info = getLocaleDisplayName(code);
              const isActive = locale === code;
              return (
                <SelectItem key={code} value={code}>
                  <div className="flex items-center gap-2">
                    {showFlag && (
                      <span className="text-sm md:text-base lg:text-lg">
                        {info.flag}
                      </span>
                    )}
                    <span>{showNativeName ? info.nativeName : info.name}</span>
                    {isActive && (
                      <Check className="h-4 w-4 ml-auto text-primary" />
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

  /* Variant: Inline (pill buttons) */
  if (variant === "inline") {
    return (
      <div className={cn("flex flex-wrap items-center gap-1", className)}>
        {locales.map((code) => {
          const info = getLocaleDisplayName(code);
          const isActive = locale === code;
          return (
            <Button
              key={code}
              variant={isActive ? "default" : "ghost"}
              size="sm"
              onClick={() => changeLocale(code)}
              className={cn(
                "h-8 px-2 text-xs",
                isActive && "bg-primary text-primary-foreground"
              )}
              aria-label={`Switch to ${info.name}`}
              aria-pressed={isActive}
              title={showNativeName ? info.nativeName : info.name}
            >
              {showFlag && <span className="mr-1">{info.flag}</span>}
              <span className="uppercase font-medium">{code}</span>
            </Button>
          );
        })}
      </div>
    );
  }

  /* Default variant: Dropdown (Shadcn DropdownMenu) */
  return (
    <div className={cn("relative", className)}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2"
            aria-label={t("settings.language")}
          >
            <Globe className="h-4 w-4 mr-1" />
            {showFlag && <span className="mr-1">{currentLocaleInfo.flag}</span>}
            <span className="uppercase text-xs font-medium sm:text-sm md:text-base">
              {locale}
            </span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-44">
          <DropdownMenuLabel>{t("settings.language")}</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {locales.map((code) => {
            const info = getLocaleDisplayName(code);
            const isActive = locale === code;
            return (
              <DropdownMenuItem
                key={code}
                onClick={() => changeLocale(code)}
                aria-checked={isActive}
                role="menuitemradio"
              >
                <div className="flex items-center gap-2 w-full">
                  {showFlag && <span>{info.flag}</span>}
                  <span className="truncate">
                    {showNativeName ? info.nativeName : info.name}
                  </span>
                  {isActive && (
                    <Check className="h-4 w-4 ml-auto text-primary" />
                  )}
                </div>
              </DropdownMenuItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

export default LanguageSelector;
