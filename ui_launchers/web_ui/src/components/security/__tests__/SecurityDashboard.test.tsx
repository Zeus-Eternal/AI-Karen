import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { SecurityDashboard } from '../SecurityDashboard';
import { useRBAC } from '@/providers/rbac-provider';

// Mock dependencies
vi.mock('@/providers/rbac-provider');
vi.mock('@/lib/enhanced-api-client');

const mockUseRBAC = vi.mocked(useRBAC);

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

describe('SecurityDashboard', () => {
  const mockRBACContext = {
    hasPermission: vi.fn(),
    hasAllPermissions: vi.fn(),
    hasAnyPermission: vi.fn(),
    checkPermission: vi.fn(),
    currentUser: null,
    userRoles: [],
    effectivePermissions: [],
    getUserRoles: vi.fn(),
    assignRole: vi.fn(),
    removeRole: vi.fn(),
    isEvilModeEnabled: false,
    canEnableEvilMode: false,
    enableEvilMode: vi.fn(),
    disableEvilMode: vi.fn(),
    evilModeSession: null,
    rbacConfig: {} as any,
    evilModeConfig: {} as any,
    isLoading: false,
    isError: false,
    error: null
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseRBAC.mockReturnValue(mockRBACContext);

  it('renders security dashboard when user has permission', () => {
    mockRBACContext.hasPermission.mockReturnValue(true);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: true,
      reason: 'Permission granted',
      appliedRules: [],
      restrictions: []

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <SecurityDashboard />
      </Wrapper>
    );

    expect(screen.getByText('Security Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Monitor security metrics, threats, and compliance status')).toBeInTheDocument();

  it('does not render when user lacks permission', () => {
    mockRBACContext.hasPermission.mockReturnValue(false);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: false,
      reason: 'Permission denied',
      appliedRules: [],
      restrictions: []

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <SecurityDashboard />
      </Wrapper>
    );

    expect(screen.queryByText('Security Dashboard')).not.toBeInTheDocument();

  it('renders navigation tabs when data is loaded', async () => {
    mockRBACContext.hasPermission.mockReturnValue(true);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: true,
      reason: 'Permission granted',
      appliedRules: [],
      restrictions: []

    // Mock the API calls to return data immediately
    const mockQueryClient = new QueryClient({
      defaultOptions: {
        queries: { 
          retry: false,
          staleTime: Infinity,
        },
      },

    // Pre-populate the cache with mock data
    mockQueryClient.setQueryData(['security', 'metrics', '24h'], {
      overallSecurityScore: 87,
      threatLevel: 'medium',
      activeThreats: 3,
      resolvedThreats: 12,
      vulnerabilities: { critical: 1, high: 5, medium: 15, low: 32 },
      complianceScore: 92,
      incidentResponse: { averageResponseTime: 12, resolvedIncidents: 8, openIncidents: 3 },
      systemHealth: {
        authentication: 'healthy',
        authorization: 'healthy',
        dataProtection: 'warning',
        networkSecurity: 'healthy'
      }

    const Wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={mockQueryClient}>
        {children}
      </QueryClientProvider>
    );

    render(
      <Wrapper>
        <SecurityDashboard />
      </Wrapper>
    );

    // Wait for the component to render with data
    await screen.findByText('Overview');
    
    expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Threats' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Vulnerabilities' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Compliance' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Incidents' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Evil Mode' })).toBeInTheDocument();

  it('shows loading state initially', () => {
    mockRBACContext.hasPermission.mockReturnValue(true);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: true,
      reason: 'Permission granted',
      appliedRules: [],
      restrictions: []

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <SecurityDashboard />
      </Wrapper>
    );

    // Should show loading spinner
    expect(document.querySelector('.animate-spin')).toBeInTheDocument();

  it('renders timeframe selector', () => {
    mockRBACContext.hasPermission.mockReturnValue(true);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: true,
      reason: 'Permission granted',
      appliedRules: [],
      restrictions: []

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <SecurityDashboard />
      </Wrapper>
    );

    // Should have timeframe selector
    expect(screen.getByRole('combobox')).toBeInTheDocument();

