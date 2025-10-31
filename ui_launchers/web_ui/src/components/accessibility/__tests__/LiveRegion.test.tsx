/**
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { LiveRegion, useLiveRegion } from '../LiveRegion';

describe('LiveRegion', () => {
  it('renders with default props', () => {
    render(<LiveRegion message="Test message" />);

    const region = screen.getByText('Test message');
    expect(region).toBeInTheDocument();
    expect(region).toHaveAttribute('aria-live', 'polite');
    expect(region).toHaveAttribute('aria-atomic', 'true');
    expect(region).toHaveAttribute('aria-relevant', 'all');
  });

  it('renders with custom politeness', () => {
    render(<LiveRegion message="Urgent message" politeness="assertive" />);

    const region = screen.getByText('Urgent message');
    expect(region).toHaveAttribute('aria-live', 'assertive');
  });

  it('renders with custom atomic setting', () => {
    render(<LiveRegion message="Test message" atomic={false} />);

    const region = screen.getByText('Test message');
    expect(region).toHaveAttribute('aria-atomic', 'false');
  });

  it('renders with custom relevant setting', () => {
    render(<LiveRegion message="Test message" relevant="additions" />);

    const region = screen.getByText('Test message');
    expect(region).toHaveAttribute('aria-relevant', 'additions');
  });

  it('renders with custom id', () => {
    render(<LiveRegion message="Test message" id="custom-live-region" />);

    const region = screen.getByText('Test message');
    expect(region).toHaveAttribute('id', 'custom-live-region');
  });

  it('renders children instead of message', () => {
    render(
      <LiveRegion>
        <span>Child content</span>
      </LiveRegion>
    );

    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  it('applies screen reader only styles', () => {
    render(<LiveRegion message="Test message" />);

    const region = screen.getByText('Test message');
    expect(region).toHaveClass('sr-only', 'absolute');
  });

  it('applies custom className', () => {
    render(<LiveRegion message="Test message" className="custom-class" />);

    const region = screen.getByText('Test message');
    expect(region).toHaveClass('custom-class');
  });

  it('updates message content', async () => {
    const { rerender } = render(<LiveRegion message="Initial message" />);

    expect(screen.getByText('Initial message')).toBeInTheDocument();

    rerender(<LiveRegion message="Updated message" />);

    // The component clears and then sets the message with a delay
    await waitFor(() => {
      expect(screen.getByText('Updated message')).toBeInTheDocument();
    }, { timeout: 200 });
  });

  it('handles empty message', () => {
    render(<LiveRegion message="" />);

    const region = screen.getByRole('status', { hidden: true });
    expect(region).toBeInTheDocument();
    expect(region).toBeEmptyDOMElement();
  });

  it('handles politeness off', () => {
    render(<LiveRegion message="Test message" politeness="off" />);

    const region = screen.getByText('Test message');
    expect(region).toHaveAttribute('aria-live', 'off');
  });
});

describe('useLiveRegion', () => {
  function TestComponent({ politeness }: { politeness?: 'polite' | 'assertive' }) {
    const { announce, LiveRegionComponent } = useLiveRegion(politeness);

    return (
      <div>
        <button onClick={() => announce('Test announcement')}>
          Announce
        </button>
        <LiveRegionComponent />
      </div>
    );
  }

  it('creates live region component', () => {
    render(<TestComponent />);

    const button = screen.getByText('Announce');
    expect(button).toBeInTheDocument();

    // The live region should be present but hidden
    const liveRegion = document.querySelector('[aria-live="polite"]');
    expect(liveRegion).toBeInTheDocument();
  });

  it('uses custom politeness', () => {
    render(<TestComponent politeness="assertive" />);

    const liveRegion = document.querySelector('[aria-live="assertive"]');
    expect(liveRegion).toBeInTheDocument();
  });

  it('announces messages', async () => {
    render(<TestComponent />);

    const button = screen.getByText('Announce');
    const liveRegion = document.querySelector('[aria-live="polite"]');

    expect(liveRegion).toBeEmptyDOMElement();

    // Click to announce
    button.click();

    // Message should appear after delay
    await waitFor(() => {
      expect(liveRegion).toHaveTextContent('Test announcement');
    }, { timeout: 200 });
  });

  it('applies custom className to live region', () => {
    function TestWithClassName() {
      const { LiveRegionComponent } = useLiveRegion();
      return <LiveRegionComponent className="custom-live-region" />;
    }

    render(<TestWithClassName />);

    const liveRegion = document.querySelector('[aria-live="polite"]');
    expect(liveRegion).toHaveClass('custom-live-region');
  });

  it('clears previous messages before announcing new ones', async () => {
    render(<TestComponent />);

    const button = screen.getByText('Announce');
    const liveRegion = document.querySelector('[aria-live="polite"]');

    // First announcement
    button.click();
    await waitFor(() => {
      expect(liveRegion).toHaveTextContent('Test announcement');
    });

    // Second announcement should clear first
    button.click();
    
    // Should be cleared initially
    expect(liveRegion).toHaveTextContent('');
    
    // Then show new message
    await waitFor(() => {
      expect(liveRegion).toHaveTextContent('Test announcement');
    }, { timeout: 200 });
  });
});