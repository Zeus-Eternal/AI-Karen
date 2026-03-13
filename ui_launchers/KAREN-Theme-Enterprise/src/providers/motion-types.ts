import * as React from 'react';

export interface MotionContextValue {
  reducedMotion: boolean;
  animationsEnabled: boolean;
  setReducedMotion: (reduced: boolean) => void;
  setAnimationsEnabled: (enabled: boolean) => void;
  transitionConfig: {
    duration: number;
    ease: 'linear' | readonly [0.4, 0, 0.2, 1];
  };
}

export interface MotionProviderProps {
  children: React.ReactNode;
  defaultReducedMotion?: boolean;
  defaultAnimationsEnabled?: boolean;
}