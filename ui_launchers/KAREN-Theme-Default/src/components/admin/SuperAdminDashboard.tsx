/**
 * SuperAdminDashboard - Production-Ready Admin Interface
 *
 * Comprehensive super admin dashboard with full system access:
 * - User Management & RBAC
 * - System Configuration
 * - Security & Audit Logs
 * - Performance Monitoring
 * - Cognitive API Health
 * - Memory Subsystem Status
 * - Reasoning Engine Monitoring
 *
 * Production-ready with full backend integration
 */

"use client";

import React, { useCallback, useEffect, useState, useRef } from "react";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";
import { useRole } from "@/hooks/useRole";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { AdminDashboard } from "./AdminDashboard";
import { SecuritySettingsPanel } from "./SecuritySettingsPanel";
import { SystemConfigurationPanel } from "./SystemConfigurationPanel";
import { PerformanceDashboard } from "./PerformanceDashboard";
import { AuditLogViewer } from "./audit/AuditLogViewer";
import { AdminAPITester } from "./AdminAPITester";

interface SuperAdminDashboardProps {
  className?: string;
}

type AdminView =
  | "overview"
  | "users"
  | "security"
  | "system-config"
  | "performance"
  | "cognitive-health"
  | "audit-logs"
  | "api-tester";

interface SystemHealth {
  status: "healthy" | "degraded" | "unhealthy";
  components: {
    database: { status: string; latency_ms?: number };
    redis: { status: string; latency_ms?: number };
    milvus: { status: string; latency_ms?: number };
  };
  timestamp: string;
}

interface CognitiveHealth {
  status: "healthy" | "degraded" | "unhealthy";
  layers: {
    executive?: { status: string; latency_ms?: number };
    reasoning?: { status: string; latency_ms?: number };
    memory?: { status: string; latency_ms?: number };
    generation?: { status: string; latency_ms?: number };
    learning?: { status: string; latency_ms?: number };
  };
  overall_latency_ms: number;
  memory_usage_mb: number;
  timestamp: string;
}

interface ReasoningHealth {
  status: string;
  components: {
    soft_reasoning_engine: string;
    ice_wrapper: string;
    graph_constructor: string;
  };
  latency_ms: number;
  timestamp: string;
}

export default function SuperAdminDashboard({ className = "" }: SuperAdminDashboardProps) {
  const { hasRole } = useRole();
  const [currentView, setCurrentView] = useState<AdminView>("overview");
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [cognitiveHealth, setCognitiveHealth] = useState<CognitiveHealth | null>(null);
  const [reasoningHealth, setReasoningHealth] = useState<ReasoningHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Navigation items
  const navItems = [
    { key: "overview" as const, label: "Overview", icon: "📊" },
    { key: "users" as const, label: "User Management", icon: "👥" },
    { key: "security" as const, label: "Security", icon: "🔒" },
    { key: "system-config" as const, label: "System Config", icon: "⚙️" },
    { key: "performance" as const, label: "Performance", icon: "📈" },
    { key: "cognitive-health" as const, label: "Cognitive Health", icon: "🧠" },
    { key: "audit-logs" as const, label: "Audit Logs", icon: "📋" },
    { key: "api-tester" as const, label: "API Tester", icon: "🔧" },
  ];

  const fetchJSON = useCallback(async <T,>(url: string, signal: AbortSignal): Promise<T | null> => {
    try {
      const res = await fetch(url, { signal, headers: { "Cache-Control": "no-store" } });
      if (!res.ok) {
        console.warn(`${res.status} ${res.statusText} while fetching ${url}`);
        return null;
      }
      return await res.json() as T;
    } catch (err: any) {
      if (err?.name !== "AbortError") {
        console.error(`Error fetching ${url}:`, err);
      }
      return null;
    }
  }, []);

  const loadSystemHealth = useCallback(async (signal: AbortSignal) => {
    // Load system health
    const sysHealth = await fetchJSON<SystemHealth>("/api/admin/system/health", signal);
    if (sysHealth) setSystemHealth(sysHealth);

    // Load cognitive health from new cognitive API
    const cogHealth = await fetchJSON<CognitiveHealth>("/api/cognitive/health", signal);
    if (cogHealth) setCognitiveHealth(cogHealth);

    // Load reasoning engine health
    const reasonHealth = await fetchJSON<ReasoningHealth>("/api/reasoning/health", signal);
    if (reasonHealth) setReasoningHealth(reasonHealth);
  }, [fetchJSON]);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await loadSystemHealth(controller.signal);
    } catch (err: any) {
      if (err?.name !== "AbortError") {
        setError(err instanceof Error ? err.message : "Failed to load dashboard data");
      }
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, [loadSystemHealth]);

  useEffect(() => {
    loadDashboardData();

    // Auto-refresh health every 30 seconds
    const interval = setInterval(() => {
      if (currentView === "overview" || currentView === "cognitive-health") {
        loadSystemHealth(new AbortController().signal);
      }
    }, 30000);

    return () => {
      clearInterval(interval);
      abortRef.current?.abort();
    };
  }, [loadDashboardData, currentView, loadSystemHealth]);

  // RBAC gate
  if (!hasRole("super_admin")) {
    return (
      <ErrorBoundary fallback={<div>Something went wrong in SuperAdminDashboard</div>}>
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
            <p className="text-gray-600">You need super admin privileges to access this dashboard.</p>
          </div>
        </div>
      </ErrorBoundary>
    );
  }

  const renderStatusBadge = (status: string) => {
    const colors = {
      healthy: "bg-green-100 text-green-800",
      online: "bg-green-100 text-green-800",
      degraded: "bg-yellow-100 text-yellow-800",
      unhealthy: "bg-red-100 text-red-800",
      offline: "bg-red-100 text-red-800",
    };
    const color = colors[status as keyof typeof colors] || "bg-gray-100 text-gray-800";

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${color}`}>
        {status}
      </span>
    );
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* System Health Overview */}
      <Card className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">System Health</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Overall Status</h3>
            {systemHealth ? (
              <>
                {renderStatusBadge(systemHealth.status)}
                <p className="text-xs text-gray-500 mt-2">
                  Last checked: {new Date(systemHealth.timestamp).toLocaleTimeString()}
                </p>
              </>
            ) : (
              <p className="text-sm text-gray-400">Loading...</p>
            )}
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Database</h3>
            {systemHealth?.components.database ? (
              <>
                {renderStatusBadge(systemHealth.components.database.status)}
                {systemHealth.components.database.latency_ms && (
                  <p className="text-xs text-gray-500 mt-2">
                    Latency: {systemHealth.components.database.latency_ms.toFixed(1)}ms
                  </p>
                )}
              </>
            ) : (
              <p className="text-sm text-gray-400">N/A</p>
            )}
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Cache (Redis)</h3>
            {systemHealth?.components.redis ? (
              <>
                {renderStatusBadge(systemHealth.components.redis.status)}
                {systemHealth.components.redis.latency_ms && (
                  <p className="text-xs text-gray-500 mt-2">
                    Latency: {systemHealth.components.redis.latency_ms.toFixed(1)}ms
                  </p>
                )}
              </>
            ) : (
              <p className="text-sm text-gray-400">N/A</p>
            )}
          </div>
        </div>
      </Card>

      {/* Cognitive Engine Health */}
      <Card className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Cognitive Engine Status</h2>
        {cognitiveHealth ? (
          <>
            <div className="mb-4 flex items-center gap-4">
              <div>
                <span className="text-sm font-medium text-gray-500">Overall: </span>
                {renderStatusBadge(cognitiveHealth.status)}
              </div>
              <div className="text-sm text-gray-600">
                Latency: {cognitiveHealth.overall_latency_ms.toFixed(1)}ms
              </div>
              <div className="text-sm text-gray-600">
                Memory: {cognitiveHealth.memory_usage_mb.toFixed(1)}MB
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {Object.entries(cognitiveHealth.layers).map(([layer, health]) => (
                <div key={layer} className="bg-white border border-gray-200 rounded p-3">
                  <h4 className="text-xs font-medium text-gray-700 mb-1 capitalize">
                    {layer}
                  </h4>
                  {renderStatusBadge(health.status)}
                  {health.latency_ms && (
                    <p className="text-xs text-gray-500 mt-1">
                      {health.latency_ms.toFixed(0)}ms
                    </p>
                  )}
                </div>
              ))}
            </div>
          </>
        ) : (
          <p className="text-sm text-gray-400">Loading cognitive health...</p>
        )}
      </Card>

      {/* Reasoning Engine Health */}
      <Card className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Reasoning Engine Status</h2>
        {reasoningHealth ? (
          <>
            <div className="mb-4 flex items-center gap-4">
              <div>
                <span className="text-sm font-medium text-gray-500">Status: </span>
                {renderStatusBadge(reasoningHealth.status)}
              </div>
              <div className="text-sm text-gray-600">
                Latency: {reasoningHealth.latency_ms.toFixed(1)}ms
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {Object.entries(reasoningHealth.components).map(([component, status]) => (
                <div key={component} className="bg-white border border-gray-200 rounded p-3">
                  <h4 className="text-xs font-medium text-gray-700 mb-1">
                    {component.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                  </h4>
                  {renderStatusBadge(status)}
                </div>
              ))}
            </div>
          </>
        ) : (
          <p className="text-sm text-gray-400">Loading reasoning health...</p>
        )}
      </Card>

      {/* Quick Actions */}
      <Card className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Button
            onClick={() => setCurrentView("users")}
            className="p-4 h-auto flex flex-col items-start"
            variant="outline"
          >
            <span className="text-2xl mb-2">👥</span>
            <span className="font-medium">Manage Users</span>
            <span className="text-xs text-gray-500 mt-1">User administration</span>
          </Button>

          <Button
            onClick={() => setCurrentView("security")}
            className="p-4 h-auto flex flex-col items-start"
            variant="outline"
          >
            <span className="text-2xl mb-2">🔒</span>
            <span className="font-medium">Security</span>
            <span className="text-xs text-gray-500 mt-1">Security settings</span>
          </Button>

          <Button
            onClick={() => setCurrentView("performance")}
            className="p-4 h-auto flex flex-col items-start"
            variant="outline"
          >
            <span className="text-2xl mb-2">📈</span>
            <span className="font-medium">Performance</span>
            <span className="text-xs text-gray-500 mt-1">System metrics</span>
          </Button>

          <Button
            onClick={() => setCurrentView("audit-logs")}
            className="p-4 h-auto flex flex-col items-start"
            variant="outline"
          >
            <span className="text-2xl mb-2">📋</span>
            <span className="font-medium">Audit Logs</span>
            <span className="text-xs text-gray-500 mt-1">Activity logs</span>
          </Button>
        </div>
      </Card>
    </div>
  );

  const renderCognitiveHealth = () => (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Cognitive API Health</h2>
          <Button onClick={() => loadSystemHealth(new AbortController().signal)} variant="outline" size="sm">
            Refresh
          </Button>
        </div>

        {cognitiveHealth && reasoningHealth ? (
          <div className="space-y-6">
            {/* Cognitive Layers */}
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Cognitive Layers</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(cognitiveHealth.layers).map(([layer, health]) => (
                  <Card key={layer} className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900 capitalize">{layer}</h4>
                      {renderStatusBadge(health.status)}
                    </div>
                    {health.latency_ms && (
                      <div className="space-y-1 text-sm text-gray-600">
                        <p>Latency: {health.latency_ms.toFixed(2)}ms</p>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              health.latency_ms < 100 ? "bg-green-500" :
                              health.latency_ms < 500 ? "bg-yellow-500" :
                              "bg-red-500"
                            }`}
                            style={{ width: `${Math.min((health.latency_ms / 1000) * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            </div>

            {/* Reasoning Components */}
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Reasoning Components</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(reasoningHealth.components).map(([component, status]) => (
                  <Card key={component} className="p-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-gray-900 text-sm">
                        {component.replace(/_/g, " ").toUpperCase()}
                      </h4>
                      {renderStatusBadge(status)}
                    </div>
                  </Card>
                ))}
              </div>
            </div>

            {/* System Metrics */}
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-3">System Metrics</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="p-4">
                  <p className="text-sm text-gray-500 mb-1">Overall Latency</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {cognitiveHealth.overall_latency_ms.toFixed(1)}ms
                  </p>
                </Card>
                <Card className="p-4">
                  <p className="text-sm text-gray-500 mb-1">Memory Usage</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {cognitiveHealth.memory_usage_mb.toFixed(1)}MB
                  </p>
                </Card>
                <Card className="p-4">
                  <p className="text-sm text-gray-500 mb-1">Reasoning Latency</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {reasoningHealth.latency_ms.toFixed(1)}ms
                  </p>
                </Card>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
            <p className="text-gray-500 mt-4">Loading cognitive health data...</p>
          </div>
        )}
      </Card>
    </div>
  );

  const renderCurrentView = () => {
    switch (currentView) {
      case "overview":
        return renderOverview();
      case "users":
        return <AdminDashboard />;
      case "security":
        return <SecuritySettingsPanel />;
      case "system-config":
        return <SystemConfigurationPanel />;
      case "performance":
        return <PerformanceDashboard />;
      case "cognitive-health":
        return renderCognitiveHealth();
      case "audit-logs":
        return <AuditLogViewer />;
      case "api-tester":
        return <AdminAPITester />;
      default:
        return renderOverview();
    }
  };

  return (
    <ErrorBoundary fallback={<div>Something went wrong in SuperAdminDashboard</div>}>
      <div className={`min-h-screen bg-gray-50 ${className}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <header className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Super Admin Dashboard</h1>
            <p className="text-gray-600 mt-2">Complete system administration and monitoring</p>
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-800">{error}</p>
                <Button onClick={loadDashboardData} className="mt-2 text-sm" variant="destructive">
                  Retry
                </Button>
              </div>
            )}
          </header>

          {/* Navigation */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex flex-wrap gap-2" role="tablist">
              {navItems.map((item) => {
                const active = currentView === item.key;
                return (
                  <Button
                    key={item.key}
                    onClick={() => setCurrentView(item.key)}
                    role="tab"
                    aria-selected={active}
                    className={`py-2 px-4 border-b-2 font-medium text-sm ${
                      active
                        ? "border-blue-500 text-blue-600"
                        : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                    }`}
                    variant="ghost"
                  >
                    <span className="mr-2">{item.icon}</span>
                    {item.label}
                  </Button>
                );
              })}
            </nav>
          </div>

          {/* Content */}
          {loading && currentView === "overview" ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
            </div>
          ) : (
            renderCurrentView()
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
}
