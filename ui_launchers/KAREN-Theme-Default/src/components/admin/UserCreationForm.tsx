/**
 * User Creation Form Component (Production-Grade)
 *
 * Provides a comprehensive form for creating new users with validation,
 * role assignment, and optional email invitation. Accessible, resilient,
 * and instrumented for admin flows.
 *
 * Requirements: 4.2 (Create Users), 4.3 (Role Assignment), 7.4 (Admin UX polish)
 */

"use client";

import React, { useId, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { useRole } from "@/hooks/useRole";
import { validateEmail } from "@/lib/auth/setup-validation";
import type { CreateUserRequest, AdminApiResponse, User } from "@/types/admin";

/* ----------------------------- Types & Shapes ---------------------------- */

export interface UserCreationFormProps {
  onUserCreated: () => void;
  className?: string;
}

export interface FormData {
  email: string;
  full_name: string;
  password: string;
  confirm_password: string;
  role: "admin" | "user";
  send_invitation: boolean;
  tenant_id: string;
}

export interface FormErrors {
  email?: string;
  full_name?: string;
  password?: string;
  confirm_password?: string;
  role?: string;
  tenant_id?: string;
  general?: string;
}

/* --------------------------------- Consts -------------------------------- */

const initialFormData: FormData = {
  email: "",
  full_name: "",
  password: "",
  confirm_password: "",
  role: "user",
  send_invitation: true,
  tenant_id: "default",
};

const PASSWORD_RULE = /(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}/;

/* --------------------------------- Utils --------------------------------- */

function normalizeEmail(v: string) {
  return v.trim().toLowerCase();
}

function safeTrim(v: string) {
  return (v ?? "").trim();
}

/* --------------------------------- View ---------------------------------- */

function UserCreationForm({
  onUserCreated,
  className = "",
}: UserCreationFormProps) {
  const { hasRole } = useRole();

  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const alertRegionId = useId();
  const emailHelpId = useId();
  const roleHelpId = useId();
  const inviteHelpId = useId();
  const passwordHelpId = useId();
  const tenantHelpId = useId();

  const abortRef = useRef<AbortController | null>(null);

  const canSelectAdmin = hasRole("super_admin");
  const roleOptions = useMemo(
    () => [
      { label: "User", value: "user" as const },
      ...(canSelectAdmin ? [{ label: "Admin", value: "admin" as const }] : []),
    ],
    [canSelectAdmin]
  );

  const handleInputChange = (
    field: keyof FormData,
    value: string | boolean
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
    if (field === "email") {
      setErrors((prev) => ({ ...prev, email: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const nextErrors: FormErrors = {};

    // Email
    const email = normalizeEmail(formData.email);
    if (!email) {
      nextErrors.email = "Email is required";
    } else if (!validateEmail(email)) {
      nextErrors.email = "Please enter a valid email address";
    }

    // Full name
    const fullName = safeTrim(formData.full_name);
    if (!fullName) {
      nextErrors.full_name = "Full name is required";
    } else if (fullName.length < 2) {
      nextErrors.full_name = "Full name must be at least 2 characters";
    }

    // Tenant
    const tenant = safeTrim(formData.tenant_id);
    if (!tenant) {
      nextErrors.tenant_id = "Tenant is required";
    }

    // Role
    if (formData.role === "admin" && !canSelectAdmin) {
      nextErrors.role = "Only super admins can create admin users";
    }

    // Password (only when NOT sending invitation)
    if (!formData.send_invitation) {
      const pw = formData.password ?? "";
      const cpw = formData.confirm_password ?? "";

      if (!pw) {
        nextErrors.password = "Password is required when not sending invitation";
      } else if (!PASSWORD_RULE.test(pw)) {
        nextErrors.password =
          "Password must be at least 8 chars and include uppercase, lowercase, and a number";
      }

      if (!cpw) {
        nextErrors.confirm_password = "Please confirm your password";
      } else if (pw !== cpw) {
        nextErrors.confirm_password = "Passwords do not match";
      }
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    // Abort any inflight request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setErrors({});
    setSuccess(null);

    try {
      const payload: CreateUserRequest = {
        email: normalizeEmail(formData.email),
        full_name: safeTrim(formData.full_name),
        role: formData.role,
        send_invitation: formData.send_invitation,
        tenant_id: safeTrim(formData.tenant_id),
      };

      if (!formData.send_invitation && formData.password) {
        payload.password = formData.password;
      }

      const response = await fetch("/api/admin/users", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        signal: controller.signal,
        body: JSON.stringify(payload),
      });

      const data: AdminApiResponse<{
        user: User;
        invitation_sent?: boolean;
      }> = await response.json();

      if (!response.ok || !data?.success) {
        const code = data?.error?.code || "CREATE_USER_FAILED";
        const message =
          data?.error?.message || "Failed to create user. Please try again.";
        // Map common codes to field errors
        if (code === "EMAIL_ALREADY_EXISTS") {
          setErrors({ email: "A user with this email address already exists" });
        } else if (code === "INSUFFICIENT_PERMISSIONS") {
          setErrors({
            role: "You do not have permission to create users with this role",
          });
        } else {
          setErrors({ general: message });
        }
        return;
      }

      // Success UX
      const successMessage = formData.send_invitation
        ? `User created successfully. An invitation email has been sent to ${payload.email}.`
        : `User created successfully. ${payload.email} can now log in with the provided password.`;
      setSuccess(successMessage);

      // Reset
      setFormData(initialFormData);

      // Notify parent after short delay to allow user to read success
      setTimeout(() => onUserCreated(), 800);
    } catch (err: unknown) {
      const asError = err as Error;
      if (asError?.name === "AbortError") {
        // silently ignore aborted requests
      } else if (asError?.message?.includes("Failed to fetch")) {
        setErrors({
          general:
            "Network error while creating user. Please check your connection and try again.",
        });
      } else {
        setErrors({
          general:
            asError?.message ||
            "An unexpected error occurred. Please try again.",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    abortRef.current?.abort();
    setFormData(initialFormData);
    setErrors({});
    setSuccess(null);
    setShowPassword(false);
    setShowConfirm(false);
  };

  return (
    <div className={`max-w-2xl mx-auto ${className}`}>
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Create New User
          </h2>
          <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">
            Add a new user with the appropriate role and onboarding method.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-6">
          {/* Live region for status */}
          <div
            id={alertRegionId}
            role="status"
            aria-live="polite"
            className="sr-only"
          >
            {success ? "Success: " + success : ""}
            {errors.general ? "Error: " + errors.general : ""}
          </div>

          {/* Success */}
          {success && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-md sm:p-4 md:p-6">
              <div className="flex">
                <svg
                  className="h-5 w-5 text-green-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <p className="ml-3 text-sm text-green-700 md:text-base lg:text-lg">
                  {success}
                </p>
              </div>
            </div>
          )}

          {/* General Error */}
          {errors.general && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-md sm:p-4 md:p-6">
              <div className="flex">
                <svg
                  className="h-5 w-5 text-red-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="ml-3 text-sm text-red-700 md:text-base lg:text-lg">
                  {errors.general}
                </p>
              </div>
            </div>
          )}

          {/* Email */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg"
            >
              Email Address *
            </label>
            <input
              id="email"
              type="email"
              inputMode="email"
              autoComplete="email"
              value={formData.email}
              onChange={(e) => handleInputChange("email", e.target.value)}
              className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.email ? "border-red-300" : "border-gray-300"
              }`}
              placeholder="user@example.com"
              disabled={loading}
              aria-describedby={emailHelpId}
              aria-invalid={!!errors.email}
              required
            />
            <p
              id={emailHelpId}
              className="mt-1 text-sm text-gray-500 md:text-base lg:text-lg"
            >
              Use a valid email. Invitations (if enabled) are sent here.
            </p>
            {errors.email && (
              <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">
                {errors.email}
              </p>
            )}
          </div>

          {/* Full Name */}
          <div>
            <label
              htmlFor="full_name"
              className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg"
            >
              Full Name *
            </label>
            <input
              id="full_name"
              type="text"
              autoComplete="name"
              value={formData.full_name}
              onChange={(e) => handleInputChange("full_name", e.target.value)}
              className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.full_name ? "border-red-300" : "border-gray-300"
              }`}
              placeholder="John Doe"
              disabled={loading}
              aria-invalid={!!errors.full_name}
              required
            />
            {errors.full_name && (
              <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">
                {errors.full_name}
              </p>
            )}
          </div>

          {/* Role */}
          <div>
            <label
              htmlFor="role"
              className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg"
            >
              Role *
            </label>
            <select
              id="role"
              value={formData.role}
              onChange={(e) => handleInputChange("role", e.target.value)}
              className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.role ? "border-red-300" : "border-gray-300"
              }`}
              disabled={loading}
              aria-describedby={roleHelpId}
              aria-invalid={!!errors.role}
              required
            >
              {roleOptions.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
            <p
              id={roleHelpId}
              className="mt-1 text-sm text-gray-500 md:text-base lg:text-lg"
            >
              {formData.role === "admin"
                ? "Admins can manage users but cannot access super admin functions."
                : "Users have standard access to the application."}
            </p>
            {errors.role && (
              <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">
                {errors.role}
              </p>
            )}
          </div>

          {/* Tenant */}
          <div>
            <label
              htmlFor="tenant_id"
              className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg"
            >
              Tenant *
            </label>
            <input
              id="tenant_id"
              type="text"
              value={formData.tenant_id}
              onChange={(e) => handleInputChange("tenant_id", e.target.value)}
              className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.tenant_id ? "border-red-300" : "border-gray-300"
              }`}
              placeholder="default"
              disabled={loading}
              aria-describedby={tenantHelpId}
              aria-invalid={!!errors.tenant_id}
              required
            />
            <p
              id={tenantHelpId}
              className="mt-1 text-sm text-gray-500 md:text-base lg:text-lg"
            >
              Route the user to a specific tenant or keep “default”.
            </p>
            {errors.tenant_id && (
              <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">
                {errors.tenant_id}
              </p>
            )}
          </div>

          {/* Invitation Toggle */}
          <div>
            <div className="flex items-center">
              <input
                id="send_invitation"
                type="checkbox"
                checked={formData.send_invitation}
                onChange={(e) =>
                  handleInputChange("send_invitation", e.target.checked)
                }
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={loading}
                aria-describedby={inviteHelpId}
              />
              <label
                htmlFor="send_invitation"
                className="ml-2 block text-sm text-gray-900 md:text-base lg:text-lg"
              >
                Send invitation email
              </label>
            </div>
            <p
              id={inviteHelpId}
              className="mt-1 text-sm text-gray-500 md:text-base lg:text-lg"
            >
              {formData.send_invitation
                ? "User will receive an email with instructions to set up their account."
                : "Provide a password for immediate access."}
            </p>
          </div>

          {/* Passwords (only when NOT sending invitation) */}
          {!formData.send_invitation && (
            <>
              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg"
                >
                  Password *
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={formData.password}
                    onChange={(e) =>
                      handleInputChange("password", e.target.value)
                    }
                    className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.password ? "border-red-300" : "border-gray-300"
                    }`}
                    placeholder="Enter a secure password"
                    disabled={loading}
                    aria-describedby={passwordHelpId}
                    aria-invalid={!!errors.password}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((s) => !s)}
                    className="absolute inset-y-0 right-2 my-auto px-2 text-sm text-gray-600 hover:text-gray-800"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
                {errors.password && (
                  <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">
                    {errors.password}
                  </p>
                )}
                <p
                  id={passwordHelpId}
                  className="mt-1 text-sm text-gray-500 md:text-base lg:text-lg"
                >
                  Must be 8+ chars with uppercase, lowercase, and numbers.
                </p>
              </div>

              <div>
                <label
                  htmlFor="confirm_password"
                  className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg"
                >
                  Confirm Password *
                </label>
                <div className="relative">
                  <input
                    id="confirm_password"
                    type={showConfirm ? "text" : "password"}
                    value={formData.confirm_password}
                    onChange={(e) =>
                      handleInputChange("confirm_password", e.target.value)
                    }
                    className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.confirm_password
                        ? "border-red-300"
                        : "border-gray-300"
                    }`}
                    placeholder="Confirm the password"
                    disabled={loading}
                    aria-invalid={!!errors.confirm_password}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm((s) => !s)}
                    className="absolute inset-y-0 right-2 my-auto px-2 text-sm text-gray-600 hover:text-gray-800"
                    aria-label={
                      showConfirm ? "Hide confirmation" : "Show confirmation"
                    }
                  >
                    {showConfirm ? "Hide" : "Show"}
                  </button>
                </div>
                {errors.confirm_password && (
                  <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">
                    {errors.confirm_password}
                  </p>
                )}
              </div>
            </>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <Button
              type="button"
              onClick={handleReset}
              disabled={loading}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
              aria-label="Reset form"
            >
              Reset
            </Button>

            <Button
              type="submit"
              disabled={loading}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
              aria-label="Create user"
            >
              {loading ? (
                <div className="flex items-center">
                  <svg
                    className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Creating…
                </div>
              ) : (
                "Create User"
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export { UserCreationForm };
export default UserCreationForm;
