// Haptic System Components and Utilities Export

// Haptic components
export { HapticProvider } from './haptic-provider';
export { useHaptic } from './use-haptic';
export { HapticButton } from './haptic-button';
export { HapticSettings } from './haptic-settings';

// Haptic utilities
export { 
  triggerHapticFeedback,
  isHapticSupported,
  isHapticEnabled,
  setHapticEnabled 
} from './haptic-utils';

// Type exports
export type { 
  HapticButtonProps,
  HapticSettingsProps 
} from './types'; // Assuming you have types defined in the 'types' file for these components
