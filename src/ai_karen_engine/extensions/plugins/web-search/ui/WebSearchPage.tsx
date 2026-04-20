import React from 'react';
import { useWebSearch } from './hooks/useWebSearch';
import { SearchHeader } from './components/SearchHeader';
import { SearchControlsPanel } from './components/SearchControlsPanel';
import { ResultsWorkspace } from './components/ResultsWorkspace';

export default function WebSearchPage() {
  const {
    state,
    modeConfig,
    setQuery,
    setMode,
    updateOptions,
    executeSearch,
  } = useWebSearch();

  return (
    <div className="flex flex-col h-full min-h-[calc(100vh-4rem)] bg-background text-foreground overflow-hidden">
      <div className="p-6 pb-2">
        <SearchHeader modeConfig={modeConfig} state={state} />
      </div>
      
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden pb-6">
        {/* Left Side: Controls */}
        <div className="w-full md:w-80 lg:w-96 flex-shrink-0 md:border-r border-border/40 overflow-y-auto px-6 py-4">
          <SearchControlsPanel 
            state={state}
            modeConfig={modeConfig}
            onQueryChange={setQuery}
            onModeChange={setMode}
            onOptionsChange={updateOptions}
            onSubmit={executeSearch}
          />
        </div>
        
        {/* Right Side: Results Workspace */}
        <div className="flex-1 min-w-0 overflow-y-auto relative bg-card/10">
          <ResultsWorkspace 
            state={state} 
            modeConfig={modeConfig} 
          />
        </div>
      </div>
    </div>
  );
}
