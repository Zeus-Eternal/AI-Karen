/**
 * Plugin Manager Basic Tests
 * 
 * Simplified unit tests for plugin management core functionality.
 * Based on requirements: 5.1, 5.4
 */


import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { PluginManager } from '../PluginManager';

// Mock all dependencies
const mockStore = {
  plugins: [],
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

vi.mock('@/store/plugin-store', () => ({
  usePluginStore: vi.fn((selector?: any) => {
    if (selector) {
      return selector(mockStore);
    }
    return mockStore;
  }),
  selectFilteredPlugins: vi.fn(() => []),
  selectPluginLoading: vi.fn(() => false),
  selectPluginError: vi.fn(() => null),
}));

// Mock UI components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: any) => <Button {...props} aria-label="Button">{children}</Button>,
}));

vi.mock('@/components/ui/input', () => ({
  Input: (props: any) => <input {...props} />,
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div>{children}</div>,
  CardDescription: ({ children }: any) => <p>{children}</p>,
  CardHeader: ({ children }: any) => <div>{children}</div>,
  CardTitle: ({ children }: any) => <h3>{children}</h3>,
}));

vi.mock('@/components/ui/alert', () => ({
  Alert: ({ children }: any) => <div data-testid="alert">{children}</div>,
  AlertDescription: ({ children }: any) => <div>{children}</div>,
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children }: any) => <div>{children}</div>,
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children }: any) => <div>{children}</div>,
  SelectTrigger: ({ children }: any) => <div>{children}</div>,
  SelectValue: ({ placeholder }: any) => <span>{placeholder}</span>,
}));

vi.mock('@/components/ui/separator', () => ({
  Separator: () => <hr />,
}));

// Mock child components
vi.mock('../PluginDetailView', () => ({
  PluginDetailView: () => <div data-testid="plugin-detail-view">Plugin Detail View</div>,
}));

vi.mock('../PluginInstallationWizard', () => ({
  PluginInstallationWizard: () => <div data-testid="plugin-installation-wizard">Installation Wizard</div>,
}));

vi.mock('../PluginMarketplace', () => ({
  PluginMarketplace: () => <div data-testid="plugin-marketplace">Plugin Marketplace</div>,
}));

describe('PluginManager Basic Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();

  it('renders plugin manager header', () => {
    render(<PluginManager />);
    
    expect(screen.getByText('Plugin Manager')).toBeInTheDocument();
    expect(screen.getByText('Manage and monitor your installed plugins and extensions')).toBeInTheDocument();

  it('renders main action buttons', () => {
    render(<PluginManager />);
    
    expect(screen.getByText('Refresh')).toBeInTheDocument();
    expect(screen.getByText('Browse Marketplace')).toBeInTheDocument();
    expect(screen.getByText('Install Plugin')).toBeInTheDocument();

  it('renders search input', () => {
    render(<PluginManager />);
    
    expect(screen.getByPlaceholderText('Search plugins...')).toBeInTheDocument();

  it('renders filter controls', () => {
    render(<PluginManager />);
    
    expect(screen.getByText('All Status')).toBeInTheDocument();
    expect(screen.getByText('Name A-Z')).toBeInTheDocument();

  it('renders empty state when no plugins', () => {
    render(<PluginManager />);
    
    // Debug: log what's being rendered
    screen.debug();
    
    // Should show empty state since we mocked empty plugins array
    expect(screen.getByText('No plugins installed')).toBeInTheDocument();
    expect(screen.getByText('Get started by installing your first plugin')).toBeInTheDocument();

