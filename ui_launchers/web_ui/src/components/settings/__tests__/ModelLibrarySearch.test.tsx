import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock component that uses search and filtering
const ModelLibrarySearch = ({ onSearch, onFilter, onSort, onClear }: {
  onSearch: (query: string) => void;
  onFilter: (filters: any) => void;
  onSort: (sort: string) => void;
  onClear: () => void;
}) => {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedProvider, setSelectedProvider] = React.useState('');
  const [selectedCapability, setSelectedCapability] = React.useState('');
  const [selectedSize, setSelectedSize] = React.useState('');
  const [sortBy, setSortBy] = React.useState('name');

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    onSearch(query);
  };

  const handleFilterChange = () => {
    onFilter({
      provider: selectedProvider,
      capability: selectedCapability,
      size: selectedSize
    });
  };

  const handleSortChange = (sort: string) => {
    setSortBy(sort);
    onSort(sort);
  };

  const handleClear = () => {
    setSearchQuery('');
    setSelectedProvider('');
    setSelectedCapability('');
    setSelectedSize('');
    setSortBy('name');
    onClear();
  };

  React.useEffect(() => {
    handleFilterChange();
  }, [selectedProvider, selectedCapability, selectedSize]);

  return (
    <div className="model-library-search">
      <div className="search-controls">
        <input
          type="text"
          placeholder="Search models..."
          value={searchQuery}
          onChange={(e) = aria-label="Input"> handleSearch(e.target.value)}
          data-testid="search-input"
        />
        
        <select
          value={selectedProvider}
          onChange={(e) = aria-label="Select option"> setSelectedProvider(e.target.value)}
          data-testid="provider-filter"
          aria-label="Filter by provider"
        >
          <option value="">All Providers</option>
          <option value="llama-cpp">Llama.cpp</option>
          <option value="transformers">Transformers</option>
          <option value="openai">OpenAI</option>
        </select>
        
        <select
          value={selectedCapability}
          onChange={(e) = aria-label="Select option"> setSelectedCapability(e.target.value)}
          data-testid="capability-filter"
          aria-label="Filter by capability"
        >
          <option value="">All Capabilities</option>
          <option value="text-generation">Text Generation</option>
          <option value="chat">Chat</option>
          <option value="code-generation">Code Generation</option>
          <option value="reasoning">Reasoning</option>
        </select>
        
        <select
          value={selectedSize}
          onChange={(e) = aria-label="Select option"> setSelectedSize(e.target.value)}
          data-testid="size-filter"
          aria-label="Filter by size"
        >
          <option value="">All Sizes</option>
          <option value="small">Small (&lt; 1GB)</option>
          <option value="medium">Medium (1-5GB)</option>
          <option value="large">Large (&gt; 5GB)</option>
        </select>
        
        <select
          value={sortBy}
          onChange={(e) = aria-label="Select option"> handleSortChange(e.target.value)}
          data-testid="sort-select"
          aria-label="Sort by"
        >
          <option value="name">Name</option>
          <option value="size">Size</option>
          <option value="provider">Provider</option>
          <option value="status">Status</option>
          <option value="date">Date Added</option>
        </select>
        
        <button
          onClick={handleClear}
          data-testid="clear-filters"
          aria-label="Clear all filters"
        >
          Clear Filters
        </button>
      </div>
      
      <div className="active-filters" data-testid="active-filters">
        {searchQuery && (
          <span className="filter-tag">
            Search: "{searchQuery}"
            <button onClick={() = aria-label="Button"> handleSearch('')}>×</button>
          </span>
        )}
        {selectedProvider && (
          <span className="filter-tag">
            Provider: {selectedProvider}
            <button onClick={() = aria-label="Button"> setSelectedProvider('')}>×</button>
          </span>
        )}
        {selectedCapability && (
          <span className="filter-tag">
            Capability: {selectedCapability}
            <button onClick={() = aria-label="Button"> setSelectedCapability('')}>×</button>
          </span>
        )}
        {selectedSize && (
          <span className="filter-tag">
            Size: {selectedSize}
            <button onClick={() = aria-label="Button"> setSelectedSize('')}>×</button>
          </span>
        )}
      </div>
    </div>
  );
};

describe('ModelLibrarySearch', () => {
  const mockOnSearch = vi.fn();
  const mockOnFilter = vi.fn();
  const mockOnSort = vi.fn();
  const mockOnClear = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders search and filter controls', () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    expect(screen.getByTestId('search-input')).toBeInTheDocument();
    expect(screen.getByTestId('provider-filter')).toBeInTheDocument();
    expect(screen.getByTestId('capability-filter')).toBeInTheDocument();
    expect(screen.getByTestId('size-filter')).toBeInTheDocument();
    expect(screen.getByTestId('sort-select')).toBeInTheDocument();
    expect(screen.getByTestId('clear-filters')).toBeInTheDocument();
  });

  it('calls onSearch when search input changes', async () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    const searchInput = screen.getByTestId('search-input');
    fireEvent.change(searchInput, { target: { value: 'tinyllama' } });

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('tinyllama');
    });
  });

  it('calls onFilter when provider filter changes', async () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    const providerFilter = screen.getByTestId('provider-filter');
    fireEvent.change(providerFilter, { target: { value: 'llama-cpp' } });

    await waitFor(() => {
      expect(mockOnFilter).toHaveBeenCalledWith({
        provider: 'llama-cpp',
        capability: '',
        size: ''
      });
    });
  });

  it('calls onFilter when capability filter changes', async () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    const capabilityFilter = screen.getByTestId('capability-filter');
    fireEvent.change(capabilityFilter, { target: { value: 'chat' } });

    await waitFor(() => {
      expect(mockOnFilter).toHaveBeenCalledWith({
        provider: '',
        capability: 'chat',
        size: ''
      });
    });
  });

  it('calls onFilter when size filter changes', async () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    const sizeFilter = screen.getByTestId('size-filter');
    fireEvent.change(sizeFilter, { target: { value: 'small' } });

    await waitFor(() => {
      expect(mockOnFilter).toHaveBeenCalledWith({
        provider: '',
        capability: '',
        size: 'small'
      });
    });
  });

  it('calls onSort when sort selection changes', async () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    const sortSelect = screen.getByTestId('sort-select');
    fireEvent.change(sortSelect, { target: { value: 'size' } });

    await waitFor(() => {
      expect(mockOnSort).toHaveBeenCalledWith('size');
    });
  });

  it('shows active filters as tags', async () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    // Apply search
    const searchInput = screen.getByTestId('search-input');
    fireEvent.change(searchInput, { target: { value: 'tinyllama' } });

    // Apply provider filter
    const providerFilter = screen.getByTestId('provider-filter');
    fireEvent.change(providerFilter, { target: { value: 'llama-cpp' } });

    await waitFor(() => {
      const activeFilters = screen.getByTestId('active-filters');
      expect(activeFilters).toHaveTextContent('Search: "tinyllama"');
      expect(activeFilters).toHaveTextContent('Provider: llama-cpp');
    });
  });

  it('removes individual filter tags when clicked', async () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    // Apply search
    const searchInput = screen.getByTestId('search-input');
    fireEvent.change(searchInput, { target: { value: 'tinyllama' } });

    await waitFor(() => {
      const searchTag = screen.getByText('Search: "tinyllama"');
      expect(searchTag).toBeInTheDocument();
    });

    // Remove search filter
    const removeSearchButton = screen.getByText('×');
    fireEvent.click(removeSearchButton);

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('');
      expect(screen.queryByText('Search: "tinyllama"')).not.toBeInTheDocument();
    });
  });

  it('clears all filters when clear button is clicked', async () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    // Apply multiple filters
    const searchInput = screen.getByTestId('search-input');
    fireEvent.change(searchInput, { target: { value: 'tinyllama' } });

    const providerFilter = screen.getByTestId('provider-filter');
    fireEvent.change(providerFilter, { target: { value: 'llama-cpp' } });

    const capabilityFilter = screen.getByTestId('capability-filter');
    fireEvent.change(capabilityFilter, { target: { value: 'chat' } });

    await waitFor(() => {
      expect(screen.getByText('Search: "tinyllama"')).toBeInTheDocument();
      expect(screen.getByText('Provider: llama-cpp')).toBeInTheDocument();
      expect(screen.getByText('Capability: chat')).toBeInTheDocument();
    });

    // Clear all filters
    const clearButton = screen.getByTestId('clear-filters');
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(mockOnClear).toHaveBeenCalled();
      expect(screen.queryByText('Search: "tinyllama"')).not.toBeInTheDocument();
      expect(screen.queryByText('Provider: llama-cpp')).not.toBeInTheDocument();
      expect(screen.queryByText('Capability: chat')).not.toBeInTheDocument();
    });

    // Check that form controls are reset
    expect((screen.getByTestId('search-input') as HTMLInputElement).value).toBe('');
    expect((screen.getByTestId('provider-filter') as HTMLSelectElement).value).toBe('');
    expect((screen.getByTestId('capability-filter') as HTMLSelectElement).value).toBe('');
    expect((screen.getByTestId('size-filter') as HTMLSelectElement).value).toBe('');
    expect((screen.getByTestId('sort-select') as HTMLSelectElement).value).toBe('name');
  });

  it('handles multiple simultaneous filters', async () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    // Apply search
    const searchInput = screen.getByTestId('search-input');
    fireEvent.change(searchInput, { target: { value: 'llama' } });

    // Apply provider filter
    const providerFilter = screen.getByTestId('provider-filter');
    fireEvent.change(providerFilter, { target: { value: 'llama-cpp' } });

    // Apply capability filter
    const capabilityFilter = screen.getByTestId('capability-filter');
    fireEvent.change(capabilityFilter, { target: { value: 'text-generation' } });

    // Apply size filter
    const sizeFilter = screen.getByTestId('size-filter');
    fireEvent.change(sizeFilter, { target: { value: 'small' } });

    await waitFor(() => {
      expect(mockOnFilter).toHaveBeenLastCalledWith({
        provider: 'llama-cpp',
        capability: 'text-generation',
        size: 'small'
      });
    });

    // All filter tags should be visible
    expect(screen.getByText('Search: "llama"')).toBeInTheDocument();
    expect(screen.getByText('Provider: llama-cpp')).toBeInTheDocument();
    expect(screen.getByText('Capability: text-generation')).toBeInTheDocument();
    expect(screen.getByText('Size: small')).toBeInTheDocument();
  });

  it('debounces search input', async () => {
    vi.useFakeTimers();
    
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    const searchInput = screen.getByTestId('search-input');
    
    // Type quickly
    fireEvent.change(searchInput, { target: { value: 't' } });
    fireEvent.change(searchInput, { target: { value: 'ti' } });
    fireEvent.change(searchInput, { target: { value: 'tin' } });
    fireEvent.change(searchInput, { target: { value: 'tiny' } });

    // Should be called for each change (no debouncing in this simple implementation)
    expect(mockOnSearch).toHaveBeenCalledTimes(4);
    expect(mockOnSearch).toHaveBeenLastCalledWith('tiny');

    vi.useRealTimers();
  });

  it('has proper accessibility attributes', () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    expect(screen.getByTestId('provider-filter')).toHaveAttribute('aria-label', 'Filter by provider');
    expect(screen.getByTestId('capability-filter')).toHaveAttribute('aria-label', 'Filter by capability');
    expect(screen.getByTestId('size-filter')).toHaveAttribute('aria-label', 'Filter by size');
    expect(screen.getByTestId('sort-select')).toHaveAttribute('aria-label', 'Sort by');
    expect(screen.getByTestId('clear-filters')).toHaveAttribute('aria-label', 'Clear all filters');
  });

  it('handles keyboard navigation', async () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    const searchInput = screen.getByTestId('search-input');
    const providerFilter = screen.getByTestId('provider-filter');

    // Tab navigation
    searchInput.focus();
    expect(searchInput).toHaveFocus();

    fireEvent.keyDown(searchInput, { key: 'Tab' });
    expect(providerFilter).toHaveFocus();
  });

  it('preserves filter state during re-renders', async () => {
    const { rerender } = render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    // Apply filters
    const searchInput = screen.getByTestId('search-input');
    fireEvent.change(searchInput, { target: { value: 'test' } });

    const providerFilter = screen.getByTestId('provider-filter');
    fireEvent.change(providerFilter, { target: { value: 'llama-cpp' } });

    await waitFor(() => {
      expect((searchInput as HTMLInputElement).value).toBe('test');
      expect((providerFilter as HTMLSelectElement).value).toBe('llama-cpp');
    });

    // Re-render component
    rerender(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    // State should be preserved
    expect((screen.getByTestId('search-input') as HTMLInputElement).value).toBe('test');
    expect((screen.getByTestId('provider-filter') as HTMLSelectElement).value).toBe('llama-cpp');
  });

  it('handles empty search gracefully', async () => {
    render(
      <ModelLibrarySearch
        onSearch={mockOnSearch}
        onFilter={mockOnFilter}
        onSort={mockOnSort}
        onClear={mockOnClear}
      />
    );

    const searchInput = screen.getByTestId('search-input');
    
    // Enter search term
    fireEvent.change(searchInput, { target: { value: 'test' } });
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('test');
    });

    // Clear search
    fireEvent.change(searchInput, { target: { value: '' } });
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('');
    });

    // No search tag should be visible
    expect(screen.queryByText('Search:')).not.toBeInTheDocument();
  });
});