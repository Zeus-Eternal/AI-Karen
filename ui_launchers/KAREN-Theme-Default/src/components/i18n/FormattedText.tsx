"use client";

import React from "react";
import { useFormatting, useLocale } from "../../providers/i18n-hooks";
import type { FormatOptions } from "../../lib/i18n";

/* ===========================
   Number / Currency / Percent
   =========================== */

export interface FormattedNumberProps {
  value: number;
  style?: "decimal" | "currency" | "percent";
  currency?: string;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  className?: string;
}

export const FormattedNumber: React.FC<FormattedNumberProps> = React.memo(
  ({
    value,
    style = "decimal",
    currency,
    minimumFractionDigits,
    maximumFractionDigits,
    className,
  }) => {
    const { formatNumber } = useFormatting();

    // Merge Intl options into your FormatOptions so your provider can pass them through.
    const options: FormatOptions = {
      numberStyle: style,
      currency,
      minimumFractionDigits,
      maximumFractionDigits,
    };

    const formattedValue = React.useMemo(
      () => formatNumber(value, options),
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [value, style, currency, minimumFractionDigits, maximumFractionDigits]
    );

    return <span className={className}>{formattedValue}</span>;
  }
);

/* ==============
   Date / Time
   ============== */

export interface FormattedDateProps {
  value: Date | string | number; // accept common inputs; provider should coerce
  dateStyle?: "full" | "long" | "medium" | "short";
  timeStyle?: "full" | "long" | "medium" | "short";
  timeZone?: string;
  className?: string;
}

export const FormattedDate: React.FC<FormattedDateProps> = React.memo(
  ({ value, dateStyle, timeStyle, timeZone, className }) => {
    const { formatDate } = useFormatting();
    const options: FormatOptions = { dateStyle, timeStyle, timeZone };

    const formattedValue = React.useMemo(
      () => formatDate(value, options),
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [value, dateStyle, timeStyle, timeZone]
    );

    return <span className={className}>{formattedValue}</span>;
  }
);

/* ==================
   Relative Time / Ago
   ================== */

export interface FormattedRelativeTimeProps {
  value: number;
  unit: Intl.RelativeTimeFormatUnit;
  numeric?: "always" | "auto";
  className?: string;
}

export const FormattedRelativeTime: React.FC<FormattedRelativeTimeProps> =
  React.memo(({ value, unit, numeric = "auto", className }) => {
    const { formatRelativeTime } = useFormatting();

    const formattedValue = React.useMemo(
      () => formatRelativeTime(value, unit, { numeric }),
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [value, unit, numeric]
    );

    return <span className={className}>{formattedValue}</span>;
  });

export interface TimeAgoProps {
  date: Date | string | number;
  className?: string;
}

type RelativeTimeParts = { value: number; unit: Intl.RelativeTimeFormatUnit };

const DEFAULT_RELATIVE_TIME: RelativeTimeParts = { value: 0, unit: "second" };

const computeRelativeTimeParts = (referenceMs: number, inputMs: number): RelativeTimeParts => {
  const diffInSeconds = Math.floor((referenceMs - inputMs) / 1000);

  if (Math.abs(diffInSeconds) < 60) {
    return { value: -diffInSeconds, unit: "second" };
  }
  if (Math.abs(diffInSeconds) < 3600) {
    return { value: -Math.floor(diffInSeconds / 60), unit: "minute" };
  }
  if (Math.abs(diffInSeconds) < 86400) {
    return { value: -Math.floor(diffInSeconds / 3600), unit: "hour" };
  }
  if (Math.abs(diffInSeconds) < 2592000) {
    return { value: -Math.floor(diffInSeconds / 86400), unit: "day" };
  }
  if (Math.abs(diffInSeconds) < 31536000) {
    return { value: -Math.floor(diffInSeconds / 2592000), unit: "month" };
  }
  return { value: -Math.floor(diffInSeconds / 31536000), unit: "year" };
};

export const TimeAgo: React.FC<TimeAgoProps> = React.memo(({ date, className }) => {
  const [relativeTime, setRelativeTime] = React.useState<RelativeTimeParts>(DEFAULT_RELATIVE_TIME);

  React.useEffect(() => {
    const inputMs =
      date instanceof Date ? date.getTime() : typeof date === "number" ? date : new Date(date).getTime();

    if (Number.isNaN(inputMs)) {
      setRelativeTime(DEFAULT_RELATIVE_TIME);
      return;
    }

    setRelativeTime(computeRelativeTimeParts(Date.now(), inputMs));
  }, [date]);

  return <FormattedRelativeTime value={relativeTime.value} unit={relativeTime.unit} className={className} />;
});

/* =====================
   Currency / Percentage
   ===================== */

export interface FormattedCurrencyProps {
  value: number;
  currency: string;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  className?: string;
}

export const FormattedCurrency: React.FC<FormattedCurrencyProps> = React.memo(
  ({
    value,
    currency,
    minimumFractionDigits = 2,
    maximumFractionDigits = 2,
    className,
  }) => {
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
);

export interface FormattedPercentProps {
  value: number; // 0.15 => 15%
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  className?: string;
}

export const FormattedPercent: React.FC<FormattedPercentProps> = React.memo(
  ({ value, minimumFractionDigits = 0, maximumFractionDigits = 2, className }) => {
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
);

/* ==================
   File Size Formatter
   ================== */

export interface FormattedFileSizeProps {
  bytes: number;
  binary?: boolean; // false => SI (KB=1000), true => IEC (KiB=1024)
  className?: string;
}

export const FormattedFileSize: React.FC<FormattedFileSizeProps> = React.memo(
  ({ bytes, binary = false, className }) => {
    const { locale } = useLocale();

    const units = binary
      ? ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
      : ["B", "KB", "MB", "GB", "TB", "PB"];

    const base = binary ? 1024 : 1000;

    if (!Number.isFinite(bytes)) {
      return <span className={className}>—</span>;
    }

    const sign = Math.sign(bytes) || 1;
    const abs = Math.abs(bytes);

    if (abs === 0) {
      return <span className={className}>0 B</span>;
    }

    const exponent = Math.min(Math.floor(Math.log(abs) / Math.log(base)), units.length - 1);
    const value = abs / Math.pow(base, exponent);
    const unit = units[exponent];

    const formatter = new Intl.NumberFormat(locale, {
      minimumFractionDigits: 0,
      maximumFractionDigits: exponent === 0 ? 0 : 1,
    });

    return (
      <span className={className}>
        {sign < 0 ? "-" : ""}
        {formatter.format(value)} {unit}
      </span>
    );
  }
);
