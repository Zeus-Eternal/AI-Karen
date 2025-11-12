/**
 * Admin Dashboard Component (Prod-Grade)
 *
 * Main dashboard for admin users focused on user management.
 * Provides access to user management, bulk operations, and user activity monitoring.
 *
 * Requirements: 4.1, 4.2, 7.3, 7.4
 */
"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";
import { useRole } from "@/hooks/useRole";
import { UserManagementTable } from "./UserManagementTable";
import { UserCreationForm } from "./UserCreationForm";
import { UserActivityMonitor } from "./UserActivityMonitor";
import { BulkUserOperations } from "./BulkUserOperations";
import { Button } from "@/components/ui/button";
import type { UserStatistics, ActivitySummary } from "@/types/admin";

export interface AdminDashboardProps {
  className?: string;
}

export type DashboardView = "overview" | "users" | "create-user" | "activity" | "bulk-operations";

export function AdminDashboard({ className = "" }: AdminDashboardProps) {
  const { hasRole } = useRole();
  const [currentView, setCurrentView] = useState<DashboardView>("overview");
  const [userStats, setUserStats] = useState<UserStatistics | null>(null);
  const [activitySummary, setActivitySummary] = useState<ActivitySummary | null>(null);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const navItems = useMemo(
    () => [
      { key: "overview" as const, label: "Overview" },
      { key: "users" as const, label: "Users" },
      { key: "create-user" as const, label: "Create User" },
      { key: "activity" as const, label: "Activity" },
    ],
    []
  );

  const fetchJSON = useCallback(async <T,>(url: string, signal: AbortSignal): Promise<T> => {
    const res = await fetch(url, { signal, headers: { "Cache-Control": "no-store" } });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText} while fetching ${url}`);
    const data = (await res.json()) as unknown;
    return (data?.data ?? data) as T;
  }, []);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const [stats, activity] = await Promise.all([
        fetchJSON<UserStatistics>("/api/admin/users/stats", controller.signal),
        fetchJSON<ActivitySummary>("/api/admin/system/activity-summary?period=week", controller.signal),
      ]);
      setUserStats(stats);
      setActivitySummary(activity);
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        return;
      }
      setError(error instanceof Error ? error.message : "Failed to load dashboard data");
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, [fetchJSON]);

  useEffect(() => {
    loadDashboardData();
    return () => abortRef.current?.abort();
  }, [loadDashboardData]);

  const handleUserCreated = useCallback(() => {
    loadDashboardData();
    setCurrentView("users");
  }, [loadDashboardData]);

  const handleBulkOperationComplete = useCallback(() => {
    loadDashboardData();
    setSelectedUsers([]);
  }, [loadDashboardData]);

  const renderNavigationTabs = () => (
    <div className="border-b border-gray-200 mb-6">
      <nav className="-mb-px flex flex-wrap gap-2" role="tablist" aria-label="Admin dashboard tabs">
        {navItems.map((item) => {
          const active = currentView === item.key;
          return (
            <Button
              key={item.key}
              onClick={() => setCurrentView(item.key)}
              role="tab"
              aria-selected={active}
              aria-controls={`panel-${item.key}`}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                active
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
              variant="ghost"
            >
              {item.label}
            </Button>
          );
        })}
        {selectedUsers.length > 0 && (
          <Button
            onClick={() => setCurrentView("bulk-operations")}
            role="tab"
            aria-selected={currentView === "bulk-operations"}
            aria-controls="panel-bulk-operations"
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              currentView === "bulk-operations"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
            variant="ghost"
          >
            Bulk Operations ({selectedUsers.length})
          </Button>
        )}
      </nav>
    </div>
  );

  const renderOverview = () => (
    <section id="panel-overview" role="tabpanel" aria-labelledby="tab-overview" className="space-y-6">
      {/* Statistics Cards */}
      {userStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
            <h3 className="text-sm font-medium text-gray-500 md:text-base lg:text-lg">Total Users</h3>
            <p className="text-3xl font-bold text-gray-900">{userStats.total_users}</p>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">
              {userStats.users_created_this_month} new this month
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
            <h3 className="text-sm font-medium text-gray-500 md:text-base lg:text-lg">Active Users</h3>
            <p className="text-3xl font-bold text-green-600">{userStats.active_users}</p>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">
              {userStats.last_login_today} logged in today
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
            <h3 className="text-sm font-medium text-gray-500 md:text-base lg:text-lg">Verified Users</h3>
            <p className="text-3xl font-bold text-blue-600">{userStats.verified_users}</p>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">
              {Math.round((userStats.verified_users / Math.max(userStats.total_users, 1)) * 100)}% verified
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
            <h3 className="text-sm font-medium text-gray-500 md:text-base lg:text-lg">2FA Enabled</h3>
            <p className="text-3xl font-bold text-purple-600">{userStats.two_factor_enabled}</p>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">
              {Math.round((userStats.two_factor_enabled / Math.max(userStats.total_users, 1)) * 100)}% adoption
            </p>
          </div>
        </div>
      )}

      {/* Recent Activity Summary */}
      {activitySummary && (
        <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Weekly Activity Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 md:text-base lg:text-lg">Key Metrics</h4>
              <ul className="space-y-2 text-sm md:text-base lg:text-lg">
                <li className="flex justify-between">
                  <span>New Registrations:</span>
                  <span className="font-medium">{activitySummary.user_registrations}</span>
                </li>
                <li className="flex justify-between">
                  <span>Admin Actions:</span>
                  <span className="font-medium">{activitySummary.admin_actions}</span>
                </li>
                <li className="flex justify-between">
                  <span>Successful Logins:</span>
                  <span className="font-medium text-green-600">{activitySummary.successful_logins}</span>
                </li>
                <li className="flex justify-between">
                  <span>Failed Logins:</span>
                  <span className="font-medium text-red-600">{activitySummary.failed_logins}</span>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 md:text-base lg:text-lg">Top Actions</h4>
              <ul className="space-y-2 text-sm md:text-base lg:text-lg">
                {activitySummary.top_actions.slice(0, 4).map((action, index) => (
                  <li key={index} className="flex justify-between">
                    <span className="capitalize">{String(action.action).replaceAll("_", " ")}</span>
                    <span className="font-medium">{action.count}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button
            onClick={() => setCurrentView("create-user")}
            className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left sm:p-4 md:p-6"
            aria-label="Create New User"
            variant="outline"
          >
            <h4 className="font-medium text-gray-900">Create New User</h4>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">Add a new user account</p>
          </Button>
          <Button
            onClick={() => setCurrentView("users")}
            className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left sm:p-4 md:p-6"
            aria-label="Manage Users"
            variant="outline"
          >
            <h4 className="font-medium text-gray-900">Manage Users</h4>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">View and edit user accounts</p>
          </Button>
          <Button
            onClick={() => setCurrentView("activity")}
            className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left sm:p-4 md:p-6"
            aria-label="View Activity"
            variant="outline"
          >
            <h4 className="font-medium text-gray-900">View Activity</h4>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">Monitor user activity and events</p>
          </Button>
        </div>
      </div>
    </section>
  );

  const renderCurrentView = () => {
    switch (currentView) {
      case "overview":
        return renderOverview();
      case "users":
        return (
          <section id="panel-users" role="tabpanel" aria-labelledby="tab-users">
            <UserManagementTable
              selectedUsers={selectedUsers}
              onSelectionChange={setSelectedUsers}
              onUserUpdated={loadDashboardData}
            />
          </section>
        );
      case "create-user":
        return (
          <section id="panel-create-user" role="tabpanel" aria-labelledby="tab-create-user">
            <UserCreationForm onUserCreated={handleUserCreated} />
          </section>
        );
      case "activity":
        return (
          <section id="panel-activity" role="tabpanel" aria-labelledby="tab-activity">
            <UserActivityMonitor />
          </section>
        );
      case "bulk-operations":
        return (
          <section id="panel-bulk-operations" role="tabpanel" aria-labelledby="tab-bulk-operations">
            <BulkUserOperations
              selectedUserIds={selectedUsers}
              onOperationComplete={handleBulkOperationComplete}
              onCancel={() => setCurrentView("users")}
            />
          </section>
        );
      default:
        return renderOverview();
    }
  };

  // RBAC gate (outside of fetch flow so we don't leak UI)
  if (!hasRole("admin")) {
    return (
      <ErrorBoundary>
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
            <p className="text-gray-600">You need admin privileges to access this dashboard.</p>
          </div>
        </div>
      </ErrorBoundary>
    );
  }

  if (loading) {
    return (
      <ErrorBoundary>
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
          <div
            className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"
            role="status"
            aria-label="Loading admin dashboard"
          />
        </div>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <div className={`min-h-screen bg-gray-50 ${className}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <header className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
            <p className="text-gray-600 mt-2">Manage users and monitor system activity</p>
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md sm:p-4 md:p-6">
                <p className="text-red-800">{error}</p>
                <Button
                  onClick={loadDashboardData}
                  className="mt-2 text-sm md:text-base lg:text-lg"
                  aria-label="Retry loading dashboard"
                  variant="destructive"
                >
                  Retry
                </Button>
              </div>
            )}
          </header>

          {/* Navigation */}
          {renderNavigationTabs()}

          {/* Content */}
          {renderCurrentView()}
        </div>
      </div>
    </ErrorBoundary>
  );
}
