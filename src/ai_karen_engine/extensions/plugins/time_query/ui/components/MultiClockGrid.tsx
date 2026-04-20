import React from 'react';
import { ClockItem } from '../types';
import { EmptyState } from './EmptyState';
import { offsetToLabel } from '../utils/timeFormatters';

export const MultiClockGrid: React.FC<{ clocks: ClockItem[]; onRemove: (tz: string) => void }> = ({ clocks, onRemove }) => {
  if (clocks.length === 0) {
    return <EmptyState title="No Clocks Saved" message="Search and add a world clock to keep track of it here." />;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {clocks.map((c, i) => {
        // if there's an error in the payload it might not have standard payload fields
        if ((c as any).error) {
          return (
            <div key={i} className="bg-neutral-950 border border-red-900/50 rounded flex justify-between items-center p-4">
              <span className="text-red-400 text-sm">{(c as any).error}</span>
              <button className="text-neutral-500 hover:text-white" onClick={() => onRemove(c.timezone)}>×</button>
            </div>
          );
        }
        return (
          <div key={c.timezone} className="bg-neutral-950 border border-neutral-800 rounded p-4 relative group">
            <button 
              onClick={() => onRemove(c.timezone)}
              className="absolute top-2 right-2 text-neutral-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
              title="Remove"
            >
               × 
            </button>
            <div className="text-xs text-neutral-500 uppercase tracking-widest mb-1">{c.label}</div>
            <div className="text-2xl font-light text-white">{c.time}</div>
            <div className="text-xs text-neutral-400 mt-1">{c.weekday}, {c.date}</div>
            <div className="text-xs text-neutral-600 mt-2">{offsetToLabel(c.utc_offset)}</div>
          </div>
        );
      })}
    </div>
  );
};
