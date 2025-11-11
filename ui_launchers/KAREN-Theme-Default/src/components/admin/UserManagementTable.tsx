/**
 * User Management Table Component (Production Hardened)
 *
 * Provides a comprehensive table for managing users with sorting, filtering, pagination,
 * search capabilities, selection, inline status toggling, and modal-based editing.
 *
 * Requirements: 4.1, 4.2, 4.4, 4.5, 4.6, 7.3, 7.4
 */

"use client";

import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useRole } from "@/hooks/useRole";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { UserEditModal } from "./UserEditModal";
import { UserSearchFilters } from "./UserSearchFilters";
import type {
  User,
  UserListFilter,
  PaginationParams,
  PaginatedResponse,
  AdminApiResponse,
} from "@/types/admin";

export interface UserManagementTableProps {
  selectedUsers: string[];
  onSelectionChange: (userIds: string[]) => void;
  onUserUpdated: () => void;
  className?: string;
}

export interface TableColumn {
  key: keyof User | "actions";
  label: string;
  sortable: boolean;
  width?: string;
}

const columns: TableColumn[] = [
  { key: "email", label: "Email", sortable: true, width: "w-1/4" },
  { key: "full_name", label: "Full Name", sortable: true, width: "w-1/6" },
  { key: "role", label: "Role", sortable: true, width: "w-24" },
  { key: "is_active", label: "Status", sortable: true, width: "w-20" },
  { key: "is_verified", label: "Verified", sortable: true, width: "w-20" },
  { key: "last_login_at", label: "Last Login", sortable: true, width: "w-32" },
  { key: "created_at", label: "Created", sortable: true, width: "w-32" },
  { key: "actions", label: "Actions", sortable: false, width: "w-40" },
];

export function UserManagementTable({
  selectedUsers,
  onSelectionChange,
  onUserUpdated,
  className = "",
}: UserManagementTableProps) {
  const { hasRole, hasPermission } = useRole();

  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  // Filters & pagination
  const [filters, setFilters] = useState<UserListFilter>({});
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    limit: 20,
    sort_by: "created_at",
    sort_order: "desc",
  });
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalUsers, setTotalUsers] = useState<number>(0);

  // Abort in-flight loads on rapid changes
  const fetchAbortRef = useRef<AbortController | null>(null);

  const canEditUser = useCallback(
    (target: User) => {
      // Super admins can edit anyone
      if (hasRole("super_admin")) return true;
      // Admins can only edit regular users
      if (hasRole("admin")) return target.role === "user";
      return false;
    },
    [hasRole]
  );

  const getRoleColor = (role: string) => {
    switch (role) {
      case "super_admin":
        return "bg-purple-100 text-purple-800";
      case "admin":
        return "bg-blue-100 text-blue-800";
      case "user":
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusColor = (isActive: boolean) =>
    isActive ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800";

  const formatDate = (date: Date | string | null | undefined) => {
    if (!date) return "Never";
    const d = typeof date === "string" ? new Date(date) : date;
    return (
      d.toLocaleDateString() +
      " " +
      d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    );
  };

  const buildQueryString = useCallback(() => {
    const params = new URLSearchParams();
    // Pagination
    params.append("page", String(pagination.page));
    params.append("limit", String(pagination.limit));
    params.append("sort_by", (pagination.sort_by as string) || "created_at");
    params.append("sort_order", pagination.sort_order || "desc");
    // Filters
    Object.entries(filters).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") return;
      if (value instanceof Date) {
        params.append(key, value.toISOString());
      } else {
        params.append(key, String(value));
      }
    });
    return params.toString();
  }, [filters, pagination]);

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Abort previous request if any
      if (fetchAbortRef.current) fetchAbortRef.current.abort();
      const controller = new AbortController();
      fetchAbortRef.current = controller;

      const qs = buildQueryString();
      const response = await fetch(`/api/admin/users?${qs}`, {
        method: "GET",
        signal: controller.signal,
        headers: { accept: "application/json" },
      });

      if (!response.ok) {
        throw new Error(`Failed to load users: ${response.status} ${response.statusText}`);
      }

      const data: AdminApiResponse<PaginatedResponse<User>> = await response.json();
      if (!data?.success || !data?.data) {
        throw new Error(data?.error?.message || "Failed to load users");
      }

      setUsers(data.data.data || []);
      setTotalPages(data.data.pagination.total_pages || 1);
      setTotalUsers(data.data.pagination.total || 0);
    } catch (err: Error) {
      if (err?.name === "AbortError") return; // ignore aborts
      setError(err instanceof Error ? err.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, [buildQueryString]);

  // Load on first mount and whenever filters/pagination change
  useEffect(() => {
    loadUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, pagination.page, pagination.limit, pagination.sort_by, pagination.sort_order]);

  const handleSort = (column: keyof User) => {
    setPagination((prev) => ({
      ...prev,
      sort_by: column,
      sort_order: prev.sort_by === column && prev.sort_order === "asc" ? "desc" : "asc",
      page: 1,
    }));
  };

  const handlePageChange = (newPage: number) => {
    setPagination((prev) => ({ ...prev, page: Math.max(1, Math.min(totalPages, newPage)) }));
  };

  const handleLimitChange = (newLimit: number) => {
    setPagination((prev) => ({ ...prev, limit: newLimit, page: 1 }));
  };

  const handleFilterChange = (newFilters: UserListFilter) => {
    setFilters(newFilters);
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handleSelectUser = (userId: string, selected: boolean) => {
    if (selected) {
      if (!selectedUsers.includes(userId)) onSelectionChange([...selectedUsers, userId]);
    } else {
      onSelectionChange(selectedUsers.filter((id) => id !== userId));
    }
  };

  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      onSelectionChange(users.map((u) => u.user_id));
    } else {
      onSelectionChange([]);
    }
  };

  const handleEditUser = (u: User) => setEditingUser(u);

  const handleUserUpdated = () => {
    setEditingUser(null);
    loadUsers();
    onUserUpdated();
  };

  const handleToggleUserStatus = async (u: User) => {
    try {
      const response = await fetch(`/api/admin/users/${u.user_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !u.is_active }),
      });
      if (!response.ok) throw new Error("Failed to update user status");
      loadUsers();
      onUserUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user status");
    }
  };

  const allSelected = useMemo(
    () => users.length > 0 && selectedUsers.length === users.length,
    [users.length, selectedUsers.length]
  );

  const renderTableHeader = () => (
    <thead className="bg-gray-50">
      <tr>
        <th className="px-6 py-3 text-left">
          <input
            type="checkbox"
            aria-label="Select all users on page"
            checked={allSelected}
            onChange={(e) => handleSelectAll(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
        </th>
        {columns.map((column) => (
          <th
            key={column.key}
            className={cn(
              "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
              column.width || ""
            )}
          >
            {column.sortable ? (
              <Button
                type="button"
                onClick={() => handleSort(column.key as keyof User)}
                className="flex items-center space-x-1 hover:text-gray-700"
                aria-label={`Sort by ${column.label}`}
                variant="ghost"
              >
                <span>{column.label}</span>
                {pagination.sort_by === column.key && (
                  <span className="text-blue-600">{pagination.sort_order === "asc" ? "↑" : "↓"}</span>
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

  const renderTableRow = (u: User) => (
    <tr key={u.user_id} className="bg-white hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap">
        <input
          type="checkbox"
          aria-label={`Select user ${u.email}`}
          checked={selectedUsers.includes(u.user_id)}
          onChange={(e) => handleSelectUser(u.user_id, e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm font-medium text-gray-900">{u.email}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-gray-900">{u.full_name || "Not set"}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={cn("inline-flex px-2 py-1 text-xs font-semibold rounded-full", getRoleColor(u.role))}>
          {u.role.replace("_", " ")}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={cn("inline-flex px-2 py-1 text-xs font-semibold rounded-full", getStatusColor(u.is_active))}>
          {u.is_active ? "Active" : "Inactive"}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span
          className={cn(
            "inline-flex px-2 py-1 text-xs font-semibold rounded-full",
            u.is_verified ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
          )}
        >
          {u.is_verified ? "Verified" : "Pending"}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(u.last_login_at)}</td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(u.created_at)}</td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
        <div className="flex space-x-2">
          {canEditUser(u) && (
            <>
              <Button
                type="button"
                onClick={() => handleEditUser(u)}
                className="text-blue-600 hover:text-blue-900"
                variant="link"
                aria-label={`Edit ${u.email}`}
              >
                Edit
              </Button>
              <Button
                type="button"
                onClick={() => handleToggleUserStatus(u)}
                className={cn(
                  "px-2 py-1 text-sm",
                  u.is_active ? "text-red-600 hover:text-red-900" : "text-green-600 hover:text-green-900"
                )}
                variant="link"
                aria-label={`${u.is_active ? "Deactivate" : "Activate"} ${u.email}`}
              >
                {u.is_active ? "Deactivate" : "Activate"}
              </Button>
            </>
          )}
        </div>
      </td>
    </tr>
  );

  const renderPagination = () => (
    <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
      {/* Mobile simple pager */}
      <div className="flex-1 flex justify-between sm:hidden">
        <Button
          type="button"
          onClick={() => handlePageChange(pagination.page - 1)}
          disabled={pagination.page <= 1}
          className="px-4 py-2"
          variant="outline"
          aria-label="Previous page"
        >
          Previous
        </Button>
        <Button
          type="button"
          onClick={() => handlePageChange(pagination.page + 1)}
          disabled={pagination.page >= totalPages}
          className="ml-3 px-4 py-2"
          variant="outline"
          aria-label="Next page"
        >
          Next
        </Button>
      </div>

      {/* Desktop pager */}
      <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
        <div className="flex items-center space-x-4">
          <p className="text-sm text-gray-700">
            Showing{" "}
            <span className="font-medium">
              {totalUsers === 0 ? 0 : (pagination.page - 1) * pagination.limit + 1}
            </span>{" "}
            to{" "}
            <span className="font-medium">
              {Math.min(pagination.page * pagination.limit, totalUsers)}
            </span>{" "}
            of <span className="font-medium">{totalUsers}</span> results
          </p>
          <select
            value={pagination.limit}
            onChange={(e) => handleLimitChange(parseInt(e.target.value))}
            className="border border-gray-300 rounded-md text-sm"
            aria-label="Rows per page"
          >
            <option value={10}>10 per page</option>
            <option value={20}>20 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
          </select>
        </div>
        <div>
          <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
            <Button
              type="button"
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
              className="px-2 py-2 rounded-l-md"
              variant="outline"
              aria-label="Previous page"
            >
              ‹
            </Button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const start = Math.max(1, pagination.page - 2);
              const pageNum = start + i;
              if (pageNum > totalPages) return null;
              const isCurrent = pageNum === pagination.page;
              return (
                <Button
                  type="button"
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={cn(
                    "px-4 py-2 border text-sm font-medium",
                    isCurrent ? "z-10 bg-blue-50 border-blue-500 text-blue-600" : "bg-white"
                  )}
                  variant={isCurrent ? "default" : "outline"}
                  aria-current={isCurrent ? "page" : undefined}
                  aria-label={`Go to page ${pageNum}`}
                >
                  {pageNum}
                </Button>
              );
            })}
            <Button
              type="button"
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page >= totalPages}
              className="px-2 py-2 rounded-r-md"
              variant="outline"
              aria-label="Next page"
            >
              ›
            </Button>
          </nav>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className={cn("bg-white shadow overflow-hidden sm:rounded-md", className)}>
      {/* Search & Filters */}
      <UserSearchFilters filters={filters} onFiltersChange={handleFilterChange} onRefresh={loadUsers} />

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border-l-4 border-red-400">
          <p className="text-red-700">{error}</p>
          <Button
            type="button"
            onClick={loadUsers}
            className="mt-2 text-sm"
            variant="link"
            aria-label="Retry loading users"
          >
            Retry
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
        <UserEditModal user={editingUser} onClose={() => setEditingUser(null)} onUserUpdated={handleUserUpdated} />
      )}
    </div>
  );
}
