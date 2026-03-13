// ui_launchers/KAREN-Theme-Default/src/components/dashboard/widgets/LogWidget.tsx
"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FixedSizeList as List } from "react-window";
import {
  Bug,
  Info,
  AlertTriangle,
  AlertCircle,
  Search,
  Filter,
  Play,
  Pause,
  Download,
  RotateCcw,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { WidgetBase } from "../WidgetBase";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuCheckboxItem,
} from "@/components/ui/dropdown-menu";

import type { WidgetProps, LogData } from "@/types/dashboard";

interface LogWidgetProps extends WidgetProps {
  data?: {
    id: string;
    data: LogData;
    loading: boolean;
    error?: string;
    lastUpdated: Date;
  };
  /** Optional callbacks to wire server actions */
  onLoadMore?: (widgetId: string) => void;
  onClearLogs?: (widgetId: string) => void;
}

const LOG_LEVEL_CONFIG = {
  debug: {
    icon: Bug,
    color: "text-gray-600",
    bgColor: "bg-gray-100 dark:bg-gray-900/40",
    label: "DEBUG",
  },
  info: {
    icon: Info,
    color: "text-blue-600",
    bgColor: "bg-blue-100 dark:bg-blue-900/30",
    label: "INFO",
  },
  warn: {
    icon: AlertTriangle,
    color: "text-yellow-600",
    bgColor: "bg-yellow-100 dark:bg-yellow-900/30",
    label: "WARN",
  },
  error: {
    icon: AlertCircle,
    color: "text-red-600",
    bgColor: "bg-red-100 dark:bg-red-900/30",
    label: "ERROR",
  },
};

type LevelKey = keyof typeof LOG_LEVEL_CONFIG;

interface LogEntryProps {
  index: number;
  style: React.CSSProperties;
  data: {
    entries: LogData["entries"];
    searchTerm: string;
  };
}

const highlight = (text: string, term: string) => {
  if (!term) return text;
  const safe = term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(`(${safe})`, "gi");
  const parts = text.split(regex);
  return parts.map((part, i) =>
    regex.test(part) ? (
      <mark key={`${part}-${i}`} className="bg-yellow-200 px-0.5 rounded">
        {part}
      </mark>
    ) : (
      <React.Fragment key={`${part}-${i}`}>{part}</React.Fragment>
    )
  );
};

const LogEntry: React.FC<LogEntryProps> = ({ index, style, data }) => {
  const { entries, searchTerm } = data;
  const entry = entries[index];
  if (!entry) return null;

  const levelCfg = LOG_LEVEL_CONFIG[entry.level as LevelKey] ?? LOG_LEVEL_CONFIG.info;
  const LevelIcon = levelCfg.icon;

  return (
    <div style={style} className="px-2 py-1 border-b border-border/50 hover:bg-muted/50">
      <div className="flex items-start gap-2 text-xs sm:text-sm md:text-base">
        {/* Timestamp */}
        <span className="text-muted-foreground font-mono text-[10px] min-w-[72px]">
          {new Date(entry.timestamp).toLocaleTimeString()}
        </span>

        {/* Level */}
        <Badge
          variant="outline"
          className={cn(
            "text-[10px] px-1 py-0 h-4 min-w-[52px] justify-center",
            levelCfg.bgColor,
            levelCfg.color
          )}
        >
          <LevelIcon className="h-2.5 w-2.5 mr-1" />
          {levelCfg.label}
        </Badge>

        {/* Source */}
        {entry.source && (
          <span className="text-muted-foreground text-[10px] min-w-[80px] truncate">
            [{entry.source}]
          </span>
        )}

        {/* Message */}
        <span className="flex-1 text-[11px] leading-tight break-words">
          {highlight(entry.message, searchTerm)}
        </span>
      </div>

      {/* Metadata (first 3 keys) */}
      {entry.metadata && Object.keys(entry.metadata).length > 0 && (
        <div className="ml-[160px] mt-1 text-[10px] text-muted-foreground">
          {Object.entries(entry.metadata)
            .slice(0, 3)
            .map(([key, value]) => (
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
  const { data: widgetData, onLoadMore, onClearLogs } = props;

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedLevels, setSelectedLevels] = useState<Set<LevelKey>>(
    new Set<LevelKey>(["info", "warn", "error"])
  );
  const [isPaused, setIsPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);

  const listRef = useRef<List>(null);

  const entries = useMemo(
    () => widgetData?.data?.entries ?? [],
    [widgetData?.data?.entries]
  );

  const filteredEntries = useMemo(() => {
    const q = searchTerm.toLowerCase();
    return entries.filter((e) => {
      if (!selectedLevels.has(e.level as LevelKey)) return false;
      if (!q) return true;
      const inMsg = e.message.toLowerCase().includes(q);
      const inSrc = (e.source ?? "").toLowerCase().includes(q);
      const inMeta = Object.values(e.metadata ?? {}).some((v) =>
        String(v).toLowerCase().includes(q)
      );
      return inMsg || inSrc || inMeta;
    });
  }, [entries, selectedLevels, searchTerm]);

  const handleLevelToggle = useCallback((level: LevelKey) => {
    setSelectedLevels((prev) => {
      const copy = new Set(prev);
      if (copy.has(level)) copy.delete(level);
      else copy.add(level);
      return copy;
    });
  }, []);

  const widgetId = widgetData?.id;

  const handleClearLogs = useCallback(() => {
    // delegate to parent if provided
    if (widgetId && onClearLogs) onClearLogs(widgetId);
  }, [onClearLogs, widgetId]);

  const handleExportLogs = useCallback(() => {
    const text = filteredEntries
      .map(
        (e) =>
          `${new Date(e.timestamp).toISOString()} [${e.level.toUpperCase()}] ${
            e.source ? `[${e.source}] ` : ""
          }${e.message}`
      )
      .join("\n");

    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `logs-${new Date().toISOString().split("T")[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [filteredEntries]);

  const handleTogglePause = useCallback(() => setIsPaused((p) => !p), []);
  const handleToggleAutoScroll = useCallback(() => setAutoScroll((p) => !p), []);

  // Auto-scroll to bottom when new filtered entries arrive
  useEffect(() => {
    if (autoScroll && !isPaused && listRef.current && filteredEntries.length > 0) {
      listRef.current.scrollToItem(filteredEntries.length - 1, "end");
    }
  }, [filteredEntries.length, autoScroll, isPaused]);

  if (!widgetData?.data) {
    return (
      <WidgetBase {...props}>
        <div className="flex items-center justify-center h-full text-muted-foreground">
          No data.
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
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
            <Input
              placeholder="Search logs…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-7 h-7 text-xs sm:text-sm md:text-base"
              aria-label="Search logs"
            />
          </div>

          {/* Level Filter */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="h-7 px-2" aria-label="Filter levels">
                <Filter className="h-3 w-3 mr-1" />
                Levels
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-44">
              {(Object.keys(LOG_LEVEL_CONFIG) as LevelKey[]).map((level) => {
                const Cfg = LOG_LEVEL_CONFIG[level];
                const Icon = Cfg.icon;
                return (
                  <DropdownMenuCheckboxItem
                    key={level}
                    checked={selectedLevels.has(level)}
                    onCheckedChange={() => handleLevelToggle(level)}
                  >
                    <Icon className="h-3 w-3 mr-2" />
                    {Cfg.label}
                  </DropdownMenuCheckboxItem>
                );
              })}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Pause/Play */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleTogglePause}
            className="h-7 px-2"
            aria-label={isPaused ? "Resume log streaming" : "Pause log streaming"}
            title={isPaused ? "Resume" : "Pause"}
          >
            {isPaused ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
          </Button>

          {/* Auto-Scroll */}
          <Button
            variant={autoScroll ? "default" : "outline"}
            size="sm"
            onClick={handleToggleAutoScroll}
            className="h-7 px-2"
            aria-pressed={autoScroll}
            aria-label="Toggle auto-scroll"
            title="Toggle auto-scroll"
          >
            {autoScroll ? "Auto" : "Manual"}
          </Button>

          {/* Actions */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="h-7 px-2" aria-label="Log actions">
                <Download className="h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-44">
              <DropdownMenuItem onClick={handleExportLogs}>
                <Download className="h-3 w-3 mr-2" />
                Export .txt
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleClearLogs}>
                <RotateCcw className="h-3 w-3 mr-2" />
                Clear (server)
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Log Stats */}
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-2 sm:text-sm md:text-base">
          <span>
            {filteredEntries.length} of {logData.entries.length} entries
            {logData.hasMore ? " (more available)" : ""}
          </span>
          <div className="flex items-center gap-2">
            {isPaused && (
              <Badge variant="outline" className="text-[10px] px-1 py-0">
                Paused
              </Badge>
            )}
            <span>
              Last:{" "}
              {logData.entries.length > 0
                ? new Date(
                    logData.entries[logData.entries.length - 1].timestamp
                  ).toLocaleTimeString()
                : "N/A"}
            </span>
          </div>
        </div>

        {/* Log Entries */}
        <div className="flex-1 border rounded-md bg-background">
          {filteredEntries.length > 0 ? (
            <List
              ref={listRef}
              height={240}
              width="100%"
              itemCount={filteredEntries.length}
              itemSize={44}
              itemData={{
                entries: filteredEntries,
                searchTerm,
              }}
              className="scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent"
            >
              {LogEntry}
            </List>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm md:text-base lg:text-lg">
              {searchTerm || selectedLevels.size < 4
                ? "No logs match the current filters"
                : "No log entries available"}
            </div>
          )}
        </div>

        {/* Load More */}
        {logData.hasMore && (
          <div className="mt-2 text-center">
            <Button
              variant="outline"
              size="sm"
              className="text-xs sm:text-sm md:text-base"
              onClick={() => widgetData?.id && onLoadMore?.(widgetData.id)}
            >
              Load more
            </Button>
          </div>
        )}
      </div>
    </WidgetBase>
  );
};

export default LogWidget;
