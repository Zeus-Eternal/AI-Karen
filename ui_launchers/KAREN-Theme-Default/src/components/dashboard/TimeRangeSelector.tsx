// ui_launchers/KAREN-Theme-Default/src/components/dashboard/TimeRangeSelector.tsx
"use client";

import React, { useMemo, useState } from "react";
import { Calendar, Clock, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import type { TimeRange } from "@/store/dashboard-store";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

/* ------------------------------------------------------------------ */
/* Presets                                                            */
/* ------------------------------------------------------------------ */
const presetRanges = [
  { key: "last-15-min", label: "Last 15 Minutes", duration: 15 * 60 * 1000 },
  { key: "last-hour", label: "Last Hour", duration: 60 * 60 * 1000 },
  { key: "last-day", label: "Last 24 Hours", duration: 24 * 60 * 60 * 1000 },
  { key: "last-week", label: "Last 7 Days", duration: 7 * 24 * 60 * 60 * 1000 },
  { key: "last-month", label: "Last 30 Days", duration: 30 * 24 * 60 * 60 * 1000 },
] as const;

type PresetKey = (typeof presetRanges)[number]["key"] | "custom";

interface TimeRangeSelectorProps {
  value: TimeRange; // { start: Date; end: Date; preset?: string }
  onChange: (timeRange: TimeRange) => void;
  className?: string;
}

/* ------------------------------------------------------------------ */
/* Component                                                          */
/* ------------------------------------------------------------------ */
export const TimeRangeSelector: React.FC<TimeRangeSelectorProps> = ({
  value,
  onChange,
  className,
}) => {
  const [isCustomOpen, setIsCustomOpen] = useState(false);

  // Initialize custom inputs from current value
  const [customStart, setCustomStart] = useState(
    toLocalInput(value.start)
  );
  const [customEnd, setCustomEnd] = useState(
    toLocalInput(value.end)
  );

  // Keep inputs in sync if parent `value` changes (e.g., external store updates)
  React.useEffect(() => {
    setCustomStart(toLocalInput(value.start));
    setCustomEnd(toLocalInput(value.end));
  }, [value.start, value.end]);

  const currentPresetLabel = useMemo(() => {
    if (value.preset && value.preset !== "custom") {
      return presetRanges.find((p) => p.key === value.preset)?.label ?? "Custom Range";
    }
    return "Custom Range";
  }, [value.preset]);

  const handlePresetSelect = (preset: (typeof presetRanges)[number]) => {
    const end = new Date();
    const start = new Date(end.getTime() - preset.duration);
    onChange({
      start,
      end,
      preset: preset.key,
    } as TimeRange);
  };

  const handleCustomApply = () => {
    const start = new Date(customStart);
    const end = new Date(customEnd);

    if (!isValidDate(start) || !isValidDate(end)) return;
    if (start >= end) return;

    onChange({
      start,
      end,
      preset: "custom",
    } as TimeRange);
    setIsCustomOpen(false);
  };

  const formattedDisplay = useMemo(() => formatTimeRange(value), [value]);

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Clock className="h-4 w-4 text-muted-foreground" aria-hidden="true" />

      {/* Preset Selector */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="h-8" aria-label="Select time range preset">
            {currentPresetLabel}
            <ChevronDown className="h-3 w-3 ml-2" aria-hidden="true" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          {presetRanges.map((preset) => (
            <DropdownMenuItem
              key={preset.key}
              onClick={() => handlePresetSelect(preset)}
              className={cn(value.preset === preset.key && "bg-accent")}
            >
              {preset.label}
            </DropdownMenuItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setIsCustomOpen(true)}>
            <Calendar className="h-4 w-4 mr-2" aria-hidden="true" />
            Custom Range…
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Custom Range Popover */}
      <Popover open={isCustomOpen} onOpenChange={setIsCustomOpen}>
        {/* Hidden trigger to satisfy Popover API; we control `open` via state */}
        <PopoverTrigger asChild>
          <button className="hidden" aria-hidden="true" />
        </PopoverTrigger>
        <PopoverContent className="w-80" align="end">
          <Card className="p-4 sm:p-4 md:p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Custom Time Range</h4>
                <Button variant="ghost" size="sm" onClick={() => setIsCustomOpen(false)} aria-label="Close custom range">
                  ×
                </Button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="start-time">Start</Label>
                  <Input
                    id="start-time"
                    type="datetime-local"
                    value={customStart}
                    onChange={(e) => setCustomStart(e.target.value)}
                    max={customEnd || undefined}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="end-time">End</Label>
                  <Input
                    id="end-time"
                    type="datetime-local"
                    value={customEnd}
                    onChange={(e) => setCustomEnd(e.target.value)}
                    min={customStart || undefined}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={() => setIsCustomOpen(false)}>
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleCustomApply}
                  disabled={!customStart || !customEnd || new Date(customStart) >= new Date(customEnd)}
                >
                  Apply
                </Button>
              </div>
            </div>
          </Card>
        </PopoverContent>
      </Popover>

      {/* Live Summary */}
      <div className="text-xs text-muted-foreground sm:text-sm md:text-base" aria-live="polite">
        {formattedDisplay}
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Helpers                                                            */
/* ------------------------------------------------------------------ */

function toLocalInput(d: Date): string {
  // Returns `YYYY-MM-DDTHH:mm` in local time for <input type="datetime-local">
  const pad = (n: number) => String(n).padStart(2, "0");
  const year = d.getFullYear();
  const month = pad(d.getMonth() + 1);
  const day = pad(d.getDate());
  const hours = pad(d.getHours());
  const minutes = pad(d.getMinutes());
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function isValidDate(d: Date) {
  return d instanceof Date && !isNaN(d.getTime());
}

function formatTimeRange(timeRange: TimeRange) {
  if (timeRange.preset && timeRange.preset !== "custom") {
    const preset = presetRanges.find((p) => p.key === timeRange.preset);
    return preset?.label ?? "Custom Range";
  }

  const formatDate = (date: Date) => {
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    if (isToday) {
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
    return date.toLocaleDateString([], {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return `${formatDate(timeRange.start)} – ${formatDate(timeRange.end)}`;
}

export default TimeRangeSelector;
