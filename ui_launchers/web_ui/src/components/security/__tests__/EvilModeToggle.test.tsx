import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { EvilModeToggle } from '../EvilModeToggle';
import { useRBAC } from '@/providers/rbac-provider';
import { auditLogger } from '@/services/audit-logger';

// Mock dependencies
vi.mock('@/providers/rbac-provider');
vi.mock('@/services/audit-logger');

const mockUseRBAC = vi.mocked(useRBAC);
const mockAuditLogger = vi.mocked(auditLogger);

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

describe('EvilModeToggle', () => {
  const mockRBACContext = {
    isEvilModeEnabled: false,
    canEnableEvilMode: true,
    enableEvilMode: vi.fn(),
    disableEvilMode: vi.fn(),
    evilModeSession: null,
    evilModeConfig: {
      enabled: true,
      requiredRole: 'security:evil_mode',
      confirmationRequired: true,
      additionalAuthRequired: true,
      auditLevel: 'comprehensive',
      restrictions: [],
      warningMessage: 'You are about to enable Evil Mode. This grants elevated privileges that can potentially harm the system. Proceed with extreme caution.',
      timeLimit: 60
    },
    currentUser: null,
    userRoles: [],
    effectivePermissions: [],
    getUserRoles: vi.fn(),
    assignRole: vi.fn(),
    removeRole: vi.fn(),
    checkPermission: vi.fn(),
    hasPermission: vi.fn(),
    hasAllPermissions: vi.fn(),
    hasAnyPermission: vi.fn(),
    rbacConfig: {} as any,
    isLoading: false,
    isError: false,
    error: null
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseRBAC.mockReturnValue(mockRBACContext);
    mockAuditLogger.logAuthz = vi.fn().mockResolvedValue(undefined);
  });

  it('renders permission denied when user cannot enable evil mode', () => {
    mockUseRBAC.mockReturnValue({
      ...mockRBACContext,
      canEnableEvilMode: false
    });

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    expect(screen.getByText('You do not have permission to access Evil Mode')).toBeInTheDocument();
  });

  it('renders enable button when evil mode is disabled', () => {
    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    expect(screen.getByText('Enable Evil Mode')).toBeInTheDocument();
    expect(screen.getByText('Elevated privileges system')).toBeInTheDocument();
  });

  it('renders disable button when evil mode is enabled', () => {
    mockUseRBAC.mockReturnValue({
      ...mockRBACContext,
      isEvilModeEnabled: true,
      evilModeSession: {
        userId: 'user-1',
        sessionId: 'session-1',
        startTime: new Date(),
        actions: [],
        justification: 'Test justification'
      }
    });

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    expect(screen.getByText('Disable')).toBeInTheDocument();
    expect(screen.getByText('Currently active')).toBeInTheDocument();
  });

  it('opens enable dialog when enable button is clicked', async () => {
    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    const enableButton = screen.getByRole('button', { name: /Enable Evil Mode/ });
    fireEvent.click(enableButton);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(mockRBACContext.evilModeConfig.warningMessage)).toBeInTheDocument();
    });
  });

  it('shows security warnings in enable dialog', async () => {
    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    fireEvent.click(screen.getByText('Enable Evil Mode'));

    await waitFor(() => {
      expect(screen.getByText('Security Warnings')).toBeInTheDocument();
      expect(screen.getByText('System Integrity Risk')).toBeInTheDocument();
      expect(screen.getByText('Enhanced Monitoring')).toBeInTheDocument();
      expect(screen.getByText('Compliance Impact')).toBeInTheDocument();
      expect(screen.getByText('Responsibility')).toBeInTheDocument();
    });
  });

  it('requires justification to enable evil mode', async () => {
    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    fireEvent.click(screen.getByText('Enable Evil Mode'));

    await waitFor(() => {
      const enableButton = screen.getByRole('button', { name: 'Enable Evil Mode' });
      expect(enableButton).toBeDisabled();
    });

    const justificationInput = screen.getByPlaceholderText('Provide a detailed justification for enabling Evil Mode...');
    fireEvent.change(justificationInput, { target: { value: 'Emergency maintenance required' } });

    // Still disabled because additional auth and acknowledgment are required
    await waitFor(() => {
      const enableButton = screen.getByRole('button', { name: 'Enable Evil Mode' });
      expect(enableButton).toBeDisabled();
    });
  });

  it('requires additional authentication when configured', async () => {
    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    fireEvent.click(screen.getByText('Enable Evil Mode'));

    await waitFor(() => {
      expect(screen.getByText('Additional Authentication')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your password to confirm')).toBeInTheDocument();
    });
  });

  it('requires acknowledgment checkbox to be checked', async () => {
    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    fireEvent.click(screen.getByText('Enable Evil Mode'));

    await waitFor(() => {
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).not.toBeChecked();
      
      const enableButton = screen.getByRole('button', { name: 'Enable Evil Mode' });
      expect(enableButton).toBeDisabled();
    });
  });

  it('enables evil mode when all requirements are met', async () => {
    const mockEnableEvilMode = vi.fn().mockResolvedValue(undefined);
    mockUseRBAC.mockReturnValue({
      ...mockRBACContext,
      enableEvilMode: mockEnableEvilMode
    });

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    fireEvent.click(screen.getByText('Enable Evil Mode'));

    await waitFor(() => {
      // Fill in justification
      const justificationInput = screen.getByPlaceholderText('Provide a detailed justification for enabling Evil Mode...');
      fireEvent.change(justificationInput, { target: { value: 'Emergency maintenance required' } });

      // Fill in additional auth
      const authInput = screen.getByPlaceholderText('Enter your password to confirm');
      fireEvent.change(authInput, { target: { value: 'password123' } });

      // Check acknowledgment
      const checkbox = screen.getByRole('checkbox');
      fireEvent.click(checkbox);
    });

    await waitFor(() => {
      const enableButton = screen.getByRole('button', { name: 'Enable Evil Mode' });
      expect(enableButton).not.toBeDisabled();
      
      fireEvent.click(enableButton);
    });

    await waitFor(() => {
      expect(mockEnableEvilMode).toHaveBeenCalledWith('Emergency maintenance required');
      expect(mockAuditLogger.logAuthz).toHaveBeenCalledWith(
        'authz:evil_mode_enabled',
        'system',
        'success',
        expect.objectContaining({
          justification: 'Emergency maintenance required',
          additionalAuth: true,
          timeLimit: 60
        })
      );
    });
  });

  it('opens disable dialog when disable button is clicked', async () => {
    mockUseRBAC.mockReturnValue({
      ...mockRBACContext,
      isEvilModeEnabled: true,
      evilModeSession: {
        userId: 'user-1',
        sessionId: 'session-1',
        startTime: new Date(),
        actions: [],
        justification: 'Test justification'
      }
    });

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    fireEvent.click(screen.getByText('Disable'));

    await waitFor(() => {
      expect(screen.getByText('Disable Evil Mode?')).toBeInTheDocument();
      expect(screen.getByText(/This will immediately revoke all elevated privileges/)).toBeInTheDocument();
    });
  });

  it('disables evil mode when confirmed', async () => {
    const mockDisableEvilMode = vi.fn().mockResolvedValue(undefined);
    mockUseRBAC.mockReturnValue({
      ...mockRBACContext,
      isEvilModeEnabled: true,
      disableEvilMode: mockDisableEvilMode,
      evilModeSession: {
        userId: 'user-1',
        sessionId: 'session-1',
        startTime: new Date(Date.now() - 1800000), // 30 minutes ago
        actions: [],
        justification: 'Test justification'
      }
    });

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    fireEvent.click(screen.getByText('Disable'));

    await waitFor(() => {
      const disableButton = screen.getByText('Disable Evil Mode');
      fireEvent.click(disableButton);
    });

    await waitFor(() => {
      expect(mockDisableEvilMode).toHaveBeenCalled();
      expect(mockAuditLogger.logAuthz).toHaveBeenCalledWith(
        'authz:evil_mode_disabled',
        'system',
        'success',
        expect.objectContaining({
          sessionDuration: expect.any(Number)
        })
      );
    });
  });

  it('shows time limit warning when configured', async () => {
    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    fireEvent.click(screen.getByText('Enable Evil Mode'));

    await waitFor(() => {
      expect(screen.getByText(/Evil Mode will automatically expire after 60 minutes/)).toBeInTheDocument();
    });
  });

  it('displays remaining time when evil mode is active', () => {
    const startTime = new Date(Date.now() - 30 * 60 * 1000); // 30 minutes ago
    mockUseRBAC.mockReturnValue({
      ...mockRBACContext,
      isEvilModeEnabled: true,
      evilModeSession: {
        userId: 'user-1',
        sessionId: 'session-1',
        startTime,
        actions: [],
        justification: 'Test justification'
      }
    });

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EvilModeToggle />
      </Wrapper>
    );

    expect(screen.getByText('30m left')).toBeInTheDocument();
  });
});