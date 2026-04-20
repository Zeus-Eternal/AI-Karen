import React from 'react';
import { ModeConfigItem } from '../configs/modeConfig';
import { WebSearchState } from '../types';

interface SearchHeaderProps {
  modeConfig: ModeConfigItem;
  state: WebSearchState;
}

export function SearchHeader({ modeConfig, state }: SearchHeaderProps) {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-border/40">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          Web Search
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          <span className="font-medium text-foreground">{modeConfig.label}</span> — {modeConfig.description}
        </p>
      </div>
      
      <div className="mt-4 md:mt-0 flex items-center gap-3">
        {state.isLoading ? (
          <div className="flex items-center gap-2 text-sm text-yellow-600 bg-yellow-500/10 px-3 py-1 rounded-full border border-yellow-500/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-yellow-500"></span>
            </span>
            Executing Request...
          </div>
        ) : state.error ? (
           <div className="flex items-center gap-2 text-sm text-red-500 bg-red-500/10 px-3 py-1 rounded-full border border-red-500/20">
            Error
          </div>
        ) : state.response ? (
          <div className="flex items-center gap-2 text-sm text-green-500 bg-green-500/10 px-3 py-1 rounded-full border border-green-500/20">
            Ready
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 px-3 py-1 rounded-full border border-border">
            Idle
          </div>
        )}
      </div>
    </div>
  );
}
