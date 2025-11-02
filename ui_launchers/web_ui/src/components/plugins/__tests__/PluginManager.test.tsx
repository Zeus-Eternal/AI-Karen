/**
 * Plugin Manager Component Tests
 * 
 * Unit tests for plugin management operations and state handling.
 * Based on requirements: 5.1, 5.4
 */


import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { PluginManager } from '../PluginManager';
import { PluginInfo } from '@/types/plugins';

// Mock the plugin store
const mockUsePluginStore = vi.fn();
vi.mock('@/store/plugin-store', () => ({
  usePluginStore: mockUsePluginStore,
  selectFilteredPlugins: vi.fn(),
  selectPluginLoading: vi.fn(),
  selectPluginError: vi.fn(),
}));

// Mock UI components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, ...props }: any) => (
    <button 
      onClick={onClick} 
      disabled={disabled} 
      data-variant={variant}
      {...props}
     aria-label="Button">
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/input', () => ({
  Input: ({ value, onChange, placeholder, ...props }: any) => (
    <input 
      value={value} 
      onChange={onChange} 
      placeholder={placeholder}
      {...props} />
  ),
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardContent: ({ children }: any) => <div>{children}</div>,
  CardDescription: ({ children }: any) => <p>{children}</p>,
  CardHeader: ({ children }: any) => <div>{children}</div>,
  CardTitle: ({ children }: any) => <h3>{children}</h3>,
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: any) => <span data-variant={variant}>{children}</span>,
}));

vi.mock('@/components/ui/alert', () => ({
  Alert: ({ children, variant }: any) => <div data-variant={variant}>{children}</div>,
  AlertDescription: ({ children }: any) => <div>{typeof children === 'string' ? children : JSON.stringify(children)}</div>,
}));

vi.mock('@/components/ui/skeleton', () => ({
  Skeleton: ({ className }: any) => <div className={className} data-testid="skeleton" />,
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, value, onValueChange }: any) => (
    <select value={value} onChange={(e) = aria-label="Select option"> onValueChange(e.target.value)}>
      {children}
    </select>
  ),
  SelectContent: ({ children }: any) => <>{children}</>,
  SelectItem: ({ children, value }: any) => <option value={value}>{children}</option>,
  SelectTrigger: ({ children }: any) => <div>{children}</div>,
  SelectValue: ({ placeholder }: any) => <span>{placeholder}</span>,
}));

vi.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: any) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: any) => <div>{children}</div>,
  DropdownMenuItem: ({ children, onClick }: any) => (
    <button onClick={onClick} aria-label="Button">{children}</button>
  ),
  DropdownMenuSeparator: () => <hr />,
  DropdownMenuTrigger: ({ children }: any) => <div>{children}</div>,
}));

vi.mock('@/components/ui/separator', () => ({
  Separator: () => <hr />,
}));

// Mock child components
vi.mock('../PluginDetailView', () => ({
  PluginDetailView: ({ plugin, onClose }: any) => (
    <div data-testid="plugin-detail-view">
      <h2>{plugin.name} Details</h2>
      <button onClick={onClose} aria-label="Button">Close</button>
    </div>
  ),
}));

vi.mock('../PluginInstallationWizard', () => ({
  PluginInstallationWizard: ({ onClose, onComplete }: any) => (
    <div data-testid="plugin-installation-wizard">
      <h2>Installation Wizard</h2>
      <button onClick={onClose} aria-label="Button">Close</button>
      <button onClick={onComplete} aria-label="Button">Complete</button>
    </div>
  ),
}));

vi.mock('../PluginMarketplace', () => ({
  PluginMarketplace: ({ onClose, onInstall }: any) => (
    <div data-testid="plugin-marketplace">
      <h2>Plugin Marketplace</h2>
      <button onClick={onClose} aria-label="Button">Close</button>
    </div>
  ),
}));

describe('PluginManager', () => {
  const mockPlugins: PluginInfo[] = [
    {
      id: 'weather-plugin',
      name: 'Weather Service',
      version: '1.2.0',
      status: 'active',
      enabled: true,
      autoStart: true,
      restartCount: 0,
      installedAt: new Date('2024-01-15'),
      updatedAt: new Date('2024-01-20'),
      installedBy: 'admin',
      manifest: {
        id: 'weather-plugin',
        name: 'Weather Service',
        version: '1.2.0',
        description: 'Provides current weather information',
        author: { name: 'Kari AI Team' },
        license: 'MIT',
        keywords: ['weather', 'api'],
        category: 'integration',
        runtime: { platform: ['node'] },
        dependencies: [],
        systemRequirements: {},
        permissions: [],
        sandboxed: true,
        securityPolicy: {
          allowNetworkAccess: true,
          allowFileSystemAccess: false,
          allowSystemCalls: false,
        },
        configSchema: [],
        apiVersion: '1.0',
      },
      config: {},
      permissions: [],
      metrics: {
        performance: {
          averageExecutionTime: 250,
          totalExecutions: 1247,
          errorRate: 0.02,
          lastExecution: new Date(),
        },
        resources: {
          memoryUsage: 15.2,
          cpuUsage: 0.5,
          diskUsage: 2.1,
          networkUsage: 0.8,
        },
        health: {
          status: 'healthy',
          uptime: 99.8,
          lastHealthCheck: new Date(),
          issues: [],
        },
      },
      dependencyStatus: {
        satisfied: true,
        missing: [],
        conflicts: [],
      },
    },
    {
      id: 'gmail-plugin',
      name: 'Gmail Integration',
      version: '2.1.0',
      status: 'error',
      enabled: false,
      autoStart: false,
      restartCount: 2,
      installedAt: new Date('2024-01-10'),
      updatedAt: new Date('2024-01-25'),
      installedBy: 'admin',
      manifest: {
        id: 'gmail-plugin',
        name: 'Gmail Integration',
        version: '2.1.0',
        description: 'Gmail integration for AI chat',
        author: { name: 'Kari AI Team' },
        license: 'MIT',
        keywords: ['gmail', 'email'],
        category: 'integration',
        runtime: { platform: ['node'] },
        dependencies: [],
        systemRequirements: {},
        permissions: [],
        sandboxed: true,
        securityPolicy: {
          allowNetworkAccess: true,
          allowFileSystemAccess: false,
          allowSystemCalls: false,
        },
        configSchema: [],
        apiVersion: '1.0',
      },
      config: {},
      permissions: [],
      metrics: {
        performance: {
          averageExecutionTime: 1200,
          totalExecutions: 45,
          errorRate: 0.15,
          lastExecution: new Date(Date.now() - 86400000),
        },
        resources: {
          memoryUsage: 8.5,
          cpuUsage: 0.2,
          diskUsage: 1.2,
          networkUsage: 0.3,
        },
        health: {
          status: 'warning',
          uptime: 85.2,
          lastHealthCheck: new Date(),
          issues: ['Authentication token expired'],
        },
      },
      dependencyStatus: {
        satisfied: true,
        missing: [],
        conflicts: [],
      },
      lastError: {
        message: 'Authentication failed: Token expired',
        timestamp: new Date(Date.now() - 3600000),
      },
    },
  ];

  const mockStoreState = {
    plugins: mockPlugins,
    selectedPlugin: null,
    searchQuery: '',
    filters: {},
    sortBy: 'name',
    sortOrder: 'asc',
    view: 'list',
    showInstallationWizard: false,
    showMarketplace: false,
    loadPlugins: vi.fn(),
    selectPlugin: vi.fn(),
    enablePlugin: vi.fn(),
    disablePlugin: vi.fn(),
    uninstallPlugin: vi.fn(),
    setSearchQuery: vi.fn(),
    setFilters: vi.fn(),
    setSorting: vi.fn(),
    setView: vi.fn(),
    setShowInstallationWizard: vi.fn(),
    setShowMarketplace: vi.fn(),
    clearErrors: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock the store hook with default values
    mockUsePluginStore.mockImplementation((selector?: any) => {
      if (selector) {
        // Handle selector functions
        if (typeof selector === 'function') {
          return selector(mockStoreState);
        }
        return mockStoreState;
      }
      return mockStoreState;
    });
  });

  it('renders plugin manager with header and controls', () => {
    render(<PluginManager />);
    
    expect(screen.getByText('Plugin Manager')).toBeInTheDocument();
    expect(screen.getByText('Manage and monitor your installed plugins and extensions')).toBeInTheDocument();
    expect(screen.getByText('Refresh')).toBeInTheDocument();
    expect(screen.getByText('Browse Marketplace')).toBeInTheDocument();
    expect(screen.getByText('Install Plugin')).toBeInTheDocument();
  });

  it('displays plugin cards with correct information', () => {
    render(<PluginManager />);
    
    expect(screen.getByText('Weather Service')).toBeInTheDocument();
    expect(screen.getByText('Gmail Integration')).toBeInTheDocument();
    expect(screen.getByText('Provides current weather information')).toBeInTheDocument();
    expect(screen.getByText('Gmail integration for AI chat')).toBeInTheDocument();
  });

  it('shows plugin status badges correctly', () => {
    render(<PluginManager />);
    
    const statusBadges = screen.getAllByText(/Active|Error/);
    expect(statusBadges).toHaveLength(2);
  });

  it('displays plugin metrics', () => {
    render(<PluginManager />);
    
    expect(screen.getByText('1,247')).toBeInTheDocument(); // Weather plugin executions
    expect(screen.getByText('250ms')).toBeInTheDocument(); // Weather plugin avg time
    expect(screen.getByText('45')).toBeInTheDocument(); // Gmail plugin executions
  });

  it('handles search input changes', () => {
    render(<PluginManager />);
    
    const searchInput = screen.getByPlaceholderText('Search plugins...');
    fireEvent.change(searchInput, { target: { value: 'weather' } });
    
    expect(mockStoreState.setSearchQuery).toHaveBeenCalledWith('weather');
  });

  it('handles filter changes', () => {
    render(<PluginManager />);
    
    const statusSelect = screen.getByDisplayValue('All Status');
    fireEvent.change(statusSelect, { target: { value: 'active' } });
    
    expect(mockStoreState.setFilters).toHaveBeenCalledWith({ status: ['active'] });
  });

  it('handles sorting changes', () => {
    render(<PluginManager />);
    
    const sortSelect = screen.getByDisplayValue('Name A-Z');
    fireEvent.change(sortSelect, { target: { value: 'status-asc' } });
    
    expect(mockStoreState.setSorting).toHaveBeenCalledWith('status', 'asc');
  });

  it('handles view toggle between list and grid', () => {
    render(<PluginManager />);
    
    const gridButton = screen.getByRole('button', { name: /grid/i });
    fireEvent.click(gridButton);
    
    expect(mockStoreState.setView).toHaveBeenCalledWith('grid');
  });

  it('handles refresh button click', () => {
    render(<PluginManager />);
    
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    expect(mockStoreState.clearErrors).toHaveBeenCalled();
    expect(mockStoreState.loadPlugins).toHaveBeenCalled();
  });

  it('handles install plugin button click', () => {
    render(<PluginManager />);
    
    const installButton = screen.getByText('Install Plugin');
    fireEvent.click(installButton);
    
    expect(mockStoreState.setShowInstallationWizard).toHaveBeenCalledWith(true);
  });

  it('handles browse marketplace button click', () => {
    render(<PluginManager />);
    
    const marketplaceButton = screen.getByText('Browse Marketplace');
    fireEvent.click(marketplaceButton);
    
    expect(mockStoreState.setShowMarketplace).toHaveBeenCalledWith(true);
  });

  it('shows loading skeleton when loading', () => {
    (usePluginStore as any).mockImplementation((selector?: any) => {
      if (selector?.name === 'selectPluginLoading') {
        return true;
      }
      if (selector?.name === 'selectFilteredPlugins') {
        return [];
      }
      if (selector?.name === 'selectPluginError') {
        return null;
      }
      return { ...mockStoreState, plugins: [] };
    });

    render(<PluginManager />);
    
    expect(screen.getAllByTestId('skeleton')).toHaveLength(18); // 6 cards × 3 skeletons each
  });

  it('shows error message when there is an error', () => {
    (usePluginStore as any).mockImplementation((selector?: any) => {
      if (selector?.name === 'selectPluginError') {
        return 'Failed to load plugins';
      }
      if (selector?.name === 'selectFilteredPlugins') {
        return [];
      }
      if (selector?.name === 'selectPluginLoading') {
        return false;
      }
      return { ...mockStoreState, plugins: [] };
    });

    render(<PluginManager />);
    
    expect(screen.getByText('Failed to load plugins')).toBeInTheDocument();
  });

  it('shows empty state when no plugins are installed', () => {
    (usePluginStore as any).mockImplementation((selector?: any) => {
      if (selector?.name === 'selectFilteredPlugins') {
        return [];
      }
      if (selector?.name === 'selectPluginLoading') {
        return false;
      }
      if (selector?.name === 'selectPluginError') {
        return null;
      }
      return { ...mockStoreState, plugins: [] };
    });

    render(<PluginManager />);
    
    expect(screen.getByText('No plugins installed')).toBeInTheDocument();
    expect(screen.getByText('Get started by installing your first plugin')).toBeInTheDocument();
  });

  it('shows installation wizard when showInstallationWizard is true', () => {
    (usePluginStore as any).mockImplementation((selector?: any) => {
      if (selector) {
        return selector({ ...mockStoreState, showInstallationWizard: true });
      }
      return { ...mockStoreState, showInstallationWizard: true };
    });

    render(<PluginManager />);
    
    expect(screen.getByTestId('plugin-installation-wizard')).toBeInTheDocument();
    expect(screen.getByText('Installation Wizard')).toBeInTheDocument();
  });

  it('shows marketplace when showMarketplace is true', () => {
    (usePluginStore as any).mockImplementation((selector?: any) => {
      if (selector) {
        return selector({ ...mockStoreState, showMarketplace: true });
      }
      return { ...mockStoreState, showMarketplace: true };
    });

    render(<PluginManager />);
    
    expect(screen.getByTestId('plugin-marketplace')).toBeInTheDocument();
    expect(screen.getByText('Plugin Marketplace')).toBeInTheDocument();
  });

  it('shows plugin detail view when a plugin is selected', () => {
    (usePluginStore as any).mockImplementation((selector?: any) => {
      if (selector) {
        return selector({ ...mockStoreState, selectedPlugin: mockPlugins[0] });
      }
      return { ...mockStoreState, selectedPlugin: mockPlugins[0] };
    });

    render(<PluginManager />);
    
    expect(screen.getByTestId('plugin-detail-view')).toBeInTheDocument();
    expect(screen.getByText('Weather Service Details')).toBeInTheDocument();
  });

  it('calls loadPlugins on component mount', () => {
    render(<PluginManager />);
    
    expect(mockStoreState.loadPlugins).toHaveBeenCalled();
  });

  it('displays health issues for plugins with warnings', () => {
    render(<PluginManager />);
    
    expect(screen.getByText('Authentication token expired')).toBeInTheDocument();
  });

  it('displays last error information', () => {
    render(<PluginManager />);
    
    expect(screen.getByText('Authentication failed: Token expired')).toBeInTheDocument();
  });
});