
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import SuperAdminDashboard from '../SuperAdminDashboard';

// Mock the hooks using factory functions to avoid hoisting issues
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn()
}));

vi.mock('@/hooks/useRole', () => ({
  useRole: vi.fn()
}));

// Import the mocked hooks after mocking
const { useAuth } = await import('@/contexts/AuthContext');
const { useRole } = await import('@/hooks/useRole');

// Mock user data
const mockSuperAdminUser = {
  user_id: 'super-admin-001',
  email: 'superadmin@example.com',
  roles: ['super_admin'],
  tenant_id: 'test-tenant-001',
  role: 'super_admin' as const,
  permissions: [
    'user_management',
    'admin_management', 
    'system_config',
    'audit_logs',
    'security_settings',
    'user_create',
    'user_edit',
    'user_delete',
    'admin_create',
    'admin_edit',
    'admin_delete'
  ]
};

const mockRegularUser = {
  user_id: 'user-003',
  email: 'user@example.com',
  roles: ['user'],
  tenant_id: 'test-tenant-001',
  role: 'user' as const,
  permissions: []
};

// Mock the component dependencies
vi.mock('../AdminManagementInterface', () => ({
  default: function MockAdminManagementInterface() {
    return <div data-testid="admin-management-interface">Admin Management Interface</div>;
  }
}));
vi.mock('../SystemConfigurationPanel', () => ({
  default: function MockSystemConfigurationPanel() {
    return <div data-testid="system-configuration-panel">System Configuration Panel</div>;
  }
}));
vi.mock('../SecuritySettingsPanel', () => ({
  default: function MockSecuritySettingsPanel() {
    return <div data-testid="security-settings-panel">Security Settings Panel</div>;
  }
}));
vi.mock('../audit/AuditLogViewer', () => ({
  default: function MockAuditLogViewer() {
    return <div data-testid="audit-log-viewer">Audit Log Viewer</div>;
  }
}));

// Mock UI components
vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardContent: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardDescription: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardHeader: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardTitle: ({ children, className }: any) => <div className={className}>{children}</div>,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, className, variant }: any) => (
    <button onClick={onClick} className={className} data-variant={variant} aria-label="Button">
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value, onValueChange }: any) => (
    <div data-testid="tabs" data-value={value} onClick={() => onValueChange?.('test')}>
      {children}
    </div>
  ),
  TabsContent: ({ children, value }: any) => (
    <div data-testid={`tab-content-${value}`}>{children}</div>
  ),
  TabsList: ({ children }: any) => <div data-testid="tabs-list">{children}</div>,
  TabsTrigger: ({ children, value, onClick }: any) => (
    <button data-testid={`tab-trigger-${value}`} onClick={onClick} aria-label="Button">
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: any) => (
    <span data-testid="badge" data-variant={variant}>{children}</span>
  ),
}));

// Mock fetch with proper Response type
global.fetch = vi.fn();

const mockUseAuth = vi.mocked(useAuth);
const mockUseRole = vi.mocked(useRole);

// Helper function to create proper fetch response mock
const createMockResponse = (data: any, ok: boolean = true): Response => {
  return {
    ok,
    json: async () => data,
    status: ok ? 200 : 500,
    statusText: ok ? 'OK' : 'Internal Server Error',
    headers: new Headers(),
    redirected: false,
    type: 'basic',
    url: '',
    clone: vi.fn(),
    body: null,
    bodyUsed: false,
    arrayBuffer: vi.fn(),
    blob: vi.fn(),
    formData: vi.fn(),
    text: vi.fn(),
  } as Response;
};

// Helper function to setup super admin mocks
const setupSuperAdminMocks = () => {
  mockUseAuth.mockReturnValue({
    user: mockSuperAdminUser,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
    checkAuth: vi.fn(),
    hasRole: vi.fn((role) => role === 'super_admin'),
    hasPermission: vi.fn(() => true),
    isAdmin: vi.fn(() => true),
    isSuperAdmin: vi.fn(() => true),
  });

  mockUseRole.mockReturnValue({
    role: 'super_admin',
    hasRole: vi.fn((role) => role === 'super_admin'),
    hasPermission: vi.fn(() => true),
    isAdmin: true,
    isSuperAdmin: true,
    isUser: false,
    canManageUsers: true,
    canManageAdmins: true,
    canManageSystem: true,
    canViewAuditLogs: true,
  });
};

// Helper function to setup regular user mocks
const setupRegularUserMocks = () => {
  mockUseAuth.mockReturnValue({
    user: mockRegularUser,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
    checkAuth: vi.fn(),
    hasRole: vi.fn(() => false),
    hasPermission: vi.fn(() => false),
    isAdmin: vi.fn(() => false),
    isSuperAdmin: vi.fn(() => false),
  });

  mockUseRole.mockReturnValue({
    role: 'user',
    hasRole: vi.fn(() => false),
    hasPermission: vi.fn(() => false),
    isAdmin: false,
    isSuperAdmin: false,
    isUser: true,
    canManageUsers: false,
    canManageAdmins: false,
    canManageSystem: false,
    canViewAuditLogs: false,
  });
};

describe('SuperAdminDashboard', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();
    
    // Setup default fetch mock with proper Response type
    vi.mocked(global.fetch).mockResolvedValue(
      createMockResponse({
        totalUsers: 150,
        totalAdmins: 5,
        activeUsers: 45,
        securityAlerts: 2,
        systemHealth: 'healthy'
      })
    );
  });

  it('renders access denied for non-super admin users', () => {
    setupRegularUserMocks();
    render(<SuperAdminDashboard />);

    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.getByText("You don't have permission to access the super admin dashboard.")).toBeInTheDocument();
  });

  it('renders dashboard for super admin users', async () => {
    setupSuperAdminMocks();
    render(<SuperAdminDashboard />);

    expect(screen.getByText('Super Admin Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Manage administrators, system configuration, and security settings')).toBeInTheDocument();
    expect(screen.getByText('Welcome, superadmin@example.com')).toBeInTheDocument();
  });

  it('loads and displays dashboard statistics', async () => {
    setupSuperAdminMocks();
    render(<SuperAdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument(); // Total Users
      expect(screen.getByText('5')).toBeInTheDocument(); // Total Admins
      expect(screen.getByText('45')).toBeInTheDocument(); // Active Users
      expect(screen.getByText('2')).toBeInTheDocument(); // Security Alerts
    });

    expect(global.fetch).toHaveBeenCalledWith('/api/admin/dashboard/stats');
  });

  it('displays correct system health badge', async () => {
    setupSuperAdminMocks();
    render(<SuperAdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('System healthy')).toBeInTheDocument();
    });
  });

  it('handles tab navigation correctly', async () => {
    setupSuperAdminMocks();
    render(<SuperAdminDashboard />);

    // Initially should show overview tab
    expect(screen.getByText('Quick Actions')).toBeInTheDocument();

    // Click on Admin Management tab
    fireEvent.click(screen.getByText('Admin Management'));
    await waitFor(() => {
      expect(screen.getByTestId('admin-management-interface')).toBeInTheDocument();
    });

    // Click on System Config tab
    fireEvent.click(screen.getByText('System Config'));
    await waitFor(() => {
      expect(screen.getByTestId('system-configuration-panel')).toBeInTheDocument();
    });

    // Click on Security tab
    fireEvent.click(screen.getByText('Security'));
    await waitFor(() => {
      expect(screen.getByTestId('security-settings-panel')).toBeInTheDocument();
    });

    // Click on Audit Logs tab
    fireEvent.click(screen.getByText('Audit Logs'));
    await waitFor(() => {
      expect(screen.getByTestId('audit-log-viewer')).toBeInTheDocument();
    });
  });

  it('handles quick action buttons correctly', async () => {
    setupSuperAdminMocks();
    render(<SuperAdminDashboard />);

    // Click on "Create New Administrator" quick action
    fireEvent.click(screen.getByText('Create New Administrator'));
    await waitFor(() => {
      expect(screen.getByTestId('admin-management-interface')).toBeInTheDocument();
    });

    // Go back to overview
    fireEvent.click(screen.getByText('Overview'));

    // Click on "Update System Configuration" quick action
    fireEvent.click(screen.getByText('Update System Configuration'));
    await waitFor(() => {
      expect(screen.getByTestId('system-configuration-panel')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    setupSuperAdminMocks();

    // Mock fetch to return an error
    vi.mocked(global.fetch).mockRejectedValue(new Error('API Error'));

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<SuperAdminDashboard />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to load dashboard stats:', expect.any(Error));
    });

    // Should still render the dashboard with default stats
    expect(screen.getByText('Super Admin Dashboard')).toBeInTheDocument();
    expect(screen.getAllByText('0')).toHaveLength(4); // Default stats for all metrics

    consoleSpy.mockRestore();
  });

  it('displays correct system status indicators', async () => {
    setupSuperAdminMocks();
    render(<SuperAdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument(); // Database status
      expect(screen.getByText('Active')).toBeInTheDocument(); // Authentication status
      expect(screen.getByText('Recording')).toBeInTheDocument(); // Audit logging status
      expect(screen.getByText('Normal')).toBeInTheDocument(); // Security monitoring status
    });
  });

  it('shows security alerts in system status when present', async () => {
    setupSuperAdminMocks();

    // Mock stats with security alerts using proper Response type
    vi.mocked(global.fetch).mockResolvedValue(
      createMockResponse({
        totalUsers: 150,
        totalAdmins: 5,
        activeUsers: 45,
        securityAlerts: 5,
        systemHealth: 'warning'
      })
    );

    render(<SuperAdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('5 Alerts')).toBeInTheDocument();
      expect(screen.getByText('System warning')).toBeInTheDocument();
    });
  });
});