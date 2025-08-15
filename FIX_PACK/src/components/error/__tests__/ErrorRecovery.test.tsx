import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { 
  ErrorRecovery, 
  createRetryAction, 
  createReloadAction, 
  createGoBackAction, 
  createContactSupportAction,
  createReportIssueAction 
} from '../ErrorRecovery';
import { telemetryService } from '../../../lib/telemetry';

// Mock telemetry service
vi.mock('../../../lib/telemetry', () => ({
  telemetryService: {
    track: vi.fn(),
  },
}));

describe('ErrorRecovery', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders basic error recovery correctly', () => {
    const actions = [
      {
        id: 'retry',
        label: 'Try Again',
        action: vi.fn(),
      },
    ];

    render(
      <ErrorRecovery
        title="Something went wrong"
        message="Please try again"
        actions={actions}
      />
    );

    expect(screen.getByRole('region')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Please try again')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('renders compact version correctly', () => {
    const actions = [
      {
        id: 'retry',
        label: 'Retry',
        action: vi.fn(),
      },
    ];

    render(
      <ErrorRecovery
        actions={actions}
        compact={true}
      />
    );

    expect(screen.getByRole('region')).toHaveClass('error-recovery--compact');
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
  });

  it('handles action clicks and tracks telemetry', async () => {
    const mockAction = vi.fn();
    const actions = [
      {
        id: 'test-action',
        label: 'Test Action',
        action: mockAction,
      },
    ];

    render(
      <ErrorRecovery
        actions={actions}
        errorId="test-error"
        correlationId="test-correlation"
      />
    );

    const actionButton = screen.getByText('Test Action');
    fireEvent.click(actionButton);

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error_recovery.action_clicked',
      expect.objectContaining({
        actionId: 'test-action',
        actionLabel: 'Test Action',
        errorId: 'test-error',
        correlationId: 'test-correlation',
      }),
      'test-correlation'
    );

    await waitFor(() => {
      expect(mockAction).toHaveBeenCalled();
    });

    expect(telemetryService.track).toHaveBeenCalledWith(
      'error_recovery.action_completed',
      expect.objectContaining({
        actionId: 'test-action',
        actionLabel: 'Test Action',
      }),
      'test-correlation'
    );
  });

  it('handles async action failures', async () => {
    const failingAction = vi.fn().mockRejectedValue(new Error('Action failed'));
    const actions = [
      {
        id: 'failing-action',
        label: 'Failing Action',
        action: failingAction,
      },
    ];

    render(
      <ErrorRecovery
        actions={actions}
        errorId="test-error"
        correlationId="test-correlation"
      />
    );

    const actionButton = screen.getByText('Failing Action');
    fireEvent.click(actionButton);

    await waitFor(() => {
      expect(telemetryService.track).toHaveBeenCalledWith(
        'error_recovery.action_failed',
        expect.objectContaining({
          actionId: 'failing-action',
          actionLabel: 'Failing Action',
          error: 'Action failed',
        }),
        'test-correlation'
      );
    });
  });

  it('shows loading state during async actions', async () => {
    const slowAction = vi.fn().mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 100))
    );
    
    const actions = [
      {
        id: 'slow-action',
        label: 'Slow Action',
        action: slowAction,
      },
    ];

    render(<ErrorRecovery actions={actions} />);

    const actionButton = screen.getByText('Slow Action');
    fireEvent.click(actionButton);

    expect(actionButton).toBeDisabled();
    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument(); // Spinner

    await waitFor(() => {
      expect(actionButton).not.toBeDisabled();
    });
  });

  it('handles pre-loading actions', () => {
    const actions = [
      {
        id: 'loading-action',
        label: 'Loading Action',
        action: vi.fn(),
        loading: true,
      },
    ];

    render(<ErrorRecovery actions={actions} />);

    const actionButton = screen.getByText('Loading Action');
    expect(actionButton).toBeDisabled();
    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument(); // Spinner
  });

  it('handles disabled actions', () => {
    const actions = [
      {
        id: 'disabled-action',
        label: 'Disabled Action',
        action: vi.fn(),
        disabled: true,
      },
    ];

    render(<ErrorRecovery actions={actions} />);

    const actionButton = screen.getByText('Disabled Action');
    expect(actionButton).toBeDisabled();
    
    fireEvent.click(actionButton);
    expect(actions[0].action).not.toHaveBeenCalled();
  });

  it('renders action variants correctly', () => {
    const actions = [
      {
        id: 'primary',
        label: 'Primary Action',
        action: vi.fn(),
        variant: 'primary' as const,
      },
      {
        id: 'secondary',
        label: 'Secondary Action',
        action: vi.fn(),
        variant: 'secondary' as const,
      },
      {
        id: 'danger',
        label: 'Danger Action',
        action: vi.fn(),
        variant: 'danger' as const,
      },
    ];

    render(<ErrorRecovery actions={actions} />);

    expect(screen.getByText('Primary Action')).toHaveClass('error-recovery__action--primary');
    expect(screen.getByText('Secondary Action')).toHaveClass('error-recovery__action--secondary');
    expect(screen.getByText('Danger Action')).toHaveClass('error-recovery__action--danger');
  });

  it('renders action icons and descriptions', () => {
    const actions = [
      {
        id: 'icon-action',
        label: 'Icon Action',
        description: 'This action has an icon',
        icon: <span data-testid="custom-icon">🔄</span>,
        action: vi.fn(),
      },
    ];

    render(<ErrorRecovery actions={actions} />);

    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    expect(screen.getByText('This action has an icon')).toBeInTheDocument();
  });

  it('hides descriptions in compact mode', () => {
    const actions = [
      {
        id: 'desc-action',
        label: 'Action with Description',
        description: 'This description should be hidden',
        action: vi.fn(),
      },
    ];

    render(<ErrorRecovery actions={actions} compact={true} />);

    expect(screen.getByText('Action with Description')).toBeInTheDocument();
    expect(screen.queryByText('This description should be hidden')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <ErrorRecovery
        actions={[]}
        className="custom-recovery-class"
      />
    );

    expect(screen.getByRole('region')).toHaveClass('custom-recovery-class');
  });

  it('has correct accessibility attributes', () => {
    const actions = [
      {
        id: 'accessible-action',
        label: 'Accessible Action',
        description: 'Action description',
        action: vi.fn(),
      },
    ];

    render(<ErrorRecovery actions={actions} />);

    const region = screen.getByRole('region');
    expect(region).toHaveAttribute('aria-labelledby', 'error-recovery-title');

    const actionButton = screen.getByText('Accessible Action');
    expect(actionButton).toHaveAttribute('aria-describedby', 'accessible-action-description');
  });
});

describe('Predefined Actions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('creates retry action correctly', () => {
    const onRetry = vi.fn();
    const retryAction = createRetryAction(onRetry);

    expect(retryAction.id).toBe('retry');
    expect(retryAction.label).toBe('Try Again');
    expect(retryAction.variant).toBe('primary');
    expect(retryAction.action).toBe(onRetry);
  });

  it('creates reload action correctly', () => {
    const reloadSpy = vi.spyOn(window.location, 'reload').mockImplementation(() => {});
    
    const reloadAction = createReloadAction();
    reloadAction.action();

    expect(reloadSpy).toHaveBeenCalled();
    expect(reloadAction.id).toBe('reload');
    expect(reloadAction.label).toBe('Reload Page');
    
    reloadSpy.mockRestore();
  });

  it('creates go back action correctly', () => {
    const backSpy = vi.spyOn(window.history, 'back').mockImplementation(() => {});
    
    const goBackAction = createGoBackAction();
    goBackAction.action();

    expect(backSpy).toHaveBeenCalled();
    expect(goBackAction.id).toBe('go-back');
    expect(goBackAction.label).toBe('Go Back');
    
    backSpy.mockRestore();
  });

  it('creates contact support action correctly', () => {
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    
    const supportAction = createContactSupportAction('https://support.example.com');
    supportAction.action();

    expect(openSpy).toHaveBeenCalledWith(
      'https://support.example.com',
      '_blank',
      'noopener,noreferrer'
    );
    expect(supportAction.id).toBe('contact-support');
    expect(supportAction.label).toBe('Contact Support');
    
    openSpy.mockRestore();
  });

  it('creates report issue action correctly', () => {
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    
    const errorDetails = { error: 'Test error', stack: 'Test stack' };
    const reportAction = createReportIssueAction('https://report.example.com', errorDetails);
    reportAction.action();

    expect(openSpy).toHaveBeenCalledWith(
      expect.stringContaining('https://report.example.com?error='),
      '_blank',
      'noopener,noreferrer'
    );
    expect(reportAction.id).toBe('report-issue');
    expect(reportAction.label).toBe('Report Issue');
    
    openSpy.mockRestore();
  });

  it('allows overriding predefined action options', () => {
    const customRetryAction = createRetryAction(vi.fn(), {
      label: 'Custom Retry',
      variant: 'danger',
      disabled: true,
    });

    expect(customRetryAction.label).toBe('Custom Retry');
    expect(customRetryAction.variant).toBe('danger');
    expect(customRetryAction.disabled).toBe(true);
  });
});