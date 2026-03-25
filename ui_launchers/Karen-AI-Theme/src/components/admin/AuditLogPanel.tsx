"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText, UserCog, Settings, Bot, Shield, Clock } from "lucide-react";

type AuditEntry = {
  id: string;
  timestamp: string;
  action: string;
  actor: string;
  target?: string;
  details?: string;
  category: "user" | "settings" | "model" | "security" | "system";
};

const mockAuditLog: AuditEntry[] = [
  {
    id: "audit_001",
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
    action: "Model configuration updated",
    actor: "admin@example.com",
    target: "llama-cpp / Phi-3-mini-4k-instruct-q4.gguf",
    details: "Changed default provider from ollama to llama-cpp",
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
    details: "IP: 172.21.0.1",
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
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <FileText className="h-5 w-5 text-primary" />
            Admin Activity Log
          </CardTitle>
          <CardDescription>
            Recent administrative actions and system events. This is a preview — full audit logging will be connected to the backend.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[560px]">
            <div className="space-y-1">
              {mockAuditLog.map((entry) => {
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
        </CardContent>
      </Card>
    </div>
  );
}
