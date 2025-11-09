// Haptic feedback utility functions
export type HapticPattern = 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error';
export interface HapticConfig {
  pattern: number | number[];
  duration?: number;
}
const hapticPatterns: Record<HapticPattern, HapticConfig> = {
  light: { pattern: 10 },
  medium: { pattern: 50 },
  heavy: { pattern: 100 },
  success: { pattern: [50, 50, 100] },
  warning: { pattern: [100, 50, 100] },
  error: { pattern: [100, 100, 50, 50, 100] }
};
export function triggerHapticFeedback(pattern: HapticPattern = 'light'): void {
  // Check if the device supports vibration
  if (!('vibrate' in navigator)) {
    return;
  }
  // Check if user has enabled haptic feedback (this would come from user preferences)
  const hapticEnabled = localStorage.getItem('haptic-feedback-enabled') !== 'false';
  if (!hapticEnabled) {
    return;
  }
  const config = hapticPatterns[pattern];
  try {
    if (Array.isArray(config.pattern)) {
      navigator.vibrate(config.pattern);
    } else {
      navigator.vibrate(config.pattern);
    }
  } catch (error) {
    // Silently fail if vibration is not supported or blocked
  }
}
export function isHapticSupported(): boolean {
  return 'vibrate' in navigator;
}
export function setHapticEnabled(enabled: boolean): void {
  localStorage.setItem('haptic-feedback-enabled', enabled.toString());
}
export function isHapticEnabled(): boolean {
  return localStorage.getItem('haptic-feedback-enabled') !== 'false';
}
