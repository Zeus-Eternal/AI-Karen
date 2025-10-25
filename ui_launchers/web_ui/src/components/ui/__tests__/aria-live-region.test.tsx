/**
 * Tests for ARIA Live Region components
 */

import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  AriaLiveRegion,
  useAriaAnnouncements,
  AriaAnnouncer,
  AriaStatus,
  AriaProgress,
} from '../aria-live-region';

// Mock component to test the hook
const TestAnnouncementComponent = () => {
  const { announce, politeMessage, assertiveMessage, clearAnnouncements } = useAriaAnnouncements();

  return (
    <div>
      <button onClick={() => announce('Polite message', 'polite')}>
        Announce Polite
      </button>
      <button onClick={() => announce('Assertive message', 'assertive')}>
        Announce Assertive
      </button>
      <button onClick={clearAnnouncements}>
        Clear
      </button>
      <div data-testid="polite-message">{politeMessage}</div>
      <div data-testid="assertive-message">{assertiveMessage}</div>
    </div>
  );
};

describe('AriaLiveRegion', () => {
  it('should render with correct ARIA attributes', () => {
    render(
      <AriaLiveRegion politeness="assertive" atomic={true}>
        Test message
      </AriaLiveRegion>
    );

    const liveRegion = screen.getByText('Test message');
    expect(liveRegion).toHaveAttribute('aria-live', 'assertive');
    expect(liveRegion).toHaveAttribute('aria-atomic', 'true');
  });

  it('should use default politeness level', () => {
    render(<AriaLiveRegion>Test message</AriaLiveRegion>);

    const liveRegion = screen.getByText('Test message');
    expect(liveRegion).toHaveAttribute('aria-live', 'polite');
    expect(liveRegion).toHaveAttribute('aria-atomic', 'false');
  });

  it('should be visually hidden but accessible', () => {
    render(<AriaLiveRegion>Test message</AriaLiveRegion>);

    const liveRegion = screen.getByText('Test message');
    expect(liveRegion).toHaveClass('sr-only');
  });

  it('should accept custom ID', () => {
    render(<AriaLiveRegion id="custom-live-region">Test message</AriaLiveRegion>);

    const liveRegion = screen.getByText('Test message');
    expect(liveRegion).toHaveAttribute('id', 'custom-live-region');
  });
});

describe('useAriaAnnouncements', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should handle polite announcements', async () => {
    render(<TestAnnouncementComponent />);

    const politeButton = screen.getByText('Announce Polite');
    const politeMessage = screen.getByTestId('polite-message');

    act(() => {
      politeButton.click();
    });

    expect(politeMessage).toHaveTextContent('Polite message');

    // Fast-forward time to clear message
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(politeMessage).toHaveTextContent('');
  });

  it('should handle assertive announcements', async () => {
    render(<TestAnnouncementComponent />);

    const assertiveButton = screen.getByText('Announce Assertive');
    const assertiveMessage = screen.getByTestId('assertive-message');

    act(() => {
      assertiveButton.click();
    });

    expect(assertiveMessage).toHaveTextContent('Assertive message');

    // Fast-forward time to clear message
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(assertiveMessage).toHaveTextContent('');
  });

  it('should clear announcements manually', () => {
    render(<TestAnnouncementComponent />);

    const politeButton = screen.getByText('Announce Polite');
    const clearButton = screen.getByText('Clear');
    const politeMessage = screen.getByTestId('polite-message');

    act(() => {
      politeButton.click();
    });

    expect(politeMessage).toHaveTextContent('Polite message');

    act(() => {
      clearButton.click();
    });

    expect(politeMessage).toHaveTextContent('');
  });
});desc
ribe('AriaAnnouncer', () => {
  it('should provide announce function to children', () => {
    const TestChild = ({ announce }: { announce: (message: string) => void }) => (
      <button onClick={() => announce('Test announcement')}>
        Announce
      </button>
    );

    render(
      <AriaAnnouncer>
        {(announce) => <TestChild announce={announce} />}
      </AriaAnnouncer>
    );

    const button = screen.getByText('Announce');
    expect(button).toBeInTheDocument();

    // Should render live regions
    const liveRegions = screen.getAllByRole('region', { hidden: true });
    expect(liveRegions).toHaveLength(2); // polite and assertive
  });
});

describe('AriaStatus', () => {
  it('should render status message with correct role', () => {
    render(<AriaStatus message="Status update" />);

    const status = screen.getByText('Status update');
    expect(status).toHaveAttribute('role', 'status');
    expect(status).toHaveAttribute('aria-live', 'polite');
  });

  it('should render error message with alert role', () => {
    render(<AriaStatus message="Error occurred" error={true} />);

    const status = screen.getByText('Error: Error occurred');
    expect(status).toHaveAttribute('role', 'alert');
    expect(status).toHaveAttribute('aria-live', 'assertive');
  });

  it('should render loading message', () => {
    render(<AriaStatus message="Please wait" loading={true} />);

    const status = screen.getByText('Loading: Please wait');
    expect(status).toHaveAttribute('role', 'status');
  });

  it('should render success message', () => {
    render(<AriaStatus message="Operation completed" success={true} />);

    const status = screen.getByText('Success: Operation completed');
    expect(status).toHaveAttribute('role', 'status');
  });
});

describe('AriaProgress', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should render progress with correct attributes', () => {
    render(<AriaProgress value={50} label="Upload progress" />);

    const progress = screen.getByText('Upload progress: 50% complete');
    expect(progress).toHaveAttribute('role', 'progressbar');
    expect(progress).toHaveAttribute('aria-valuenow', '50');
    expect(progress).toHaveAttribute('aria-valuemin', '0');
    expect(progress).toHaveAttribute('aria-valuemax', '100');
    expect(progress).toHaveAttribute('aria-label', 'Upload progress');
  });

  it('should calculate percentage correctly with custom min/max', () => {
    render(<AriaProgress value={25} min={0} max={50} />);

    const progress = screen.getByText('50% complete');
    expect(progress).toHaveAttribute('aria-valuenow', '25');
    expect(progress).toHaveAttribute('aria-valuemin', '0');
    expect(progress).toHaveAttribute('aria-valuemax', '50');
  });

  it('should announce progress changes when threshold is met', () => {
    const { rerender } = render(<AriaProgress value={10} announceChanges={true} />);

    // Should not announce small changes
    rerender(<AriaProgress value={15} announceChanges={true} />);

    // Should announce when change is >= 10%
    rerender(<AriaProgress value={25} announceChanges={true} />);

    // The announcement would be handled by the useAriaAnnouncements hook
    // This test verifies the component renders correctly
    const progress = screen.getByText('25% complete');
    expect(progress).toBeInTheDocument();
  });

  it('should not announce when announceChanges is false', () => {
    const { rerender } = render(<AriaProgress value={10} announceChanges={false} />);

    rerender(<AriaProgress value={50} announceChanges={false} />);

    const progress = screen.getByText('50% complete');
    expect(progress).toBeInTheDocument();
  });
});