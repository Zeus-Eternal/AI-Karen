import React from 'react';
import { SearchQueryInput } from './SearchQueryInput';
import { ModeSelector } from './ModeSelector';
import { ModeSpecificControls } from './ModeSpecificControls';
import { WebSearchState, WebSearchOptions, SearchModeId } from '../types';
import { ModeConfigItem } from '../configs/modeConfig';

interface SearchControlsPanelProps {
  state: WebSearchState;
  modeConfig: ModeConfigItem;
  onQueryChange: (q: string) => void;
  onModeChange: (m: SearchModeId) => void;
  onOptionsChange: (opts: Partial<WebSearchOptions>) => void;
  onSubmit: () => void;
}

export function SearchControlsPanel({ 
  state, modeConfig, onQueryChange, onModeChange, onOptionsChange, onSubmit 
}: SearchControlsPanelProps) {
  const isDisabled = state.isLoading;

  return (
    <div className="flex flex-col gap-6 p-4 md:p-0">
      <SearchQueryInput 
        query={state.query} 
        onQueryChange={onQueryChange} 
        onSubmit={onSubmit} 
        disabled={isDisabled} 
      />
      
      <ModeSelector 
        currentMode={state.mode} 
        onModeChange={onModeChange} 
        disabled={isDisabled} 
      />

      <ModeSpecificControls 
        modeConfig={modeConfig} 
        options={state.options} 
        onOptionsChange={onOptionsChange} 
        disabled={isDisabled} 
      />

      <div className="pt-2">
        <button
          onClick={onSubmit}
          disabled={isDisabled || (!state.query.trim() && !['weather', 'stock_market'].includes(state.mode))}
          className="w-full bg-primary text-primary-foreground font-medium py-2 px-4 rounded-lg shadow hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {isDisabled ? 'Searching...' : 'Execute Search'}
        </button>
      </div>
    </div>
  );
}
