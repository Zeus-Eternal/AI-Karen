/**
 * Virtualized User Table Component (Production-Grade)
 *
 * High-performance user list with virtual scrolling, infinite pagination,
 * client-side sort controls, cache-first data loading, and resilient UX.
 *
 * Requirements: 7.3 (high-perf tables), 7.5 (admin polish)
 */

"use client";

import React, {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";
import { FixedSizeList as List, ListOnScrollProps } from "react-window";
import AutoSizer from "react-virtualized-auto-sizer";
import { Button } from "@/components/ui/button";
import { useRole } from "@/hooks/useRole";
import {
  UserListCache,
  AdminCacheManager,
} from "@/lib/cache/admin-cache";
import type {
  User,
  UserListFilter,
  PaginationParams,
  PaginatedResponse,
  AdminApiResponse,
} from "@/types/admin";

/* --------------------------------- Types --------------------------------- */

export interface VirtualizedUserTableProps {
  selectedUsers: string[];
  onSelectionChange: (userIds: string[]) => void;
  onUserUpdated: () => void;
  className?: string;
  height?: number; // optional fixed height fallback if AutoSizer fails
  itemHeight?: number;
  overscan?: number;
}

export interface TableColumn {
  key: keyof User | "actions" | "select";
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

/* ------------------------------- Utilities ------------------------------- */

function getRoleColor(role: string): string {
  switch (role) {
    case "super_admin":
      return "bg-purple-100 text-purple-800";
    case "admin":
      return "bg-blue-100 text-blue-800";
    case "user":
      return "bg-gray-100 text-gray-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
}

function formatDate(date: Date | string | null | undefined): string {
  if (!date) return "Never";
  const d = typeof date === "string" ? new Date(date) : date;
  if (Number.isNaN(d?.getTime?.())) return "-";
  return (
    d.toLocaleDateString() +
    " " +
    d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  );
}

/* -------------------------------- Columns -------------------------------- */

const buildColumns = (): TableColumn[] => [
  {
    key: "select",
    label: "",
    sortable: false,
    width: 48,
    minWidth: 48,
    render: (user, value, helpers) => (
      <input
        type="checkbox"
        checked={Boolean(value)}
        onChange={(e) => helpers.onSelect?.(user.user_id, e.target.checked)}
        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        aria-label={`Select ${user.email}`}
      />
    ),
  },
  { key: "email", label: "Email", sortable: true, width: 260, minWidth: 200 },
  {
    key: "full_name",
    label: "Full Name",
    sortable: true,
    width: 220,
    minWidth: 160,
  },
  {
    key: "role",
    label: "Role",
    sortable: true,
    width: 120,
    minWidth: 110,
    render: (_user, value) => (
      <span
        className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleColor(
          String(value ?? "")
        )}`}
      >
        {String(value ?? "").replace("_", " ").toUpperCase() || "-"}
      </span>
    ),
  },
  {
    key: "is_active",
    label: "Status",
    sortable: true,
    width: 110,
    minWidth: 100,
    render: (_user, value) => (
      <span
        className={`px-2 py-1 rounded-full text-xs font-medium ${
          value ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
        }`}
      >
        {value ? "Active" : "Inactive"}
      </span>
    ),
  },
  {
    key: "is_verified",
    label: "Verified",
    sortable: true,
    width: 110,
    minWidth: 100,
    render: (_user, value) => (
      <span
        className={`px-2 py-1 rounded-full text-xs font-medium ${
          value ? "bg-blue-100 text-blue-800" : "bg-yellow-100 text-yellow-800"
        }`}
      >
        {value ? "Yes" : "No"}
      </span>
    ),
  },
  {
    key: "last_login_at",
    label: "Last Login",
    sortable: true,
    width: 170,
    minWidth: 150,
    render: (_user, value) => formatDate(value),
  },
  {
    key: "created_at",
    label: "Created",
    sortable: true,
    width: 170,
    minWidth: 150,
    render: (_user, value) => formatDate(value),
  },
  {
    key: "actions",
    label: "Actions",
    sortable: false,
    width: 160,
    minWidth: 140,
    render: (user, _value, helpers) => (
      <div className="flex items-center gap-2">
        <Button
          onClick={() => helpers.onEdit?.(user)}
          className="text-blue-600 hover:text-blue-800 text-sm"
          aria-label={`Edit ${user.email}`}
          type="button"
        >
          Edit
        </Button>
        <Button
          onClick={() => helpers.onToggleStatus?.(user)}
          className={`text-sm ${
            user.is_active
              ? "text-red-600 hover:text-red-800"
              : "text-green-600 hover:text-green-800"
          }`}
          aria-label={`${user.is_active ? "Deactivate" : "Activate"} ${
            user.email
          }`}
          type="button"
        >
          {user.is_active ? "Deactivate" : "Activate"}
        </Button>
      </div>
    ),
  },
];

/* -------------------------------- Row Cell -------------------------------- */

export interface RowProps {
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
  const {
    users,
    selectedUsers,
    onSelectionChange,
    onEditUser,
    onToggleStatus,
    columns,
  } = data;
  const user = users[index];

  // Skeleton row (for overscan/loading placeholders)
  if (!user) {
    return (
      <div
        style={style}
        className="flex items-center px-4 py-2 border-b border-gray-200"
      >
        <div className="animate-pulse bg-gray-200 h-4 w-full rounded" />
      </div>
    );
  }

  const isSelected = selectedUsers.includes(user.user_id);

  return (
    <div
      style={style}
      className={`flex items-center px-4 py-2 border-b border-gray-200 hover:bg-gray-50 ${
        isSelected ? "bg-blue-50" : ""
      }`}
      role="row"
      aria-selected={isSelected}
    >
      {columns.map((column) => {
        const value =
          column.key === "select"
            ? isSelected
            : column.key === "actions"
            ? null
            : (user[column.key as keyof User] as any);

        return (
          <div
            key={String(column.key)}
            style={{
              width: column.width,
              minWidth: column.minWidth ?? column.width,
            }}
            className="flex-shrink-0 px-2 text-sm text-gray-900 truncate md:text-base lg:text-lg"
            role="cell"
            title={
              typeof value === "string"
                ? value
                : column.key === "actions"
                ? "Actions"
                : undefined
            }
          >
            {column.render
              ? column.render(user, value, {
                  onSelect: onSelectionChange,
                  onEdit: onEditUser,
                  onToggleStatus,
                })
              : value?.toString() ?? "-"}
          </div>
        );
      })}
    </div>
  );
};

/* ----------------------------- Main Component ---------------------------- */

export function VirtualizedUserTable({
  selectedUsers,
  onSelectionChange,
  onUserUpdated,
  className = "",
  height = 600, // fallback height if AutoSizer can't measure
  itemHeight = 60,
  overscan = 6,
}: VirtualizedUserTableProps) {
  const { hasRole } = useRole(); // reserved for future column gating
  const columns = useMemo(() => buildColumns(), []);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  const [filters, setFilters] = useState<UserListFilter>({});
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    limit: 100, // large page for virtual scroll
    sort_by: "created_at" as keyof User,
    sort_order: "desc",
  });

  const [totalUsers, setTotalUsers] = useState(0);
  const [hasNextPage, setHasNextPage] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  const listRef = useRef<List>(null);

  const statusRegionId = useId();

  // Stable row data for react-window
  const rowData = useMemo(
    () => ({
      users,
      selectedUsers,
      onSelectionChange: (userId: string, selected: boolean) => {
        if (selected) {
          if (!selectedUsers.includes(userId)) {
            onSelectionChange([...selectedUsers, userId]);
          }
        } else {
          if (selectedUsers.includes(userId)) {
            onSelectionChange(selectedUsers.filter((id) => id !== userId));
          }
        }
      },
      onEditUser: setEditingUser,
      onToggleStatus: handleToggleUserStatus,
      columns,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [users, selectedUsers, onSelectionChange, columns]
  );

  /* ------------------------------ Data Loader ----------------------------- */

  const loadUsers = useCallback(
    async (append = false) => {
      try {
        if (!append) setLoading(true);
        else setIsLoadingMore(true);

        setError(null);

        // Cancel inflight
        abortRef.current?.abort();
        const controller = new AbortController();
        abortRef.current = controller;

        // Try cache (only for first-page fetches)
        if (!append) {
          const cached = await UserListCache.get(
            filters,
            pagination.page,
            pagination.limit,
            pagination.sort_by,
            pagination.sort_order
          );
          if (cached?.data) {
            setUsers(cached.data);
            setTotalUsers(cached.pagination.total);
            setHasNextPage(cached.pagination.has_next);
            return;
          }
        }

        // Build query
        const params = new URLSearchParams();
        params.set("page", String(pagination.page));
        params.set("limit", String(pagination.limit));
        params.set("sort_by", String(pagination.sort_by ?? "created_at"));
        params.set("sort_order", String(pagination.sort_order ?? "desc"));
        Object.entries(filters).forEach(([key, value]) => {
          if (value === undefined || value === null || value === "") return;
          params.append(
            key,
            value instanceof Date ? value.toISOString() : String(value)
          );
        });

        const response = await fetch(`/api/admin/users?${params.toString()}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Failed to load users: ${response.statusText}`);
        }

        const payload: AdminApiResponse<PaginatedResponse<User>> =
          await response.json();
        if (!payload?.success || !payload.data) {
          throw new Error(payload?.error?.message || "Failed to load users");
        }

        // Cache store
        UserListCache.set(
          filters,
          pagination.page,
          pagination.limit,
          payload.data,
          pagination.sort_by,
          pagination.sort_order
        );

        // Merge / replace rows
        const newRows = payload.data.data ?? [];
        setUsers((prev) => (append ? [...prev, ...newRows] : newRows));
        setTotalUsers(payload.data.pagination.total ?? 0);
        setHasNextPage(Boolean(payload.data.pagination.has_next));
      } catch (err: any) {
        if (err?.name !== "AbortError") {
          setError(err instanceof Error ? err.message : "Failed to load users");
        }
      } finally {
        setLoading(false);
        setIsLoadingMore(false);
      }
    },
    [filters, pagination]
  );

  const loadMoreUsers = useCallback(async () => {
    if (isLoadingMore || !hasNextPage) return;
    // move page forward, then fetch append
    setPagination((prev) => ({ ...prev, page: prev.page + 1 }));
    await loadUsers(true);
  }, [isLoadingMore, hasNextPage, loadUsers]);

  const handleScroll = useCallback(
    (p: ListOnScrollProps) => {
      if (p.scrollUpdateWasRequested) return;
      const totalHeight = users.length * itemHeight;
      const threshold = totalHeight - itemHeight * 5; // ~5 rows from bottom
      if (p.scrollOffset > threshold && hasNextPage && !isLoadingMore) {
        loadMoreUsers();
      }
    },
    [users.length, itemHeight, hasNextPage, isLoadingMore, loadMoreUsers]
  );

  // (Re)load on initial mount + on filter/sort/page changes
  useEffect(() => {
    loadUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, pagination.page, pagination.limit, pagination.sort_by, pagination.sort_order]);

  // Reset page when filters change
  const updateFilters = useCallback((newFilters: UserListFilter) => {
    setUsers([]);
    setPagination((p) => ({ ...p, page: 1 }));
    setFilters(newFilters);
  }, []);

  // Sorting
  const handleSort = (column: keyof User) => {
    setUsers([]);
    setPagination((prev) => ({
      ...prev,
      sort_by: column,
      sort_order:
        prev.sort_by === column && prev.sort_order === "asc" ? "desc" : "asc",
      page: 1,
    }));
  };

  // Select all visible
  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      const ids = users.map((u) => u.user_id);
      onSelectionChange(Array.from(new Set([...selectedUsers, ...ids])));
    } else {
      const visible = new Set(users.map((u) => u.user_id));
      onSelectionChange(selectedUsers.filter((id) => !visible.has(id)));
    }
  };

  // Toggle active/inactive
  async function handleToggleUserStatus(user: User) {
    try {
      const res = await fetch(`/api/admin/users/${user.user_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !user.is_active }),
      });
      if (!res.ok) throw new Error("Failed to update user status");

      // Invalidate caches + refresh
      AdminCacheManager.invalidateUserCaches(user.user_id, user.email);
      UserListCache.invalidateAll();

      setUsers([]);
      setPagination((p) => ({ ...p, page: 1 }));
      await loadUsers();
      onUserUpdated();
    } catch (err: any) {
      setError(
        err instanceof Error ? err.message : "Failed to update user status"
      );
    }
  }

  const handleUserUpdated = () => {
    setEditingUser(null);
    UserListCache.invalidateAll();
    AdminCacheManager.clearAll();
    setUsers([]);
    setPagination((p) => ({ ...p, page: 1 }));
    loadUsers();
    onUserUpdated();
  };

  /* ------------------------------- Renderers ------------------------------ */

  if (loading && users.length === 0) {
    return (
      <div className={`bg-white shadow rounded-lg ${className}`}>
        <div className="p-6 sm:p-4 md:p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4" />
            <div className="space-y-3">
              {Array.from({ length: 7 }).map((_, i) => (
                <div key={i} className="h-4 bg-gray-200 rounded" />
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
            <Button
              onClick={() => loadUsers()}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              type="button"
            >
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white shadow rounded-lg ${className}`}>
      {/* Screen Reader status */}
      <div id={statusRegionId} role="status" aria-live="polite" className="sr-only">
        Loaded {users.length} of {totalUsers} users.
      </div>

      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Users ({totalUsers.toLocaleString()})
            </h3>
            <p className="text-sm text-gray-500 md:text-base lg:text-lg">
              Showing {users.length.toLocaleString()} of{" "}
              {totalUsers.toLocaleString()} users
            </p>
          </div>

          <div className="flex items-center gap-2">
            <label className="flex items-center text-sm text-gray-600 md:text-base lg:text-lg">
              <input
                type="checkbox"
                aria-label="Select all visible rows"
                checked={
                  users.length > 0 &&
                  users.every((u) => selectedUsers.includes(u.user_id))
                }
                onChange={(e) => handleSelectAll(e.target.checked)}
                className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              Select all
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
      <div
        className="flex items-center px-4 py-3 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500 uppercase tracking-wider sm:text-sm md:text-base"
        role="row"
      >
        {columns.map((column) => (
          <div
            key={String(column.key)}
            style={{
              width: column.width,
              minWidth: column.minWidth ?? column.width,
            }}
            className="flex-shrink-0 px-2"
            role="columnheader"
          >
            {column.sortable ? (
              <Button
                onClick={() => handleSort(column.key as keyof User)}
                className="flex items-center gap-1 hover:text-gray-700"
                type="button"
                aria-label={`Sort by ${column.label}`}
              >
                <span>{column.label}</span>
                {pagination.sort_by === column.key && (
                  <span className="text-blue-600">
                    {pagination.sort_order === "asc" ? "↑" : "↓"}
                  </span>
                )}
              </Button>
            ) : (
              <span>{column.label}</span>
            )}
          </div>
        ))}
      </div>

      {/* Virtual List (AutoSizer for width/height when possible) */}
      <div style={{ height }}>
        <AutoSizer disableWidth>
          {({ height: autoH }) => (
            <List
              ref={listRef}
              height={autoH || height}
              width={"100%"}
              itemCount={users.length + (isLoadingMore ? 3 : 0)}
              itemSize={itemHeight}
              itemKey={(index) => users[index]?.user_id ?? `loading-${index}`}
              itemData={rowData}
              overscanCount={overscan}
              onScroll={handleScroll}
            >
              {Row}
            </List>
          )}
        </AutoSizer>
      </div>

      {/* Footer Status */}
      {isLoadingMore && (
        <div className="px-6 py-4 border-t border-gray-200 text-center">
          <div className="animate-pulse text-sm text-gray-500 md:text-base lg:text-lg">
            Loading more users...
          </div>
        </div>
      )}

      {!isLoadingMore && !hasNextPage && users.length > 0 && (
        <div className="px-6 py-4 border-t border-gray-200 text-center text-sm text-gray-500 md:text-base lg:text-lg">
          End of results
        </div>
      )}

      {/* Edit Modal (lightweight inline) */}
      {editingUser && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          role="dialog"
          aria-modal="true"
          aria-label="Edit user"
        >
          <div className="bg-white rounded-lg p-6 w-full max-w-md sm:p-4 md:p-6">
            <h3 className="text-lg font-medium mb-4">Edit User</h3>
            <p className="text-sm text-gray-600 mb-4 md:text-base lg:text-lg">
              Editing: {editingUser.email}
            </p>
            <div className="flex justify-end gap-3">
              <Button
                onClick={() => setEditingUser(null)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
                type="button"
              >
                Cancel
              </Button>
              <Button
                onClick={handleUserUpdated}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                aria-label="Save changes"
                type="button"
              >
                Save
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
