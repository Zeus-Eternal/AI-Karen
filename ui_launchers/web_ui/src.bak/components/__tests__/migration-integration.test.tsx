import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SanitizedMarkdown } from '../security/SanitizedMarkdown';
import { RBACGuard } from '../security/RBACGuard';
import { ErrorToast } from '../error/ErrorToast';

// Mock dependencies
vi.mock('@/hooks/use-telemetry', () => ({
  useTelemetry: () => ({
    track: vi.fn(),
  }),
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      user_id: 'test-user',
      roles: ['user'],
    },
    isAuthenticated: true,
  }),
}));

describe('Migration Integration Tests', () => {
  it('SanitizedMarkdown renders without errors', () => {
    render(
      <SanitizedMarkdown 
        content="# Test Content\n\nThis is a **test** with [link](https://example.com)" 
      />
    );
    
    // Check that the content is rendered (text might be split across elements)
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    expect(screen.getByText('test')).toBeInTheDocument();
    expect(screen.getByText('link')).toBeInTheDocument();
  });

  it('RBACGuard allows access for authenticated users', () => {
    render(
      <RBACGuard requiredRole="user">
        <div>Protected Content</div>
      </RBACGuard>
    );
    
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('ErrorToast displays error messages', () => {
    render(
      <ErrorToast
        message="Test error message"
        type="error"
        onClose={vi.fn()}
      />
    );
    
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('Components can be used together', () => {
    render(
      <RBACGuard requiredRole="user">
        <div>
          <SanitizedMarkdown content="# Protected Content" />
          <ErrorToast
            message="Info message"
            type="info"
            onClose={vi.fn()}
          />
        </div>
      </RBACGuard>
    );
    
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
    expect(screen.getByText('Info message')).toBeInTheDocument();
  });
});

describe('Telemetry Integration', () => {
  it('components use telemetry without errors', () => {
    // This test verifies that the telemetry integration doesn't break component rendering
    expect(() => {
      render(
        <div>
          <SanitizedMarkdown content="Test content" />
          <ErrorToast message="Test message" type="info" onClose={vi.fn()} />
        </div>
      );
    }).not.toThrow();
  });
});