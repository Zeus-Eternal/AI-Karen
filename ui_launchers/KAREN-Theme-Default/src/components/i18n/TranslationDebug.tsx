"use client";

import React from "react";
import { useI18n, useLocale } from "../../providers/i18n-hooks";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { AlertCircle, CheckCircle, Copy, Eye, EyeOff } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export interface TranslationDebugProps {
  /** Only show in development mode */
  devOnly?: boolean;
  /** Show missing translations */
  showMissing?: boolean;
  /** Show all available translations */
  showAll?: boolean;
  /** Specific namespace to debug */
  namespace?: string;
  className?: string;
}

/**
 * Debug component to visualize translation status
 * Useful during development to identify missing translations
 */
export function TranslationDebug({
  devOnly = true,
  showMissing = true,
  showAll = false,
  namespace,
  className,
}: TranslationDebugProps) {
  const { t } = useI18n();
  const { locale } = useLocale();
  const { toast } = useToast();
  const [isVisible, setIsVisible] = React.useState(false);

  // Only render in development if devOnly is true
  if (devOnly && process.env.NODE_ENV === "production") {
    return null;
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied",
      description: "Translation key copied to clipboard",
    });
  };

  return (
    <div className={className}>
      <Button
        size="sm"
        variant="outline"
        onClick={() => setIsVisible(!isVisible)}
        className="fixed bottom-4 right-4 z-50"
      >
        {isVisible ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
        i18n Debug
      </Button>

      {isVisible && (
        <Card className="fixed bottom-16 right-4 z-50 w-96 max-h-96 overflow-auto shadow-lg">
          <CardHeader>
            <CardTitle className="text-sm flex items-center justify-between">
              <span>Translation Debug</span>
              <Badge variant="secondary">{locale}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Current Locale:</span>
                <span className="font-mono font-medium">{locale}</span>
              </div>

              {namespace && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Namespace:</span>
                  <span className="font-mono font-medium">{namespace}</span>
                </div>
              )}

              <div className="pt-2">
                <p className="text-muted-foreground mb-2">Test Translation Keys:</p>
                <div className="space-y-1">
                  {["common.welcome", "common.save", "common.cancel", "errors.notFound"].map(
                    (key) => {
                      const translated = t(key);
                      const isMissing = translated === key;

                      return (
                        <div
                          key={key}
                          className="flex items-center justify-between gap-2 p-2 bg-muted/50 rounded"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="font-mono text-xs truncate">{key}</div>
                            <div className="text-xs text-muted-foreground truncate">
                              {translated}
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            {isMissing ? (
                              <AlertCircle className="h-3 w-3 text-destructive" />
                            ) : (
                              <CheckCircle className="h-3 w-3 text-green-500" />
                            )}
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 w-6 p-0"
                              onClick={() => copyToClipboard(key)}
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      );
                    }
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export interface TranslationKeyDisplayProps {
  /** Translation key being used */
  i18nKey: string;
  /** Show the key alongside the translated text */
  showKey?: boolean;
  /** Highlight if translation is missing */
  highlightMissing?: boolean;
  children: React.ReactNode;
  className?: string;
}

/**
 * Wrapper component that displays translation keys in development
 */
export function TranslationKeyDisplay({
  i18nKey,
  showKey = false,
  highlightMissing = true,
  children,
  className,
}: TranslationKeyDisplayProps) {
  const { t } = useI18n();
  const translated = t(i18nKey);
  const isMissing = translated === i18nKey;

  const isDev = process.env.NODE_ENV === "development";

  if (!isDev || !showKey) {
    return <span className={className}>{children}</span>;
  }

  return (
    <span
      className={`${className} ${
        isMissing && highlightMissing
          ? "border-b-2 border-dashed border-destructive"
          : ""
      }`}
      title={`Key: ${i18nKey}${isMissing ? " (MISSING)" : ""}`}
    >
      {children}
    </span>
  );
}

export interface MissingTranslationIndicatorProps {
  /** Translation key */
  i18nKey: string;
  /** Custom fallback text */
  fallback?: string;
  className?: string;
}

/**
 * Shows a warning indicator for missing translations
 */
export function MissingTranslationIndicator({
  i18nKey,
  fallback,
  className,
}: MissingTranslationIndicatorProps) {
  const { t } = useI18n();
  const translated = t(i18nKey);
  const isMissing = translated === i18nKey;

  if (!isMissing) {
    return <span className={className}>{translated}</span>;
  }

  const displayText = fallback || i18nKey;

  return (
    <span
      className={`${className} inline-flex items-center gap-1 bg-destructive/10 px-1 rounded`}
      title={`Missing translation: ${i18nKey}`}
    >
      <AlertCircle className="h-3 w-3 text-destructive" />
      <span>{displayText}</span>
    </span>
  );
}

export default TranslationDebug;
