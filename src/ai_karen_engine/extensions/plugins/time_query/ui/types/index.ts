export interface TimezoneResolutionMeta {
  query: string;
  resolvedTimezone: string;
  isAmbiguousDefault: boolean;
  resolutionType: "alias" | "country_default" | "direct_timezone" | "direct";
}

export interface TimePayload {
  source: string;
  timestamp: number;
  iso: string;
  formatted: string;
  date: string;
  time: string;
  weekday: string;
  timezone: string;
  utc_timestamp: string;
  utc_offset: number;
  resolution_meta?: TimezoneResolutionMeta;
}

export interface ClockItem extends TimePayload {
  label: string;
}

export interface StopwatchState {
  stopwatch_id: string;
  running: boolean;
  paused: boolean;
  elapsed_ms: number;
  started_at: number | null;
  last_updated_at: number;
}

export interface AlarmItem {
  alarm_id: string;
  title: string;
  alarm_datetime: string;
  timezone: string;
  enabled: boolean;
  recurrence?: string | null;
}

export interface TimezoneConversionResult {
  source: {
    datetime: string;
    timezone: string;
    utc_offset: number;
  };
  converted: {
    datetime: string;
    timezone: string;
    utc_offset: number;
  };
}

export interface TimeQueryState {
  loading: boolean;
  error: string | null;
  currentTime: TimePayload | null;
  worldTime: TimePayload | null;
  clocks: ClockItem[];
  stopwatch: StopwatchState | null;
  alarms: AlarmItem[];
  conversion: TimezoneConversionResult | null;
  diagnostics: Record<string, any> | null;
}
