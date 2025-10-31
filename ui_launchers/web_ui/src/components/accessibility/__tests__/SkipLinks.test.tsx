/**
 * @vitest-environment jsdom
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { SkipLinks } from '../SkipLinks';

describe('SkipLinks', () => {
  beforeEach(() => {
    // Mock querySelector to simulate target elements
    document.querySelector = vi.fn((selector) => {
      if (selector === '#main-content' || selector === '#navigation' || selector === '#search') {
        return document.createElement('div');
      }
      return null;
    });
  });

  it('renders default skip links', () => {
    render(<SkipLinks />);

    expect(screen.getByText('Skip to main content')).toBeInTheDocument();
    expect(screen.getByText('Skip to navigation')).toBeInTheDocument();
    expect(screen.getByText('Skip to search')).toBeInTheDocument();
  });

  it('renders custom skip links', () => {
    const customLinks = [
      { href: '#custom-main', label: 'Skip to custom main' },
      { href: '#custom-nav', label: 'Skip to custom navigation' },
    ];

    render(<SkipLinks links={customLinks} />);

    expect(screen.getByText('Skip to custom main')).toBeInTheDocument();
    expect(screen.getByText('Skip to custom navigation')).toBeInTheDocument();
    expect(screen.queryByText('Skip to main content')).not.toBeInTheDocument();
  });

  it('has correct href attributes', () => {
    render(<SkipLinks />);

    const mainLink = screen.getByText('Skip to main content');
    const navLink = screen.getByText('Skip to navigation');
    const searchLink = screen.getByText('Skip to search');

    expect(mainLink).toHaveAttribute('href', '#main-content');
    expect(navLink).toHaveAttribute('href', '#navigation');
    expect(searchLink).toHaveAttribute('href', '#search');
  });

  it('applies correct CSS classes', () => {
    render(<SkipLinks />);

    const links = screen.getAllByRole('link');
    
    links.forEach(link => {
      expect(link).toHaveClass('absolute', 'left-4', 'top-4', 'z-[9999]');
      expect(link).toHaveClass('-translate-y-full', 'opacity-0');
      expect(link).toHaveClass('focus:translate-y-0', 'focus:opacity-100');
    });
  });

  it('applies custom className', () => {
    render(<SkipLinks className="custom-class" />);

    const container = screen.getAllByRole('link')[0].parentElement;
    expect(container).toHaveClass('custom-class');
  });

  it('sets tabindex on target elements when focused', () => {
    const mockElement = document.createElement('div');
    mockElement.setAttribute = vi.fn();
    
    document.querySelector = vi.fn(() => mockElement);

    render(<SkipLinks />);

    const mainLink = screen.getByText('Skip to main content');
    fireEvent.focus(mainLink);

    expect(mockElement.setAttribute).toHaveBeenCalledWith('tabindex', '-1');
  });

  it('handles missing target elements gracefully', () => {
    document.querySelector = vi.fn(() => null);

    render(<SkipLinks />);

    const mainLink = screen.getByText('Skip to main content');
    
    // Should not throw error when target doesn't exist
    expect(() => {
      fireEvent.focus(mainLink);
    }).not.toThrow();
  });

  it('is keyboard accessible', () => {
    render(<SkipLinks />);

    const links = screen.getAllByRole('link');
    
    links.forEach(link => {
      // Links are keyboard accessible by default, no need for explicit tabIndex
      expect(link.tagName).toBe('A');
      expect(link).toHaveAttribute('href');
    });
  });

  it('has proper focus management', () => {
    render(<SkipLinks />);

    const mainLink = screen.getByText('Skip to main content');
    
    // Initially hidden
    expect(mainLink).toHaveClass('-translate-y-full', 'opacity-0');
    
    // Should become visible on focus (handled by CSS)
    expect(mainLink).toHaveClass('focus:translate-y-0', 'focus:opacity-100');
  });

  it('supports high contrast mode', () => {
    render(<SkipLinks />);

    const links = screen.getAllByRole('link');
    
    links.forEach(link => {
      expect(link).toHaveClass('high-contrast:bg-black', 'high-contrast:text-white', 'high-contrast:border-white');
    });
  });
});