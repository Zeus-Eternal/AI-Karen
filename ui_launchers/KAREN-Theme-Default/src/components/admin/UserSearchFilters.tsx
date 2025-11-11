// ui_launchers/KAREN-Theme-Default/src/components/admin/UserSearchFilters.tsx
/**
 * User Search Filters Component
 *
 * Provides comprehensive search and filtering capabilities for the user management table.
 * Includes text search, role filters, status filters, and date range filters.
 *
 * Requirements: 4.6, 7.3
 */

"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { UserListFilter } from "@/types/admin";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { RefreshCcw, SlidersHorizontal, Search, X } from "lucide-react";

export interface UserSearchFiltersProps {
  filters: UserListFilter;
  onFiltersChange: (filters: UserListFilter) => void;
  onRefresh: () => void;
  className?: string;
}

export function UserSearchFilters({
  filters,
  onFiltersChange,
  onRefresh,
  className = "",
}: UserSearchFiltersProps) {
  const [localFilters, setLocalFilters] = useState<UserListFilter>(filters);
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  // Keep local state in sync with external filters
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  // Debounce for text search to avoid spamming parent
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const debounce = useCallback((fn: () => void, delay = 350) => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(fn, delay);
  }, []);

  const handleFilterChange = useCallback(
    (key: keyof UserListFilter, value: unknown, opts?: { immediate?: boolean }) => {
      const next = { ...localFilters, [key]: value };
      setLocalFilters(next);
      if (opts?.immediate) onFiltersChange(next);
    },
    [localFilters, onFiltersChange]
  );

  const applyFilters = useCallback(() => {
    onFiltersChange(localFilters);
  }, [localFilters, onFiltersChange]);

  const clearFilters = useCallback(() => {
    const empty: UserListFilter = {};
    setLocalFilters(empty);
    onFiltersChange(empty);
  }, [onFiltersChange]);

  const hasActiveFilters = useMemo(() => {
    return Object.values(localFilters).some((v) => v !== undefined && v !== null && v !== "");
  }, [localFilters]);

  const formatDateForInput = (date?: Date) => {
    if (!date) return "";
    const d = typeof date === "string" ? new Date(date) : date;
    return new Date(d).toISOString().split("T")[0];
  };

  const parseDateFromInput = (str: string) => (str ? new Date(str) : undefined);

  // accessibility helpers
  const onKeyDownApply = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") applyFilters();
  };

  // derived counts for quick indicator
  const activeCount = useMemo(() => {
    return Object.entries(localFilters).reduce((acc, [k, v]) => {
      if (v === undefined || v === null || v === "") return acc;
      return acc + 1;
    }, 0);
  }, [localFilters]);

  return (
    <div className={`bg-gray-50 border-b border-gray-200 p-4 ${className}`}>
      {/* Basic Search Row */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-2">
        <div className="flex-1">
          <label htmlFor="search-users" className="sr-only">
            Search users
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-500" aria-hidden />
            </div>
            <Input
              id="search-users"
              placeholder="Search by email or name…"
              value={localFilters.search || ""}
              onChange={(e) => {
                const val = e.target.value;
                setLocalFilters((prev) => ({ ...prev, search: val || undefined }));
                // Debounced push upward for responsive UX
                debounce(() => onFiltersChange({ ...localFilters, search: val || undefined }));
              }}
              onKeyDown={onKeyDownApply}
              className="pl-9"
              aria-label="Search by email or name"
            />
          </div>
        </div>

        <div className="flex gap-2 justify-end">
          <Button
            onClick={applyFilters}
            aria-label="Apply filters"
            title="Apply filters"
          >
            Apply
          </Button>

          <Button
            variant="outline"
            onClick={() => setShowAdvanced((s) => !s)}
            aria-pressed={showAdvanced}
            aria-label="Toggle advanced filters"
            title="Toggle advanced filters"
          >
            <SlidersHorizontal className="h-4 w-4 mr-2" />
            {showAdvanced ? "Hide" : "Advanced"}
          </Button>

          <Button
            variant="outline"
            onClick={onRefresh}
            aria-label="Refresh"
            title="Refresh"
          >
            <RefreshCcw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Advanced Filters */}
      {showAdvanced && (
        <div className="border-t border-gray-200 pt-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            {/* Role */}
            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <Select
                value={localFilters.role || ""}
                onValueChange={(v) => handleFilterChange("role", v || undefined, { immediate: true })}
              >
                <SelectTrigger id="role" aria-label="Filter by role">
                  <SelectValue placeholder="All roles" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Roles</SelectItem>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="super_admin">Super Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Active */}
            <div>
              <label htmlFor="is_active" className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <Select
                value={
                  localFilters.is_active === undefined ? "" : String(Boolean(localFilters.is_active))
                }
                onValueChange={(v) =>
                  handleFilterChange(
                    "is_active",
                    v === "" ? undefined : v === "true",
                    { immediate: true }
                  )
                }
              >
                <SelectTrigger id="is_active" aria-label="Filter by active status">
                  <SelectValue placeholder="All status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Status</SelectItem>
                  <SelectItem value="true">Active</SelectItem>
                  <SelectItem value="false">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Verified */}
            <div>
              <label htmlFor="is_verified" className="block text-sm font-medium text-gray-700 mb-1">
                Verification
              </label>
              <Select
                value={
                  localFilters.is_verified === undefined ? "" : String(Boolean(localFilters.is_verified))
                }
                onValueChange={(v) =>
                  handleFilterChange(
                    "is_verified",
                    v === "" ? undefined : v === "true",
                    { immediate: true }
                  )
                }
              >
                <SelectTrigger id="is_verified" aria-label="Filter by verification">
                  <SelectValue placeholder="All verification" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Verification</SelectItem>
                  <SelectItem value="true">Verified</SelectItem>
                  <SelectItem value="false">Unverified</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Date Ranges */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div>
              <label htmlFor="created_after" className="block text-sm font-medium text-gray-700 mb-1">
                Created After
              </label>
              <Input
                id="created_after"
                type="date"
                value={formatDateForInput(localFilters.created_after as unknown)}
                onChange={(e) =>
                  handleFilterChange("created_after", parseDateFromInput(e.target.value))
                }
              />
            </div>
            <div>
              <label htmlFor="created_before" className="block text-sm font-medium text-gray-700 mb-1">
                Created Before
              </label>
              <Input
                id="created_before"
                type="date"
                value={formatDateForInput(localFilters.created_before as unknown)}
                onChange={(e) =>
                  handleFilterChange("created_before", parseDateFromInput(e.target.value))
                }
              />
            </div>
            <div>
              <label htmlFor="last_login_after" className="block text-sm font-medium text-gray-700 mb-1">
                Last Login After
              </label>
              <Input
                id="last_login_after"
                type="date"
                value={formatDateForInput(localFilters.last_login_after as unknown)}
                onChange={(e) =>
                  handleFilterChange("last_login_after", parseDateFromInput(e.target.value))
                }
              />
            </div>
            <div>
              <label htmlFor="last_login_before" className="block text-sm font-medium text-gray-700 mb-1">
                Last Login Before
              </label>
              <Input
                id="last_login_before"
                type="date"
                value={formatDateForInput(localFilters.last_login_before as unknown)}
                onChange={(e) =>
                  handleFilterChange("last_login_before", parseDateFromInput(e.target.value))
                }
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <Button onClick={applyFilters} aria-label="Apply filters">
                Apply
              </Button>
              {hasActiveFilters && (
                <Button variant="outline" onClick={clearFilters} aria-label="Clear all filters">
                  Clear
                </Button>
              )}
            </div>

            {hasActiveFilters && (
              <div className="text-sm text-gray-600" aria-live="polite">
                {activeCount} filter{activeCount === 1 ? "" : "s"} active
              </div>
            )}
          </div>
        </div>
      )}

      {/* Quick Filter Chips */}
      {hasActiveFilters && (
        <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-200">
          {localFilters.search && (
            <Badge variant="secondary" className="px-3 py-1">
              Search: “{localFilters.search}”
              <Button
                variant="ghost"
                className="h-6 px-1 ml-2"
                onClick={() => handleFilterChange("search", undefined, { immediate: true })}
                aria-label="Remove search filter"
                title="Remove search filter"
              >
                <X className="h-4 w-4" />
              </Button>
            </Badge>
          )}
          {localFilters.role && (
            <Badge variant="secondary" className="px-3 py-1">
              Role: {String(localFilters.role).replace("_", " ")}
              <Button
                variant="ghost"
                className="h-6 px-1 ml-2"
                onClick={() => handleFilterChange("role", undefined, { immediate: true })}
                aria-label="Remove role filter"
                title="Remove role filter"
              >
                <X className="h-4 w-4" />
              </Button>
            </Badge>
          )}
          {localFilters.is_active !== undefined && (
            <Badge variant="secondary" className="px-3 py-1">
              Status: {localFilters.is_active ? "Active" : "Inactive"}
              <Button
                variant="ghost"
                className="h-6 px-1 ml-2"
                onClick={() => handleFilterChange("is_active", undefined, { immediate: true })}
                aria-label="Remove status filter"
                title="Remove status filter"
              >
                <X className="h-4 w-4" />
              </Button>
            </Badge>
          )}
          {localFilters.is_verified !== undefined && (
            <Badge variant="secondary" className="px-3 py-1">
              Verification: {localFilters.is_verified ? "Verified" : "Unverified"}
              <Button
                variant="ghost"
                className="h-6 px-1 ml-2"
                onClick={() => handleFilterChange("is_verified", undefined, { immediate: true })}
                aria-label="Remove verification filter"
                title="Remove verification filter"
              >
                <X className="h-4 w-4" />
              </Button>
            </Badge>
          )}
          {(localFilters.created_after || localFilters.created_before) && (
            <Badge variant="secondary" className="px-3 py-1">
              Created: {formatDateForInput(localFilters.created_after as unknown)} →{" "}
              {formatDateForInput(localFilters.created_before as unknown)}
              <Button
                variant="ghost"
                className="h-6 px-1 ml-2"
                onClick={() => {
                  handleFilterChange("created_after", undefined, { immediate: true });
                  handleFilterChange("created_before", undefined, { immediate: true });
                }}
                aria-label="Remove created date filters"
                title="Remove created date filters"
              >
                <X className="h-4 w-4" />
              </Button>
            </Badge>
          )}
          {(localFilters.last_login_after || localFilters.last_login_before) && (
            <Badge variant="secondary" className="px-3 py-1">
              Last Login: {formatDateForInput(localFilters.last_login_after as unknown)} →{" "}
              {formatDateForInput(localFilters.last_login_before as unknown)}
              <Button
                variant="ghost"
                className="h-6 px-1 ml-2"
                onClick={() => {
                  handleFilterChange("last_login_after", undefined, { immediate: true });
                  handleFilterChange("last_login_before", undefined, { immediate: true });
                }}
                aria-label="Remove last login date filters"
                title="Remove last login date filters"
              >
                <X className="h-4 w-4" />
              </Button>
            </Badge>
          )}
        </div>
      )}
    </div>
  );
}
