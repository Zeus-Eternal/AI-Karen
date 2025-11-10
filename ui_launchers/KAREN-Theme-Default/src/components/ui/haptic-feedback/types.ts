import type { ButtonHTMLAttributes, ReactNode } from 'react';

export type HapticPattern =
  | 'light'
  | 'medium'
  | 'heavy'
  | 'success'
  | 'warning' 
  | 'error'
  | 'notification'
  | 'selection'
  | 'impact';

export interface HapticConfig {
  pattern: number | number[];
  duration?: number;
}

export interface HapticProviderProps {
  children: ReactNode;
  defaultEnabled?: boolean;
}

export interface HapticButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  hapticPattern?: HapticPattern;
  hapticEnabled?: boolean;
  children: ReactNode;
  ariaLabel?: string;
}

export interface HapticSettingsProps {
  className?: string;
  onSettingsChange?: (enabled: boolean) => void;
}

export interface HapticContextType {
  enabled: boolean;
  supported: boolean;
  setEnabled: (enabled: boolean) => void;
  trigger: (pattern: HapticPattern) => void;
}