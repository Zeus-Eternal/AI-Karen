'use client';

import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { FixedSizeList as List } from 'react-window';
import { 
  Search, 
  Filter, 
  Download, 
  Pause, 
  Play,
  RotateCcw,
  AlertCircle,
  Info,
  AlertTriangle,
  Bug
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { WidgetBase } from '../WidgetBase';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
} from '@/components/ui/dropdown-menu';
import type { WidgetProps, LogData } from '@/types/dashboard';

interface LogWidgetProps extends WidgetProps {
  data?: {
    id: string;
    data: LogData;
    loading: boolean;
    error?: string;
    lastUpdated: Date;
  };
}

const LOG_LEVEL_CONFIG = {
  debug: {
    icon: Bug,
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
    label: 'DEBUG'
  },
  info: {
    icon: Info,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    label: 'INFO'
  },
  warn: {
    icon: AlertTriangle,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
    label: 'WARN'
  },
  error: {
    icon: AlertCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    label: 'ERROR'
  }
};

interface LogEntryProps {
  index: number;
  style: React.CSSProperties;
  data: {
    entries: LogData['entries'];
    searchTerm: string;
    selectedLevels: Set<string>;
  };
}

const LogEntry: React.FC<LogEntryProps> = ({ index, style, data }) => {
  const { entries, searchTerm } = data;
  const entry = entries[index];
  
  if (!entry) return null;

  const levelConfig = LOG_LEVEL_CONFIG[entry.level];
  const LevelIcon = levelConfig.icon;

  const highlightText = (text: string, term: string) => {
    if (!term) return text;
    
    const regex = new RegExp(`(${term})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, i) => 
      regex.test(part) ? (
        <mark key={i} className="bg-yellow-200 px-0.5 rounded">
          {part}
        </mark>
      ) : part
    );
  };

  return (
    <div style={style} className="px-2 py-1 border-b border-border/50 hover:bg-muted/50">
      <div className="flex items-start gap-2 text-xs">
        {/* Timestamp */}
        <span className="text-muted-foreground font-mono text-[10px] min-w-[60px]">
          {new Date(entry.timestamp).toLocaleTimeString()}
        </span>

        {/* Level Badge */}
        <Badge 
          variant="outline" 
          className={cn(
            "text-[10px] px-1 py-0 h-4 min-w-[45px] justify-center",
            levelConfig.bgColor,
            levelConfig.color
          )}
        >
          <LevelIcon className="h-2 w-2 mr-1" />
          {levelConfig.label}
        </Badge>

        {/* Source */}
        {entry.source && (
          <span className="text-muted-foreground text-[10px] min-w-[60px] truncate">
            [{entry.source}]
          </span>
        )}

        {/* Message */}
        <span className="flex-1 text-[11px] leading-tight">
          {highlightText(entry.message, searchTerm)}
        </span>
      </div>

      {/* Metadata */}
      {entry.metadata && Object.keys(entry.metadata).length > 0 && (
        <div className="ml-[140px] mt-1 text-[10px] text-muted-foreground">
          {Object.entries(entry.metadata).slice(0, 3).map(([key, value]) => (
            <span key={key} className="mr-3">
              {key}: {String(value)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export const LogWidget: React.FC<LogWidgetProps> = (props) => {
  const { data: widgetData } = props;
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLevels, setSelectedLevels] = useState<Set<string>>(
    new Set(['debug', 'info', 'warn', 'error'])
  );
  const [isPaused, setIsPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const listRef = useRef<List>(null);

  const filteredEntries = useMemo(() => {
    if (!widgetData?.data?.entries) return [];

    return widgetData.data.entries.filter(entry => {
      // Level filter
      if (!selectedLevels.has(entry.level)) return false;
      
      // Search filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        return (
          entry.message.toLowerCase().includes(searchLower) ||
          entry.source?.toLowerCase().includes(searchLower) ||
          Object.values(entry.metadata || {}).some(value => 
            String(value).toLowerCase().includes(searchLower)
          )
        );
      }
      
      return true;
    });
  }, [widgetData?.data?.entries, selectedLevels, searchTerm]);

  const handleLevelToggle = useCallback((level: string) => {
    setSelectedLevels(prev => {
      const newSet = new Set(prev);
      if (newSet.has(level)) {
        newSet.delete(level);
      } else {
        newSet.add(level);
      }
      return newSet;
    });
  }, []);

  const handleClearLogs = useCallback(() => {
    // In a real implementation, this would clear the logs
    console.log('Clear logs');
  }, []);

  const handleExportLogs = useCallback(() => {
    // In a real implementation, this would export the logs
    const logsText = filteredEntries.map(entry => 
      `${new Date(entry.timestamp).toISOString()} [${entry.level.toUpperCase()}] ${entry.source ? `[${entry.source}] ` : ''}${entry.message}`
    ).join('\n');
    
    const blob = new Blob([logsText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [filteredEntries]);

  const handleTogglePause = useCallback(() => {
    setIsPaused(prev => !prev);
  }, []);

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (autoScroll && !isPaused && listRef.current && filteredEntries.length > 0) {
      listRef.current.scrollToItem(filteredEntries.length - 1, 'end');
    }
  }, [filteredEntries.length, autoScroll, isPaused]);

  if (!widgetData?.data) {
    return (
      <WidgetBase {...props}>
        <div className="flex items-center justify-center h-full text-muted-foreground">
          No log data available
        </div>
      </WidgetBase>
    );
  }

  const logData = widgetData.data;

  return (
    <WidgetBase {...props}>
      <div className="flex flex-col h-full">
        {/* Controls */}
        <div className="flex items-center gap-2 mb-2 pb-2 border-b">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground" />
            <Input
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-7 h-7 text-xs"
            />
          </div>

          {/* Level Filter */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="h-7 px-2">
                <Filter className="h-3 w-3 mr-1" />
                Levels
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              {Object.entries(LOG_LEVEL_CONFIG).map(([level, config]) => (
                <DropdownMenuCheckboxItem
                  key={level}
                  checked={selectedLevels.has(level)}
                  onCheckedChange={() => handleLevelToggle(level)}
                >
                  <config.icon className="h-3 w-3 mr-2" />
                  {config.label}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Pause/Play */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleTogglePause}
            className="h-7 px-2"
            aria-label={isPaused ? 'Resume log streaming' : 'Pause log streaming'}
          >
            {isPaused ? (
              <Play className="h-3 w-3" />
            ) : (
              <Pause className="h-3 w-3" />
            )}
          </Button>

          {/* Actions */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="h-7 px-2">
                <Download className="h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              <DropdownMenuItem onClick={handleExportLogs}>
                <Download className="h-3 w-3 mr-2" />
                Export Logs
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleClearLogs}>
                <RotateCcw className="h-3 w-3 mr-2" />
                Clear Logs
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Log Stats */}
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
          <span>
            {filteredEntries.length} of {logData.entries.length} entries
            {logData.hasMore && ' (more available)'}
          </span>
          <div className="flex items-center gap-2">
            {isPaused && (
              <Badge variant="outline" className="text-[10px] px-1 py-0">
                PAUSED
              </Badge>
            )}
            <span>
              Last: {logData.entries.length > 0 ? 
                new Date(logData.entries[logData.entries.length - 1].timestamp).toLocaleTimeString() : 
                'N/A'
              }
            </span>
          </div>
        </div>

        {/* Log Entries */}
        <div className="flex-1 border rounded-md bg-background">
          {filteredEntries.length > 0 ? (
            <List
              ref={listRef}
              height={200}
              width="100%"
              itemCount={filteredEntries.length}
              itemSize={40}
              itemData={{
                entries: filteredEntries,
                searchTerm,
                selectedLevels
              }}
              className="scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent"
            >
              {LogEntry}
            </List>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
              {searchTerm || selectedLevels.size < 4 ? 
                'No logs match the current filters' : 
                'No log entries available'
              }
            </div>
          )}
        </div>

        {/* Load More */}
        {logData.hasMore && (
          <div className="mt-2 text-center">
            <Button variant="outline" size="sm" className="text-xs">
              Load More Entries
            </Button>
          </div>
        )}
      </div>
    </WidgetBase>
  );
};

export default LogWidget;