"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { getAuditLogger } from "@/lib/audit/audit-logger";

/**
 * Full, self-contained Audit Log Viewer with:
 * - Strong typing (filters, pagination, logs)
 * - Search query parser (key:value with smart parsing)
 * - Preset filters and advanced filters
 * - CSV/JSON export
 * - Multi-select with header checkbox
 * - Robust, accessible table UI
 */

/* ------------------------------------ Types ------------------------------------ */

type UUID = string;

interface UserRef {
  id?: UUID;
  email?: string;
  full_name?: string;
}

export interface AuditLog {
  id: UUID;
  timestamp: string | number | Date;
  user_id?: UUID;
  user?: UserRef;
  action: string;
  resource_type?: string;
  resource_id?: string;
  ip_address?: string;
  details?: Record<string, unknown>;
}

export interface PaginationParams {
  page: number;
  limit: number;
  sort?: "asc" | "desc";
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface AuditLogFilter {
  user_id?: string;
  user_email?: string;
  action?: string;
  resource_type?: string;
  resource_id?: string;
  ip_address?: string;
  start_date?: Date;
  end_date?: Date;
  q?: string; // raw free-text
}

/* --------------------------------- Utilities ---------------------------------- */

const auditPagination = {
  default(): PaginationParams {
    return { page: 1, limit: 50, sort: "desc" };
  },
};

const ACTION_CATEGORIES: Record<
  string,
  { name: string; actions: string[] }
> = {
  user: {
    name: "User",
    actions: [
      "user.create",
      "user.update",
      "user.delete",
      "user.login",
      "user.logout",
      "user.password.change",
    ],
  },
  security: {
    name: "Security",
    actions: [
      "security.mfa.setup",
      "security.mfa.verify",
      "security.lockout",
      "security.breach.attempt",
    ],
  },
  system: {
    name: "System",
    actions: [
      "system.config.update",
      "system.health.check",
      "system.job.run",
      "system.job.fail",
    ],
  },
  resource: {
    name: "Resource",
    actions: [
      "resource.create",
      "resource.update",
      "resource.delete",
      "resource.access",
    ],
  },
};

const RESOURCE_TYPE_CATEGORIES: Record<string, { value: string; name: string }> =
  {
    user: { value: "user", name: "User" },
    session: { value: "session", name: "Session" },
    plugin: { value: "plugin", name: "Plugin" },
    config: { value: "config", name: "Configuration" },
    document: { value: "document", name: "Document" },
    job: { value: "job", name: "Background Job" },
  };

const AUDIT_FILTER_PRESETS: Record<
  string,
  { name: string; filter: Partial<AuditLogFilter> }
> = {
  lastHour: { name: "Last Hour", filter: { start_date: hoursAgo(1) } },
  last24h: { name: "Last 24h", filter: { start_date: hoursAgo(24) } },
  logins: { name: "Logins", filter: { action: "user.login" } },
  security: {
    name: "Security Events",
    filter: { action: "security." }, // prefix match via backend or parser "q"
  },
  resourceChanges: {
    name: "Resource Changes",
    filter: { action: "resource." },
  },
};

function hoursAgo(h: number): Date {
  const d = new Date();
  d.setHours(d.getHours() - h);
  return d;
}

/** Converts an array of logs to CSV (RFC4180-ish). */
const AuditLogExporter = {
  toCsv(rows: AuditLog[]): string {
    const headers = [
      "id",
      "timestamp",
      "user_id",
      "user_email",
      "user_full_name",
      "action",
      "resource_type",
      "resource_id",
      "ip_address",
      "details",
    ];
    const escape = (v: unknown) => {
      const s =
        v === null || v === undefined
          ? ""
          : typeof v === "string"
          ? v
          : typeof v === "object"
          ? JSON.stringify(v)
          : String(v);
      const needsQuotes = /[",\n]/.test(s);
      const escaped = s.replace(/"/g, '""');
      return needsQuotes ? `"${escaped}"` : escaped;
    };
    const lines = [headers.join(",")];
    for (const r of rows) {
      lines.push(
        [
          r.id,
          new Date(r.timestamp).toISOString(),
          r.user_id ?? "",
          r.user?.email ?? "",
          r.user?.full_name ?? "",
          r.action,
          r.resource_type ?? "",
          r.resource_id ?? "",
          r.ip_address ?? "",
          r.details ? JSON.stringify(r.details) : "",
        ]
          .map(escape)
          .join(",")
      );
    }
    return lines.join("\n");
  },
  toJson(rows: AuditLog[], pretty = true): string {
    return pretty ? JSON.stringify(rows, null, 2) : JSON.stringify(rows);
  },
  generateFilename(fmt: "csv" | "json", filter: AuditLogFilter): string {
    const parts = ["audit-logs"];
    if (filter.user_email) parts.push(`user_${safeSlug(filter.user_email)}`);
    if (filter.action) parts.push(`action_${safeSlug(filter.action)}`);
    if (filter.resource_type) parts.push(`res_${safeSlug(filter.resource_type)}`);
    parts.push(new Date().toISOString().replace(/[:.]/g, "-"));
    return `${parts.join("_")}.${fmt}`;
  },
};

function safeSlug(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

/**
 * Search parser:
 * Supports tokens like:
 *   user:email@x.com
 *   action:user.create
 *   ip:1.2.3.4
 *   resource:user|session|...
 *   resource_id:<id>
 *   after:2025-11-01T00:00  before:2025-11-04T23:59
 * Unrecognized tokens appended to `q`.
 */
const AuditSearchParser = {
  parseSearchQuery(query: string): { filters: Partial<AuditLogFilter> } {
    const tokens = query.split(/\s+/).filter(Boolean);
    const filters: Partial<AuditLogFilter> = {};
    const q: string[] = [];

    for (const t of tokens) {
      const [key, ...rest] = t.split(":");
      const value = rest.join(":");
      if (!value) {
        q.push(t);
        continue;
      }
      switch (key.toLowerCase()) {
        case "user":
        case "email":
          filters.user_email = value;
          break;
        case "user_id":
          filters.user_id = value;
          break;
        case "action":
          filters.action = value;
          break;
        case "ip":
        case "ip_address":
          filters.ip_address = value;
          break;
        case "resource":
        case "type":
        case "resource_type":
          filters.resource_type = value;
          break;
        case "resource_id":
          filters.resource_id = value;
          break;
        case "after":
          {
            const d = parseDateLoose(value);
            if (d) filters.start_date = d;
          }
          break;
        case "before":
          {
            const d = parseDateLoose(value);
            if (d) filters.end_date = d;
          }
          break;
        default:
          q.push(t);
      }
    }

    if (q.length) filters.q = q.join(" ");
    return { filters };
  },
};

function parseDateLoose(v: string): Date | null {
  const tryDate = new Date(v);
  if (!Number.isNaN(tryDate.getTime())) return tryDate;
  // support date-only YYYY-MM-DD
  const m = v.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (m) {
    const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    if (!Number.isNaN(d.getTime())) return d;
  }
  return null;
}

/* --------------------------------- Component ---------------------------------- */

interface AuditLogViewerProps {
  userId?: string;
  resourceType?: string;
  className?: string;
  showExportButton?: boolean;
  showFilters?: boolean;
  maxHeight?: string;
}

export default function AuditLogViewer({
  userId,
  resourceType,
  className = "",
  showExportButton = true,
  showFilters = true,
  maxHeight = "600px",
}: AuditLogViewerProps) {
  const [logs, setLogs] = useState<PaginatedResponse<AuditLog>>({
    data: [],
    pagination: {
      page: 1,
      limit: 50,
      total: 0,
      total_pages: 0,
      has_next: false,
      has_prev: false,
    },
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filter, setFilter] = useState<AuditLogFilter>({
    ...(userId ? { user_id: userId } : {}),
    ...(resourceType ? { resource_type: resourceType } : {}),
  });

  const [pagination, setPagination] = useState<PaginationParams>(
    auditPagination.default()
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [selectedLogs, setSelectedLogs] = useState<Set<string>>(new Set());

  const auditLogger = getAuditLogger();

  /* ------------------------------ Data Loading ------------------------------ */

  const loadLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result: PaginatedResponse<AuditLog> = await auditLogger.getAuditLogs(
        filter,
        pagination
      );
      setLogs(result);
      // Prune selections not on page
      setSelectedLogs((prev) => {
        const currentIds = new Set(result.data.map((l) => l.id));
        const next = new Set<string>();
        for (const id of prev) if (currentIds.has(id)) next.add(id);
        return next;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  }, [auditLogger, filter, pagination]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  /* ------------------------------ Handlers ------------------------------ */

  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
    if (query.trim()) {
      const parsed = AuditSearchParser.parseSearchQuery(query);
      setFilter((prev) => ({
        ...prev,
        ...parsed.filters,
      }));
      setPagination((p) => ({ ...p, page: 1 }));
    } else {
      // clearing query resets q
      setFilter((prev) => {
        const next = { ...prev };
        delete next.q;
        return next;
      });
      setPagination((p) => ({ ...p, page: 1 }));
    }
  };

  const handleFilterChange = (newFilter: Partial<AuditLogFilter>) => {
    setFilter((prev) => ({ ...prev, ...newFilter }));
    setPagination((p) => ({ ...p, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setPagination((p) => ({ ...p, page }));
  };

  const handlePresetFilter = (
    presetKey: keyof typeof AUDIT_FILTER_PRESETS
  ) => {
    const preset = AUDIT_FILTER_PRESETS[presetKey];
    setFilter((prev) => ({ ...prev, ...preset.filter }));
    setPagination((p) => ({ ...p, page: 1 }));
  };

  const clearFilters = () => {
    const base: AuditLogFilter = {
      ...(userId ? { user_id: userId } : {}),
      ...(resourceType ? { resource_type: resourceType } : {}),
    };
    setFilter(base);
    setSearchQuery("");
    setPagination(auditPagination.default());
  };

  const handleExport = async (format: "csv" | "json") => {
    try {
      const exportPagination: PaginationParams = {
        ...pagination,
        limit: 10000,
        page: 1,
      };
      const result: PaginatedResponse<AuditLog> = await auditLogger.getAuditLogs(
        filter,
        exportPagination
      );
      const content =
        format === "csv"
          ? AuditLogExporter.toCsv(result.data)
          : AuditLogExporter.toJson(result.data, true);
      const mime =
        format === "csv" ? "text/csv" : "application/json";
      const filename = AuditLogExporter.generateFilename(format, filter);
      const blob = new Blob([content], { type: mime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to export logs");
    }
  };

  const toggleLogSelection = (logId: string) => {
    setSelectedLogs((prev) => {
      const next = new Set(prev);
      if (next.has(logId)) next.delete(logId);
      else next.add(logId);
      return next;
    });
  };

  const selectAllLogs = () => {
    setSelectedLogs(new Set(logs.data.map((l) => l.id)));
  };

  const clearSelections = () => setSelectedLogs(new Set());

  /* ------------------------------ Render Helpers ------------------------------ */

  const formatTimestamp = (ts: Date | string | number) => {
    const d = ts instanceof Date ? ts : new Date(ts);
    return isNaN(d.getTime()) ? "-" : d.toLocaleString();
  };

  const formatAction = (action: string) =>
    action.replace(/\./g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

  const getActionColorClass = (action: string) => {
    const a = action.toLowerCase();
    if (a.includes("create")) return "text-green-600";
    if (a.includes("delete")) return "text-red-600";
    if (a.includes("update") || a.includes("change")) return "text-blue-600";
    if (a.includes("login")) return "text-purple-600";
    if (a.includes("security") || a.includes("breach")) return "text-red-700";
    return "text-gray-600";
  };

  const allOnPageSelected =
    logs.data.length > 0 && selectedLogs.size === logs.data.length;

  /* ---------------------------------- UI ---------------------------------- */

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200 sm:p-4 md:p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Audit Logs</h3>
            <p className="text-sm text-gray-500 mt-1">
              {logs.pagination.total} total entries
            </p>
          </div>

          {showExportButton && (
            <div className="flex space-x-2">
              <Button onClick={() => handleExport("csv")} variant="outline">
                Export CSV
              </Button>
              <Button onClick={() => handleExport("json")} variant="outline">
                Export JSON
              </Button>
            </div>
          )}
        </div>

        {/* Search & Filters */}
        {showFilters && (
          <div className="mt-4 space-y-4">
            {/* Search */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search (e.g., user:john@example.com action:user.create after:2025-11-01)"
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                <svg
                  className="h-5 w-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
            </div>

            {/* Presets */}
            <div className="flex flex-wrap gap-2">
              {Object.entries(AUDIT_FILTER_PRESETS).map(([key, preset]) => (
                <Button
                  key={key}
                  onClick={() =>
                    handlePresetFilter(key as keyof typeof AUDIT_FILTER_PRESETS)
                  }
                  variant="secondary"
                  className="px-3 py-1 text-xs sm:text-sm"
                >
                  {preset.name}
                </Button>
              ))}
              <Button
                onClick={() => setShowAdvancedFilters((s) => !s)}
                variant="outline"
                className="px-3 py-1 text-xs sm:text-sm"
              >
                {showAdvancedFilters ? "Hide Advanced" : "Advanced Filters"}
              </Button>
              <Button
                onClick={clearFilters}
                variant="ghost"
                className="px-3 py-1 text-xs sm:text-sm text-red-700"
              >
                Clear Filters
              </Button>
            </div>

            {/* Advanced */}
            {showAdvancedFilters && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Action
                  </label>
                  <select
                    value={filter.action || ""}
                    onChange={(e) =>
                      handleFilterChange({
                        action: e.target.value || undefined,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Actions</option>
                    {Object.entries(ACTION_CATEGORIES).map(([key, cat]) => (
                      <optgroup key={key} label={cat.name}>
                        {cat.actions.map((a) => (
                          <option key={a} value={a}>
                            {formatAction(a)}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Resource Type
                  </label>
                  <select
                    value={filter.resource_type || ""}
                    onChange={(e) =>
                      handleFilterChange({
                        resource_type: e.target.value || undefined,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Resources</option>
                    {Object.values(RESOURCE_TYPE_CATEGORIES).map((cat) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    IP Address
                  </label>
                  <input
                    type="text"
                    placeholder="192.168.1.1"
                    value={filter.ip_address || ""}
                    onChange={(e) =>
                      handleFilterChange({
                        ip_address: e.target.value || undefined,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start Date
                  </label>
                  <input
                    type="datetime-local"
                    value={
                      filter.start_date
                        ? new Date(filter.start_date)
                            .toISOString()
                            .slice(0, 16)
                        : ""
                    }
                    onChange={(e) =>
                      handleFilterChange({
                        start_date: e.target.value
                          ? new Date(e.target.value)
                          : undefined,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Date
                  </label>
                  <input
                    type="datetime-local"
                    value={
                      filter.end_date
                        ? new Date(filter.end_date).toISOString().slice(0, 16)
                        : ""
                    }
                    onChange={(e) =>
                      handleFilterChange({
                        end_date: e.target.value
                          ? new Date(e.target.value)
                          : undefined,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border-l-4 border-red-400">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-hidden" style={{ maxHeight }}>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <input
                    type="checkbox"
                    checked={allOnPageSelected}
                    onChange={() =>
                      allOnPageSelected ? clearSelections() : selectAllLogs()
                    }
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    aria-label="Select all on page"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Resource
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IP
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      <span className="ml-2 text-gray-500">
                        Loading audit logs...
                      </span>
                    </div>
                  </td>
                </tr>
              ) : logs.data.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    No audit logs found matching your criteria.
                  </td>
                </tr>
              ) : (
                logs.data.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedLogs.has(log.id)}
                        onChange={() => toggleLogSelection(log.id)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        aria-label={`Select log ${log.id}`}
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatTimestamp(log.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {log.user?.email || log.user_id || "-"}
                      </div>
                      {log.user?.full_name && (
                        <div className="text-sm text-gray-500">
                          {log.user.full_name}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`text-sm font-medium ${getActionColorClass(
                          log.action
                        )}`}
                      >
                        {formatAction(log.action)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {log.resource_type || "-"}
                      </div>
                      {log.resource_id && (
                        <div
                          className="text-sm text-gray-500 truncate max-w-52"
                          title={log.resource_id}
                        >
                          {log.resource_id}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.ip_address || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.details && Object.keys(log.details).length > 0 ? (
                        <details className="cursor-pointer">
                          <summary className="text-blue-600 hover:text-blue-800">
                            View Details
                          </summary>
                          <pre className="mt-2 text-xs bg-gray-100 p-2 rounded max-w-xs overflow-auto">
                            {JSON.stringify(log.details, null, 2)}
                          </pre>
                        </details>
                      ) : (
                        "-"
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {logs.pagination.total_pages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {(logs.pagination.page - 1) * logs.pagination.limit + 1} to{" "}
            {Math.min(
              logs.pagination.page * logs.pagination.limit,
              logs.pagination.total
            )}{" "}
            of {logs.pagination.total} results
          </div>

          <div className="flex items-center space-x-2">
            <Button
              onClick={() => handlePageChange(logs.pagination.page - 1)}
              disabled={!logs.pagination.has_prev}
              variant="outline"
            >
              Previous
            </Button>

            <span className="text-sm text-gray-700">
              Page {logs.pagination.page} of {logs.pagination.total_pages}
            </span>

            <Button
              onClick={() => handlePageChange(logs.pagination.page + 1)}
              disabled={!logs.pagination.has_next}
              variant="outline"
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Selection Actions */}
      {selectedLogs.size > 0 && (
        <div className="px-6 py-3 bg-blue-50 border-t border-blue-200">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-700">
              {selectedLogs.size} log{selectedLogs.size !== 1 ? "s" : ""} selected
            </span>
            <div className="flex space-x-2">
              <Button onClick={() => handleExport("csv")} variant="secondary">
                Export Selected (CSV)
              </Button>
              <Button onClick={clearSelections} variant="outline">
                Clear Selection
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
