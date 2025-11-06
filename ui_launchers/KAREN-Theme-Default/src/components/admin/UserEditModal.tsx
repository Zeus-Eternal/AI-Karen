/**
 * User Edit Modal Component (Production Hardened)
 *
 * Provides a modal interface for editing user profiles, status changes,
 * role management (RBAC enforced), and password reset dispatch.
 *
 * Requirements: 4.4 (RBAC), 4.5 (Admin actions), 7.4 (Observability/UX polish)
 */

"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRole } from "@/hooks/useRole";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import type { User, UpdateUserRequest, AdminApiResponse } from "@/types/admin";

export interface UserEditModalProps {
  user: User;
  onClose: () => void;
  onUserUpdated: () => void;
}

export type Role = "super_admin" | "admin" | "user";

export interface FormData {
  full_name: string;
  role: Role;
  is_active: boolean;
  is_verified: boolean;
  two_factor_enabled: boolean;
}

export interface FormErrors {
  full_name?: string;
  role?: string;
  general?: string;
}

export function UserEditModal({ user, onClose, onUserUpdated }: UserEditModalProps) {
  const { hasRole } = useRole();
  const { user: currentUser } = useAuth();

  const [formData, setFormData] = useState<FormData>({
    full_name: user.full_name || "",
    role: user.role as Role,
    is_active: user.is_active,
    is_verified: user.is_verified,
    two_factor_enabled: user.two_factor_enabled,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [showPasswordReset, setShowPasswordReset] = useState(false);

  const overlayRef = useRef<HTMLDivElement | null>(null);

  /** RBAC checks */
  const isSelf = currentUser?.userId === user.user_id;

  const canEdit = useMemo(() => {
    // Users cannot edit themselves through this interface
    if (isSelf) return false;

    // Super admins can edit anyone
    if (hasRole("super_admin")) return true;

    // Admins can only edit regular users (not admins or super_admins)
    if (hasRole("admin")) return user.role === "user";

    return false;
  }, [hasRole, isSelf, user.role]);

  const canChangeRole = useMemo(() => {
    // Only super admins can change roles; cannot demote another super_admin unless you are super_admin
    if (!hasRole("super_admin")) return false;
    // Changing the role of a super_admin is allowed here only if current user is super_admin,
    // but we’ll forbid changing a super_admin into something else by default for safety.
    return user.role !== "super_admin";
  }, [hasRole, user.role]);

  const handleInputChange = (field: keyof FormData, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value as never }));
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Full name validation
    const name = formData.full_name.trim();
    if (!name) {
      newErrors.full_name = "Full name is required";
    } else if (name.length < 2) {
      newErrors.full_name = "Full name must be at least 2 characters";
    }

    // Role validation (if changed)
    if (formData.role !== (user.role as Role) && !canChangeRole) {
      newErrors.role = "You do not have permission to change user roles";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setErrors({});
    try {
      const updateData: UpdateUserRequest = {
        full_name: formData.full_name.trim(),
        is_active: formData.is_active,
        is_verified: formData.is_verified,
        two_factor_enabled: formData.two_factor_enabled,
      };

      // Only include role if it changed and user has permission
      if (formData.role !== (user.role as Role) && canChangeRole) {
        updateData.role = formData.role;
      }

      const response = await fetch(`/api/admin/users/${user.user_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updateData),
      });

      const data: AdminApiResponse<{ user: User }> = await response.json();

      if (!response.ok || !data?.success) {
        throw new Error(data?.error?.message || "Failed to update user");
      }

      onUserUpdated();
      onClose();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to update user";
      if (msg.includes("INSUFFICIENT_PERMISSIONS")) {
        setErrors({ general: "You do not have permission to perform this action" });
      } else if (msg.includes("CANNOT_MODIFY_SELF")) {
        setErrors({ general: "You cannot modify your own account through this interface" });
      } else {
        setErrors({ general: msg });
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordReset = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/admin/users/${user.user_id}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      const data: AdminApiResponse<{ reset_sent: boolean }> = await response.json();

      if (!response.ok || !data?.success) {
        throw new Error(data?.error?.message || "Failed to send password reset");
      }

      alert("Password reset email sent successfully!");
      setShowPasswordReset(false);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to send password reset");
    } finally {
      setLoading(false);
    }
  };

  /** Close on ESC */
  const onKeyDown = useCallback(
    (ev: KeyboardEvent) => {
      if (ev.key === "Escape") onClose();
    },
    [onClose]
  );

  useEffect(() => {
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onKeyDown]);

  /** Click outside to close */
  const onOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  };

  if (!canEdit) {
    return (
      <div
        ref={overlayRef}
        onClick={onOverlayClick}
        className="fixed inset-0 bg-gray-600/50 overflow-y-auto h-full w-full z-50"
        role="dialog"
        aria-modal="true"
      >
        <div className="relative top-20 mx-auto p-5 w-96 shadow-lg rounded-md bg-white border">
          <div className="mt-3 text-center">
            <h3 className="text-lg font-medium text-gray-900">Access Denied</h3>
            <p className="text-sm text-gray-600 mt-2">
              You do not have permission to edit this user.
            </p>
            <Button
              onClick={onClose}
              className="mt-4"
              aria-label="Close access denied modal"
            >
              Close
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={overlayRef}
      onClick={onOverlayClick}
      className="fixed inset-0 bg-gray-600/50 overflow-y-auto h-full w-full z-50"
      role="dialog"
      aria-modal="true"
      aria-label="Edit user modal"
    >
      <div className="relative top-20 mx-auto p-5 w-full max-w-2xl shadow-lg rounded-md bg-white border">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Edit User</h3>
          <Button
            onClick={onClose}
            variant="ghost"
            className="text-gray-500 hover:text-gray-700"
            aria-label="Close"
          >
            ✕
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* General Error */}
          {errors.general && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="flex">
                <svg className="h-5 w-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="ml-3 text-sm text-red-700">{errors.general}</p>
              </div>
            </div>
          )}

          {/* User Info Display */}
          <div className="bg-gray-50 p-4 rounded-md">
            <h4 className="text-sm font-medium text-gray-900 mb-2">User Information</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Email:</span>
                <span className="ml-2 font-medium break-all">{user.email}</span>
              </div>
              <div>
                <span className="text-gray-500">User ID:</span>
                <span className="ml-2 font-mono text-xs sm:text-sm break-all">{user.user_id}</span>
              </div>
              <div>
                <span className="text-gray-500">Created:</span>
                <span className="ml-2">
                  {user.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Last Login:</span>
                <span className="ml-2">
                  {user.last_login_at ? new Date(user.last_login_at).toLocaleString() : "Never"}
                </span>
              </div>
            </div>
          </div>

          {/* Full Name Field */}
          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-1">
              Full Name *
            </label>
            <input
              id="full_name"
              type="text"
              value={formData.full_name}
              onChange={(e) => handleInputChange("full_name", e.target.value)}
              className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.full_name ? "border-red-300" : "border-gray-300"
              }`}
              disabled={loading}
              aria-invalid={Boolean(errors.full_name)}
              aria-describedby={errors.full_name ? "full_name_error" : undefined}
            />
            {errors.full_name && (
              <p id="full_name_error" className="mt-1 text-sm text-red-600">
                {errors.full_name}
              </p>
            )}
          </div>

          {/* Role Field (only if allowed) */}
          {canChangeRole && (
            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <select
                id="role"
                value={formData.role}
                onChange={(e) => handleInputChange("role", e.target.value as Role)}
                className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.role ? "border-red-300" : "border-gray-300"
                }`}
                disabled={loading}
                aria-invalid={Boolean(errors.role)}
                aria-describedby={errors.role ? "role_error" : undefined}
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
              {errors.role && (
                <p id="role_error" className="mt-1 text-sm text-red-600">
                  {errors.role}
                </p>
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
                onChange={(e) => handleInputChange("is_active", e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={loading}
              />
              <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                Active
              </label>
            </div>
            <div className="flex items-center">
              <input
                id="is_verified"
                type="checkbox"
                checked={formData.is_verified}
                onChange={(e) => handleInputChange("is_verified", e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={loading}
              />
              <label htmlFor="is_verified" className="ml-2 block text-sm text-gray-900">
                Email Verified
              </label>
            </div>
            <div className="flex items-center">
              <input
                id="two_factor_enabled"
                type="checkbox"
                checked={formData.two_factor_enabled}
                onChange={(e) => handleInputChange("two_factor_enabled", e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={loading}
              />
              <label htmlFor="two_factor_enabled" className="ml-2 block text-sm text-gray-900">
                Two-Factor Authentication Enabled
              </label>
            </div>
          </div>

          {/* Password Reset Section */}
          <div className="border-t border-gray-200 pt-4">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Password Management</h4>
            {!showPasswordReset ? (
              <Button
                type="button"
                onClick={() => setShowPasswordReset(true)}
                className="text-blue-600 hover:text-blue-800 p-0 h-auto"
                variant="link"
              >
                Send password reset email…
              </Button>
            ) : (
              <div className="bg-yellow-50 p-3 rounded-md">
                <p className="text-sm text-yellow-800 mb-2">
                  This will send a password reset email to <b>{user.email}</b>. The user will be able to set a new password using the link in the email.
                </p>
                <div className="flex space-x-2">
                  <Button
                    type="button"
                    onClick={handlePasswordReset}
                    disabled={loading}
                    className="bg-yellow-600 text-white hover:bg-yellow-700"
                    aria-label="Send password reset email"
                  >
                    {loading ? "Sending…" : "Send Reset Email"}
                  </Button>
                  <Button
                    type="button"
                    onClick={() => setShowPasswordReset(false)}
                    variant="ghost"
                    aria-label="Cancel password reset"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <Button
              type="button"
              onClick={onClose}
              disabled={loading}
              variant="outline"
              aria-label="Cancel and close"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              aria-label="Submit user update"
            >
              {loading ? (
                <span className="inline-flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Updating…
                </span>
              ) : (
                "Update User"
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
