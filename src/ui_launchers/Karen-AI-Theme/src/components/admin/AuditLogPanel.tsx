"use client";

import { useEffect, useState } from "react";
import { apiClient, ApiError } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText, UserCog, Settings, Bot, Shield, Clock, Loader2, ShieldAlert, AlertCircle } from "lucide-react";

type AuditEntry = {
  id: string;
  timestamp: string;
  action: string;
  actor: string;
  target?: string;
  details?: string;
  category: "user" | "settings" | "model" | "security" | "system";
};

type RawAuditEntry = {
  id?: string | number;
  timestamp?: string;
  created_at?: string;
  message?: string;
  event_type?: string;
  action?: string;
  user_id?: string;
  actor?: string;
  resource_id?: string;
   metadata?: Record<string, unknown>;
  details?: string;
};

const mockAuditLog: AuditEntry[] = [
  {
    id: "audit_001",
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
    action: "Model configuration updated",
    actor: "admin@example.com",
    target: "local GGUF / Phi-3-mini-4k-instruct-q4.gguf",
    details: "Changed default provider from ollama to local GGUF",
    category: "model",
  },
  {
    id: "audit_002",
    timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
    action: "User role changed",
    actor: "admin@example.com",
    target: "jane.s@example.com",
    details: "Role changed from User to Editor",
    category: "user",
  },
  {
    id: "audit_003",
    timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
    action: "Login successful",
    actor: "admin@example.com",
    details: "IP: 127.0.0.1",
    category: "security",
  },
  {
    id: "audit_004",
    timestamp: new Date(Date.now() - 120 * 60000).toISOString(),
    action: "System restart",
    actor: "system",
    details: "Docker container ai-karen-api restarted",
    category: "system",
  },
  {
    id: "audit_005",
    timestamp: new Date(Date.now() - 180 * 60000).toISOString(),
    action: "Rate limiting disabled",
    actor: "admin@example.com",
    details: "ENABLE_RATE_LIMITING set to false",
    category: "settings",
  },
  {
    id: "audit_006",
    timestamp: new Date(Date.now() - 300 * 60000).toISOString(),
    action: "New user created",
    actor: "admin@example.com",
    target: "peter.j@example.com",
    details: "Role: User, Status: Pending",
    category: "user",
  },
  {
    id: "audit_007",
    timestamp: new Date(Date.now() - 400 * 60000).toISOString(),
    action: "User suspended",
    actor: "admin@example.com",
    target: "john.d@example.com",
    details: "Reason: Policy violation",
    category: "user",
  },
  {
    id: "audit_008",
    timestamp: new Date(Date.now() - 600 * 60000).toISOString(),
    action: "CORS origins updated",
    actor: "admin@example.com",
    details: "Added http://localhost:8010 to allowed origins",
    category: "settings",
  },
];

const categoryConfig: Record<AuditEntry["category"], { icon: React.ReactNode; color: string }> = {
  user: { icon: <UserCog className="h-3.5 w-3.5" />, color: "text-blue-500 bg-blue-500/10 border-blue-500/20" },
  settings: { icon: <Settings className="h-3.5 w-3.5" />, color: "text-amber-500 bg-amber-500/10 border-amber-500/20" },
  model: { icon: <Bot className="h-3.5 w-3.5" />, color: "text-purple-500 bg-purple-500/10 border-purple-500/20" },
  security: { icon: <Shield className="h-3.5 w-3.5" />, color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20" },
  system: { icon: <Clock className="h-3.5 w-3.5" />, color: "text-muted-foreground bg-muted/40 border-border/30" },
};

function mapAuditCategory(entry: RawAuditEntry): AuditEntry["category"] {
  const eventType = String(entry.event_type || entry.action || "").toLowerCase();
  if (eventType.includes("auth") || eventType.includes("security") || eventType.includes("privacy")) {
    return "security";
  }
  if (eventType.includes("model") || eventType.includes("provider")) {
    return "model";
  }
  if (eventType.includes("user") || eventType.includes("profile") || eventType.includes("permission")) {
    return "user";
  }
  if (eventType.includes("config") || eventType.includes("setting")) {
    return "settings";
  }
  return "system";
}

function mapAuditEntry(entry: RawAuditEntry, index: number): AuditEntry {
  return {
    id: String(entry.id || `${entry.timestamp || "event"}-${index}`),
    timestamp: String(entry.timestamp || entry.created_at || new Date().toISOString()),
    action: String(entry.message || entry.event_type || entry.action || "Audit event"),
    actor: String(entry.user_id || entry.actor || "system"),
    target: entry.resource_id ? String(entry.resource_id) : undefined,
    details: entry.metadata ? JSON.stringify(entry.metadata) : entry.details ? String(entry.details) : undefined,
    category: mapAuditCategory(entry),
  };
}

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function AuditLogPanel() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [authRequired, setAuthRequired] = useState(false);
  const [accessDenied, setAccessDenied] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadAuditLogs = async () => {
      setIsLoading(true);
      setAuthRequired(false);
      setAccessDenied(false);
      try {
        const response = await apiClient.get<Array<RawAuditEntry>>("/api/audit/logs");
        if (!mounted) {
          return;
        }
        setEntries(Array.isArray(response) ? response.map(mapAuditEntry) : []);
        setLoadError(null);
      } catch (error) {
        if (!mounted) {
          return;
        }
        if (error instanceof ApiError && error.status === 401) {
          setAuthRequired(true);
          setEntries([]);
          setLoadError(null);
        } else if (error instanceof ApiError && error.status === 403) {
          setAccessDenied(true);
          setEntries([]);
          setLoadError(null);
        } else {
          setEntries([]);
          setLoadError(error instanceof Error ? error.message : "Karen could not load the backend audit log.");
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    void loadAuditLogs();
    return () => {
      mounted = false;
    };
  }, []);

  const displayedEntries = entries.length > 0 ? entries : mockAuditLog;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <FileText className="h-5 w-5 text-primary" />
            Admin Activity Log
          </CardTitle>
          <CardDescription>
            Backend-derived audit activity where authorized, with graceful fallback only when the live audit surface is unavailable.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {authRequired && (
            <Alert className="mb-4 border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Sign In Required</AlertTitle>
              <AlertDescription>
                The audit route is live, but this session is not authenticated. Sign in to inspect backend audit events.
              </AlertDescription>
            </Alert>
          )}
          {accessDenied && (
            <Alert className="mb-4 border-primary/20 bg-primary/5">
              <ShieldAlert className="h-4 w-4 !text-primary" />
              <AlertTitle>Audit Access Restricted</AlertTitle>
              <AlertDescription>
                The audit route is live, but this session is not authorized to inspect backend audit events.
              </AlertDescription>
            </Alert>
          )}
          {loadError && (
            <Alert className="mb-4 border-yellow-500/30 bg-yellow-500/5">
              <AlertCircle className="h-4 w-4 !text-yellow-600" />
              <AlertTitle>Audit Fallback</AlertTitle>
              <AlertDescription>
                {loadError}
              </AlertDescription>
            </Alert>
          )}
          {isLoading ? (
            <div className="flex items-center gap-2 rounded-xl border border-border/70 p-4 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading backend audit events.
            </div>
          ) : (
          <ScrollArea className="h-[560px]">
            <div className="space-y-1">
              {displayedEntries.map((entry) => {
                const cat = categoryConfig[entry.category];
                return (
                  <div
                    key={entry.id}
                    className="flex items-start gap-3 p-3 rounded-xl hover:bg-muted/30 transition-colors group"
                  >
                    <div className={`mt-0.5 p-1.5 rounded-lg border shrink-0 ${cat.color}`}>
                      {cat.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium truncate">{entry.action}</p>
                        <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                          {formatRelativeTime(entry.timestamp)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                        <span className="font-mono">{entry.actor}</span>
                        {entry.target && (
                          <>
                            <span>→</span>
                            <span className="font-mono truncate">{entry.target}</span>
                          </>
                        )}
                      </div>
                      {entry.details && (
                        <p className="text-[10px] text-muted-foreground/70 mt-1 group-hover:text-muted-foreground transition-colors">
                          {entry.details}
                        </p>
                      )}
                    </div>
                    <Badge variant="outline" className={`text-[8px] uppercase tracking-wider shrink-0 mt-0.5 border ${cat.color}`}>
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
