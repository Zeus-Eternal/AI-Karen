"use client";

import React from "react";
import { useLocale } from "../../providers/i18n-provider";
import { cn } from "../../lib/utils";

export interface DirectionalContentProps {
  children: React.ReactNode;
  className?: string;
  /** Override automatic direction detection */
  direction?: "ltr" | "rtl";
  /** Apply direction to document root */
  applyToDocument?: boolean;
}

// RTL languages
const RTL_LOCALES = new Set([
  "ar", // Arabic
  "arc", // Aramaic
  "dv", // Divehi
  "fa", // Persian
  "ha", // Hausa
  "he", // Hebrew
  "khw", // Khowar
  "ks", // Kashmiri
  "ku", // Kurdish
  "ps", // Pashto
  "ur", // Urdu
  "yi", // Yiddish
]);

/**
 * Determines if a locale uses right-to-left text direction
 */
export function isRTLLocale(locale: string): boolean {
  const baseLocale = locale.split("-")[0].toLowerCase();
  return RTL_LOCALES.has(baseLocale);
}

/**
 * Component that automatically handles text direction based on locale
 */
export function DirectionalContent({
  children,
  className,
  direction: overrideDirection,
  applyToDocument = false,
}: DirectionalContentProps) {
  const { locale } = useLocale();

  const textDirection = React.useMemo(() => {
    if (overrideDirection) {
      return overrideDirection;
    }
    return isRTLLocale(locale) ? "rtl" : "ltr";
  }, [locale, overrideDirection]);

  // Apply direction to document if requested
  React.useEffect(() => {
    if (applyToDocument && typeof document !== "undefined") {
      const prevDirection = document.documentElement.dir;
      document.documentElement.dir = textDirection;

      return () => {
        document.documentElement.dir = prevDirection;
      };
    }
  }, [textDirection, applyToDocument]);

  return (
    <div dir={textDirection} className={cn(className)}>
      {children}
    </div>
  );
}

export interface RTLAwareProps {
  children: React.ReactNode;
  /** Content to render in RTL mode */
  rtl?: React.ReactNode;
  /** Content to render in LTR mode */
  ltr?: React.ReactNode;
}

/**
 * Component that renders different content based on text direction
 */
export function RTLAware({ children, rtl, ltr }: RTLAwareProps) {
  const { locale } = useLocale();
  const isRTL = isRTLLocale(locale);

  if (isRTL && rtl) {
    return <>{rtl}</>;
  }

  if (!isRTL && ltr) {
    return <>{ltr}</>;
  }

  return <>{children}</>;
}

export interface FlipIconProps {
  /** Whether to flip the icon in RTL mode */
  flip?: boolean;
  children: React.ReactNode;
  className?: string;
}

/**
 * Flips icons horizontally for RTL languages (useful for arrows, chevrons, etc.)
 */
export function FlipIcon({ flip = true, children, className }: FlipIconProps) {
  const { locale } = useLocale();
  const isRTL = isRTLLocale(locale);
  const shouldFlip = flip && isRTL;

  return (
    <span
      className={cn(shouldFlip && "scale-x-[-1]", className)}
      style={{ display: "inline-block" }}
    >
      {children}
    </span>
  );
}

export default DirectionalContent;
