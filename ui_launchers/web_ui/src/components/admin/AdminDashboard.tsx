/**
 * Admin Dashboard Component
 * 
 * Main dashboard for admin users focused on user management.
 * Provides access to user management, bulk operations, and user activity monitoring.
 * 
 * Requirements: 4.1, 4.2, 7.3, 7.4
 */
"use client";

import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { useRole } from '@/hooks/useRole';
import { UserManagementTable } from './UserManagementTable';
import { UserCreationForm } from './UserCreationForm';
import { UserActivityMonitor } from './UserActivityMonitor';
import { BulkUserOperations } from './BulkUserOperations';
import type { User, UserStatistics, ActivitySummary } from '@/types/admin';
interface AdminDashboardProps {
  className?: string;
}
type DashboardView = 'overview' | 'users' | 'create-user' | 'activity' | 'bulk-operations';
export function AdminDashboard({ className = '' }: AdminDashboardProps) {
  const { hasRole, hasPermission } = useRole();
  const [currentView, setCurrentView] = useState<DashboardView>('overview');
  const [userStats, setUserStats] = useState<UserStatistics | null>(null);
  const [activitySummary, setActivitySummary] = useState<ActivitySummary | null>(null);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Ensure user has admin permissions
  if (!hasRole('admin')) {
    return (
    <ErrorBoundary fallback={<div>Something went wrong in AdminDashboard</div>}>
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">You need admin privileges to access this dashboard.</p>
        </div>
      </div>
    );
  }
  // Load dashboard data
  useEffect(() => {
    loadDashboardData();
  }, []);
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      // Load user statistics
      const statsResponse = await fetch('/api/admin/users/stats');
      if (!statsResponse.ok) {
        throw new Error('Failed to load user statistics');
      }
      const statsData = await statsResponse.json();
      setUserStats(statsData.data);
      // Load activity summary
      const activityResponse = await fetch('/api/admin/system/activity-summary?period=week');
      if (!activityResponse.ok) {
        throw new Error('Failed to load activity summary');
      }
      const activityData = await activityResponse.json();
      setActivitySummary(activityData.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };
  const handleUserCreated = () => {
    // Refresh dashboard data and switch to users view
    loadDashboardData();
    setCurrentView('users');
  };
  const handleBulkOperationComplete = () => {
    // Refresh dashboard data
    loadDashboardData();
    setSelectedUsers([]);
  };
  const renderNavigationTabs = () => (
    <div className="border-b border-gray-200 mb-6">
      <nav className="-mb-px flex space-x-8">
        <button
          onClick={() => setCurrentView('overview')}
          className={`py-2 px-1 border-b-2 font-medium text-sm ${
            currentView === 'overview'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
        </button>
        <button
          onClick={() => setCurrentView('users')}
          className={`py-2 px-1 border-b-2 font-medium text-sm ${
            currentView === 'users'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
        </button>
        <button
          onClick={() => setCurrentView('create-user')}
          className={`py-2 px-1 border-b-2 font-medium text-sm ${
            currentView === 'create-user'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
        </button>
        <button
          onClick={() => setCurrentView('activity')}
          className={`py-2 px-1 border-b-2 font-medium text-sm ${
            currentView === 'activity'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
        </button>
        {selectedUsers.length > 0 && (
          <button
            onClick={() => setCurrentView('bulk-operations')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              currentView === 'bulk-operations'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Bulk Operations ({selectedUsers.length})
          </button>
        )}
      </nav>
    </div>
  );
  const renderOverview = () => (
    <div className="space-y-6">
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
              {Math.round((userStats.verified_users / userStats.total_users) * 100)}% verified
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow sm:p-4 md:p-6">
            <h3 className="text-sm font-medium text-gray-500 md:text-base lg:text-lg">2FA Enabled</h3>
            <p className="text-3xl font-bold text-purple-600">{userStats.two_factor_enabled}</p>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">
              {Math.round((userStats.two_factor_enabled / userStats.total_users) * 100)}% adoption
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
                    <span className="capitalize">{action.action.replace('_', ' ')}</span>
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
          <button
            onClick={() => setCurrentView('create-user')}
            className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left sm:p-4 md:p-6"
          >
            <h4 className="font-medium text-gray-900">Create New User</h4>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">Add a new user account</p>
          </button>
          <button
            onClick={() => setCurrentView('users')}
            className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left sm:p-4 md:p-6"
          >
            <h4 className="font-medium text-gray-900">Manage Users</h4>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">View and edit user accounts</p>
          </button>
          <button
            onClick={() => setCurrentView('activity')}
            className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left sm:p-4 md:p-6"
          >
            <h4 className="font-medium text-gray-900">View Activity</h4>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">Monitor user activity and events</p>
          </button>
        </div>
      </div>
    </div>
  );
  const renderCurrentView = () => {
    switch (currentView) {
      case 'overview':
        return renderOverview();
      case 'users':
        return (
          <UserManagementTable
            selectedUsers={selectedUsers}
            onSelectionChange={setSelectedUsers}
            onUserUpdated={loadDashboardData}
          />
        );
      case 'create-user':
        return <UserCreationForm onUserCreated={handleUserCreated} />;
      case 'activity':
        return <UserActivityMonitor />;
      case 'bulk-operations':
        return (
          <BulkUserOperations
            selectedUserIds={selectedUsers}
            onOperationComplete={handleBulkOperationComplete}
            onCancel={() => setCurrentView('users')}
          />
        );
      default:
        return renderOverview();
    }
  };
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 "></div>
      </div>
    );
  }
  return (
    <div className={`min-h-screen bg-gray-50 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-2">Manage users and monitor system activity</p>
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md sm:p-4 md:p-6">
              <p className="text-red-800">{error}</p>
              <button
                onClick={loadDashboardData}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline md:text-base lg:text-lg"
               aria-label="Button">
              </button>
            </div>
          )}
        </div>
        {/* Navigation */}
        {renderNavigationTabs()}
        {/* Content */}
        {renderCurrentView()}
      </div>
    </div>
    </ErrorBoundary>
  );
}
