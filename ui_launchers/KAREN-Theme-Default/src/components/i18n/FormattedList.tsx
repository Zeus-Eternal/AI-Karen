"use client";

import React from "react";
import { useLocale } from "../../providers/i18n-hooks";

export interface FormattedListProps {
  /** Array of items to format */
  items: string[];
  /** List type: conjunction (and), disjunction (or), or unit */
  type?: "conjunction" | "disjunction" | "unit";
  /** Style: long, short, or narrow */
  style?: "long" | "short" | "narrow";
  className?: string;
}

/**
 * Formats a list of items according to locale conventions
 * Uses Intl.ListFormat for proper formatting
 *
 * Examples:
 * - en: "apples, oranges, and bananas"
 * - es: "manzanas, naranjas y plátanos"
 * - ja: "りんご、オレンジ、バナナ"
 */
export function FormattedList({
  items,
  type = "conjunction",
  style = "long",
  className,
}: FormattedListProps) {
  const { locale } = useLocale();

  const formattedList = React.useMemo(() => {
    if (!items || items.length === 0) {
      return "";
    }

    try {
      const formatter = new Intl.ListFormat(locale, {
        style,
        type,
      });
      return formatter.format(items);
    } catch (error) {
      console.error("Error formatting list:", error);
      // Fallback to simple join
      return items.join(", ");
    }
  }, [items, locale, style, type]);

  return <span className={className}>{formattedList}</span>;
}

export interface FormattedListItemsProps<T> {
  /** Array of items to format */
  items: T[];
  /** Function to extract display string from item */
  getLabel: (item: T) => string;
  /** List type: conjunction (and), disjunction (or), or unit */
  type?: "conjunction" | "disjunction" | "unit";
  /** Style: long, short, or narrow */
  style?: "long" | "short" | "narrow";
  className?: string;
}

/**
 * Generic version of FormattedList that accepts any item type
 */
export function FormattedListItems<T>({
  items,
  getLabel,
  type = "conjunction",
  style = "long",
  className,
}: FormattedListItemsProps<T>) {
  const labels = React.useMemo(() => items.map(getLabel), [items, getLabel]);

  return <FormattedList items={labels} type={type} style={style} className={className} />;
}

export interface FormattedCompactListProps {
  /** Array of items to display */
  items: string[];
  /** Maximum number of items to show before truncating */
  maxVisible?: number;
  /** Text to show for remaining items (defaults to "+N more") */
  renderRemaining?: (count: number) => React.ReactNode;
  className?: string;
}

/**
 * Displays a list with truncation for long lists
 * Example: "Apple, Orange, Banana +3 more"
 */
export function FormattedCompactList({
  items,
  maxVisible = 3,
  renderRemaining,
  className,
}: FormattedCompactListProps) {
  const { locale } = useLocale();

  const visibleItems = items.slice(0, maxVisible);
  const remainingCount = items.length - maxVisible;

  const formattedVisible = React.useMemo(() => {
    if (visibleItems.length === 0) return "";

    try {
      const formatter = new Intl.ListFormat(locale, {
        style: "long",
        type: "conjunction",
      });
      return formatter.format(visibleItems);
    } catch (error) {
      return visibleItems.join(", ");
    }
  }, [visibleItems, locale]);

  const remainingText = React.useMemo(() => {
    if (remainingCount <= 0) return null;

    if (renderRemaining) {
      return renderRemaining(remainingCount);
    }

    // Default format using Intl.NumberFormat
    try {
      const numberFormatter = new Intl.NumberFormat(locale);
      return ` +${numberFormatter.format(remainingCount)} more`;
    } catch (error) {
      return ` +${remainingCount} more`;
    }
  }, [remainingCount, locale, renderRemaining]);

  return (
    <span className={className}>
      {formattedVisible}
      {remainingText && (
        <span className="text-muted-foreground">{remainingText}</span>
      )}
    </span>
  );
}

export default FormattedList;
