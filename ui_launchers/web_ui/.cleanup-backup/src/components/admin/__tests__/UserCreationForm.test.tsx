/**
 * UserCreationForm Component Tests
 * 
 * Tests for the user creation form including validation,
 * role assignment, and invitation functionality.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import { UserCreationForm } from '../UserCreationForm';
import { useRole } from '@/hooks/useRole';

// Mock the useRole hook
jest.mock('@/hooks/useRole');
const mockUseRole = useRole as jest.MockedFunction<typeof useRole>;

// Mock validation function
jest.mock('@/lib/auth/setup-validation', () => ({
  validateEmail: jest.fn((email: string) => email.includes('@'))
}));

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('UserCreationForm', () => {
  const mockOnUserCreated = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseRole.mockReturnValue({
      hasRole: jest.fn((role: string) => role === 'admin'),
      hasPermission: jest.fn(() => true),
      user: {
        user_id: 'admin1',
        email: 'admin@test.com',
        role: 'admin'
      } as any,
      loading: false
    });

    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        data: {
          user: {
            user_id: 'new-user',
            email: 'newuser@test.com',
            role: 'user'
          },
          invitation_sent: true
        }
      })
    } as any);
  });

  it('renders user creation form', () => {
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    expect(screen.getByText('Create New User')).toBeInTheDocument();
    expect(screen.getByLabelText('Email Address *')).toBeInTheDocument();
    expect(screen.getByLabelText('Full Name *')).toBeInTheDocument();
    expect(screen.getByLabelText('Role *')).toBeInTheDocument();
    expect(screen.getByLabelText('Send invitation email')).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Try to submit without filling required fields
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument();
      expect(screen.getByText('Full name is required')).toBeInTheDocument();
    });
  });

  it('validates email format', async () => {
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Enter invalid email
    fireEvent.change(screen.getByLabelText('Email Address *'), {
      target: { value: 'invalid-email' }
    });
    fireEvent.change(screen.getByLabelText('Full Name *'), {
      target: { value: 'Test User' }
    });
    
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    });
  });

  it('shows password fields when invitation is disabled', () => {
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Uncheck send invitation
    fireEvent.click(screen.getByLabelText('Send invitation email'));
    
    expect(screen.getByLabelText('Password *')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirm Password *')).toBeInTheDocument();
  });

  it('validates password when invitation is disabled', async () => {
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Uncheck send invitation
    fireEvent.click(screen.getByLabelText('Send invitation email'));
    
    // Fill form with weak password
    fireEvent.change(screen.getByLabelText('Email Address *'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Full Name *'), {
      target: { value: 'Test User' }
    });
    fireEvent.change(screen.getByLabelText('Password *'), {
      target: { value: 'weak' }
    });
    
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument();
    });
  });

  it('validates password confirmation', async () => {
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Uncheck send invitation
    fireEvent.click(screen.getByLabelText('Send invitation email'));
    
    // Fill form with mismatched passwords
    fireEvent.change(screen.getByLabelText('Email Address *'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Full Name *'), {
      target: { value: 'Test User' }
    });
    fireEvent.change(screen.getByLabelText('Password *'), {
      target: { value: 'StrongPass123' }
    });
    fireEvent.change(screen.getByLabelText('Confirm Password *'), {
      target: { value: 'DifferentPass123' }
    });
    
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    });
  });

  it('shows admin role option for super admins only', () => {
    // Test as regular admin
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    const roleSelect = screen.getByLabelText('Role *');
    expect(roleSelect).toHaveValue('user');
    expect(screen.queryByText('Admin')).not.toBeInTheDocument();
    
    // Test as super admin
    mockUseRole.mockReturnValue({
      hasRole: jest.fn((role: string) => role === 'super_admin' || role === 'admin'),
      hasPermission: jest.fn(() => true),
      user: { user_id: 'super1', email: 'super@test.com', role: 'super_admin' } as any,
      loading: false
    });
    
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('prevents admin role creation by regular admins', async () => {
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Manually set role to admin (simulating form manipulation)
    const form = screen.getByRole('form') as HTMLFormElement;
    const roleSelect = screen.getByLabelText('Role *') as HTMLSelectElement;
    
    // Add admin option temporarily
    const adminOption = document.createElement('option');
    adminOption.value = 'admin';
    adminOption.textContent = 'Admin';
    roleSelect.appendChild(adminOption);
    
    fireEvent.change(roleSelect, { target: { value: 'admin' } });
    
    // Fill other required fields
    fireEvent.change(screen.getByLabelText('Email Address *'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Full Name *'), {
      target: { value: 'Test User' }
    });
    
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      expect(screen.getByText('Only super admins can create admin users')).toBeInTheDocument();
    });
  });

  it('successfully creates user with invitation', async () => {
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Fill form
    fireEvent.change(screen.getByLabelText('Email Address *'), {
      target: { value: 'newuser@test.com' }
    });
    fireEvent.change(screen.getByLabelText('Full Name *'), {
      target: { value: 'New User' }
    });
    
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'newuser@test.com',
          full_name: 'New User',
          role: 'user',
          send_invitation: true,
          tenant_id: 'default'
        })
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText(/User created successfully! An invitation email has been sent/)).toBeInTheDocument();
    });
    
    // Should call callback after delay
    await waitFor(() => {
      expect(mockOnUserCreated).toHaveBeenCalled();
    }, { timeout: 3000 });
  });

  it('successfully creates user with password', async () => {
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Uncheck send invitation
    fireEvent.click(screen.getByLabelText('Send invitation email'));
    
    // Fill form
    fireEvent.change(screen.getByLabelText('Email Address *'), {
      target: { value: 'newuser@test.com' }
    });
    fireEvent.change(screen.getByLabelText('Full Name *'), {
      target: { value: 'New User' }
    });
    fireEvent.change(screen.getByLabelText('Password *'), {
      target: { value: 'StrongPass123' }
    });
    fireEvent.change(screen.getByLabelText('Confirm Password *'), {
      target: { value: 'StrongPass123' }
    });
    
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'newuser@test.com',
          full_name: 'New User',
          role: 'user',
          send_invitation: false,
          tenant_id: 'default',
          password: 'StrongPass123'
        })
      });
    });
  });

  it('handles API errors', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({
        success: false,
        error: { message: 'Email already exists' }
      })
    } as any);

    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Fill and submit form
    fireEvent.change(screen.getByLabelText('Email Address *'), {
      target: { value: 'existing@test.com' }
    });
    fireEvent.change(screen.getByLabelText('Full Name *'), {
      target: { value: 'Test User' }
    });
    
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });
  });

  it('handles specific error types', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({
        success: false,
        error: { message: 'EMAIL_ALREADY_EXISTS: User exists' }
      })
    } as any);

    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Fill and submit form
    fireEvent.change(screen.getByLabelText('Email Address *'), {
      target: { value: 'existing@test.com' }
    });
    fireEvent.change(screen.getByLabelText('Full Name *'), {
      target: { value: 'Test User' }
    });
    
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      expect(screen.getByText('A user with this email address already exists')).toBeInTheDocument();
    });
  });

  it('resets form after successful creation', async () => {
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Fill form
    fireEvent.change(screen.getByLabelText('Email Address *'), {
      target: { value: 'newuser@test.com' }
    });
    fireEvent.change(screen.getByLabelText('Full Name *'), {
      target: { value: 'New User' }
    });
    
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('')).toBeInTheDocument(); // Email field should be empty
    });
  });

  it('shows loading state during submission', async () => {
    // Mock slow API response
    mockFetch.mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, data: {} })
        } as any), 100)
      )
    );

    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Fill and submit form
    fireEvent.change(screen.getByLabelText('Email Address *'), {
      target: { value: 'newuser@test.com' }
    });
    fireEvent.change(screen.getByLabelText('Full Name *'), {
      target: { value: 'New User' }
    });
    
    fireEvent.click(screen.getByText('Create User'));
    
    expect(screen.getByText('Creating...')).toBeInTheDocument();
    expect(screen.getByText('Creating...')).toBeDisabled();
  });

  it('resets form when reset button is clicked', () => {
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Fill form
    fireEvent.change(screen.getByLabelText('Email Address *'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Full Name *'), {
      target: { value: 'Test User' }
    });
    
    // Click reset
    fireEvent.click(screen.getByText('Reset'));
    
    expect(screen.getByLabelText('Email Address *')).toHaveValue('');
    expect(screen.getByLabelText('Full Name *')).toHaveValue('');
  });

  it('clears field errors when user starts typing', async () => {
    render(<UserCreationForm onUserCreated={mockOnUserCreated} />);
    
    // Submit to trigger validation errors
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument();
    });
    
    // Start typing in email field
    fireEvent.change(screen.getByLabelText('Email Address *'), {
      target: { value: 't' }
    });
    
    expect(screen.queryByText('Email is required')).not.toBeInTheDocument();
  });
});