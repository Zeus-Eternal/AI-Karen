import React from 'react';
import { WebSearchState } from '../types';

export function LoadingState({ state }: { state: WebSearchState }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-muted-foreground p-8">
      <div className="relative mb-6">
        <div className="w-12 h-12 rounded-full border-4 border-muted border-t-primary animate-spin"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
          <svg className="w-5 h-5 text-primary" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
          </svg>
        </div>
      </div>
      <h3 className="text-lg font-medium text-foreground mb-2">Analyzing the web...</h3>
      <p className="text-sm max-w-sm text-center">
        Running <span className="font-semibold text-primary">{state.mode}</span> logic for 
        "{state.query.slice(0, 40)}{state.query.length > 40 ? '...' : ''}"
      </p>
    </div>
  );
}

export function ErrorState({ error }: { error: Error }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-red-500/80 p-8">
      <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mb-6">
        <svg className="w-8 h-8 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h3 className="text-xl font-bold text-red-500 mb-2">Search Execution Failed</h3>
      <p className="text-sm text-red-400 max-w-lg text-center break-words font-mono bg-red-950/20 p-4 rounded-lg border border-red-500/20">
        {error.message || "An unknown error occurred while communicating with the plugin host."}
      </p>
    </div>
  );
}

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-muted-foreground p-8">
      <div className="w-20 h-20 bg-card rounded-2xl shadow-sm border border-border flex items-center justify-center mb-6">
        <svg className="w-10 h-10 text-muted-foreground/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-foreground mb-2">Workspace Ready</h3>
      <p className="text-sm text-center max-w-sm">
        Enter a query and configure the mode parameters to extract organized knowledge from the web.
      </p>
    </div>
  );
}
