"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Bot,
  Clock,
  FileText,
  Loader2,
  RefreshCw,
  Settings,
  Shield,
  ShieldAlert,
  UserCog,
} from "lucide-react";

import { apiClient, ApiError } from "@/lib/api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

type AuditCategory = "user" | "settings" | "model" | "security" | "system";

type AuditEntry = {
  id: string;
  timestamp: string;
  action: string;
  actor: string;
  target?: string;
  details?: string;
  category: AuditCategory;
};

type RawAuditEntry = {
  id?: string | number;
  timestamp?: string;
  created_at?: string;
  updated_at?: string;
  occurred_at?: string;
  message?: string;
  event_type?: string;
  event?: string;
  action?: string;
  user_id?: string;
  actor?: string;
  actor_id?: string;
  actor_email?: string;
  resource_id?: string;
  target?: string;
  target_id?: string;
  metadata?: Record<string, unknown>;
  details?: string | Record<string, unknown>;
  category?: string;
  severity?: string;
  status?: string;
};

type AuditListResponse =
  | RawAuditEntry[]
  | {
      logs?: RawAuditEntry[];
      entries?: RawAuditEntry[];
      items?: RawAuditEntry[];
      events?: RawAuditEntry[];
      total?: number;
    };

const categoryConfig: Record<
  AuditCategory,
  { icon: React.ReactNode; color: string }
> = {
  user: {
    icon: <UserCog className="h-3.5 w-3.5" />,
    color: "border-blue-500/20 bg-blue-500/10 text-blue-500",
  },
  settings: {
    icon: <Settings className="h-3.5 w-3.5" />,
    color: "border-amber-500/20 bg-amber-500/10 text-amber-500",
  },
  model: {
    icon: <Bot className="h-3.5 w-3.5" />,
    color: "border-purple-500/20 bg-purple-500/10 text-purple-500",
  },
  security: {
    icon: <Shield className="h-3.5 w-3.5" />,
    color: "border-emerald-500/20 bg-emerald-500/10 text-emerald-500",
  },
  system: {
    icon: <Clock className="h-3.5 w-3.5" />,
    color: "border-border/30 bg-muted/40 text-muted-foreground",
  },
};

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "This session is not authenticated. Sign in to inspect backend audit events.";
    }

    if (error.status === 403) {
      return "This session is not authorized to inspect backend audit events.";
    }

    return error.message || fallback;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
};

const coerceAuditEntries = (response: AuditListResponse): RawAuditEntry[] => {
  if (Array.isArray(response)) {
    return response;
  }

  if (Array.isArray(response.logs)) {
    return response.logs;
  }

  if (Array.isArray(response.entries)) {
    return response.entries;
  }

  if (Array.isArray(response.items)) {
    return response.items;
  }

  if (Array.isArray(response.events)) {
    return response.events;
  }

  return [];
};

const stringifyDetails = (value: unknown): string | undefined => {
  if (value == null) {
    return undefined;
  }

  if (typeof value === "string") {
    return value;
  }

  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
};

const truncateText = (value: string, maxLength = 420) => {
  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength)}…`;
};

const normalizeCategory = (value: string | undefined | null): AuditCategory | null => {
  const normalized = String(value || "").toLowerCase();

  if (
    normalized === "user" ||
    normalized === "settings" ||
    normalized === "model" ||
    normalized === "security" ||
    normalized === "system"
  ) {
    return normalized;
  }

  return null;
};

const mapAuditCategory = (entry: RawAuditEntry): AuditCategory => {
  const explicitCategory = normalizeCategory(entry.category);

  if (explicitCategory) {
    return explicitCategory;
  }

  const eventType = String(
    entry.event_type ||
      entry.event ||
      entry.action ||
      entry.message ||
      "",
  ).toLowerCase();

  if (
    eventType.includes("auth") ||
    eventType.includes("login") ||
    eventType.includes("logout") ||
    eventType.includes("security") ||
    eventType.includes("privacy") ||
    eventType.includes("rbac") ||
    eventType.includes("permission") ||
    eventType.includes("token") ||
    eventType.includes("credential")
  ) {
    return "security";
  }

  if (
    eventType.includes("model") ||
    eventType.includes("provider") ||
    eventType.includes("llm") ||
    eventType.includes("runtime") ||
    eventType.includes("fallback")
  ) {
    return "model";
  }

  if (
    eventType.includes("user") ||
    eventType.includes("profile") ||
    eventType.includes("account") ||
    eventType.includes("role")
  ) {
    return "user";
  }

  if (
    eventType.includes("config") ||
    eventType.includes("setting") ||
    eventType.includes("environment") ||
    eventType.includes("maintenance")
  ) {
    return "settings";
  }

  return "system";
};

const getTimestamp = (entry: RawAuditEntry): string => {
  return String(
    entry.timestamp ||
      entry.created_at ||
      entry.occurred_at ||
      entry.updated_at ||
      "",
  );
};

const formatDateTime = (value: string | null | undefined): string => {
  if (!value) {
    return "Unknown time";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
};

const formatRelativeTime = (value: string): string => {
  if (!value) {
    return "Unknown";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return formatDateTime(value);
  }

  const diff = Date.now() - parsed.getTime();

  if (diff < 0) {
    return formatDateTime(value);
  }

  const mins = Math.floor(diff / 60_000);

  if (mins < 1) {
    return "Just now";
  }

  if (mins < 60) {
    return `${mins}m ago`;
  }

  const hrs = Math.floor(mins / 60);

  if (hrs < 24) {
    return `${hrs}h ago`;
  }

  const days = Math.floor(hrs / 24);

  if (days < 30) {
    return `${days}d ago`;
  }

  return formatDateTime(value);
};

const mapAuditEntry = (entry: RawAuditEntry, index: number): AuditEntry => {
  const timestamp = getTimestamp(entry);
  const idSeed =
    entry.id ||
    `${timestamp || "audit-event"}-${entry.event_type || entry.action || index}`;

  const metadataDetails = stringifyDetails(entry.metadata);
  const rawDetails = stringifyDetails(entry.details);
  const actor =
    entry.actor_email ||
    entry.actor ||
    entry.actor_id ||
    entry.user_id ||
    "system";

  const target =
    entry.target ||
    entry.target_id ||
    entry.resource_id ||
    undefined;

  return {
    id: String(idSeed),
    timestamp,
    action: String(
      entry.message ||
        entry.event_type ||
        entry.event ||
        entry.action ||
        "Audit event",
    ),
    actor: String(actor),
    target: target ? String(target) : undefined,
    details: truncateText(metadataDetails || rawDetails || ""),
    category: mapAuditCategory(entry),
  };
};

export default function AuditLogPanel() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [authRequired, setAuthRequired] = useState(false);
  const [accessDenied, setAccessDenied] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadAuditLogs = useCallback(async () => {
    setIsLoading(true);
    setAuthRequired(false);
    setAccessDenied(false);
    setLoadError(null);

    try {
      const response = await apiClient.get<AuditListResponse>("/api/audit/logs");
      const rawEntries = coerceAuditEntries(response);

      setEntries(rawEntries.map(mapAuditEntry));
    } catch (error) {
      setEntries([]);

      if (error instanceof ApiError && error.status === 401) {
        setAuthRequired(true);
        return;
      }

      if (error instanceof ApiError && error.status === 403) {
        setAccessDenied(true);
        return;
      }

      setLoadError(getErrorMessage(error, "Karen could not load the backend audit log."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAuditLogs();
  }, [loadAuditLogs]);

  const categoryCounts = useMemo(() => {
    return entries.reduce<Record<AuditCategory, number>>(
      (counts, entry) => {
        counts[entry.category] += 1;
        return counts;
      },
      {
        user: 0,
        settings: 0,
        model: 0,
        security: 0,
        system: 0,
      },
    );
  }, [entries]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <FileText className="h-5 w-5 text-primary" />
              Admin Activity Log
            </CardTitle>
            <CardDescription>
              Read-only backend audit events. This panel never displays synthetic security data.
            </CardDescription>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => void loadAuditLogs()}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Refresh
          </Button>
        </CardHeader>

        <CardContent>
          {authRequired && (
            <Alert className="mb-4 border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Sign In Required</AlertTitle>
              <AlertDescription>
                The audit route is live, but this session is not authenticated. Sign in to
                inspect backend audit events.
              </AlertDescription>
            </Alert>
          )}

          {accessDenied && (
            <Alert className="mb-4 border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Audit Access Restricted</AlertTitle>
              <AlertDescription>
                The audit route is live, but this session is not authorized to inspect
                backend audit events.
              </AlertDescription>
            </Alert>
          )}

          {loadError && (
            <Alert className="mb-4 border-yellow-500/30 bg-yellow-500/5">
              <AlertCircle className="h-4 w-4 !text-yellow-600" />
              <AlertTitle>Audit Log Unavailable</AlertTitle>
              <AlertDescription>{loadError}</AlertDescription>
            </Alert>
          )}

          {entries.length > 0 && (
            <div className="mb-4 flex flex-wrap gap-2">
              {Object.entries(categoryCounts).map(([category, count]) => {
                const cat = categoryConfig[category as AuditCategory];

                return (
                  <Badge
                    key={category}
                    variant="outline"
                    className={`border text-[10px] uppercase tracking-wider ${cat.color}`}
                  >
                    {category}: {count}
                  </Badge>
                );
              })}
            </div>
          )}

          {isLoading ? (
            <div className="flex items-center gap-2 rounded-xl border border-border/70 p-4 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading backend audit events.
            </div>
          ) : authRequired ? (
            <div className="rounded-xl border border-dashed border-border/70 p-6 text-sm text-muted-foreground">
              Audit events require an authenticated session.
            </div>
          ) : accessDenied ? (
            <div className="rounded-xl border border-dashed border-border/70 p-6 text-sm text-muted-foreground">
              Audit events are restricted by backend permissions.
            </div>
          ) : loadError ? (
            <div className="rounded-xl border border-dashed border-border/70 p-6 text-sm text-muted-foreground">
              Audit events could not be loaded from the backend.
            </div>
          ) : entries.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border/70 p-6 text-sm text-muted-foreground">
              No backend audit events were returned.
            </div>
          ) : (
            <ScrollArea className="h-[560px]">
              <div className="space-y-1">
                {entries.map((entry) => {
                  const cat = categoryConfig[entry.category];

                  return (
                    <div
                      key={entry.id}
                      className="group flex items-start gap-3 rounded-xl p-3 transition-colors hover:bg-muted/30"
                    >
                      <div className={`mt-0.5 shrink-0 rounded-lg border p-1.5 ${cat.color}`}>
                        {cat.icon}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-2">
                          <p className="truncate text-sm font-medium">{entry.action}</p>
                          <span
                            className="whitespace-nowrap text-[10px] text-muted-foreground"
                            title={formatDateTime(entry.timestamp)}
                          >
                            {formatRelativeTime(entry.timestamp)}
                          </span>
                        </div>

                        <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                          <span className="font-mono">{entry.actor}</span>
                          {entry.target && (
                            <>
                              <span>→</span>
                              <span className="truncate font-mono">{entry.target}</span>
                            </>
                          )}
                        </div>

                        {entry.details && (
                          <p className="mt-1 break-words text-[10px] text-muted-foreground/70 transition-colors group-hover:text-muted-foreground">
                            {entry.details}
                          </p>
                        )}
                      </div>

                      <Badge
                        variant="outline"
                        className={`mt-0.5 shrink-0 border text-[8px] uppercase tracking-wider ${cat.color}`}
                      >
                        {entry.category}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}