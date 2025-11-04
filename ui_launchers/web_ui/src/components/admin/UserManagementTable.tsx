/**
 * User Management Table Component
 * 
 * Provides a comprehensive table for managing users with sorting, filtering, pagination,
 * search capabilities, and inline editing functionality.
 * 
 * Requirements: 4.1, 4.2, 4.4, 4.5, 4.6, 7.3, 7.4
 */
"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { useRole } from '@/hooks/useRole';
import { UserEditModal } from './UserEditModal';
import { UserSearchFilters } from './UserSearchFilters';
import type {  User, UserListFilter, PaginationParams, PaginatedResponse, AdminApiResponse } from '@/types/admin';
interface UserManagementTableProps {
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
}
const columns: TableColumn[] = [
  { key: 'email', label: 'Email', sortable: true, width: 'w-1/4' },
  { key: 'full_name', label: 'Full Name', sortable: true, width: 'w-1/6' },
  { key: 'role', label: 'Role', sortable: true, width: 'w-24' },
  { key: 'is_active', label: 'Status', sortable: true, width: 'w-20' },
  { key: 'is_verified', label: 'Verified', sortable: true, width: 'w-20' },
  { key: 'last_login_at', label: 'Last Login', sortable: true, width: 'w-32' },
  { key: 'created_at', label: 'Created', sortable: true, width: 'w-32' },
  { key: 'actions', label: 'Actions', sortable: false, width: 'w-32' }
];
export function UserManagementTable({
  selectedUsers,
  onSelectionChange,
  onUserUpdated,
  className = ''
}: UserManagementTableProps) {
  const { hasRole, hasPermission } = useRole();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  // Filter and pagination state
  const [filters, setFilters] = useState<UserListFilter>({});
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    limit: 20,
    sort_by: 'created_at',
    sort_order: 'desc'

  const [totalPages, setTotalPages] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  // Load users with current filters and pagination
  const loadUsers = useCallback(async () => {
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
        throw new Error(`Failed to load users: ${response.statusText}`);
      }
      const data: AdminApiResponse<PaginatedResponse<User>> = await response.json();
      if (!data.success || !data.data) {
        throw new Error(data.error?.message || 'Failed to load users');
      }
      setUsers(data.data?.data || []);
      setTotalPages(data.data?.pagination.total_pages || 1);
      setTotalUsers(data.data?.pagination.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  }, [filters, pagination]);
  // Load users when filters or pagination change
  useEffect(() => {
    loadUsers();
  }, [loadUsers]);
  const handleSort = (column: keyof User) => {
    setPagination(prev => ({
      ...prev,
      sort_by: column,
      sort_order: prev.sort_by === column && prev.sort_order === 'asc' ? 'desc' : 'asc',
      page: 1 // Reset to first page when sorting
    }));
  };
  const handlePageChange = (newPage: number) => {
    setPagination(prev => ({ ...prev, page: newPage }));
  };
  const handleLimitChange = (newLimit: number) => {
    setPagination(prev => ({ ...prev, limit: newLimit, page: 1 }));
  };
  const handleFilterChange = (newFilters: UserListFilter) => {
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, page: 1 })); // Reset to first page when filtering
  };
  const handleSelectUser = (userId: string, selected: boolean) => {
    if (selected) {
      onSelectionChange([...selectedUsers, userId]);
    } else {
      onSelectionChange(selectedUsers.filter(id => id !== userId));
    }
  };
  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      onSelectionChange(users.map(user => user.user_id));
    } else {
      onSelectionChange([]);
    }
  };
  const handleEditUser = (user: User) => {
    setEditingUser(user);
  };
  const handleUserUpdated = () => {
    setEditingUser(null);
    loadUsers();
    onUserUpdated();
  };
  const handleToggleUserStatus = async (user: User) => {
    try {
      const response = await fetch(`/api/admin/users/${user.user_id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !user.is_active })

      if (!response.ok) {
        throw new Error('Failed to update user status');
      }
      loadUsers();
      onUserUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user status');
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
    // Super admins can edit anyone except other super admins (unless they are super admin themselves)
    if (hasRole('super_admin')) return true;
    // Regular admins cannot edit admins or super admins
    if (hasRole('admin')) {
      return user.role === 'user';
    }
    return false;
  };
  const renderTableHeader = () => (
    <thead className="bg-gray-50">
      <tr>
        <th className="px-6 py-3 text-left">
          <input
            type="checkbox"
            checked={selectedUsers.length === users.length && users.length  aria-label="Input"> 0}
            onChange={(e) => handleSelectAll(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
        </th>
        {columns.map((column) => (
          <th
            key={column.key}
            className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${column.width || ''}`}
          >
            {column.sortable ? (
              <Button
                onClick={() => handleSort(column.key as keyof User)}
                className="flex items-center space-x-1 hover:text-gray-700"
              >
                <span>{column.label}</span>
                {pagination.sort_by === column.key && (
                  <span className="text-blue-600">
                    {pagination.sort_order === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </Button>
            ) : (
              column.label
            )}
          </th>
        ))}
      </tr>
    </thead>
  );
  const renderTableRow = (user: User) => (
    <tr key={user.user_id} className="bg-white hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap">
        <input
          type="checkbox"
          checked={selectedUsers.includes(user.user_id)}
          onChange={(e) => handleSelectUser(user.user_id, e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm font-medium text-gray-900 md:text-base lg:text-lg">{user.email}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-gray-900 md:text-base lg:text-lg">{user.full_name || 'Not set'}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColor(user.role)}`}>
          {user.role.replace('_', ' ')}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(user.is_active)}`}>
          {user.is_active ? 'Active' : 'Inactive'}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${user.is_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
          {user.is_verified ? 'Verified' : 'Pending'}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 md:text-base lg:text-lg">
        {formatDate(user.last_login_at)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 md:text-base lg:text-lg">
        {formatDate(user.created_at)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium md:text-base lg:text-lg">
        <div className="flex space-x-2">
          {canEditUser(user) && (
            <>
              <Button
                onClick={() => handleEditUser(user)}
                className="text-blue-600 hover:text-blue-900"
              >
              </Button>
              <Button
                onClick={() => handleToggleUserStatus(user)}
                className={user.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}
              >
                {user.is_active ? 'Deactivate' : 'Activate'}
              </Button>
            </>
          )}
        </div>
      </td>
    </tr>
  );
  const renderPagination = () => (
    <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
      <div className="flex-1 flex justify-between sm:hidden">
        <Button
          onClick={() => handlePageChange(pagination.page - 1)}
          disabled={pagination.page <= 1}
          className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
        >
        </Button>
        <Button
          onClick={() => handlePageChange(pagination.page + 1)}
          disabled={pagination.page >= totalPages}
          className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
        >
        </Button>
      </div>
      <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
        <div className="flex items-center space-x-4">
          <p className="text-sm text-gray-700 md:text-base lg:text-lg">
            Showing <span className="font-medium">{((pagination.page - 1) * pagination.limit) + 1}</span> to{' '}
            <span className="font-medium">{Math.min(pagination.page * pagination.limit, totalUsers)}</span> of{' '}
            <span className="font-medium">{totalUsers}</span> results
          </p>
          <select
            value={pagination.limit}
            onChange={(e) => handleLimitChange(parseInt(e.target.value))}
            className="border border-gray-300 rounded-md text-sm md:text-base lg:text-lg"
          >
            <option value={10}>10 per page</option>
            <option value={20}>20 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
          </select>
        </div>
        <div>
          <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
            <Button
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
              className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
            >
            </Button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const pageNum = i + Math.max(1, pagination.page - 2);
              if (pageNum > totalPages) return null;
              return (
                <Button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                    pageNum === pagination.page
                      ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                      : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                  }`}
                >
                  {pageNum}
                </Button>
              );
            })}
            <Button
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page >= totalPages}
              className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
            >
            </Button>
          </nav>
        </div>
      </div>
    </div>
  );
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 "></div>
      </div>
    );
  }
  return (
    <div className={`bg-white shadow overflow-hidden sm:rounded-md ${className}`}>
      {/* Search and Filters */}
      <UserSearchFilters
        filters={filters}
        onFiltersChange={handleFilterChange}
        onRefresh={loadUsers}
      />
      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border-l-4 border-red-400 sm:p-4 md:p-6">
          <p className="text-red-700">{error}</p>
          <Button
            onClick={loadUsers}
            className="mt-2 text-sm text-red-600 hover:text-red-800 underline md:text-base lg:text-lg"
           aria-label="Button">
          </Button>
        </div>
      )}
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          {renderTableHeader()}
          <tbody className="bg-white divide-y divide-gray-200">
            {users.length > 0 ? (
              users.map(renderTableRow)
            ) : (
              <tr>
                <td colSpan={columns.length + 1} className="px-6 py-12 text-center text-gray-500">
                  No users found matching your criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {/* Pagination */}
      {users.length > 0 && renderPagination()}
      {/* Edit User Modal */}
      {editingUser && (
        <UserEditModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onUserUpdated={handleUserUpdated}
        />
      )}
    </div>
  );
}
