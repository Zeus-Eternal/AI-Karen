"use client";

import * as React from 'react';
import { useI18n } from '../../providers/i18n-provider';
import type { InterpolationOptions, PluralOptions } from '../../lib/i18n';

export interface LocalizedTextProps {
  /** Translation key */
  i18nKey: string;

  /** Namespace for the translation */
  ns?: string;

  /** Interpolation values */
  values?: InterpolationOptions;

  /** Plural count */
  count?: number;

  /** Fallback text if translation is missing */
  fallback?: string;

  /** HTML element to render */
  as?: keyof JSX.IntrinsicElements;

  /** Additional props to pass to the element */
  [key: string]: any;
}

export function LocalizedText({
  i18nKey,
  ns,
  values = {},
  count,
  fallback,
  as: Component = 'span',
  ...props
}: LocalizedTextProps) {
  const { t } = useI18n();
  
  // Build translation options dynamically to match the expected type
  const translationOptions: any = {
    ...values,
  };
  
  if (ns) {
    translationOptions.ns = ns;
  }
  
  if (typeof count === 'number') {
    translationOptions.count = count;
  }
  
  const translatedText = t(i18nKey, translationOptions);
  const displayText = translatedText === i18nKey && fallback ? fallback : translatedText;
  
  return React.createElement(Component, props, displayText);
}

// Convenience components for common use cases
export function T({ children, ...props }: Omit<LocalizedTextProps, 'i18nKey'> & { children: string }) {
  return <LocalizedText i18nKey={children} {...props} />;
}

export function Plural({
  i18nKey,
  count,
  ...props
}: Omit<LocalizedTextProps, 'count'> & { count: number }) {
  return <LocalizedText i18nKey={i18nKey} count={count} {...props} />;
}

export default LocalizedText;