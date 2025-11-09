"use client";

import React, { useMemo, useState } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Download,
  FileText,
  Info,
  Lock,
  RefreshCw,
  Search,
  Settings,
  Shield,
  Unlock,
  XCircle,
} from "lucide-react";

import type { PluginInfo, PluginAuditEntry, PluginLogEntry } from "@/types/plugins";

/**
 * Plugin Audit Logger Component
 * Production-ready, shadcn-correct, and type-safe.
 */

export interface AuditSummary {
  totalEvents: number;
  criticalEvents: number;
  securityEvents: number;
  configurationChanges: number;
  permissionChanges: number;
  lastActivity: Date;
  topUsers: Array<{ userId: string; count: number }>;
  eventsByType: Record<string, number>;
  eventsByDay: Array<{ date: string; count: number }>;
}

export interface ComplianceReport {
  id: string;
  name: string;
  description: string;
  status: "compliant" | "non-compliant" | "warning";
  lastCheck: Date;
  requirements: Array<{
    id: string;
    description: string;
    status: "met" | "not-met" | "partial";
    evidence: string[];
  }>;
}

export interface PluginAuditLoggerProps {
  plugin: PluginInfo;
  onExportAuditLog?: (format: "csv" | "json" | "pdf") => void;
  onGenerateReport?: (type: "compliance" | "security" | "activity") => void;
}

/* -------------------- Mock Data (replace with API) -------------------- */

const mockAuditEntries: PluginAuditEntry[] = [
  {
    id: "audit-1",
    pluginId: "slack-integration",
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    action: "configure",
    userId: "admin@example.com",
    details: {
      field: "botToken",
      oldValue: "[REDACTED]",
      newValue: "[REDACTED]",
      reason: "Token rotation",
    },
    ipAddress: "192.168.1.100",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  },
  {
    id: "audit-2",
    pluginId: "slack-integration",
    timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
    action: "permission_grant",
    userId: "admin@example.com",
    details: {
      permission: "slack-workspace",
      level: "write",
      reason: "Required for message sending",
      security: true,
    },
    ipAddress: "192.168.1.100",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  },
  {
    id: "audit-3",
    pluginId: "slack-integration",
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
    action: "enable",
    userId: "admin@example.com",
    details: {
      previousStatus: "inactive",
      newStatus: "active",
      autoStart: true,
    },
    ipAddress: "192.168.1.100",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  },
];

const mockLogEntries: PluginLogEntry[] = [
  {
    id: "log-1",
    pluginId: "slack-integration",
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    level: "info",
    message: "Successfully connected to Slack workspace",
    context: { workspace: "acme-corp", channels: 15 },
    source: "slack-connector",
    userId: "system",
  },
  {
    id: "log-2",
    pluginId: "slack-integration",
    timestamp: new Date(Date.now() - 45 * 60 * 1000),
    level: "warn",
    message: "Rate limit approaching for Slack API",
    context: { remaining: 50, resetTime: "2024-01-15T10:30:00Z" },
    source: "rate-limiter",
  },
  {
    id: "log-3",
    pluginId: "slack-integration",
    timestamp: new Date(Date.now() - 60 * 60 * 1000),
    level: "error",
    message: "Failed to send message to channel",
    context: { channel: "#general", error: "channel_not_found" },
    source: "message-sender",
  },
];

const mockComplianceReports: ComplianceReport[] = [
  {
    id: "gdpr",
    name: "GDPR Compliance",
    description: "General Data Protection Regulation compliance check",
    status: "compliant",
    lastCheck: new Date(Date.now() - 24 * 60 * 60 * 1000),
    requirements: [
      {
        id: "data-encryption",
        description: "All personal data must be encrypted at rest and in transit",
        status: "met",
        evidence: ["TLS 1.3 for transit", "AES-256 for storage"],
      },
      {
        id: "audit-logging",
        description: "All data access must be logged and auditable",
        status: "met",
        evidence: ["Comprehensive audit trail", "Immutable log storage"],
      },
    ],
  },
  {
    id: "sox",
    name: "SOX Compliance",
    description: "Sarbanes-Oxley Act compliance for financial data",
    status: "warning",
    lastCheck: new Date(Date.now() - 48 * 60 * 60 * 1000),
    requirements: [
      {
        id: "access-controls",
        description: "Strict access controls for financial data",
        status: "partial",
        evidence: ["Role-based access implemented", "Missing segregation of duties"],
      },
    ],
  },
];

/* -------------------- Component -------------------- */

export const PluginAuditLogger: React.FC<PluginAuditLoggerProps> = ({
  plugin,
  onExportAuditLog,
  onGenerateReport,
}) => {
  const [auditEntries] = useState<PluginAuditEntry[]>(mockAuditEntries);
  const [logEntries] = useState<PluginLogEntry[]>(mockLogEntries);
  const [complianceReports] = useState<ComplianceReport[]>(mockComplianceReports);

  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState<string>("all");
  const [levelFilter, setLevelFilter] = useState<string>("all");
  const [dateRange, setDateRange] = useState<string>("7d");
  const [selectedEntry, setSelectedEntry] = useState<PluginAuditEntry | null>(null);
  const [loading, setLoading] = useState(false);

  const auditSummary: AuditSummary = useMemo(() => {
    const now = new Date();
    const rangeMs =
      {
        "1d": 24 * 60 * 60 * 1000,
        "7d": 7 * 24 * 60 * 60 * 1000,
        "30d": 30 * 24 * 60 * 60 * 1000,
        "90d": 90 * 24 * 60 * 60 * 1000,
      }[dateRange] ?? 7 * 24 * 60 * 60 * 1000;

    const withinRange = auditEntries.filter(
      (e) => now.getTime() - e.timestamp.getTime() <= rangeMs
    );

    const eventsByType: Record<string, number> = {};
    const userCounts: Record<string, number> = {};
    const dayCounts: Record<string, number> = {};

    for (const e of withinRange) {
      eventsByType[e.action] = (eventsByType[e.action] || 0) + 1;
      userCounts[e.userId] = (userCounts[e.userId] || 0) + 1;
      const dayKey = e.timestamp.toISOString().slice(0, 10);
      dayCounts[dayKey] = (dayCounts[dayKey] || 0) + 1;
    }

    const topUsers = Object.entries(userCounts)
      .map(([userId, count]) => ({ userId, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    const lastActivity =
      withinRange.length > 0
        ? new Date(Math.max(...withinRange.map((e) => e.timestamp.getTime())))
        : new Date(0);

    return {
      totalEvents: withinRange.length,
      criticalEvents: withinRange.filter((e) =>
        ["permission_grant", "permission_revoke", "uninstall"].includes(e.action)
      ).length,
      securityEvents: withinRange.filter(
        (e) => e.action.includes("permission") || (e.details as any)?.security
      ).length,
      configurationChanges: withinRange.filter((e) => e.action === "configure").length,
      permissionChanges: withinRange.filter((e) => e.action.includes("permission")).length,
      lastActivity,
      topUsers,
      eventsByType,
      eventsByDay: Object.entries(dayCounts)
        .map(([date, count]) => ({ date, count }))
        .sort((a, b) => (a.date < b.date ? -1 : 1)),
    };
  }, [auditEntries, dateRange]);

  const filteredAuditEntries = useMemo(() => {
    return auditEntries.filter((entry) => {
      const matchesSearch =
        !searchQuery ||
        entry.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
        entry.userId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        JSON.stringify(entry.details).toLowerCase().includes(searchQuery.toLowerCase());

      const matchesAction = actionFilter === "all" || entry.action === actionFilter;

      return matchesSearch && matchesAction;
    });
  }, [auditEntries, searchQuery, actionFilter]);

  const filteredLogEntries = useMemo(() => {
    return logEntries.filter((entry) => {
      const matchesSearch =
        !searchQuery ||
        entry.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
        entry.source.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesLevel = levelFilter === "all" || entry.level === levelFilter;

      return matchesSearch && matchesLevel;
    });
  }, [logEntries, searchQuery, levelFilter]);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      // Hook up to your API here
      await new Promise((r) => setTimeout(r, 800));
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (format: "csv" | "json" | "pdf") => {
    onExportAuditLog?.(format);
  };

  const getActionIcon = (action: string) => {
    const map = {
      install: Download,
      uninstall: XCircle,
      enable: CheckCircle,
      disable: XCircle,
      configure: Settings,
      update: RefreshCw,
      permission_grant: Unlock,
      permission_revoke: Lock,
    };
    return (map as any)[action] ?? Activity;
  };

  const getActionColor = (action: string) => {
    const colors: Record<string, string> = {
      install: "text-green-600",
      uninstall: "text-red-600",
      enable: "text-green-600",
      disable: "text-orange-600",
      configure: "text-blue-600",
      update: "text-blue-600",
      permission_grant: "text-green-600",
      permission_revoke: "text-red-600",
    };
    return colors[action] ?? "text-gray-600";
  };

  const getLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      debug: "text-gray-600",
      info: "text-blue-600",
      warn: "text-yellow-600",
      error: "text-red-600",
    };
    return colors[level] ?? "text-gray-600";
  };

  const renderAuditEntry = (entry: PluginAuditEntry) => {
    const ActionIcon = getActionIcon(entry.action);
    const actionColor = getActionColor(entry.action);

    return (
      <TableRow
        key={entry.id}
        className="cursor-pointer hover:bg-muted/50"
        onClick={() => setSelectedEntry(entry)}
      >
        <TableCell>
          <div className="flex items-center gap-2">
            <ActionIcon className={`w-4 h-4 ${actionColor}`} />
            <span className="font-medium capitalize">{entry.action.replace("_", " ")}</span>
          </div>
        </TableCell>
        <TableCell>{entry.timestamp.toLocaleString()}</TableCell>
        <TableCell>{entry.userId}</TableCell>
        <TableCell>
          <div className="max-w-xs truncate">
            {typeof entry.details === "object" ? Object.keys(entry.details).join(", ") : entry.details}
          </div>
        </TableCell>
        <TableCell>
          <div className="text-xs text-muted-foreground">{entry.ipAddress}</div>
        </TableCell>
      </TableRow>
    );
  };

  const renderLogEntry = (entry: PluginLogEntry) => {
    const levelColor = getLevelColor(entry.level);
    return (
      <TableRow key={entry.id}>
        <TableCell>
          <Badge variant="outline" className={`text-xs ${levelColor}`}>
            {entry.level.toUpperCase()}
          </Badge>
        </TableCell>
        <TableCell>{entry.timestamp.toLocaleString()}</TableCell>
        <TableCell>{entry.source}</TableCell>
        <TableCell>
          <div className="max-w-md">{entry.message}</div>
        </TableCell>
        <TableCell>
          {entry.context && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Info className="w-4 h-4 text-muted-foreground" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <pre className="text-xs max-w-xs overflow-auto">
                    {JSON.stringify(entry.context, null, 2)}
                  </pre>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </TableCell>
      </TableRow>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Audit &amp; Compliance</h2>
          <p className="text-muted-foreground">Activity tracking and compliance reporting for {plugin.name}</p>
        </div>

        <div className="flex items-center gap-2">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Date range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1d">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          <Select onValueChange={(v: "csv" | "json" | "pdf") => handleExport(v)}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Export" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="csv">CSV</SelectItem>
              <SelectItem value="json">JSON</SelectItem>
              <SelectItem value="pdf">PDF</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium">Total Events</span>
            </div>
            <div className="text-2xl font-bold mt-2">{auditSummary.totalEvents}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600" />
              <span className="text-sm font-medium">Critical Events</span>
            </div>
            <div className="text-2xl font-bold mt-2">{auditSummary.criticalEvents}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium">Security Events</span>
            </div>
            <div className="text-2xl font-bold mt-2">{auditSummary.securityEvents}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4 text-orange-600" />
              <span className="text-sm font-medium">Config Changes</span>
            </div>
            <div className="text-2xl font-bold mt-2">{auditSummary.configurationChanges}</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="audit" className="space-y-4">
        <TabsList>
          <TabsTrigger value="audit">Audit Log</TabsTrigger>
          <TabsTrigger value="logs">System Logs</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Audit Tab */}
        <TabsContent value="audit" className="space-y-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-center">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search audit entries…"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>

                <Select value={actionFilter} onValueChange={setActionFilter}>
                  <SelectTrigger className="w-56">
                    <SelectValue placeholder="Filter by action" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Actions</SelectItem>
                    <SelectItem value="install">Install</SelectItem>
                    <SelectItem value="uninstall">Uninstall</SelectItem>
                    <SelectItem value="enable">Enable</SelectItem>
                    <SelectItem value="disable">Disable</SelectItem>
                    <SelectItem value="configure">Configure</SelectItem>
                    <SelectItem value="permission_grant">Grant Permission</SelectItem>
                    <SelectItem value="permission_revoke">Revoke Permission</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Audit Entries</CardTitle>
              <CardDescription>Detailed log of all plugin-related activities</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Action</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Details</TableHead>
                    <TableHead>IP Address</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>{filteredAuditEntries.map(renderAuditEntry)}</TableBody>
              </Table>

              {filteredAuditEntries.length === 0 && (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <h3 className="text-lg font-medium mb-2">No Audit Entries</h3>
                  <p className="text-muted-foreground">Try changing the filters or date range.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-center">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search log entries…"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>

                <Select value={levelFilter} onValueChange={setLevelFilter}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Levels</SelectItem>
                    <SelectItem value="debug">Debug</SelectItem>
                    <SelectItem value="info">Info</SelectItem>
                    <SelectItem value="warn">Warning</SelectItem>
                    <SelectItem value="error">Error</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>System Logs</CardTitle>
              <CardDescription>Runtime messages and operational telemetry</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Level</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Message</TableHead>
                    <TableHead>Context</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>{filteredLogEntries.map(renderLogEntry)}</TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Compliance Tab */}
        <TabsContent value="compliance" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {complianceReports.map((report) => (
              <Card key={report.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{report.name}</CardTitle>
                    <Badge
                      variant={
                        report.status === "compliant"
                          ? "default"
                          : report.status === "warning"
                          ? "secondary"
                          : "destructive"
                      }
                      className="capitalize"
                    >
                      {report.status}
                    </Badge>
                  </div>
                  <CardDescription>{report.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="text-sm text-muted-foreground">
                      Last checked: {report.lastCheck.toLocaleDateString()}
                    </div>

                    <div className="space-y-2">
                      {report.requirements.map((req) => (
                        <div key={req.id} className="flex items-start gap-2">
                          {req.status === "met" ? (
                            <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
                          ) : req.status === "partial" ? (
                            <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-600 mt-0.5" />
                          )}
                          <div className="flex-1">
                            <div className="text-sm font-medium">{req.description}</div>
                            {req.evidence.length > 0 && (
                              <div className="text-xs text-muted-foreground mt-1">
                                Evidence: {req.evidence.join(", ")}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>

                    {onGenerateReport && (
                      <div className="pt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onGenerateReport("compliance")}
                        >
                          Generate Compliance Report
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Activity by Action Type</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(auditSummary.eventsByType).map(([action, count]) => (
                    <div key={action} className="flex items-center justify-between">
                      <span className="text-sm capitalize">{action.replace("_", " ")}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-muted rounded-full h-2">
                          <div
                            className="bg-primary h-2 rounded-full"
                            style={{
                              width: `${
                                auditSummary.totalEvents
                                  ? (count / auditSummary.totalEvents) * 100
                                  : 0
                              }%`,
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium w-8 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {auditSummary.topUsers.map((user, idx) => (
                    <div key={user.userId} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center text-xs">
                          {idx + 1}
                        </div>
                        <span className="text-sm">{user.userId}</span>
                      </div>
                      <Badge variant="outline">{user.count} events</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Audit Entry Detail */}
      <Dialog open={!!selectedEntry} onOpenChange={() => setSelectedEntry(null)}>
        <DialogContent className="max-w-2xl">
          {selectedEntry && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {React.createElement(getActionIcon(selectedEntry.action), {
                    className: `w-5 h-5 ${getActionColor(selectedEntry.action)}`,
                  })}
                  {selectedEntry.action.replace("_", " ").toUpperCase()}
                </DialogTitle>
                <DialogDescription>{selectedEntry.timestamp.toLocaleString()}</DialogDescription>
              </DialogHeader>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium">User</Label>
                    <div className="text-sm">{selectedEntry.userId}</div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">IP Address</Label>
                    <div className="text-sm font-mono">{selectedEntry.ipAddress}</div>
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium">Details</Label>
                  <pre className="text-xs bg-muted p-3 rounded mt-2 overflow-auto">
                    {JSON.stringify(selectedEntry.details, null, 2)}
                  </pre>
                </div>

                {selectedEntry.userAgent && (
                  <div>
                    <Label className="text-sm font-medium">User Agent</Label>
                    <div className="text-xs text-muted-foreground mt-1 break-words">
                      {selectedEntry.userAgent}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PluginAuditLogger;
