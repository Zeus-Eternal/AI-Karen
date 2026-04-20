import React from 'react';

export const ErrorState: React.FC<{ error: string; onRetry?: () => void }> = ({ error, onRetry }) => (
  <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 text-red-400 flex flex-col items-start bg-neutral-900 border-neutral-800">
    <h3 className="font-medium mb-1 flex items-center">
      <span className="mr-2">⚠️</span> Error
    </h3>
    <p className="text-sm opacity-90 mb-3">{error}</p>
    {onRetry && (
      <button 
        onClick={onRetry}
        className="px-3 py-1 bg-red-900/40 hover:bg-red-900/60 rounded text-sm transition-colors"
      >
        Retry
      </button>
    )}
  </div>
);
