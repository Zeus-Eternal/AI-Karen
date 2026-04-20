import React, { useState } from 'react';
import { WebSearchState } from '../types';
import { ModeConfigItem } from '../configs/modeConfig';
import { LoadingState, EmptyState, ErrorState } from './UIStates';
import { ResultsPanel, SourcesPanel, ExtractedDataPanel, InsightsPanel, DiagnosticsPanel } from './Panels';

interface ResultsWorkspaceProps {
  state: WebSearchState;
  modeConfig: ModeConfigItem;
}

export function ResultsWorkspace({ state, modeConfig }: ResultsWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<string>(modeConfig.resultTabs[0] || 'results');

  // Handle states where we don't show the tabs
  if (state.isLoading) return <LoadingState state={state} />;
  if (state.error) return <ErrorState error={state.error} />;
  if (!state.response) return <EmptyState />;

  // Ensure active tab is valid for current mode
  const validTabs = modeConfig.resultTabs;
  const currentTab = validTabs.includes(activeTab) ? activeTab : validTabs[0];

  const renderTabContent = () => {
    switch(currentTab) {
      case 'results':
        return <ResultsPanel response={state.response!} />;
      case 'sources':
        return <SourcesPanel response={state.response!} />;
      case 'extractedData':
        return <ExtractedDataPanel response={state.response!} />;
      case 'insights':
        return <InsightsPanel response={state.response!} />;
      case 'diagnostics':
        return <DiagnosticsPanel response={state.response!} />;
      default:
        return <div className="text-muted-foreground p-8">Unknown tab: {currentTab}</div>;
    }
  };

  return (
    <div className="flex flex-col h-full bg-background rounded-tl-xl border-l border-t border-border/40 shadow-inner">
      <div className="px-6 pt-4 pb-0 border-b border-border/60 bg-muted/10">
        <nav className="-mb-px flex space-x-6">
          {validTabs.map(tabId => {
            const label = tabId.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()); // simple uncamelcase
            const isActive = currentTab === tabId;
            
            return (
              <button
                key={tabId}
                onClick={() => setActiveTab(tabId)}
                className={`
                  whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm transition-colors
                  ${isActive 
                    ? 'border-primary text-primary' 
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                  }
                `}
              >
                {label}
              </button>
            );
          })}
        </nav>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6 md:p-8">
        <div className="max-w-4xl mx-auto">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
}
