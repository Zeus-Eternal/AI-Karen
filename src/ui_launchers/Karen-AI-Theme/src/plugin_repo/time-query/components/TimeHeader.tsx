import React from 'react';
import { TimePayload } from '../types';

export const TimeHeader: React.FC<{ time: TimePayload | null }> = ({ time }) => {
  if (!time) return null;

  return (
    <div className="bg-neutral-900 border-b border-neutral-800 p-6 flex flex-col md:flex-row md:items-center justify-between">
      <div>
        <h1 className="text-4xl font-light tracking-tight text-white mb-1">
          {time.time}
        </h1>
        <p className="text-neutral-400 text-lg">
          {time.weekday}, {time.date}
        </p>
      </div>
      <div className="mt-4 md:mt-0 text-right space-y-1">
        <div className="inline-flex items-center space-x-2 bg-neutral-800/50 px-3 py-1.5 rounded-full border border-neutral-700/50">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          <span className="text-sm font-medium text-neutral-300">{time.timezone}</span>
        </div>
        <div className="text-xs text-neutral-500 font-mono">
          UTC: {time.utc_timestamp.substring(11, 19)}
        </div>
      </div>
    </div>
  );
};
