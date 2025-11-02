/**
 * User Creation Form Component
 * 
 * Provides a comprehensive form for creating new users with validation,
 * role assignment, and email invitation capabilities.
 * 
 * Requirements: 4.2, 4.3, 7.4
 */
'use client';
import React, { useState } from 'react';
import { useRole } from '@/hooks/useRole';
import { validateEmail } from '@/lib/auth/setup-validation';
import type { CreateUserRequest, AdminApiResponse, User } from '@/types/admin';
interface UserCreationFormProps {
  onUserCreated: () => void;
  className?: string;
}
interface FormData {
  email: string;
  full_name: string;
  password: string;
  confirm_password: string;
  role: 'admin' | 'user';
  send_invitation: boolean;
  tenant_id: string;
}
interface FormErrors {
  email?: string;
  full_name?: string;
  password?: string;
  confirm_password?: string;
  role?: string;
  general?: string;
}
const initialFormData: FormData = {
  email: '',
  full_name: '',
  password: '',
  confirm_password: '',
  role: 'user',
  send_invitation: true,
  tenant_id: 'default'
};
export function UserCreationForm({ onUserCreated, className = '' }: UserCreationFormProps) {
  const { hasRole } = useRole();
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const handleInputChange = (field: keyof FormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear field-specific errors when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    // Full name validation
    if (!formData.full_name.trim()) {
      newErrors.full_name = 'Full name is required';
    } else if (formData.full_name.trim().length < 2) {
      newErrors.full_name = 'Full name must be at least 2 characters';
    }
    // Role validation
    if (formData.role === 'admin' && !hasRole('super_admin')) {
      newErrors.role = 'Only super admins can create admin users';
    }
    // Password validation (only if not sending invitation)
    if (!formData.send_invitation) {
      if (!formData.password) {
        newErrors.password = 'Password is required when not sending invitation';
      } else if (formData.password.length < 8) {
        newErrors.password = 'Password must be at least 8 characters';
      } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
        newErrors.password = 'Password must contain uppercase, lowercase, and numbers';
      }
      if (!formData.confirm_password) {
        newErrors.confirm_password = 'Please confirm your password';
      } else if (formData.password !== formData.confirm_password) {
        newErrors.confirm_password = 'Passwords do not match';
      }
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
    setSuccess(null);
    try {
      const requestData: CreateUserRequest = {
        email: formData.email.trim(),
        full_name: formData.full_name.trim(),
        role: formData.role,
        send_invitation: formData.send_invitation,
        tenant_id: formData.tenant_id
      };
      // Only include password if not sending invitation
      if (!formData.send_invitation && formData.password) {
        requestData.password = formData.password;
      }
      const response = await fetch('/api/admin/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });
      const data: AdminApiResponse<{ user: User; invitation_sent?: boolean }> = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.error?.message || 'Failed to create user');
      }
      // Success
      const successMessage = formData.send_invitation
        ? `User created successfully! An invitation email has been sent to ${formData.email}.`
        : `User created successfully! ${formData.email} can now log in with the provided password.`;
      setSuccess(successMessage);
      setFormData(initialFormData);
      // Notify parent component
      setTimeout(() => {
        onUserCreated();
      }, 2000);
    } catch (err) {
      if (err instanceof Error) {
        if (err.message.includes('EMAIL_ALREADY_EXISTS')) {
          setErrors({ email: 'A user with this email address already exists' });
        } else if (err.message.includes('INSUFFICIENT_PERMISSIONS')) {
          setErrors({ role: 'You do not have permission to create users with this role' });
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
  const handleReset = () => {
    setFormData(initialFormData);
    setErrors({});
    setSuccess(null);
  };
  return (
    <div className={`max-w-2xl mx-auto ${className}`}>
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Create New User</h2>
          <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">
            Add a new user to the system with appropriate role and permissions.
          </p>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-6">
          {/* Success Message */}
          {success && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-md sm:p-4 md:p-6">
              <div className="flex">
                <svg className="h-5 w-5 text-green-400 sm:w-auto md:w-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <p className="ml-3 text-sm text-green-700 md:text-base lg:text-lg">{success}</p>
              </div>
            </div>
          )}
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
          {/* Email Field */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">
              Email Address *
            </label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) = aria-label="Input"> handleInputChange('email', e.target.value)}
              className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.email ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="user@example.com"
              disabled={loading}
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">{errors.email}</p>
            )}
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
              placeholder="John Doe"
              disabled={loading}
            />
            {errors.full_name && (
              <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">{errors.full_name}</p>
            )}
          </div>
          {/* Role Field */}
          <div>
            <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">
              Role *
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
              {hasRole('super_admin') && (
                <option value="admin">Admin</option>
              )}
            </select>
            {errors.role && (
              <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">{errors.role}</p>
            )}
            <p className="mt-1 text-sm text-gray-500 md:text-base lg:text-lg">
              {formData.role === 'admin' 
                ? 'Admin users can manage other users but cannot access super admin functions.'
                : 'Regular users have standard access to the application.'
              }
            </p>
          </div>
          {/* Invitation Toggle */}
          <div>
            <div className="flex items-center">
              <input
                id="send_invitation"
                type="checkbox"
                checked={formData.send_invitation}
                onChange={(e) = aria-label="Input"> handleInputChange('send_invitation', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded sm:w-auto md:w-full"
                disabled={loading}
              />
              <label htmlFor="send_invitation" className="ml-2 block text-sm text-gray-900 md:text-base lg:text-lg">
                Send invitation email
              </label>
            </div>
            <p className="mt-1 text-sm text-gray-500 md:text-base lg:text-lg">
              {formData.send_invitation
                ? 'User will receive an email with instructions to set up their account.'
                : 'You will need to provide a password for immediate access.'
              }
            </p>
          </div>
          {/* Password Fields (only shown when not sending invitation) */}
          {!formData.send_invitation && (
            <>
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">
                  Password *
                </label>
                <input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) = aria-label="Input"> handleInputChange('password', e.target.value)}
                  className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.password ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Enter a secure password"
                  disabled={loading}
                />
                {errors.password && (
                  <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">{errors.password}</p>
                )}
                <p className="mt-1 text-sm text-gray-500 md:text-base lg:text-lg">
                  Password must be at least 8 characters with uppercase, lowercase, and numbers.
                </p>
              </div>
              <div>
                <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">
                  Confirm Password *
                </label>
                <input
                  id="confirm_password"
                  type="password"
                  value={formData.confirm_password}
                  onChange={(e) = aria-label="Input"> handleInputChange('confirm_password', e.target.value)}
                  className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.confirm_password ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Confirm the password"
                  disabled={loading}
                />
                {errors.confirm_password && (
                  <p className="mt-1 text-sm text-red-600 md:text-base lg:text-lg">{errors.confirm_password}</p>
                )}
              </div>
            </>
          )}
          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={handleReset}
              disabled={loading}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
             aria-label="Button">
              Reset
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
                  Creating...
                </div>
              ) : (
                'Create User'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
