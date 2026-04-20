import React from 'react';
import { MODE_CONFIG } from '../configs/modeConfig';
import { SearchModeId } from '../types';

interface ModeSelectorProps {
  currentMode: SearchModeId;
  onModeChange: (mode: SearchModeId) => void;
  disabled?: boolean;
}

export function ModeSelector({ currentMode, onModeChange, disabled }: ModeSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-foreground">Search Mode</label>
      <div className="grid grid-cols-2 gap-2">
        {(Object.entries(MODE_CONFIG) as [SearchModeId, typeof MODE_CONFIG[SearchModeId]][]).map(([mode, config]) => (
          <button
            key={mode}
            type="button"
            disabled={disabled}
            onClick={() => onModeChange(mode)}
            className={`
              text-left px-3 py-2 rounded-md border transition-all text-sm
              ${currentMode === mode 
                ? 'bg-primary/10 border-primary text-primary font-medium' 
                : 'bg-card border-border text-muted-foreground hover:bg-muted/50 hover:border-primary/40'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            {config.label}
          </button>
        ))}
      </div>
    </div>
  );
}
