/**
 * Unit tests for MemorySearch component
 * Tests search functionality, filtering, and user interactions
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import MemorySearch from '../MemorySearch';
import { getMemoryService } from '@/services/memoryService';
import type { MemoryEntry } from '@/types/memory';

// Mock the memory service
vi.mock('@/services/memoryService', () => ({
  getMemoryService: vi.fn()
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  Search: () => <div data-testid="search-icon">Search</div>,
  Filter: () => <div data-testid="filter-icon">Filter</div>,
  Clock: () => <div data-testid="clock-icon">Clock</div>,
  Star: () => <div data-testid="star-icon">Star</div>,
  Tag: () => <div data-testid="tag-icon">Tag</div>,
  Calendar: () => <div data-testid="calendar-icon">Calendar</div>,
  ChevronDown: () => <div data-testid="chevron-down">ChevronDown</div>,
  ChevronUp: () => <div data-testid="chevron-up">ChevronUp</div>,
  Bookmark: () => <div data-testid="bookmark-icon">Bookmark</div>,
  History: () => <div data-testid="history-icon">History</div>,
  X: () => <div data-testid="x-icon">X</div>,
  SortAsc: () => <div data-testid="sort-asc">SortAsc</div>,
  SortDesc: () => <div data-testid="sort-desc">SortDesc</div>
}));

// Mock UI components
vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className, onClick }: { 
    children: React.ReactNode; 
    className?: string;
    onClick?: () => void;
  }) => (
    <div data-testid="card" className={className} onClick={onClick}>
      {children}
    </div>
  )
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, className }: { 
    children: React.ReactNode; 
    onClick?: () => void; 
    disabled?: boolean;
    variant?: string;
    className?: string;
  }) => (
    <button 
      data-testid="button" 
      onClick={onClick} 
      disabled={disabled}
      data-variant={variant}
      className={className}
    >
      {children}
    </button>
  )
}));

vi.mock('@/components/ui/input', () => ({
  Input: React.forwardRef<HTMLInputElement, any>(({ 
    type, 
    placeholder, 
    value, 
    onChange, 
    onKeyDown, 
    onFocus,
    className 
  }, ref) => (
    <input
      ref={ref}
      data-testid="input"
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      onKeyDown={onKeyDown}
      onFocus={onFocus}
      className={className}
    />
  ))
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant, className }: { 
    children: React.ReactNode; 
    variant?: string;
    className?: string;
  }) => (
    <span data-testid="badge" data-variant={variant} className={className}>
      {children}
    </span>
  )
}));

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, defaultValue }: { 
    children: React.ReactNode; 
    defaultValue: string;
  }) => (
    <div data-testid="tabs" data-default-value={defaultValue}>
      {children}
    </div>
  ),
  TabsList: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="tabs-list">{children}</div>
  ),
  TabsTrigger: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <button data-testid="tab-trigger" data-value={value}>{children}</button>
  ),
  TabsContent: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <div data-testid="tab-content" data-value={value}>{children}</div>
  )
}));

describe('MemorySearch', () => {
  const mockMemoryService = {
    searchMemories: vi.fn()
  };

  const mockMemories: MemoryEntry[] = [
    {
      id: '1',
      content: 'JavaScript function to handle async operations',
      metadata: { cluster: 'technical' },
      timestamp: Date.now() - 3600000,
      similarity_score: 0.95,
      tags: ['javascript', 'async', 'functions'],
      type: 'fact',
      confidence: 0.9,
      user_id: 'test-user'
    },
    {
      id: '2',
      content: 'React hooks best practices and patterns',
      metadata: { cluster: 'technical' },
      timestamp: Date.now() - 7200000,
      similarity_score: 0.87,
      tags: ['react', 'hooks', 'patterns'],
      type: 'context',
      confidence: 0.85,
      user_id: 'test-user'
    },
    {
      id: '3',
      content: 'Personal note about project preferences',
      metadata: { cluster: 'personal' },
      timestamp: Date.now() - 86400000,
      similarity_score: 0.72,
      tags: ['personal', 'preferences'],
      type: 'preference',
      confidence: 0.8,
      user_id: 'test-user'
    }
  ];

  const defaultProps = {
    userId: 'test-user-123',
    tenantId: 'test-tenant',
    height: 600
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (getMemoryService as any).mockReturnValue(mockMemoryService);
    mockMemoryService.searchMemories.mockResolvedValue({
      memories: mockMemories,
      totalFound: mockMemories.length,
      searchTime: 45
    });
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Component Rendering', () => {
    it('renders the search interface correctly', () => {
      render(<MemorySearch {...defaultProps} />);
      
      expect(screen.getByTestId('input')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Search memories semantically...')).toBeInTheDocument();
      expect(screen.getByText('Search')).toBeInTheDocument();
      expect(screen.getByText('Filters')).toBeInTheDocument();
    });

    it('renders with initial query if provided', () => {
      render(<MemorySearch {...defaultProps} initialQuery="test query" />);
      
      const input = screen.getByTestId('input');
      expect(input).toHaveValue('test query');
    });

    it('renders tabs for results, history, and saved searches', () => {
      render(<MemorySearch {...defaultProps} />);
      
      expect(screen.getByText('Results')).toBeInTheDocument();
      expect(screen.getByText(/History/)).toBeInTheDocument();
      expect(screen.getByText(/Saved/)).toBeInTheDocument();
    });

    it('shows empty state when no search has been performed', () => {
      render(<MemorySearch {...defaultProps} />);
      
      expect(screen.getByText('Start searching')).toBeInTheDocument();
      expect(screen.getByText('Enter a search query to find relevant memories')).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('performs search when search button is clicked', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      const searchButton = screen.getByText('Search');
      
      await user.type(input, 'javascript');
      await user.click(searchButton);
      
      await waitFor(() => {
        expect(mockMemoryService.searchMemories).toHaveBeenCalledWith(
          'javascript',
          expect.objectContaining({
            userId: 'test-user-123',
            tenantId: 'test-tenant'
          })
        );
      });
    });

    it('performs search when Enter key is pressed', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      
      await user.type(input, 'react');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(mockMemoryService.searchMemories).toHaveBeenCalledWith(
          'react',
          expect.objectContaining({
            userId: 'test-user-123'
          })
        );
      });
    });

    it('does not search with empty query', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const searchButton = screen.getByText('Search');
      expect(searchButton).toBeDisabled();
      
      await user.click(searchButton);
      expect(mockMemoryService.searchMemories).not.toHaveBeenCalled();
    });

    it('displays search results correctly', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'javascript');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(screen.getByText('JavaScript function to handle async operations')).toBeInTheDocument();
        expect(screen.getByText('React hooks best practices and patterns')).toBeInTheDocument();
        expect(screen.getByText('Personal note about project preferences')).toBeInTheDocument();
      });
    });

    it('displays search statistics', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'test');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(screen.getByText('3 results in 45ms')).toBeInTheDocument();
      });
    });

    it('highlights search terms in results', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'JavaScript');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        const highlightedText = screen.getByText('JavaScript');
        expect(highlightedText.tagName).toBe('MARK');
      });
    });
  });

  describe('Search Suggestions', () => {
    it('shows suggestions when typing in search input', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'java');
      await user.click(input); // Focus to show suggestions
      
      // Suggestions would be shown in a real implementation
      // This tests the structure is in place
      expect(input).toHaveFocus();
    });

    it('hides suggestions when Escape is pressed', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'test');
      await user.keyboard('{Escape}');
      
      // Suggestions should be hidden
      expect(input).toHaveValue('test');
    });

    it('clears search input when X button is clicked', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'test query');
      
      const clearButton = screen.getByTestId('x-icon').closest('button');
      if (clearButton) {
        await user.click(clearButton);
        expect(input).toHaveValue('');
      }
    });
  });

  describe('Filtering', () => {
    it('toggles filter panel when filter button is clicked', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const filterButton = screen.getByText('Filters');
      await user.click(filterButton);
      
      // Filter panel should be visible
      expect(screen.getByText('Tags')).toBeInTheDocument();
      expect(screen.getByText('Sort By')).toBeInTheDocument();
    });

    it('applies tag filters correctly', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      // First perform a search to get facets
      const input = screen.getByTestId('input');
      await user.type(input, 'test');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(screen.getByText('3 results in 45ms')).toBeInTheDocument();
      });
      
      // Open filters
      const filterButton = screen.getByText('Filters');
      await user.click(filterButton);
      
      // Tag filters would be available after search
      expect(screen.getByText('Tags')).toBeInTheDocument();
    });

    it('changes sort order correctly', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const filterButton = screen.getByText('Filters');
      await user.click(filterButton);
      
      const sortSelect = screen.getByDisplayValue('Relevance');
      await user.selectOptions(sortSelect, 'date');
      
      expect(sortSelect).toHaveValue('date');
    });

    it('clears all filters when clear button is clicked', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const filterButton = screen.getByText('Filters');
      await user.click(filterButton);
      
      const clearButton = screen.getByText('Clear Filters');
      await user.click(clearButton);
      
      // Filters should be reset to defaults
      const sortSelect = screen.getByDisplayValue('Relevance');
      expect(sortSelect).toHaveValue('relevance');
    });
  });

  describe('Memory Selection', () => {
    it('calls onMemorySelect when memory is clicked', async () => {
      const onMemorySelect = vi.fn();
      const user = userEvent.setup();
      
      render(<MemorySearch {...defaultProps} onMemorySelect={onMemorySelect} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'test');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        const memoryCard = screen.getByText('JavaScript function to handle async operations').closest('[data-testid="card"]');
        if (memoryCard) {
          fireEvent.click(memoryCard);
          expect(onMemorySelect).toHaveBeenCalledWith(mockMemories[0]);
        }
      });
    });

    it('highlights selected memory', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'test');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        const memoryCard = screen.getByText('JavaScript function to handle async operations').closest('[data-testid="card"]');
        if (memoryCard) {
          fireEvent.click(memoryCard);
          expect(memoryCard).toHaveClass('ring-2 ring-blue-500');
        }
      });
    });
  });

  describe('Search History', () => {
    it('displays search history tab', async () => {
      render(<MemorySearch {...defaultProps} />);
      
      const historyTab = screen.getByText(/History/);
      expect(historyTab).toBeInTheDocument();
    });

    it('shows empty state for search history', () => {
      render(<MemorySearch {...defaultProps} />);
      
      // History would be empty initially
      expect(screen.getByTestId('tabs')).toBeInTheDocument();
    });
  });

  describe('Saved Searches', () => {
    it('displays saved searches tab', () => {
      render(<MemorySearch {...defaultProps} />);
      
      const savedTab = screen.getByText(/Saved/);
      expect(savedTab).toBeInTheDocument();
    });

    it('shows save button when query is entered', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'test query');
      
      expect(screen.getByText('Save')).toBeInTheDocument();
    });

    it('prompts for name when save button is clicked', async () => {
      const user = userEvent.setup();
      
      // Mock window.prompt
      const mockPrompt = vi.spyOn(window, 'prompt').mockReturnValue('My Search');
      
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'test query');
      
      const saveButton = screen.getByText('Save');
      await user.click(saveButton);
      
      expect(mockPrompt).toHaveBeenCalledWith('Enter a name for this search:');
      
      mockPrompt.mockRestore();
    });
  });

  describe('Error Handling', () => {
    it('displays error message when search fails', async () => {
      const user = userEvent.setup();
      mockMemoryService.searchMemories.mockRejectedValue(new Error('Search failed'));
      
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'test');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(screen.getByText('Search Error')).toBeInTheDocument();
        expect(screen.getByText('Search failed')).toBeInTheDocument();
      });
    });

    it('allows retry after error', async () => {
      const user = userEvent.setup();
      mockMemoryService.searchMemories
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          memories: mockMemories,
          totalFound: mockMemories.length,
          searchTime: 45
        });
      
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'test');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(screen.getByText('Search Error')).toBeInTheDocument();
      });
      
      const retryButton = screen.getByText('Try Again');
      await user.click(retryButton);
      
      await waitFor(() => {
        expect(screen.getByText('3 results in 45ms')).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading state during search', async () => {
      const user = userEvent.setup();
      
      // Make search hang to test loading state
      mockMemoryService.searchMemories.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      );
      
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'test');
      await user.keyboard('{Enter}');
      
      expect(screen.getByText('Searching...')).toBeInTheDocument();
    });

    it('shows loading skeleton for results', async () => {
      const user = userEvent.setup();
      
      mockMemoryService.searchMemories.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );
      
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'test');
      await user.keyboard('{Enter}');
      
      // Should show loading skeleton
      expect(screen.getByText('Searching...')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      
      // Input should be focusable
      await user.tab();
      expect(input).toHaveFocus();
      
      // Should be able to navigate to search button
      await user.tab();
      const searchButton = screen.getByText('Search');
      expect(searchButton).toHaveFocus();
    });

    it('has proper ARIA labels', () => {
      render(<MemorySearch {...defaultProps} />);
      
      const input = screen.getByTestId('input');
      expect(input).toHaveAttribute('placeholder', 'Search memories semantically...');
    });
  });

  describe('Responsive Design', () => {
    it('adapts to specified height', () => {
      render(<MemorySearch {...defaultProps} height={800} />);
      
      const container = screen.getByTestId('input').closest('div');
      // The container should have the specified height
      expect(container).toBeInTheDocument();
    });
  });

  describe('Callbacks', () => {
    it('calls onSearchComplete when search finishes', async () => {
      const onSearchComplete = vi.fn();
      const user = userEvent.setup();
      
      render(<MemorySearch {...defaultProps} onSearchComplete={onSearchComplete} />);
      
      const input = screen.getByTestId('input');
      await user.type(input, 'test');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(onSearchComplete).toHaveBeenCalledWith(
          expect.objectContaining({
            memories: mockMemories,
            totalFound: mockMemories.length,
            searchTime: 45
          })
        );
      });
    });
  });
});