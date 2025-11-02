/**
 * AdminDashboard Component Tests
 * 
 * Tests for the main admin dashboard component including navigation,
 * data loading, and user management functionality.
 */


import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import { AdminDashboard } from '../AdminDashboard';
import { useRole } from '@/hooks/useRole';

// Mock the useRole hook
jest.mock('@/hooks/useRole');
const mockUseRole = useRole as jest.MockedFunction<typeof useRole>;

// Mock child components
jest.mock('../UserManagementTable', () => ({
  UserManagementTable: ({ onSelectionChange, onUserUpdated }: any) => (
    <div data-testid="user-management-table">
      <button onClick={() = aria-label="Button"> onSelectionChange(['user1', 'user2'])}>
        Select Users
      </button>
      <button onClick={onUserUpdated} aria-label="Button">Update User</button>
    </div>
  )
}));

jest.mock('../UserCreationForm', () => ({
  UserCreationForm: ({ onUserCreated }: any) => (
    <div data-testid="user-creation-form">
      <button onClick={onUserCreated} aria-label="Button">Create User</button>
    </div>
  )
}));

jest.mock('../UserActivityMonitor', () => ({
  UserActivityMonitor: () => <div data-testid="user-activity-monitor">Activity Monitor</div>
}));

jest.mock('../BulkUserOperations', () => ({
  BulkUserOperations: ({ selectedUserIds, onOperationComplete, onCancel }: any) => (
    <div data-testid="bulk-user-operations">
      <span>Selected: {selectedUserIds.length}</span>
      <button onClick={onOperationComplete} aria-label="Button">Complete Operation</button>
      <button onClick={onCancel} aria-label="Button">Cancel</button>
    </div>
  )
}));

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('AdminDashboard', () => {
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

    // Mock successful API responses
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/api/admin/users/stats')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: {
              total_users: 100,
              active_users: 85,
              verified_users: 90,
              admin_users: 5,
              super_admin_users: 1,
              users_created_today: 2,
              users_created_this_week: 8,
              users_created_this_month: 25,
              last_login_today: 15,
              two_factor_enabled: 30
            }
          })
        });
      }
      
      if (url.includes('/api/admin/system/activity-summary')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: {
              period: 'week',
              user_registrations: 8,
              admin_actions: 45,
              security_events: 2,
              failed_logins: 12,
              successful_logins: 234,
              top_actions: [
                { action: 'user.login', count: 234 },
                { action: 'user.update', count: 15 }
              ],
              top_users: [
                { user_id: 'user1', email: 'user1@test.com', action_count: 25 }
              ]
            }
          })
        });
      }
      
      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ success: false, error: { message: 'Not found' } })
      });
    });
  });

  it('renders admin dashboard for admin users', async () => {
    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Manage users and monitor system activity')).toBeInTheDocument();
    });
  });

  it('denies access for non-admin users', () => {
    mockUseRole.mockReturnValue({
      hasRole: jest.fn(() => false),
      hasPermission: jest.fn(() => false),
      user: { user_id: 'user1', email: 'user@test.com', role: 'user' } as any,
      loading: false
    });

    render(<AdminDashboard />);
    
    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.getByText('You need admin privileges to access this dashboard.')).toBeInTheDocument();
  });

  it('loads and displays user statistics', async () => {
    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument(); // Total users
      expect(screen.getByText('85')).toBeInTheDocument(); // Active users
      expect(screen.getByText('90')).toBeInTheDocument(); // Verified users
      expect(screen.getByText('30')).toBeInTheDocument(); // 2FA enabled
    });
  });

  it('loads and displays activity summary', async () => {
    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('8')).toBeInTheDocument(); // User registrations
      expect(screen.getByText('45')).toBeInTheDocument(); // Admin actions
      expect(screen.getByText('234')).toBeInTheDocument(); // Successful logins
      expect(screen.getByText('12')).toBeInTheDocument(); // Failed logins
    });
  });

  it('navigates between different views', async () => {
    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
    });

    // Navigate to User Management
    fireEvent.click(screen.getByText('User Management'));
    expect(screen.getByTestId('user-management-table')).toBeInTheDocument();

    // Navigate to Create User
    fireEvent.click(screen.getByText('Create User'));
    expect(screen.getByTestId('user-creation-form')).toBeInTheDocument();

    // Navigate to Activity Monitor
    fireEvent.click(screen.getByText('Activity Monitor'));
    expect(screen.getByTestId('user-activity-monitor')).toBeInTheDocument();
  });

  it('handles user selection and shows bulk operations', async () => {
    render(<AdminDashboard />);
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('User Management'));
    });

    // Select users
    fireEvent.click(screen.getByText('Select Users'));
    
    await waitFor(() => {
      expect(screen.getByText('Bulk Operations (2)')).toBeInTheDocument();
    });

    // Navigate to bulk operations
    fireEvent.click(screen.getByText('Bulk Operations (2)'));
    expect(screen.getByTestId('bulk-user-operations')).toBeInTheDocument();
    expect(screen.getByText('Selected: 2')).toBeInTheDocument();
  });

  it('handles user creation callback', async () => {
    render(<AdminDashboard />);
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('Create User'));
    });

    // Trigger user creation
    fireEvent.click(screen.getByText('Create User'));
    
    await waitFor(() => {
      // Should navigate back to users view
      expect(screen.getByTestId('user-management-table')).toBeInTheDocument();
    });
  });

  it('handles bulk operation completion', async () => {
    render(<AdminDashboard />);
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('User Management'));
    });

    // Select users and navigate to bulk operations
    fireEvent.click(screen.getByText('Select Users'));
    fireEvent.click(screen.getByText('Bulk Operations (2)'));
    
    // Complete operation
    fireEvent.click(screen.getByText('Complete Operation'));
    
    await waitFor(() => {
      // Should refresh data (fetch called again)
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/users/stats');
    });
  });

  it('handles API errors gracefully', async () => {
    mockFetch.mockImplementation(() => 
      Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ success: false, error: { message: 'API Error' } })
      })
    );

    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
      expect(screen.getByText('Try again')).toBeInTheDocument();
    });
  });

  it('retries data loading on error', async () => {
    mockFetch
      .mockImplementationOnce(() => 
        Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ success: false, error: { message: 'API Error' } })
        })
      )
      .mockImplementationOnce((url: string) => {
        if (url.includes('/api/admin/users/stats')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              success: true,
              data: { total_users: 100, active_users: 85, verified_users: 90 }
            })
          });
        }
        return Promise.resolve({ ok: false });
      });

    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Try again')).toBeInTheDocument();
    });

    // Click retry
    fireEvent.click(screen.getByText('Try again'));
    
    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });

  it('displays loading state initially', () => {
    render(<AdminDashboard />);
    
    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  it('renders quick action buttons', async () => {
    render(<AdminDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Create New User')).toBeInTheDocument();
      expect(screen.getByText('Manage Users')).toBeInTheDocument();
      expect(screen.getByText('View Activity')).toBeInTheDocument();
    });
  });

  it('handles quick action navigation', async () => {
    render(<AdminDashboard />);
    
    await waitFor(() => {
      // Click quick action for create user
      fireEvent.click(screen.getByText('Create New User'));
    });
    
    expect(screen.getByTestId('user-creation-form')).toBeInTheDocument();
  });
});