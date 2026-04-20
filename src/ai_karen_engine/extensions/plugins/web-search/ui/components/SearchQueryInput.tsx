import React from 'react';

interface SearchQueryInputProps {
  query: string;
  onQueryChange: (query: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export function SearchQueryInput({ query, onQueryChange, onSubmit, disabled }: SearchQueryInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="space-y-2 relative">
      <label className="text-sm font-medium text-foreground">Query</label>
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ask anything..."
          className="w-full bg-background border border-border px-4 py-3 rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all disabled:opacity-50"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center">
          <button
            type="button"
            onClick={onSubmit}
            disabled={disabled || !query.trim()}
            className="bg-primary text-primary-foreground p-1.5 rounded-md text-xs font-medium disabled:opacity-50 hover:bg-primary/90 transition-colors"
          >
            Search
          </button>
        </div>
      </div>
      <p className="text-xs text-muted-foreground">Press Enter to search.</p>
    </div>
  );
}
