"use client";

import React from "react";
import { useLocale } from "../../providers/i18n-hooks";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Globe, Calendar, DollarSign, Clock } from "lucide-react";
import { isRTLLocale } from "./directional-utils";

export interface LocaleMetadataProps {
  /** Show as compact badge instead of card */
  compact?: boolean;
  /** Show specific metadata fields */
  show?: {
    language?: boolean;
    region?: boolean;
    direction?: boolean;
    calendar?: boolean;
    currency?: boolean;
    timezone?: boolean;
  };
  className?: string;
}

/**
 * Display metadata about the current locale
 */
export function LocaleMetadata({
  compact = false,
  show = {
    language: true,
    region: true,
    direction: true,
    calendar: false,
    currency: false,
    timezone: false,
  },
  className,
}: LocaleMetadataProps) {
  const { locale } = useLocale();

  const metadata = React.useMemo(() => {
    try {
      const parts = locale.split("-");
      const languageCode = parts[0];
      const regionCode = parts[1] ?? null;

      const displayNames =
        typeof Intl.DisplayNames !== "undefined"
          ? new Intl.DisplayNames([locale], { type: "language" })
          : null;
      const regionDisplayNames =
        regionCode && typeof Intl.DisplayNames !== "undefined"
          ? new Intl.DisplayNames([locale], { type: "region" })
          : null;

      const direction = isRTLLocale(locale) ? "rtl" : "ltr";

      // Get calendar system (if available)
      let calendar = "gregory"; // default
      try {
        const dateFormat = new Intl.DateTimeFormat(locale);
        calendar = dateFormat.resolvedOptions().calendar;
      } catch {
        // Use default
      }

      // Get currency (if available from locale)
      let currency = "USD"; // default fallback
      try {
        const numberFormat = new Intl.NumberFormat(locale, {
          style: "currency",
          currency: "USD",
        });
        const resolvedCurrency = numberFormat.resolvedOptions().currency;
        if (resolvedCurrency) {
          currency = resolvedCurrency;
        }
      } catch {
        // Use default
      }

      // Get timezone
      const timezone =
        typeof Intl !== "undefined"
          ? new Intl.DateTimeFormat().resolvedOptions().timeZone
          : "UTC";

      return {
        locale,
        languageCode,
        regionCode,
        languageName: displayNames?.of(languageCode) || languageCode,
        regionName:
        regionCode && regionDisplayNames ? regionDisplayNames.of(regionCode) : null,
        direction,
        calendar,
        currency,
        timezone,
      };
    } catch (error) {
      console.error("Error getting locale metadata:", error);
      return {
        locale,
        languageCode: locale,
        regionCode: null,
        languageName: locale,
        regionName: null,
        direction: "ltr" as const,
        calendar: "gregory",
        currency: "USD",
        timezone: "UTC",
      };
    }
  }, [locale]);

  if (compact) {
    return (
      <div className={className}>
        <Badge variant="outline" className="gap-1">
          <Globe className="h-3 w-3" />
          <span>{metadata.languageName}</span>
          {metadata.regionName && (
            <span className="text-muted-foreground">({metadata.regionName})</span>
          )}
        </Badge>
      </div>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <Globe className="h-4 w-4" />
          Locale Information
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {show.language && (
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Language:</span>
            <span className="font-medium">
              {metadata.languageName} ({metadata.languageCode})
            </span>
          </div>
        )}

        {show.region && metadata.regionName && (
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Region:</span>
            <span className="font-medium">
              {metadata.regionName} ({metadata.regionCode})
            </span>
          </div>
        )}

        {show.direction && (
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Text Direction:</span>
            <Badge variant="secondary" className="uppercase">
              {metadata.direction}
            </Badge>
          </div>
        )}

        {show.calendar && (
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              Calendar:
            </span>
            <span className="font-medium capitalize">{metadata.calendar}</span>
          </div>
        )}

        {show.currency && (
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground flex items-center gap-1">
              <DollarSign className="h-3 w-3" />
              Currency:
            </span>
            <span className="font-medium">{metadata.currency}</span>
          </div>
        )}

        {show.timezone && (
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Timezone:
            </span>
            <span className="font-medium text-xs">{metadata.timezone}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export interface LocaleBadgeProps {
  showFlag?: boolean;
  className?: string;
}

/**
 * Simple badge showing current locale
 */
export function LocaleBadge({ showFlag = true, className }: LocaleBadgeProps) {
  const { locale } = useLocale();

  const flag = React.useMemo(() => {
    const flagMap: Record<string, string> = {
      en: "🇺🇸",
      es: "🇪🇸",
      fr: "🇫🇷",
      de: "🇩🇪",
      ja: "🇯🇵",
      zh: "🇨🇳",
      ar: "🇸🇦",
      ru: "🇷🇺",
    };

    const baseLocale = locale.split("-")[0];
    return flagMap[baseLocale] || "🌐";
  }, [locale]);

  return (
    <Badge variant="outline" className={className}>
      {showFlag && <span className="mr-1">{flag}</span>}
      <span className="uppercase font-mono text-xs">{locale}</span>
    </Badge>
  );
}

export default LocaleMetadata;
