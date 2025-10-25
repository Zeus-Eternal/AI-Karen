/**
 * User Search Filters Component
 * 
 * Provides comprehensive search and filtering capabilities for the user management table.
 * Includes text search, role filters, status filters, and date range filters.
 * 
 * Requirements: 4.6, 7.3
 */

'use client';

import React, { useState, useEffect } from 'react';
import type { UserListFilter } from '@/types/admin';

interface UserSearchFiltersProps {
  filters: UserListFilter;
  onFiltersChange: (filters: UserListFilter) => void;
  onRefresh: () => void;
  className?: string;
}

export function UserSearchFilters({
  filters,
  onFiltersChange,
  onRefresh,
  className = ''
}: UserSearchFiltersProps) {
  const [localFilters, setLocalFilters] = useState<UserListFilter>(filters);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Update local filters when props change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleFilterChange = (key: keyof UserListFilter, value: any) => {
    const newFilters = { ...localFilters, [key]: value };
    setLocalFilters(newFilters);
  };

  const applyFilters = () => {
    onFiltersChange(localFilters);
  };

  const clearFilters = () => {
    const emptyFilters: UserListFilter = {};
    setLocalFilters(emptyFilters);
    onFiltersChange(emptyFilters);
  };

  const hasActiveFilters = () => {
    return Object.values(localFilters).some(value => 
      value !== undefined && value !== null && value !== ''
    );
  };

  const formatDateForInput = (date: Date | undefined) => {
    if (!date) return '';
    return date.toISOString().split('T')[0];
  };

  const parseDateFromInput = (dateString: string) => {
    return dateString ? new Date(dateString) : undefined;
  };

  return (
    <div className={`bg-gray-50 border-b border-gray-200 p-4 ${className}`}>
      {/* Basic Search */}
      <div className="flex flex-col sm:flex-row gap-4 mb-4">
        <div className="flex-1">
          <label htmlFor="search" className="sr-only">Search users</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              id="search"
              type="text"
              placeholder="Search by email or name..."
              value={localFilters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={applyFilters}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Search
          </button>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            {showAdvanced ? 'Hide' : 'Advanced'}
          </button>
          <button
            onClick={onRefresh}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Advanced Filters */}
      {showAdvanced && (
        <div className="border-t border-gray-200 pt-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            {/* Role Filter */}
            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <select
                id="role"
                value={localFilters.role || ''}
                onChange={(e) => handleFilterChange('role', e.target.value || undefined)}
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Roles</option>
                <option value="user">User</option>
                <option value="admin">Admin</option>
                <option value="super_admin">Super Admin</option>
              </select>
            </div>

            {/* Active Status Filter */}
            <div>
              <label htmlFor="is_active" className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                id="is_active"
                value={localFilters.is_active === undefined ? '' : localFilters.is_active.toString()}
                onChange={(e) => handleFilterChange('is_active', e.target.value === '' ? undefined : e.target.value === 'true')}
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Status</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>
            </div>

            {/* Verification Status Filter */}
            <div>
              <label htmlFor="is_verified" className="block text-sm font-medium text-gray-700 mb-1">
                Verification
              </label>
              <select
                id="is_verified"
                value={localFilters.is_verified === undefined ? '' : localFilters.is_verified.toString()}
                onChange={(e) => handleFilterChange('is_verified', e.target.value === '' ? undefined : e.target.value === 'true')}
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Verification</option>
                <option value="true">Verified</option>
                <option value="false">Unverified</option>
              </select>
            </div>
          </div>

          {/* Date Range Filters */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            {/* Created Date Range */}
            <div>
              <label htmlFor="created_after" className="block text-sm font-medium text-gray-700 mb-1">
                Created After
              </label>
              <input
                id="created_after"
                type="date"
                value={formatDateForInput(localFilters.created_after)}
                onChange={(e) => handleFilterChange('created_after', parseDateFromInput(e.target.value))}
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label htmlFor="created_before" className="block text-sm font-medium text-gray-700 mb-1">
                Created Before
              </label>
              <input
                id="created_before"
                type="date"
                value={formatDateForInput(localFilters.created_before)}
                onChange={(e) => handleFilterChange('created_before', parseDateFromInput(e.target.value))}
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Last Login Date Range */}
            <div>
              <label htmlFor="last_login_after" className="block text-sm font-medium text-gray-700 mb-1">
                Last Login After
              </label>
              <input
                id="last_login_after"
                type="date"
                value={formatDateForInput(localFilters.last_login_after)}
                onChange={(e) => handleFilterChange('last_login_after', parseDateFromInput(e.target.value))}
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label htmlFor="last_login_before" className="block text-sm font-medium text-gray-700 mb-1">
                Last Login Before
              </label>
              <input
                id="last_login_before"
                type="date"
                value={formatDateForInput(localFilters.last_login_before)}
                onChange={(e) => handleFilterChange('last_login_before', parseDateFromInput(e.target.value))}
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Filter Actions */}
          <div className="flex justify-between items-center">
            <div className="flex gap-2">
              <button
                onClick={applyFilters}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Apply Filters
              </button>
              {hasActiveFilters() && (
                <button
                  onClick={clearFilters}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Clear All
                </button>
              )}
            </div>

            {hasActiveFilters() && (
              <div className="text-sm text-gray-600">
                {Object.keys(localFilters).filter(key => {
                  const value = localFilters[key as keyof UserListFilter];
                  return value !== undefined && value !== null && value !== '';
                }).length} filter(s) active
              </div>
            )}
          </div>
        </div>
      )}

      {/* Quick Filter Chips */}
      {hasActiveFilters() && (
        <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-200">
          {localFilters.search && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Search: "{localFilters.search}"
              <button
                onClick={() => handleFilterChange('search', undefined)}
                className="ml-2 text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </span>
          )}
          {localFilters.role && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Role: {localFilters.role.replace('_', ' ')}
              <button
                onClick={() => handleFilterChange('role', undefined)}
                className="ml-2 text-green-600 hover:text-green-800"
              >
                ×
              </button>
            </span>
          )}
          {localFilters.is_active !== undefined && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
              Status: {localFilters.is_active ? 'Active' : 'Inactive'}
              <button
                onClick={() => handleFilterChange('is_active', undefined)}
                className="ml-2 text-yellow-600 hover:text-yellow-800"
              >
                ×
              </button>
            </span>
          )}
          {localFilters.is_verified !== undefined && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              Verification: {localFilters.is_verified ? 'Verified' : 'Unverified'}
              <button
                onClick={() => handleFilterChange('is_verified', undefined)}
                className="ml-2 text-purple-600 hover:text-purple-800"
              >
                ×
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  );
}