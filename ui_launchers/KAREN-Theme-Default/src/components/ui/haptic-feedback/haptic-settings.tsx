"use client";

import React from 'react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

import { getHapticPatternInfo } from './haptic-utils';
import { useHaptic } from './use-haptic';
import type { HapticPattern, HapticSettingsProps } from './types';

const testPatterns: HapticPattern[] = ['light', 'medium', 'heavy', 'success', 'warning', 'error'];

export function HapticSettings({ 
  className,
  onSettingsChange
}: HapticSettingsProps) {
  const { enabled, supported, setEnabled, triggerHaptic } = useHaptic();

  const handleToggle = () => {
    const newEnabled = !enabled;
    setEnabled(newEnabled);
    onSettingsChange?.(newEnabled);
    
    // Trigger a test haptic when enabling
    if (newEnabled) {
      setTimeout(() => triggerHaptic('success'), 100);
    }
  };

  const handleTestPattern = (pattern: HapticPattern) => {
    triggerHaptic(pattern);
  };

  if (!supported) {
    return (
      <div className={cn('p-4 border rounded-lg bg-muted/50', className)}>
        <div className="flex items-center space-x-2 text-muted-foreground">
          <span className="text-lg">📱</span>
          <div>
            <h3 className="font-medium">Haptic Feedback Not Supported</h3>
            <p className="text-sm md:text-base lg:text-lg">Your device doesn't support haptic feedback.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Main Toggle */}
      <div className="flex items-center justify-between p-4 border rounded-lg sm:p-4 md:p-6">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">📳</span>
          <div>
            <h3 className="font-medium">Haptic Feedback</h3>
            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
            </p>
          </div>
        </div>
        <Button
          onClick={handleToggle}
          className={cn(
            'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
            enabled ? 'bg-primary' : 'bg-muted'
          )}
          aria-label={enabled ? 'Disable haptic feedback' : 'Enable haptic feedback'}
          type="button"
        >
          <span
            className={cn(
              'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
              enabled ? 'translate-x-6' : 'translate-x-1'
            )}
          />
        </Button>
      </div>

      {/* Test Patterns */}
      {enabled && (
        <div className="space-y-4">
          <h4 className="font-medium">Test Haptic Patterns</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {testPatterns.map((pattern) => {
              const info = getHapticPatternInfo(pattern);
              return (
                <Button
                  key={pattern}
                  onClick={() => handleTestPattern(pattern)}
                  className={cn(
                    'p-3 text-left border rounded-lg hover:bg-muted/50 transition-colors',
                    'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2'
                  )}
                  aria-label={`Trigger ${info.name} haptic feedback`}
                  type="button"
                >
                  <div className="font-medium text-sm md:text-base lg:text-lg">{info.name}</div>
                  <div className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                    {info.description}
                  </div>
                  <div className="flex items-center mt-2">
                    <div className={cn(
                      'w-2 h-2 rounded-full mr-2',
                      info.intensity === 'low' && 'bg-green-500',
                      info.intensity === 'medium' && 'bg-yellow-500',
                      info.intensity === 'high' && 'bg-red-500'
                    )} />
                    <span className="text-xs text-muted-foreground capitalize sm:text-sm md:text-base">
                      {info.intensity}
                    </span>
                  </div>
                </Button>
              );
            })}
          </div>
        </div>
      )}

      {/* Information */}
      <div className="p-4 bg-muted/30 rounded-lg sm:p-4 md:p-6">
        <h4 className="font-medium mb-2">About Haptic Feedback</h4>
        <ul className="text-sm text-muted-foreground space-y-1 md:text-base lg:text-lg">
          <li>• Provides tactile feedback for better user experience</li>
          <li>• Works on mobile devices and some desktop browsers</li>
          <li>• Can be disabled in device settings or browser preferences</li>
          <li>• Respects user's reduced motion preferences</li>
        </ul>
      </div>
    </div>
  );
}