'use client';

import React, { useState } from 'react';
import { Calendar, Clock, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import type { TimeRange } from '@/store/dashboard-store';

interface TimeRangeSelectorProps {
  value: TimeRange;
  onChange: (timeRange: TimeRange) => void;
  className?: string;
}

const presetRanges = [
  { key: 'last-hour', label: 'Last Hour', duration: 60 * 60 * 1000 },
  { key: 'last-day', label: 'Last 24 Hours', duration: 24 * 60 * 60 * 1000 },
  { key: 'last-week', label: 'Last 7 Days', duration: 7 * 24 * 60 * 60 * 1000 },
  { key: 'last-month', label: 'Last 30 Days', duration: 30 * 24 * 60 * 60 * 1000 },
] as const;

export const TimeRangeSelector: React.FC<TimeRangeSelectorProps> = ({
  value,
  onChange,
  className
}) => {
  const [isCustomOpen, setIsCustomOpen] = useState(false);
  const [customStart, setCustomStart] = useState(
    value.start.toISOString().slice(0, 16)
  );
  const [customEnd, setCustomEnd] = useState(
    value.end.toISOString().slice(0, 16)
  );

  const handlePresetSelect = (preset: typeof presetRanges[number]) => {
    const end = new Date();
    const start = new Date(end.getTime() - preset.duration);
    
    onChange({
      start,
      end,
      preset: preset.key
    });
  };

  const handleCustomApply = () => {
    const start = new Date(customStart);
    const end = new Date(customEnd);
    
    if (start >= end) {
      // Show error or handle invalid range
      return;
    }
    
    onChange({
      start,
      end,
      preset: 'custom'
    });
    
    setIsCustomOpen(false);
  };

  const formatTimeRange = (timeRange: TimeRange) => {
    if (timeRange.preset && timeRange.preset !== 'custom') {
      const preset = presetRanges.find(p => p.key === timeRange.preset);
      return preset?.label || 'Custom Range';
    }
    
    const formatDate = (date: Date) => {
      const now = new Date();
      const isToday = date.toDateString() === now.toDateString();
      
      if (isToday) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
      
      return date.toLocaleDateString([], { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    };
    
    return `${formatDate(timeRange.start)} - ${formatDate(timeRange.end)}`;
  };

  const getCurrentPresetLabel = () => {
    if (value.preset && value.preset !== 'custom') {
      const preset = presetRanges.find(p => p.key === value.preset);
      return preset?.label || 'Custom Range';
    }
    return 'Custom Range';
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Clock className="h-4 w-4 text-muted-foreground" />
      
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="h-8">
            {getCurrentPresetLabel()}
            <ChevronDown className="h-3 w-3 ml-2" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          {presetRanges.map((preset) => (
            <DropdownMenuItem
              key={preset.key}
              onClick={() => handlePresetSelect(preset)}
              className={cn(
                value.preset === preset.key && 'bg-accent'
              )}
            >
              {preset.label}
            </DropdownMenuItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setIsCustomOpen(true)}>
            <Calendar className="h-4 w-4 mr-2" />
            Custom Range...
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Popover open={isCustomOpen} onOpenChange={setIsCustomOpen}>
        <PopoverTrigger asChild>
          <div />
        </PopoverTrigger>
        <PopoverContent className="w-80" align="end">
          <Card className="p-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Custom Time Range</h4>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsCustomOpen(false)}
                >
                  ×
                </Button>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="start-time">Start Time</Label>
                  <Input
                    id="start-time"
                    type="datetime-local"
                    value={customStart}
                    onChange={(e) => setCustomStart(e.target.value)}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="end-time">End Time</Label>
                  <Input
                    id="end-time"
                    type="datetime-local"
                    value={customEnd}
                    onChange={(e) => setCustomEnd(e.target.value)}
                  />
                </div>
              </div>
              
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsCustomOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleCustomApply}
                  disabled={!customStart || !customEnd}
                >
                  Apply
                </Button>
              </div>
            </div>
          </Card>
        </PopoverContent>
      </Popover>
      
      <div className="text-xs text-muted-foreground">
        {formatTimeRange(value)}
      </div>
    </div>
  );
};

export default TimeRangeSelector;