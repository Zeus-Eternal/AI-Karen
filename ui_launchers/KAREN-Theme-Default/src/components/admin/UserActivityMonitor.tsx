// ui_launchers/KAREN-Theme-Default/src/components/admin/UserActivityMonitor.tsx
/**
 * User Activity Monitor Component
 *
 * Provides comprehensive user activity monitoring and reporting features
 * including login tracking, action history, and security events.
 *
 * Requirements: 4.6, 7.3, 7.4
 */

"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useRole } from "@/hooks/useRole";
import {
  type AuditLog,
  type ActivitySummary,
  type SecurityEvent,
  type AdminApiResponse,
  type PaginatedResponse,
  type AuditLogFilter,
  type PaginationParams,
} from "@/types/admin";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export type ViewMode = "summary" | "audit-logs" | "security-events" | "login-activity";

export interface UserActivityMonitorProps {
  className?: string;
}

const DEFAULT_PAGE_LIMIT = 20;

export function UserActivityMonitor({ className = "" }: UserActivityMonitorProps) {
  const { hasRole } = useRole();

  // ----- view state -----
  const [currentView, setCurrentView] = useState<ViewMode>("summary");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // ----- summary -----
  const [activitySummary, setActivitySummary] = useState<ActivitySummary | null>(null);

  // ----- audit logs -----
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [auditFilters, setAuditFilters] = useState<AuditLogFilter>({});
  const [auditPagination, setAuditPagination] = useState<PaginationParams>({
    page: 1,
    limit: DEFAULT_PAGE_LIMIT,
    sort_by: "timestamp",
    sort_order: "desc",
  });
  const [auditTotalPages, setAuditTotalPages] = useState<number>(1);

  // ----- security events -----
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [securityPagination, setSecurityPagination] = useState<PaginationParams>({
    page: 1,
    limit: DEFAULT_PAGE_LIMIT,
    sort_by: "created_at",
    sort_order: "desc",
  });
  const [securityTotalPages, setSecurityTotalPages] = useState<number>(1);

  // Abort control to cancel in-flight fetches on rapid tab/filter changes
  const abortRef = useRef<AbortController | null>(null);
  const resetAbort = () => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();
    return abortRef.current.signal;
  };

  // With role hierarchy, super_admins automatically pass hasRole("admin")
  const guard = hasRole("admin");

  // ---------- utilities ----------
  const formatDate = useCallback((date: Date | string) => {
    const d = typeof date === "string" ? new Date(date) : date;
    // Use user's locale; show 2-digit hour:minute
    return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  }, []);

  const getActionColor = (action: string) => {
    const a = action.toLowerCase();
    if (a.includes("create")) return "bg-green-100 text-green-800";
    if (a.includes("delete")) return "bg-red-100 text-red-800";
    if (a.includes("update") || a.includes("edit")) return "bg-blue-100 text-blue-800";
    if (a.includes("login") || a.includes("auth")) return "bg-purple-100 text-purple-800";
    return "bg-gray-100 text-gray-800";
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-red-100 text-red-800";
      case "high":
        return "bg-orange-100 text-orange-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "low":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const buildQueryParams = (obj: Record<string, unknown>) => {
    const params = new URLSearchParams();
    Object.entries(obj).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") return;
      if (value instanceof Date) {
        params.append(key, value.toISOString());
      } else {
        params.append(key, String(value));
      }
    });
    return params;
  };

  const resetToFirstPage = useCallback(() => {
    setAuditPagination((p) => ({ ...p, page: 1 }));
    setSecurityPagination((p) => ({ ...p, page: 1 }));
  }, []);

  // ---------- data loaders ----------
  const loadActivitySummary = useCallback(async () => {
    const signal = resetAbort();
    const res = await fetch("/api/admin/system/activity-summary?period=week", { signal });
    if (!res.ok) throw new Error("Failed to load activity summary");
    const data: AdminApiResponse<ActivitySummary> = await res.json();
    if (!data.success) throw new Error(data.error?.message || "Failed to load activity summary");
    setActivitySummary(data.data ?? null);
  }, []);

  const loadAuditLogs = useCallback(async () => {
    const params = buildQueryParams({
      page: auditPagination.page,
      limit: auditPagination.limit,
      sort_by: auditPagination.sort_by || "timestamp",
      sort_order: auditPagination.sort_order || "desc",
      ...auditFilters,
    });

    const signal = resetAbort();
    const res = await fetch(`/api/admin/system/audit-logs?${params.toString()}`, { signal });
    if (!res.ok) throw new Error("Failed to load audit logs");
    const data: AdminApiResponse<PaginatedResponse<AuditLog>> = await res.json();
    if (!data.success || !data.data) throw new Error(data.error?.message || "Failed to load audit logs");

    setAuditLogs(data.data.data || []);
    setAuditTotalPages(data.data.pagination.total_pages || 1);
  }, [auditFilters, auditPagination.limit, auditPagination.page, auditPagination.sort_by, auditPagination.sort_order]);

  const loadSecurityEvents = useCallback(async () => {
    const params = buildQueryParams({
      page: securityPagination.page,
      limit: securityPagination.limit,
      sort_by: securityPagination.sort_by || "created_at",
      sort_order: securityPagination.sort_order || "desc",
    });

    const signal = resetAbort();
    const res = await fetch(`/api/admin/security/events?${params.toString()}`, { signal });
    if (!res.ok) throw new Error("Failed to load security events");
    const data: AdminApiResponse<PaginatedResponse<SecurityEvent>> = await res.json();
    if (!data.success || !data.data) throw new Error(data.error?.message || "Failed to load security events");

    setSecurityEvents(data.data.data || []);
    setSecurityTotalPages(data.data.pagination.total_pages || 1);
  }, [securityPagination.limit, securityPagination.page, securityPagination.sort_by, securityPagination.sort_order]);

  const loadLoginActivity = useCallback(async () => {
    // user.login for last 7 days
    const loginFilters: AuditLogFilter = {
      action: "user.login",
      start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    };
    setAuditFilters(loginFilters);
    setAuditPagination((p) => ({ ...p, page: 1, sort_by: "timestamp", sort_order: "desc" }));
    await loadAuditLogs();
  }, [loadAuditLogs]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (!guard) throw new Error("Insufficient permissions.");
      switch (currentView) {
        case "summary":
          await loadActivitySummary();
          break;
        case "audit-logs":
          await loadAuditLogs();
          break;
        case "security-events":
          await loadSecurityEvents();
          break;
        case "login-activity":
          await loadLoginActivity();
          break;
        default:
          await loadActivitySummary();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentView, guard, loadActivitySummary, loadAuditLogs, loadLoginActivity, loadSecurityEvents]);

  // Trigger loads
  useEffect(() => {
    loadData();
    return () => abortRef.current?.abort();
  }, [loadData, auditFilters, auditPagination.page, auditPagination.limit, auditPagination.sort_by, auditPagination.sort_order, securityPagination.page, securityPagination.limit, securityPagination.sort_by, securityPagination.sort_order]);

  // ---------- memo helpers ----------
  const actionFilterValue = auditFilters.action ?? "";
  const resourceTypeFilterValue = auditFilters.resource_type ?? "";
  const startDateStr = auditFilters.start_date ? new Date(auditFilters.start_date).toISOString().split("T")[0] : "";
  const endDateStr = auditFilters.end_date ? new Date(auditFilters.end_date).toISOString().split("T")[0] : "";

  // ---------- renderers ----------
  const renderNavigationTabs = () => (
    <div className="border-b border-gray-200 mb-6">
      <nav className="-mb-px flex flex-wrap gap-2 md:space-x-8">
        {[
          { id: "summary", label: "Activity Summary" },
          { id: "audit-logs", label: "Audit Logs" },
          { id: "security-events", label: "Security Events" },
          { id: "login-activity", label: "Login Activity" },
        ].map((tab) => (
          <Button
            key={tab.id}
            variant={currentView === (tab.id as ViewMode) ? "default" : "ghost"}
            onClick={() => setCurrentView(tab.id as ViewMode)}
            aria-pressed={currentView === tab.id}
            aria-label={`Show ${tab.label}`}
          >
            {tab.label}
          </Button>
        ))}
      </nav>
    </div>
  );

  const renderActivitySummary = () => {
    if (!activitySummary) return null;
    return (
      <div className="space-y-6">
        {/* key metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm text-muted-foreground">User Registrations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">{activitySummary.user_registrations}</div>
              <div className="text-sm text-muted-foreground">This {activitySummary.period}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm text-muted-foreground">Admin Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{activitySummary.admin_actions}</div>
              <div className="text-sm text-muted-foreground">Administrative operations</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm text-muted-foreground">Successful Logins</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">{activitySummary.successful_logins}</div>
              <div className="text-sm text-muted-foreground">Authentication success</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm text-muted-foreground">Failed Logins</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-600">{activitySummary.failed_logins}</div>
              <div className="text-sm text-muted-foreground">Authentication failures</div>
            </CardContent>
          </Card>
        </div>

        {/* Top actions & users */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Top Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {activitySummary.top_actions.map((a, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="capitalize">{a.action.replaceAll("_", " ")}</span>
                  <Badge variant="secondary">{a.count}</Badge>
                </div>
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Most Active Users</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {activitySummary.top_users.map((u, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span>{u.email}</span>
                  <Badge variant="outline">{u.action_count} actions</Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  };

  const renderAuditToolbar = () => (
    <div className="flex flex-col gap-3 md:grid md:grid-cols-12 md:items-end">
      <div className="md:col-span-3">
        <Input
          aria-label="Filter by action"
          placeholder="Filter by action…"
          value={actionFilterValue}
          onChange={(e) => {
            setAuditFilters((prev) => ({ ...prev, action: e.target.value || undefined }));
            resetToFirstPage();
          }}
        />
      </div>
      <div className="md:col-span-3">
        <Input
          aria-label="Filter by resource type"
          placeholder="Filter by resource type…"
          value={resourceTypeFilterValue}
          onChange={(e) => {
            setAuditFilters((prev) => ({ ...prev, resource_type: e.target.value || undefined }));
            resetToFirstPage();
          }}
        />
      </div>
      <div className="md:col-span-2">
        <Input
          type="date"
          aria-label="Start date"
          value={startDateStr}
          onChange={(e) => {
            setAuditFilters((prev) => ({
              ...prev,
              start_date: e.target.value ? new Date(e.target.value) : undefined,
            }));
            resetToFirstPage();
          }}
        />
      </div>
      <div className="md:col-span-2">
        <Input
          type="date"
          aria-label="End date"
          value={endDateStr}
          onChange={(e) => {
            setAuditFilters((prev) => ({
              ...prev,
              end_date: e.target.value ? new Date(e.target.value) : undefined,
            }));
            resetToFirstPage();
          }}
        />
      </div>
      <div className="md:col-span-2 flex gap-2">
        <Select
          value={auditPagination.sort_order || "desc"}
          onValueChange={(v) => setAuditPagination((p) => ({ ...p, page: 1, sort_order: v as "asc" | "desc" }))}
        >
          <SelectTrigger aria-label="Sort order">
            <SelectValue placeholder="Sort order" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="desc">Newest first</SelectItem>
            <SelectItem value="asc">Oldest first</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={String(auditPagination.limit)}
          onValueChange={(v) => setAuditPagination((p) => ({ ...p, page: 1, limit: Number(v) }))}
        >
          <SelectTrigger aria-label="Rows per page">
            <SelectValue placeholder="Rows/page" />
          </SelectTrigger>
          <SelectContent>
            {[10, 20, 50, 100].map((n) => (
              <SelectItem key={n} value={String(n)}>
                {n}/page
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );

  const renderAuditLogs = () => (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle>Audit Logs</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Filters */}
        <div className="bg-muted/30 rounded-md p-4 border">{renderAuditToolbar()}</div>
        {/* Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200" role="table" aria-label="Audit log table">
            <thead className="bg-gray-50">
              <tr>
                {["Timestamp", "User", "Action", "Resource", "IP Address"].map((h) => (
                  <th
                    key={h}
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {auditLogs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-6 py-3 whitespace-nowrap text-sm">{formatDate(log.timestamp)}</td>
                  <td className="px-6 py-3 whitespace-nowrap text-sm">{log.user?.email || log.user_id}</td>
                  <td className="px-6 py-3 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getActionColor(log.action)}`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="px-6 py-3 whitespace-nowrap text-sm">
                    {log.resource_type}
                    {log.resource_id && <span className="text-gray-500"> ({String(log.resource_id).slice(0, 8)}…)</span>}
                  </td>
                  <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-600">{log.ip_address || "Unknown"}</td>
                </tr>
              ))}
              {auditLogs.length === 0 && (
                <tr>
                  <td className="px-6 py-6 text-sm text-center text-muted-foreground" colSpan={5}>
                    No audit logs found for the selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {/* Pagination */}
        <div className="flex items-center justify-between gap-2 pt-2">
          <div className="text-sm text-muted-foreground">
            Page <span className="font-medium">{auditPagination.page}</span> of{" "}
            <span className="font-medium">{auditTotalPages}</span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => setAuditPagination((p) => ({ ...p, page: Math.max(1, p.page - 1) }))}
              disabled={auditPagination.page <= 1}
              aria-label="Previous page"
            >
              Prev
            </Button>
            <Button
              variant="outline"
              onClick={() => setAuditPagination((p) => ({ ...p, page: Math.min(auditTotalPages, p.page + 1) }))}
              disabled={auditPagination.page >= auditTotalPages}
              aria-label="Next page"
            >
              Next
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderSecurityEvents = () => (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle>Security Events</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Basic pagination controls */}
        <div className="flex items-center justify-between gap-2">
          <div className="text-sm text-muted-foreground">
            Page <span className="font-medium">{securityPagination.page}</span> of{" "}
            <span className="font-medium">{securityTotalPages}</span>
          </div>
          <div className="flex items-center gap-2">
            <Select
              value={String(securityPagination.limit)}
              onValueChange={(v) => setSecurityPagination((p) => ({ ...p, page: 1, limit: Number(v) }))}
            >
              <SelectTrigger aria-label="Rows per page">
                <SelectValue placeholder="Rows/page" />
              </SelectTrigger>
              <SelectContent>
                {[10, 20, 50, 100].map((n) => (
                  <SelectItem key={n} value={String(n)}>
                    {n}/page
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={() => setSecurityPagination((p) => ({ ...p, page: Math.max(1, p.page - 1) }))}
              disabled={securityPagination.page <= 1}
              aria-label="Previous page"
            >
              Prev
            </Button>
            <Button
              variant="outline"
              onClick={() => setSecurityPagination((p) => ({ ...p, page: Math.min(securityTotalPages, p.page + 1) }))}
              disabled={securityPagination.page >= securityTotalPages}
              aria-label="Next page"
            >
              Next
            </Button>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200" role="table" aria-label="Security events table">
            <thead className="bg-gray-50">
              <tr>
                {["Timestamp", "Event", "Severity", "User", "IP Address", "Status"].map((h) => (
                  <th
                    key={h}
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {securityEvents.map((event) => (
                <tr key={event.id} className="hover:bg-gray-50">
                  <td className="px-6 py-3 whitespace-nowrap text-sm">{formatDate(event.created_at)}</td>
                  <td className="px-6 py-3 whitespace-nowrap text-sm">{event.event_type.replaceAll("_", " ")}</td>
                  <td className="px-6 py-3 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(event.severity)}`}>
                      {event.severity}
                    </span>
                  </td>
                  <td className="px-6 py-3 whitespace-nowrap text-sm">{event.user_id || "Unknown"}</td>
                  <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-600">{event.ip_address || "Unknown"}</td>
                  <td className="px-6 py-3 whitespace-nowrap">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        event.resolved ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                      }`}
                    >
                      {event.resolved ? "Resolved" : "Open"}
                    </span>
                  </td>
                </tr>
              ))}
              {securityEvents.length === 0 && (
                <tr>
                  <td className="px-6 py-6 text-sm text-center text-muted-foreground" colSpan={6}>
                    No security events found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );

  const renderCurrentView = () => {
    switch (currentView) {
      case "summary":
        return renderActivitySummary();
      case "audit-logs":
        return renderAuditLogs();
      case "security-events":
        return renderSecurityEvents();
      case "login-activity":
        return renderAuditLogs(); // same table, login filter applied
      default:
        return renderActivitySummary();
    }
  };

  // ---------- render root ----------
  if (!guard) {
    return (
      <div className={className}>
        <Card>
          <CardHeader>
            <CardTitle>User Activity Monitor</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-600">You do not have permission to view this page.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <Skeleton className="h-7 w-64" />
          <div className="flex gap-2">
            <Skeleton className="h-9 w-28" />
            <Skeleton className="h-9 w-28" />
          </div>
        </div>
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold">User Activity Monitor</h2>
        <p className="text-muted-foreground mt-1">Monitor user activity, audit logs, and security events</p>
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800">{error}</p>
            <Button onClick={loadData} variant="link" className="mt-2 p-0 h-auto">
              Retry
            </Button>
          </div>
        )}
      </div>

      {/* Navigation */}
      {renderNavigationTabs()}

      {/* Content */}
      {renderCurrentView()}
    </div>
  );
}
