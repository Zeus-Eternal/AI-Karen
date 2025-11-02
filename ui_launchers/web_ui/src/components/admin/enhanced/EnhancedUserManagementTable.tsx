/**
 * Enhanced User Management Table
 * 
 * User management table with comprehensive error handling, accessibility features,
 * keyboard navigation, and confirmation dialogs.
 * 
 * Requirements: 7.2, 7.4, 7.5, 7.7
 */

"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useRole } from '@/hooks/useRole';
import { UserEditModal } from '../UserEditModal';
import { UserSearchFilters } from '../UserSearchFilters';
import ErrorDisplay, { ErrorToast } from '@/components/ui/error-display';
import { DeleteUserConfirmation, DeactivateUserConfirmation } from '@/components/ui/confirmation-dialog';
import { SimpleProgressBar } from '@/components/ui/progress-indicator';
import { useKeyboardNavigation } from '@/lib/accessibility/keyboard-navigation';
import { useAriaLiveRegion, AriaManager } from '@/lib/accessibility/aria-helpers';
import AdminErrorHandler, { type AdminError } from '@/lib/errors/admin-error-handler';
import type {  User, UserListFilter, PaginationParams, PaginatedResponse, AdminApiResponse } from '@/types/admin';

interface EnhancedUserManagementTableProps {
  selectedUsers: string[];
  onSelectionChange: (userIds: string[]) => void;
  onUserUpdated: () => void;
  className?: string;
}

interface TableColumn {
  key: keyof User | 'actions';
  label: string;
  sortable: boolean;
  width?: string;
  ariaLabel?: string;
}

const columns: TableColumn[] = [
  { key: 'email', label: 'Email', sortable: true, width: 'w-1/4', ariaLabel: 'Sort by email address' },
  { key: 'full_name', label: 'Full Name', sortable: true, width: 'w-1/6', ariaLabel: 'Sort by full name' },
  { key: 'role', label: 'Role', sortable: true, width: 'w-24', ariaLabel: 'Sort by user role' },
  { key: 'is_active', label: 'Status', sortable: true, width: 'w-20', ariaLabel: 'Sort by account status' },
  { key: 'is_verified', label: 'Verified', sortable: true, width: 'w-20', ariaLabel: 'Sort by verification status' },
  { key: 'last_login_at', label: 'Last Login', sortable: true, width: 'w-32', ariaLabel: 'Sort by last login date' },
  { key: 'created_at', label: 'Created', sortable: true, width: 'w-32', ariaLabel: 'Sort by creation date' },
  { key: 'actions', label: 'Actions', sortable: false, width: 'w-32', ariaLabel: 'User actions' }
];

export function EnhancedUserManagementTable({
  selectedUsers,
  onSelectionChange,
  onUserUpdated,
  className = ''
}: EnhancedUserManagementTableProps) {
  const { hasRole } = useRole();
  const tableRef = useRef<HTMLDivElement>(null);
  const { announce } = useAriaLiveRegion();
  
  // State management
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AdminError | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [deletingUser, setDeletingUser] = useState<User | null>(null);
  const [deactivatingUser, setDeactivatingUser] = useState<User | null>(null);
  const [operationLoading, setOperationLoading] = useState<string | null>(null);
  
  // Filter and pagination state
  const [filters, setFilters] = useState<UserListFilter>({});
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    limit: 20,
    sort_by: 'created_at',
    sort_order: 'desc'

  const [totalPages, setTotalPages] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);

  // Keyboard navigation
  useKeyboardNavigation(tableRef, {
    enableArrowKeys: true,
    enableHomeEndKeys: true,
    focusableSelector: 'button, input[type="checkbox"], a',
    onEscape: () => {
      setEditingUser(null);
      setDeletingUser(null);
      setDeactivatingUser(null);
    }

  // Load users with error handling and retry logic
  const loadUsers = useCallback(async (retryCount = 0) => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      
      // Add pagination params
      params.append('page', pagination.page.toString());
      params.append('limit', pagination.limit.toString());
      params.append('sort_by', pagination.sort_by || 'created_at');
      params.append('sort_order', pagination.sort_order || 'desc');

      // Add filter params
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          if (value instanceof Date) {
            params.append(key, value.toISOString());
          } else {
            params.append(key, value.toString());
          }
        }

      const response = await fetch(`/api/admin/users?${params.toString()}`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw AdminErrorHandler.fromHttpError(response.status, errorData);
      }

      const data: AdminApiResponse<PaginatedResponse<User>> = await response.json();
      if (!data.success || !data.data) {
        throw AdminErrorHandler.createError('SYSTEM_SERVER_ERROR', data.error?.message);
      }

      setUsers(data.data?.data || []);
      setTotalPages(data.data?.pagination.total_pages || 1);
      setTotalUsers(data.data?.pagination.total || 0);

      // Announce successful load to screen readers
      announce(`Loaded ${data.data?.data?.length || 0} users. Page ${pagination.page} of ${data.data?.pagination.total_pages || 1}.`);

    } catch (err) {
      const adminError = err instanceof Error 
        ? AdminErrorHandler.fromNetworkError(err)
        : err as AdminError;

      AdminErrorHandler.logError(adminError, {
        operation: 'load_users',
        userId: 'current_user',
        timestamp: new Date()

      // Retry logic for retryable errors
      if (AdminErrorHandler.shouldRetry(adminError, retryCount + 1)) {
        const delay = AdminErrorHandler.getRetryDelay(adminError, retryCount + 1);
        setTimeout(() => loadUsers(retryCount + 1), delay);
        return;
      }

      setError(adminError);
      announce(`Error loading users: ${adminError.message}`, 'assertive');
    } finally {
      setLoading(false);
    }
  }, [filters, pagination, announce]);

  // Load users when filters or pagination change
  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleSort = (column: keyof User) => {
    const currentSortBy = pagination.sort_by;
    const currentSortOrder = pagination.sort_order;
    
    setPagination(prev => ({
      ...prev,
      sort_by: column,
      sort_order: prev.sort_by === column && prev.sort_order === 'asc' ? 'desc' : 'asc',
      page: 1
    }));
    
    announce(`Sorting by ${column} ${currentSortBy === column && currentSortOrder === 'asc' ? 'descending' : 'ascending'}`);
  };

  const handlePageChange = (newPage: number) => {
    setPagination(prev => ({ ...prev, page: newPage }));
    announce(`Navigated to page ${newPage}`);
  };

  const handleLimitChange = (newLimit: number) => {
    setPagination(prev => ({ ...prev, limit: newLimit, page: 1 }));
    announce(`Changed page size to ${newLimit} items`);
  };

  const handleFilterChange = (newFilters: UserListFilter) => {
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, page: 1 }));
    announce('Filters updated, refreshing user list');
  };

  const handleSelectUser = (userId: string, selected: boolean) => {
    if (selected) {
      onSelectionChange([...selectedUsers, userId]);
      announce(`Selected user ${userId}`);
    } else {
      onSelectionChange(selectedUsers.filter(id => id !== userId));
      announce(`Deselected user ${userId}`);
    }
  };

  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      onSelectionChange(users.map(user => user.user_id));
      announce(`Selected all ${users.length} users on this page`);
    } else {
      onSelectionChange([]);
      announce('Deselected all users');
    }
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    announce(`Opening edit dialog for user ${user.email}`);
  };

  const handleUserUpdated = () => {
    setEditingUser(null);
    loadUsers();
    onUserUpdated();
    announce('User updated successfully');
  };

  const handleDeleteUser = async () => {
    if (!deletingUser) return;

    try {
      setOperationLoading(`delete-${deletingUser.user_id}`);
      
      const response = await fetch(`/api/admin/users/${deletingUser.user_id}`, {
        method: 'DELETE'

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw AdminErrorHandler.fromHttpError(response.status, errorData);
      }

      setDeletingUser(null);
      loadUsers();
      onUserUpdated();
      announce(`User ${deletingUser.email} deleted successfully`, 'assertive');

    } catch (err) {
      const adminError = err instanceof Error 
        ? AdminErrorHandler.fromNetworkError(err)
        : err as AdminError;

      AdminErrorHandler.logError(adminError, {
        operation: 'delete_user',
        resource: deletingUser.user_id,
        timestamp: new Date()

      setError(adminError);
      announce(`Failed to delete user: ${adminError.message}`, 'assertive');
    } finally {
      setOperationLoading(null);
    }
  };

  const handleToggleUserStatus = async (user: User) => {
    try {
      setOperationLoading(`toggle-${user.user_id}`);
      
      const response = await fetch(`/api/admin/users/${user.user_id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !user.is_active })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw AdminErrorHandler.fromHttpError(response.status, errorData);
      }

      setDeactivatingUser(null);
      loadUsers();
      onUserUpdated();
      
      const action = user.is_active ? 'deactivated' : 'activated';
      announce(`User ${user.email} ${action} successfully`, 'assertive');

    } catch (err) {
      const adminError = err instanceof Error 
        ? AdminErrorHandler.fromNetworkError(err)
        : err as AdminError;

      AdminErrorHandler.logError(adminError, {
        operation: 'toggle_user_status',
        resource: user.user_id,
        timestamp: new Date()

      setError(adminError);
      announce(`Failed to update user status: ${adminError.message}`, 'assertive');
    } finally {
      setOperationLoading(null);
    }
  };

  const formatDate = (date: Date | string | null | undefined) => {
    if (!date) return 'Never';
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'super_admin': return 'bg-purple-100 text-purple-800';
      case 'admin': return 'bg-blue-100 text-blue-800';
      case 'user': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (isActive: boolean) => {
    return isActive 
      ? 'bg-green-100 text-green-800' 
      : 'bg-red-100 text-red-800';
  };

  const canEditUser = (user: User) => {
    if (hasRole('super_admin')) return true;
    if (hasRole('admin')) return user.role === 'user';
    return false;
  };

  const renderTableHeader = () => (
    <thead className="bg-gray-50">
      <tr>
        <th className="px-6 py-3 text-left" scope="col">
          <input
            type="checkbox"
            checked={selectedUsers.length === users.length && users.length  aria-label="Input"> 0}
            onChange={(e) => handleSelectAll(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-2"
            aria-label={`Select all ${users.length} users on this page`}
          />
        </th>
        {columns.map((column) => (
          <th
            key={column.key}
            className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${column.width || ''}`}
            scope="col"
          >
            {column.sortable ? (
              <button
                onClick={() => handleSort(column.key as keyof User)}
                className="flex items-center space-x-1 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                aria-label={column.ariaLabel}
                aria-sort={
                  pagination.sort_by === column.key 
                    ? pagination.sort_order === 'asc' ? 'ascending' : 'descending'
                    : 'none'
                }
              >
                <span>{column.label}</span>
                {pagination.sort_by === column.key && (
                  <span className="text-blue-600" aria-hidden="true">
                    {pagination.sort_order === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </button>
            ) : (
              column.label
            )}
          </th>
        ))}
      </tr>
    </thead>
  );

  const renderTableRow = (user: User, index: number) => (
    <tr 
      key={user.user_id} 
      className="bg-white hover:bg-gray-50 focus-within:bg-gray-50"
      role="row"
    >
      <td className="px-6 py-4 whitespace-nowrap" role="gridcell">
        <input
          type="checkbox"
          checked={selectedUsers.includes(user.user_id)}
          onChange={(e) => handleSelectUser(user.user_id, e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-2"
          aria-label={`Select user ${user.email}`}
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap" role="gridcell">
        <div className="text-sm font-medium text-gray-900 md:text-base lg:text-lg">{user.email}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap" role="gridcell">
        <div className="text-sm text-gray-900 md:text-base lg:text-lg">{user.full_name || 'Not set'}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap" role="gridcell">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColor(user.role)}`}>
          {user.role.replace('_', ' ')}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap" role="gridcell">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(user.is_active)}`}>
          {user.is_active ? 'Active' : 'Inactive'}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap" role="gridcell">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${user.is_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
          {user.is_verified ? 'Verified' : 'Pending'}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 md:text-base lg:text-lg" role="gridcell">
        <time dateTime={user.last_login_at?.toString()}>
          {formatDate(user.last_login_at)}
        </time>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 md:text-base lg:text-lg" role="gridcell">
        <time dateTime={user.created_at?.toString()}>
          {formatDate(user.created_at)}
        </time>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium md:text-base lg:text-lg" role="gridcell">
        <div className="flex space-x-2">
          {canEditUser(user) && (
            <>
              <button
                onClick={() => handleEditUser(user)}
                className="text-blue-600 hover:text-blue-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                aria-label={`Edit user ${user.email}`}
                disabled={operationLoading === `edit-${user.user_id}`}
              >
              </button>
              <button
                onClick={() => {
                  if (user.is_active) {
                    setDeactivatingUser(user);
                  } else {
                    handleToggleUserStatus(user);
                  }
                }}
                className={`focus:outline-none focus:ring-2 focus:ring-offset-2 rounded ${
                  user.is_active 
                    ? 'text-red-600 hover:text-red-900 focus:ring-red-500' 
                    : 'text-green-600 hover:text-green-900 focus:ring-green-500'
                }`}
                aria-label={`${user.is_active ? 'Deactivate' : 'Activate'} user ${user.email}`}
                disabled={operationLoading === `toggle-${user.user_id}`}
              >
                {operationLoading === `toggle-${user.user_id}` ? (
                  <span className="flex items-center">
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current mr-1 " />
                    Processing...
                  </span>
                ) : (
                  user.is_active ? 'Deactivate' : 'Activate'
                )}
              </button>
              {hasRole('super_admin') && (
                <button
                  onClick={() => setDeletingUser(user)}
                  className="text-red-600 hover:text-red-900 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 rounded"
                  aria-label={`Delete user ${user.email}`}
                  disabled={operationLoading === `delete-${user.user_id}`}
                >
                </button>
              )}
            </>
          )}
        </div>
      </td>
    </tr>
  );

  const renderPagination = () => (
    <nav 
      className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6"
      aria-label="User list pagination"
    >
      <div className="flex-1 flex justify-between sm:hidden">
        <button
          onClick={() => handlePageChange(pagination.page - 1)}
          disabled={pagination.page <= 1}
          className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
          aria-label="Go to previous page"
        >
        </button>
        <button
          onClick={() => handlePageChange(pagination.page + 1)}
          disabled={pagination.page >= totalPages}
          className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
          aria-label="Go to next page"
        >
        </button>
      </div>
      <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
        <div className="flex items-center space-x-4">
          <p className="text-sm text-gray-700 md:text-base lg:text-lg" role="status" aria-live="polite">
            Showing <span className="font-medium">{((pagination.page - 1) * pagination.limit) + 1}</span> to{' '}
            <span className="font-medium">{Math.min(pagination.page * pagination.limit, totalUsers)}</span> of{' '}
            <span className="font-medium">{totalUsers}</span> results
          </p>
          <label className="flex items-center text-sm md:text-base lg:text-lg">
            <span className="mr-2">Show:</span>
            <select
              value={pagination.limit}
              onChange={(e) => handleLimitChange(parseInt(e.target.value))}
              className="border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 md:text-base lg:text-lg"
              aria-label="Number of users per page"
            >
              <option value={10}>10 per page</option>
              <option value={20}>20 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>
          </label>
        </div>
        <div>
          <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
            <button
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
              className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
              aria-label="Go to previous page"
            >
            </button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const pageNum = i + Math.max(1, pagination.page - 2);
              if (pageNum > totalPages) return null;
              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    pageNum === pagination.page
                      ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                      : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                  }`}
                  aria-label={`Go to page ${pageNum}`}
                  aria-current={pageNum === pagination.page ? 'page' : undefined}
                >
                  {pageNum}
                </button>
              );
            })}
            <button
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page >= totalPages}
              className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
              aria-label="Go to next page"
            >
            </button>
          </nav>
        </div>
      </div>
    </nav>
  );

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12" role="status" aria-live="polite">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4 "></div>
        <p className="text-gray-600">Loading users...</p>
        <SimpleProgressBar progress={50} className="w-48 mt-4 " />
      </div>
    );
  }

  return (
    <div className={`bg-white shadow overflow-hidden sm:rounded-md ${className}`} ref={tableRef}>
      {/* Search and Filters */}
      <UserSearchFilters
        filters={filters}
        onFiltersChange={handleFilterChange}
        onRefresh={() => loadUsers()}
      />

      {/* Error Display */}
      {error && (
        <ErrorDisplay
          error={error}
          onRetry={() => loadUsers()}
          onDismiss={() => setError(null)}
          className="m-4"
        />
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table 
          className="min-w-full divide-y divide-gray-200" 
          role="grid" 
          aria-label="User management table"
          aria-rowcount={users.length + 1}
        >
          {renderTableHeader()}
          <tbody className="bg-white divide-y divide-gray-200">
            {users.length > 0 ? (
              users.map((user, index) => renderTableRow(user, index))
            ) : (
              <tr>
                <td colSpan={columns.length + 1} className="px-6 py-12 text-center text-gray-500">
                  <div className="flex flex-col items-center">
                    <p className="text-lg font-medium mb-2">No users found</p>
                    <p className="text-sm md:text-base lg:text-lg">Try adjusting your search criteria or filters.</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {users.length > 0 && renderPagination()}

      {/* Modals and Dialogs */}
      {editingUser && (
        <UserEditModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onUserUpdated={handleUserUpdated}
        />
      )}

      {deletingUser && (
        <DeleteUserConfirmation
          isOpen={true}
          onClose={() => setDeletingUser(null)}
          onConfirm={handleDeleteUser}
          userEmail={deletingUser.email}
          loading={operationLoading === `delete-${deletingUser.user_id}`}
        />
      )}

      {deactivatingUser && (
        <DeactivateUserConfirmation
          isOpen={true}
          onClose={() => setDeactivatingUser(null)}
          onConfirm={() => handleToggleUserStatus(deactivatingUser)}
          userEmail={deactivatingUser.email}
          loading={operationLoading === `toggle-${deactivatingUser.user_id}`}
        />
      )}

      {/* Error Toast for non-critical errors */}
      {error && error.severity === 'low' && (
        <ErrorToast
          error={error}
          onDismiss={() => setError(null)}
        />
      )}
    </div>
  );
}

export default EnhancedUserManagementTable;