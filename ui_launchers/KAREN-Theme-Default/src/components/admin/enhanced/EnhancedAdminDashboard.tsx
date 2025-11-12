/**
 * Enhanced Admin Dashboard
 *
 * Admin dashboard with comprehensive error handling, accessibility features,
 * keyboard navigation, and user experience improvements.
 *
 * Requirements: 7.2, 7.4, 7.5, 7.7
 */

"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { useRole } from "@/hooks/useRole";
import { useAdminErrorHandler } from "@/hooks/useAdminErrorHandler";
import { EnhancedUserManagementTable } from "./EnhancedUserManagementTable";
import { EnhancedBulkUserOperations } from "./EnhancedBulkUserOperations";
import { UserCreationForm } from "../UserCreationForm";
import { UserActivityMonitor } from "../UserActivityMonitor";
import ErrorDisplay, { ErrorBoundary } from "@/components/ui/error-display";
import { SimpleProgressBar } from "@/components/ui/progress-indicator";
import { useKeyboardNavigation } from "@/lib/accessibility/keyboard-navigation";
import { useAriaLiveRegion } from "@/lib/accessibility/aria-helpers";
import type { UserStatistics, ActivitySummary } from "@/types/admin";

interface EnhancedAdminDashboardProps {
  className?: string;
}

type DashboardView =
  | "overview"
  | "users"
  | "create-user"
  | "activity"
  | "bulk-operations";

interface DashboardData {
  userStats: UserStatistics | null;
  activitySummary: ActivitySummary | null;
  loading: boolean;
}

export function EnhancedAdminDashboard({
  className = "",
}: EnhancedAdminDashboardProps) {
  const { hasRole } = useRole();
  const dashboardRef = useRef<HTMLDivElement>(null);
  const { announce } = useAriaLiveRegion();
  const hasAdminAccess = hasRole("admin");

  const { error, isRetrying, handleAsyncOperation, retry, clearError, canRetry } =
    useAdminErrorHandler({
      context: { operation: "admin_dashboard" },
    });

  // State management
  const [currentView, setCurrentView] = useState<DashboardView>("overview");
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    userStats: null,
    activitySummary: null,
    loading: true,
  });

  // Keyboard navigation setup
  useKeyboardNavigation(dashboardRef, {
    enableArrowKeys: true,
    enableHomeEndKeys: true,
    enableEscapeKey: true,
    focusableSelector:
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    onEscape: () => {
      if (currentView === "bulk-operations") {
        setCurrentView("users");
        setSelectedUsers([]);
      }
    },
  });

  // Load dashboard data with error handling
  const loadDashboardData = useCallback(async () => {
    if (!hasAdminAccess) {
      return;
    }

    const result = await handleAsyncOperation(
      async () => {
        setDashboardData((prev) => ({ ...prev, loading: true }));

        // Load user statistics
        const statsResponse = await fetch("/api/admin/users/stats");
        if (!statsResponse.ok) {
          throw new Error(
            `Failed to load user statistics: ${statsResponse.statusText}`
          );
        }
        const statsData = await statsResponse.json();

        // Load activity summary
        const activityResponse = await fetch(
          "/api/admin/system/activity-summary?period=week"
        );
        if (!activityResponse.ok) {
          throw new Error(
            `Failed to load activity summary: ${activityResponse.statusText}`
          );
        }
        const activityData = await activityResponse.json();

        return {
          userStats: statsData.data as UserStatistics,
          activitySummary: activityData.data as ActivitySummary,
        };
      },
      { resource: "dashboard_data" }
    );

    if (result) {
      setDashboardData({
        userStats: result.userStats,
        activitySummary: result.activitySummary,
        loading: false,
      });
      announce("Dashboard data loaded successfully");
    } else {
      setDashboardData((prev) => ({ ...prev, loading: false }));
    }
  }, [announce, handleAsyncOperation, hasAdminAccess]);

  // Load data on mount
  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      await Promise.resolve();
      if (!cancelled) {
        await loadDashboardData();
      }
    };

    void run();

    return () => {
      cancelled = true;
    };
  }, [loadDashboardData]);

  // Access control
  if (!hasAdminAccess) {
    return (
      <div className="flex items-center justify-center min-h-screen" role="main">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600">
            You need admin privileges to access this dashboard.
          </p>
        </div>
      </div>
    );
  }

  const handleViewChange = (view: DashboardView) => {
    setCurrentView(view);
    announce(`Switched to ${view.replace("-", " ")} view`);

    // Clear selections when leaving bulk operations
    if (currentView === "bulk-operations" && view !== "bulk-operations") {
      setSelectedUsers([]);
    }
  };

  const handleUserCreated = () => {
    loadDashboardData();
    setCurrentView("users");
    announce("User created successfully, switching to user management view");
  };

  const handleBulkOperationComplete = () => {
    loadDashboardData();
    setSelectedUsers([]);
    setCurrentView("users");
    announce("Bulk operation completed, returning to user management");
  };

  const handleUserSelectionChange = (userIds: string[]) => {
    setSelectedUsers(userIds);
    if (userIds.length > 0) {
      announce(`${userIds.length} user${userIds.length === 1 ? "" : "s"} selected`);
    }
  };

  const renderNavigationTabs = () => (
    <nav
      className="border-b border-gray-200 mb-6"
      role="tablist"
      aria-label="Dashboard navigation"
    >
      <div className="-mb-px flex flex-wrap gap-2">
        {[
          { id: "overview", label: "Overview", icon: "📊" },
          { id: "users", label: "User Management", icon: "👥" },
          { id: "create-user", label: "Create User", icon: "➕" },
          { id: "activity", label: "Activity Monitor", icon: "📈" },
        ].map((tab) => (
          <Button
            key={tab.id}
            onClick={() => handleViewChange(tab.id as DashboardView)}
            className={`py-2 px-3 border-b-2 font-medium text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-t ${
              currentView === tab.id
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
            role="tab"
            aria-selected={currentView === tab.id}
            aria-controls={`${tab.id}-panel`}
            id={`${tab.id}-tab`}
            variant="ghost"
          >
            <span className="mr-2" aria-hidden="true">
              {tab.icon}
            </span>
            {tab.label}
          </Button>
        ))}

        {selectedUsers.length > 0 && (
          <Button
            onClick={() => handleViewChange("bulk-operations")}
            className={`py-2 px-3 border-b-2 font-medium text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-t ${
              currentView === "bulk-operations"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
            role="tab"
            aria-selected={currentView === "bulk-operations"}
            aria-controls="bulk-operations-panel"
            id="bulk-operations-tab"
            variant="ghost"
          >
            <span className="mr-2" aria-hidden="true">
              ⚡
            </span>
            Bulk Operations ({selectedUsers.length})
          </Button>
        )}
      </div>
    </nav>
  );

  const renderOverview = () => (
    <div
      className="space-y-6"
      role="tabpanel"
      id="overview-panel"
      aria-labelledby="overview-tab"
    >
      {/* Statistics Cards */}
      {dashboardData.userStats && (
        <section aria-labelledby="stats-heading">
          <h2 id="stats-heading" className="sr-only">
            User Statistics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                title: "Total Users",
                value: dashboardData.userStats.total_users,
                subtitle: `${dashboardData.userStats.users_created_this_month} new this month`,
                color: "text-gray-900",
              },
              {
                title: "Active Users",
                value: dashboardData.userStats.active_users,
                subtitle: `${dashboardData.userStats.last_login_today} logged in today`,
                color: "text-green-600",
              },
              {
                title: "Verified Users",
                value: dashboardData.userStats.verified_users,
                subtitle: `${Math.round(
                  (dashboardData.userStats.verified_users /
                    Math.max(dashboardData.userStats.total_users, 1)) *
                    100
                )}% verified`,
                color: "text-blue-600",
              },
              {
                title: "2FA Enabled",
                value: dashboardData.userStats.two_factor_enabled,
                subtitle: `${Math.round(
                  (dashboardData.userStats.two_factor_enabled /
                    Math.max(dashboardData.userStats.total_users, 1)) *
                    100
                )}% adoption`,
                color: "text-purple-600",
              },
            ].map((stat, index) => (
              <div key={index} className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
                <h3 className="text-sm font-medium text-gray-500">{stat.title}</h3>
                <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
                <p className="text-sm text-gray-600 mt-1">{stat.subtitle}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Recent Activity Summary */}
      {dashboardData.activitySummary && (
        <section aria-labelledby="activity-heading">
          <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
            <h2 id="activity-heading" className="text-lg font-medium text-gray-900 mb-4">
              Weekly Activity Summary
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Key Metrics</h3>
                <dl className="space-y-2 text-sm">
                  {[
                    {
                      term: "New Registrations",
                      value: dashboardData.activitySummary.user_registrations,
                    },
                    {
                      term: "Admin Actions",
                      value: dashboardData.activitySummary.admin_actions,
                    },
                    {
                      term: "Successful Logins",
                      value: dashboardData.activitySummary.successful_logins,
                      className: "text-green-600",
                    },
                    {
                      term: "Failed Logins",
                      value: dashboardData.activitySummary.failed_logins,
                      className: "text-red-600",
                    },
                  ].map((metric, index) => (
                    <div key={index} className="flex justify-between">
                      <dt>{metric.term}:</dt>
                      <dd className={`font-medium ${metric.className || ""}`}>
                        {metric.value}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Top Actions</h3>
                <dl className="space-y-2 text-sm">
                  {dashboardData.activitySummary.top_actions.slice(0, 4).map((action, i) => (
                    <div key={i} className="flex justify-between">
                      <dt className="capitalize">{action.action.replace("_", " ")}</dt>
                      <dd className="font-medium">{action.count}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Quick Actions */}
      <section aria-labelledby="quick-actions-heading">
        <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
          <h2 id="quick-actions-heading" className="text-lg font-medium text-gray-900 mb-4">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                title: "Create New User",
                description: "Add a new user account",
                action: () => handleViewChange("create-user"),
                icon: "➕",
              },
              {
                title: "Manage Users",
                description: "View and edit user accounts",
                action: () => handleViewChange("users"),
                icon: "👥",
              },
              {
                title: "View Activity",
                description: "Monitor user activity and events",
                action: () => handleViewChange("activity"),
                icon: "📈",
              },
            ].map((quickAction, index) => (
              <Button
                key={index}
                onClick={quickAction.action}
                className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                variant="outline"
                aria-label={quickAction.title}
              >
                <div className="flex items-start">
                  <span className="text-2xl mr-3" aria-hidden="true">
                    {quickAction.icon}
                  </span>
                  <div>
                    <h3 className="font-medium text-gray-900">{quickAction.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{quickAction.description}</p>
                  </div>
                </div>
              </Button>
            ))}
          </div>
        </div>
      </section>
    </div>
  );

  const renderCurrentView = () => {
    const commonProps = {
      role: "tabpanel" as const,
      "aria-labelledby": `${currentView}-tab`,
    };

    switch (currentView) {
      case "overview":
        return renderOverview();

      case "users":
        return (
          <div id="users-panel" {...commonProps}>
            <ErrorBoundary>
              <EnhancedUserManagementTable
                selectedUsers={selectedUsers}
                onSelectionChange={handleUserSelectionChange}
                onUserUpdated={loadDashboardData}
              />
            </ErrorBoundary>
          </div>
        );

      case "create-user":
        return (
          <div id="create-user-panel" {...commonProps}>
            <ErrorBoundary>
              <UserCreationForm onUserCreated={handleUserCreated} />
            </ErrorBoundary>
          </div>
        );

      case "activity":
        return (
          <div id="activity-panel" {...commonProps}>
            <ErrorBoundary>
              <UserActivityMonitor />
            </ErrorBoundary>
          </div>
        );

      case "bulk-operations":
        return (
          <div id="bulk-operations-panel" {...commonProps}>
            <ErrorBoundary>
              <EnhancedBulkUserOperations
                selectedUserIds={selectedUsers}
                onOperationComplete={handleBulkOperationComplete}
                onCancel={() => handleViewChange("users")}
              />
            </ErrorBoundary>
          </div>
        );

      default:
        return renderOverview();
    }
  };

  if (dashboardData.loading) {
    return (
      <div
        className="flex flex-col items-center justify-center min-h-screen"
        role="status"
        aria-live="polite"
      >
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        <p className="text-gray-600 mb-4">Loading dashboard...</p>
        <SimpleProgressBar
          progress={isRetrying ? 75 : 50}
          className="w-64"
          label="Loading progress"
        />
      </div>
    );
  }

  return (
    <div
      className={`min-h-screen bg-gray-50 ${className}`}
      ref={dashboardRef}
      id="top"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Manage users and monitor system activity
          </p>
        </header>

        {/* Error Display */}
        {error && (
          <div className="mb-6">
            <ErrorDisplay
              error={error}
              onRetry={canRetry ? retry : undefined}
              onDismiss={clearError}
              showRemediation={true}
            />
          </div>
        )}

        {/* Navigation */}
        {renderNavigationTabs()}

        {/* Main Content */}
        <main>{renderCurrentView()}</main>

        {/* Skip to top link for keyboard users */}
        <a
          href="#top"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-md z-50"
        >
          Skip to top
        </a>
      </div>
    </div>
  );
}

export default EnhancedAdminDashboard;
