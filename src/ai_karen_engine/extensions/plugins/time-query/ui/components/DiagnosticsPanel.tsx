import React from 'react';

export const DiagnosticsPanel: React.FC<{ payload: any }> = ({ payload }) => {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden mt-6">
      <div className="px-5 py-3 border-b border-neutral-800 bg-neutral-900/50">
        <h2 className="text-sm font-medium text-neutral-400">Plugin Diagnostics & Raw Payload</h2>
      </div>
      <div className="p-0 max-h-48 overflow-y-auto">
        <pre className="text-xs font-mono text-neutral-500 p-4">
          {JSON.stringify(payload, null, 2)}
        </pre>
      </div>
    </div>
  );
};
