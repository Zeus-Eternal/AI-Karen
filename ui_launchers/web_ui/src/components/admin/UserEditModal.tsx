/**
 * User Edit Modal Component
 * 
 * Provides a modal interface for editing user profiles, status changes,
 * and role management with appropriate permission checks.
 * 
 * Requirements: 4.4, 4.5, 7.4
 */
'use client';
import React, { useState, useEffect } from 'react';
import { useRole } from '@/hooks/useRole';
import { useAuth } from '@/contexts/AuthContext';
import type { User, UpdateUserRequest, AdminApiResponse } from '@/types/admin';
interface UserEditModalProps {
  user: User;
  onClose: () => void;
  onUserUpdated: () => void;
}
interface FormData {
  full_name: string;
  role: 'super_admin' | 'admin' | 'user';
  is_active: boolean;
  is_verified: boolean;
  two_factor_enabled: boolean;
}
interface FormErrors {
  full_name?: string;
  role?: string;
  general?: string;
}
export function UserEditModal({ user, onClose, onUserUpdated }: UserEditModalProps) {
  const { hasRole } = useRole();
  const { user: currentUser } = useAuth();
  const [formData, setFormData] = useState<FormData>({
    full_name: user.full_name || '',
    role: user.role,
    is_active: user.is_active,
    is_verified: user.is_verified,
    two_factor_enabled: user.two_factor_enabled
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [showPasswordReset, setShowPasswordReset] = useState(false);
  // Check if current user can edit this user
  const canEdit = () => {
    // Users cannot edit themselves through this interface
    if (currentUser?.userId === user.user_id) return false;
    // Super admins can edit anyone except other super admins (unless they are super admin themselves)
    if (hasRole('super_admin')) return true;
    // Regular admins can only edit regular users
    if (hasRole('admin')) {
      return user.role === 'user';
    }
    return false;
  };
  const canChangeRole = () => {
    // Only super admins can change roles
    return hasRole('super_admin') && user.role !== 'super_admin';
  };
  const handleInputChange = (field: keyof FormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear field-specific errors when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    // Full name validation
    if (!formData.full_name.trim()) {
      newErrors.full_name = 'Full name is required';
    } else if (formData.full_name.trim().length < 2) {
      newErrors.full_name = 'Full name must be at least 2 characters';
    }
    // Role validation
    if (formData.role !== user.role && !canChangeRole()) {
      newErrors.role = 'You do not have permission to change user roles';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) {
      return;
    }
    setLoading(true);
    setErrors({});
    try {
      const updateData: UpdateUserRequest = {
        full_name: formData.full_name.trim(),
        is_active: formData.is_active,
        is_verified: formData.is_verified,
        two_factor_enabled: formData.two_factor_enabled
      };
      // Only include role if it changed and user has permission
      if (formData.role !== user.role && canChangeRole()) {
        updateData.role = formData.role;
      }
      const response = await fetch(`/api/admin/users/${user.user_id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });
      const data: AdminApiResponse<{ user: User }> = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.error?.message || 'Failed to update user');
      }
      // Success
      onUserUpdated();
      onClose();
    } catch (err) {
      if (err instanceof Error) {
        if (err.message.includes('INSUFFICIENT_PERMISSIONS')) {
          setErrors({ general: 'You do not have permission to perform this action' });
        } else if (err.message.includes('CANNOT_MODIFY_SELF')) {
          setErrors({ general: 'You cannot modify your own account through this interface' });
        } else {
          setErrors({ general: err.message });
        }
      } else {
        setErrors({ general: 'An unexpected error occurred. Please try again.' });
      }
    } finally {
      setLoading(false);
    }
  };
  const handlePasswordReset = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/admin/users/${user.user_id}/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const data: AdminApiResponse<{ reset_sent: boolean }> = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.error?.message || 'Failed to send password reset');
      }
      alert('Password reset email sent successfully!');
      setShowPasswordReset(false);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to send password reset');
    } finally {
      setLoading(false);
    }
  };
  if (!canEdit()) {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white sm:w-auto md:w-full">
          <div className="mt-3 text-center">
            <h3 className="text-lg font-medium text-gray-900">Access Denied</h3>
            <p className="text-sm text-gray-500 mt-2 md:text-base lg:text-lg">
              You do not have permission to edit this user.
            </p>
            <button
              onClick={onClose}
              className="mt-4 px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
             aria-label="Button">
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white sm:w-auto md:w-full">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Edit User</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
           aria-label="Button">
            <svg className="h-6 w-6 sm:w-auto md:w-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* General Error */}
          {errors.general && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-md sm:p-4 md:p-6">
              <div className="flex">
                <svg className="h-5 w-5 text-red-400 sm:w-auto md:w-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="ml-3 text-sm text-red-700 md:text-base lg:text-lg">{errors.general}</p>
              </div>
            </div>
          )}
          {/* User Info Display */}
          <div className="bg-gray-50 p-4 rounded-md sm:p-4 md:p-6">
            <h4 className="text-sm font-medium text-gray-900 mb-2 md:text-base lg:text-lg">User Information</h4>
            <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
              <div>
                <span className="text-gray-500">Email:</span>
                <span className="ml-2 font-medium">{user.email}</span>
              </div>
              <div>
                <span className="text-gray-500">User ID:</span>
                <span className="ml-2 font-mono text-xs sm:text-sm md:text-base">{user.user_id}</span>
              </div>
              <div>
                <span className="text-gray-500">Created:</span>
                <span className="ml-2">{new Date(user.created_at).toLocaleDateString()}</span>
              </div>
              <div>
                <span className="text-gray-500">Last Login:</span>
                <span className="ml-2">{user.last_login_at ? new Date(user.last_login_at).toLocaleDateString() : 'Never'}</span>
              </div>
            </div>
          </div>
          {/* Full Name Field */}
          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">
              Full Name *
            </label>
            <input
              id="full_name"
              type="text"
              value={formData.full_name}
              onChange={(e) = aria-label="Input"> handleInputChange('full_name', e.target.value)}
              className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.full_name ? 'border-red-300' : 'border-gray-300'
              }`}
              disabled={loading}
            />
            {errors.full_name && (
              <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">{errors.full_name}</p>
            )}
          </div>
          {/* Role Field */}
          {canChangeRole() && (
            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">
                Role
              </label>
              <select
                id="role"
                value={formData.role}
                onChange={(e) = aria-label="Select option"> handleInputChange('role', e.target.value)}
                className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.role ? 'border-red-300' : 'border-gray-300'
                }`}
                disabled={loading}
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
              {errors.role && (
                <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">{errors.role}</p>
              )}
            </div>
          )}
          {/* Status Toggles */}
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                id="is_active"
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) = aria-label="Input"> handleInputChange('is_active', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded sm:w-auto md:w-full"
                disabled={loading}
              />
              <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900 md:text-base lg:text-lg">
                Account Active
              </label>
            </div>
            <div className="flex items-center">
              <input
                id="is_verified"
                type="checkbox"
                checked={formData.is_verified}
                onChange={(e) = aria-label="Input"> handleInputChange('is_verified', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded sm:w-auto md:w-full"
                disabled={loading}
              />
              <label htmlFor="is_verified" className="ml-2 block text-sm text-gray-900 md:text-base lg:text-lg">
                Email Verified
              </label>
            </div>
            <div className="flex items-center">
              <input
                id="two_factor_enabled"
                type="checkbox"
                checked={formData.two_factor_enabled}
                onChange={(e) = aria-label="Input"> handleInputChange('two_factor_enabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded sm:w-auto md:w-full"
                disabled={loading}
              />
              <label htmlFor="two_factor_enabled" className="ml-2 block text-sm text-gray-900 md:text-base lg:text-lg">
                Two-Factor Authentication Enabled
              </label>
            </div>
          </div>
          {/* Password Reset Section */}
          <div className="border-t border-gray-200 pt-4">
            <h4 className="text-sm font-medium text-gray-900 mb-2 md:text-base lg:text-lg">Password Management</h4>
            {!showPasswordReset ? (
              <button
                type="button"
                onClick={() = aria-label="Button"> setShowPasswordReset(true)}
                className="text-sm text-blue-600 hover:text-blue-800 md:text-base lg:text-lg"
              >
                Send Password Reset Email
              </button>
            ) : (
              <div className="bg-yellow-50 p-3 rounded-md sm:p-4 md:p-6">
                <p className="text-sm text-yellow-800 mb-2 md:text-base lg:text-lg">
                  This will send a password reset email to {user.email}. The user will be able to set a new password using the link in the email.
                </p>
                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={handlePasswordReset}
                    disabled={loading}
                    className="text-sm bg-yellow-600 text-white px-3 py-1 rounded hover:bg-yellow-700 disabled:opacity-50 md:text-base lg:text-lg"
                   aria-label="Button">
                    Send Reset Email
                  </button>
                  <button
                    type="button"
                    onClick={() = aria-label="Button"> setShowPasswordReset(false)}
                    className="text-sm text-gray-600 hover:text-gray-800 md:text-base lg:text-lg"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
             aria-label="Button">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
             aria-label="Submit form">
              {loading ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white sm:w-auto md:w-full" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Updating...
                </div>
              ) : (
                'Update User'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
