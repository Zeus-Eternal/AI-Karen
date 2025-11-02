'use client';


import { useFormatting, useLocale } from '../../providers/i18n-provider';
import type { FormatOptions } from '../../lib/i18n';

interface FormattedNumberProps {
  value: number;
  style?: 'decimal' | 'currency' | 'percent';
  currency?: string;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  className?: string;
}

export function FormattedNumber({
  value,
  style = 'decimal',
  currency,
  minimumFractionDigits,
  maximumFractionDigits,
  className,
}: FormattedNumberProps) {
  const { formatNumber } = useFormatting();
  
  const options: FormatOptions = {
    numberStyle: style,
    currency,
  };
  
  // Add fraction digits to Intl options if provided
  const intlOptions: Intl.NumberFormatOptions = {};
  if (minimumFractionDigits !== undefined) {
    intlOptions.minimumFractionDigits = minimumFractionDigits;
  }
  if (maximumFractionDigits !== undefined) {
    intlOptions.maximumFractionDigits = maximumFractionDigits;
  }
  
  const formattedValue = formatNumber(value, options);
  
  return <span className={className}>{formattedValue}</span>;
}

interface FormattedDateProps {
  value: Date;
  dateStyle?: 'full' | 'long' | 'medium' | 'short';
  timeStyle?: 'full' | 'long' | 'medium' | 'short';
  timeZone?: string;
  className?: string;
}

export function FormattedDate({
  value,
  dateStyle,
  timeStyle,
  timeZone,
  className,
}: FormattedDateProps) {
  const { formatDate } = useFormatting();
  
  const options: FormatOptions = {
    dateStyle,
    timeStyle,
    timeZone,
  };
  
  const formattedValue = formatDate(value, options);
  
  return <span className={className}>{formattedValue}</span>;
}

interface FormattedRelativeTimeProps {
  value: number;
  unit: Intl.RelativeTimeFormatUnit;
  numeric?: 'always' | 'auto';
  className?: string;
}

export function FormattedRelativeTime({
  value,
  unit,
  numeric = 'auto',
  className,
}: FormattedRelativeTimeProps) {
  const { formatRelativeTime } = useFormatting();
  
  const formattedValue = formatRelativeTime(value, unit);
  
  return <span className={className}>{formattedValue}</span>;
}

interface FormattedCurrencyProps {
  value: number;
  currency: string;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  className?: string;
}

export function FormattedCurrency({
  value,
  currency,
  minimumFractionDigits = 2,
  maximumFractionDigits = 2,
  className,
}: FormattedCurrencyProps) {
  return (
    <FormattedNumber
      value={value}
      style="currency"
      currency={currency}
      minimumFractionDigits={minimumFractionDigits}
      maximumFractionDigits={maximumFractionDigits}
      className={className}
    />
  );
}

interface FormattedPercentProps {
  value: number;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  className?: string;
}

export function FormattedPercent({
  value,
  minimumFractionDigits = 0,
  maximumFractionDigits = 2,
  className,
}: FormattedPercentProps) {
  return (
    <FormattedNumber
      value={value}
      style="percent"
      minimumFractionDigits={minimumFractionDigits}
      maximumFractionDigits={maximumFractionDigits}
      className={className}
    />
  );
}

// Utility component for time ago formatting
interface TimeAgoProps {
  date: Date;
  className?: string;
}

export function TimeAgo({ date, className }: TimeAgoProps) {
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  let value: number;
  let unit: Intl.RelativeTimeFormatUnit;
  
  if (Math.abs(diffInSeconds) < 60) {
    value = -diffInSeconds;
    unit = 'second';
  } else if (Math.abs(diffInSeconds) < 3600) {
    value = -Math.floor(diffInSeconds / 60);
    unit = 'minute';
  } else if (Math.abs(diffInSeconds) < 86400) {
    value = -Math.floor(diffInSeconds / 3600);
    unit = 'hour';
  } else if (Math.abs(diffInSeconds) < 2592000) {
    value = -Math.floor(diffInSeconds / 86400);
    unit = 'day';
  } else if (Math.abs(diffInSeconds) < 31536000) {
    value = -Math.floor(diffInSeconds / 2592000);
    unit = 'month';
  } else {
    value = -Math.floor(diffInSeconds / 31536000);
    unit = 'year';
  }
  
  return (
    <FormattedRelativeTime
      value={value}
      unit={unit}
      className={className}
    />
  );
}

// Utility component for file size formatting
interface FormattedFileSizeProps {
  bytes: number;
  binary?: boolean;
  className?: string;
}

export function FormattedFileSize({
  bytes,
  binary = false,
  className,
}: FormattedFileSizeProps) {
  const { locale } = useLocale();
  
  const units = binary
    ? ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
    : ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  
  const base = binary ? 1024 : 1000;
  
  if (bytes === 0) {
    return <span className={className}>0 B</span>;
  }
  
  const exponent = Math.floor(Math.log(Math.abs(bytes)) / Math.log(base));
  const value = bytes / Math.pow(base, exponent);
  const unit = units[Math.min(exponent, units.length - 1)];
  
  const formatter = new Intl.NumberFormat(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: exponent === 0 ? 0 : 1,
  });
  
  return (
    <span className={className}>
      {formatter.format(value)} {unit}
    </span>
  );
}