/**
 * Virtualized User Table Component
 * 
 * Provides high-performance table rendering for large user lists using virtual scrolling
 * and optimized pagination to handle thousands of users efficiently.
 * 
 * Requirements: 7.3, 7.5
 */
"use client";

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { FixedSizeList as List } from 'react-window';
import { useRole } from '@/hooks/useRole';
import { UserListCache, AdminCacheManager } from '@/lib/cache/admin-cache';
import type {  User, UserListFilter, PaginationParams, PaginatedResponse, AdminApiResponse } from '@/types/admin';
interface VirtualizedUserTableProps {
  selectedUsers: string[];
  onSelectionChange: (userIds: string[]) => void;
  onUserUpdated: () => void;
  className?: string;
  height?: number;
  itemHeight?: number;
  overscan?: number;
}
interface TableColumn {
  key: keyof User | 'actions' | 'select';
  label: string;
  sortable: boolean;
  width: number;
  minWidth?: number;
  render?: (
    user: User,
    value: any,
    helpers: {
      onSelect?: (userId: string, selected: boolean) => void;
      onEdit?: (user: User) => void;
      onToggleStatus?: (user: User) => void;
    }
  ) => React.ReactNode;
}
const columns: TableColumn[] = [
  { 
    key: 'select', 
    label: '', 
    sortable: false, 
    width: 50,
    render: (user, value, helpers) => (
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => helpers.onSelect?.(user.user_id, e.target.checked)}
        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
      />
    )
  },
  { key: 'email', label: 'Email', sortable: true, width: 250, minWidth: 200 },
  { key: 'full_name', label: 'Full Name', sortable: true, width: 200, minWidth: 150 },
  { 
    key: 'role', 
    label: 'Role', 
    sortable: true, 
    width: 120,
    render: (user, value) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleColor(value)}`}>
        {value.replace('_', ' ').toUpperCase()}
      </span>
    )
  },
  { 
    key: 'is_active', 
    label: 'Status', 
    sortable: true, 
    width: 100,
    render: (user, value) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
        value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
      }`}>
        {value ? 'Active' : 'Inactive'}
      </span>
    )
  },
  { 
    key: 'is_verified', 
    label: 'Verified', 
    sortable: true, 
    width: 100,
    render: (user, value) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
        value ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800'
      }`}>
        {value ? 'Yes' : 'No'}
      </span>
    )
  },
  { 
    key: 'last_login_at', 
    label: 'Last Login', 
    sortable: true, 
    width: 150,
    render: (user, value) => formatDate(value)
  },
  { 
    key: 'created_at', 
    label: 'Created', 
    sortable: true, 
    width: 150,
    render: (user, value) => formatDate(value)
  },
  { 
    key: 'actions', 
    label: 'Actions', 
    sortable: false, 
    width: 120,
    render: (user, value, helpers) => (
      <div className="flex space-x-2">
        <button
          onClick={() => helpers.onEdit?.(user)}
          className="text-blue-600 hover:text-blue-800 text-sm md:text-base lg:text-lg"
        >
        </button>
        <button
          onClick={() => helpers.onToggleStatus?.(user)}
          className={`text-sm ${
            user.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'
          }`}
        >
          {user.is_active ? 'Deactivate' : 'Activate'}
        </button>
      </div>
    )
  }
];
function getRoleColor(role: string): string {
  switch (role) {
    case 'super_admin': return 'bg-purple-100 text-purple-800';
    case 'admin': return 'bg-blue-100 text-blue-800';
    case 'user': return 'bg-gray-100 text-gray-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}
function formatDate(date: Date | string | null | undefined): string {
  if (!date) return 'Never';
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
// Row component for virtual list
interface RowProps {
  index: number;
  style: React.CSSProperties;
  data: {
    users: User[];
    selectedUsers: string[];
    onSelectionChange: (userId: string, selected: boolean) => void;
    onEditUser: (user: User) => void;
    onToggleStatus: (user: User) => void;
    columns: TableColumn[];
  };
}
const Row: React.FC<RowProps> = ({ index, style, data }) => {
  const { users, selectedUsers, onSelectionChange, onEditUser, onToggleStatus, columns } = data;
  const user = users[index];
  if (!user) {
    return (
      <div style={style} className="flex items-center px-4 py-2 border-b border-gray-200">
        <div className="animate-pulse bg-gray-200 h-4 w-full rounded"></div>
      </div>
    );
  }
  const isSelected = selectedUsers.includes(user.user_id);
  return (
    <div 
      style={style} 
      className={`flex items-center px-4 py-2 border-b border-gray-200 hover:bg-gray-50 ${
        isSelected ? 'bg-blue-50' : ''
      }`}
    >
      {columns.map((column) => {
        const value = column.key === 'select' 
          ? isSelected 
          : column.key === 'actions' 
            ? null 
            : user[column.key as keyof User];
        return (
          <div
            key={column.key}
            style={{ width: column.width, minWidth: column.minWidth || column.width }}
            className="flex-shrink-0 px-2 text-sm text-gray-900 truncate md:text-base lg:text-lg"
          >
            {column.render 
              ? column.render(user, value, {
                  onSelect: onSelectionChange,
                  onEdit: onEditUser,
                  onToggleStatus: onToggleStatus
                })
              : value?.toString() || '-'
            }
          </div>
        );
      })}
    </div>
  );
};
export function VirtualizedUserTable({
  selectedUsers,
  onSelectionChange,
  onUserUpdated,
  className = '',
  height = 600,
  itemHeight = 60,
  overscan = 5
}: VirtualizedUserTableProps) {
  const { hasRole, hasPermission } = useRole();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  // Filter and pagination state
  const [filters, setFilters] = useState<UserListFilter>({});
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    limit: 100, // Larger page size for virtual scrolling
    sort_by: 'created_at',
    sort_order: 'desc'

  const [totalPages, setTotalPages] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const [hasNextPage, setHasNextPage] = useState(false);
  // Virtual scrolling state
  const listRef = useRef<List>(null);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  // Memoized row data for virtual list
  const rowData = useMemo(() => ({
    users,
    selectedUsers,
    onSelectionChange: (userId: string, selected: boolean) => {
      if (selected) {
        onSelectionChange([...selectedUsers, userId]);
      } else {
        onSelectionChange(selectedUsers.filter(id => id !== userId));
      }
    },
    onEditUser: setEditingUser,
    onToggleStatus: handleToggleUserStatus,
    columns
  }), [users, selectedUsers, onSelectionChange]);
  // Load users with caching
  const loadUsers = useCallback(async (append = false) => {
    try {
      if (!append) {
        setLoading(true);
      } else {
        setIsLoadingMore(true);
      }
      setError(null);
      // Try cache first
      const cachedData = await UserListCache.get(
        filters, 
        pagination.page, 
        pagination.limit, 
        pagination.sort_by, 
        pagination.sort_order
      );
      if (cachedData && !append) {
        setUsers(cachedData.data);
        setTotalPages(cachedData.pagination.total_pages);
        setTotalUsers(cachedData.pagination.total);
        setHasNextPage(cachedData.pagination.has_next);
        setLoading(false);
        return;
      }
      // Fetch from API
      const params = new URLSearchParams();
      params.append('page', pagination.page.toString());
      params.append('limit', pagination.limit.toString());
      params.append('sort_by', pagination.sort_by || 'created_at');
      params.append('sort_order', pagination.sort_order || 'desc');
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
      // Cache the result
      UserListCache.set(
        filters, 
        pagination.page, 
        pagination.limit, 
        data.data,
        pagination.sort_by, 
        pagination.sort_order
      );
      if (append) {
        setUsers(prev => [...prev, ...(data.data?.data || [])]);
      } else {
        setUsers(data.data?.data || []);
      }
      setTotalPages(data.data?.pagination.total_pages || 1);
      setTotalUsers(data.data?.pagination.total || 0);
      setHasNextPage(data.data?.pagination.has_next || false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
      setIsLoadingMore(false);
    }
  }, [filters, pagination]);
  // Load more users for infinite scrolling
  const loadMoreUsers = useCallback(async () => {
    if (isLoadingMore || !hasNextPage) return;
    const nextPage = pagination.page + 1;
    setPagination(prev => ({ ...prev, page: nextPage }));
    // Load more users and append to existing list
    await loadUsers(true);
  }, [pagination.page, hasNextPage, isLoadingMore, loadUsers]);
  // Handle scroll to load more
  const handleScroll = useCallback(({ scrollOffset, scrollUpdateWasRequested }: any) => {
    if (scrollUpdateWasRequested) return;
    const scrollPercentage = scrollOffset / ((users.length * itemHeight) - height);
    // Load more when scrolled 80% down
    if (scrollPercentage > 0.8 && hasNextPage && !isLoadingMore) {
      loadMoreUsers();
    }
  }, [users.length, itemHeight, height, hasNextPage, isLoadingMore, loadMoreUsers]);
  // Load users when filters change
  useEffect(() => {
    setPagination(prev => ({ ...prev, page: 1 }));
    setUsers([]);
    loadUsers();
  }, [filters]);
  // Initial load
  useEffect(() => {
    loadUsers();
  }, []);
  const handleSort = (column: keyof User) => {
    setPagination(prev => ({
      ...prev,
      sort_by: column,
      sort_order: prev.sort_by === column && prev.sort_order === 'asc' ? 'desc' : 'asc',
      page: 1
    }));
    setUsers([]);
  };
  const handleFilterChange = (newFilters: UserListFilter) => {
    setFilters(newFilters);
  };
  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      onSelectionChange(users.map(user => user.user_id));
    } else {
      onSelectionChange([]);
    }
  };
  async function handleToggleUserStatus(user: User) {
    try {
      const response = await fetch(`/api/admin/users/${user.user_id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !user.is_active })

      if (!response.ok) {
        throw new Error('Failed to update user status');
      }
      // Invalidate caches
      AdminCacheManager.invalidateUserCaches(user.user_id, user.email);
      // Reload users
      setUsers([]);
      setPagination(prev => ({ ...prev, page: 1 }));
      await loadUsers();
      onUserUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user status');
    }
  }
  const handleUserUpdated = () => {
    setEditingUser(null);
    // Invalidate all user-related caches
    UserListCache.invalidateAll();
    AdminCacheManager.clearAll();
    // Reload users
    setUsers([]);
    setPagination(prev => ({ ...prev, page: 1 }));
    loadUsers();
    onUserUpdated();
  };
  if (loading && users.length === 0) {
    return (
      <div className={`bg-white shadow rounded-lg ${className}`}>
        <div className="p-6 sm:p-4 md:p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4 "></div>
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-4 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className={`bg-white shadow rounded-lg ${className}`}>
        <div className="p-6 sm:p-4 md:p-6">
          <div className="text-red-600 text-center">
            <p className="font-medium">Error loading users</p>
            <p className="text-sm mt-1 md:text-base lg:text-lg">{error}</p>
            <button
              onClick={() => loadUsers()}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
            </button>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className={`bg-white shadow rounded-lg ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Users ({totalUsers.toLocaleString()})
            </h3>
            <p className="text-sm text-gray-500 md:text-base lg:text-lg">
              Showing {users.length} of {totalUsers} users
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <label className="flex items-center text-sm text-gray-600 md:text-base lg:text-lg">
              <input
                type="checkbox"
                checked={selectedUsers.length === users.length && users.length  aria-label="Input"> 0}
                onChange={(e) => handleSelectAll(e.target.checked)}
                className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>
            {selectedUsers.length > 0 && (
              <span className="text-sm text-blue-600 font-medium md:text-base lg:text-lg">
                {selectedUsers.length} selected
              </span>
            )}
          </div>
        </div>
      </div>
      {/* Column Headers */}
      <div className="flex items-center px-4 py-3 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base">
        {columns.map((column) => (
          <div
            key={column.key}
            style={{ width: column.width, minWidth: column.minWidth || column.width }}
            className="flex-shrink-0 px-2"
          >
            {column.sortable ? (
              <button
                onClick={() => handleSort(column.key as keyof User)}
                className="flex items-center space-x-1 hover:text-gray-700"
              >
                <span>{column.label}</span>
                {pagination.sort_by === column.key && (
                  <span className="text-blue-600">
                    {pagination.sort_order === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </button>
            ) : (
              <span>{column.label}</span>
            )}
          </div>
        ))}
      </div>
      {/* Virtual List */}
      <div style={{ height }}>
        <List
          ref={listRef}
          height={height}
          width="100%"
          itemCount={users.length + (isLoadingMore ? 3 : 0)} // Add loading rows
          itemSize={itemHeight}
          itemData={rowData}
          overscanCount={overscan}
          onScroll={handleScroll}
        >
          {Row}
        </List>
      </div>
      {/* Loading More Indicator */}
      {isLoadingMore && (
        <div className="px-6 py-4 border-t border-gray-200 text-center">
          <div className="animate-pulse text-sm text-gray-500 md:text-base lg:text-lg">
            Loading more users...
          </div>
        </div>
      )}
      {/* No More Data Indicator */}
      {!hasNextPage && users.length > 0 && (
        <div className="px-6 py-4 border-t border-gray-200 text-center text-sm text-gray-500 md:text-base lg:text-lg">
        </div>
      )}
      {/* Edit User Modal */}
      {editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md sm:p-4 md:p-6">
            <h3 className="text-lg font-medium mb-4">Edit User</h3>
            <p className="text-sm text-gray-600 mb-4 md:text-base lg:text-lg">
              Editing: {editingUser.email}
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setEditingUser(null)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
              >
              </button>
              <button
                onClick={handleUserUpdated}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
               aria-label="Button">
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
