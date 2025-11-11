import { HapticPattern, HapticConfig } from './types';
const hapticPatterns: Record<HapticPattern, HapticConfig> = {
  light: { pattern: 10 },
  medium: { pattern: 50 },
  heavy: { pattern: 100 },
  success: { pattern: [50, 50, 100] },
  warning: { pattern: [100, 50, 100] },
  error: { pattern: [100, 100, 50, 50, 100] },
  notification: { pattern: [200, 100, 200] },
  selection: { pattern: 25 },
  impact: { pattern: [150, 50, 150] }
};
export function triggerHapticFeedback(pattern: HapticPattern = 'light'): void {
  // Check if the device supports vibration
  if (!isHapticSupported()) {
    return;
  }
  // Check if user has enabled haptic feedback
  if (!isHapticEnabled()) {
    return;
  }
  const config = hapticPatterns[pattern];
  try {
    if (Array.isArray(config.pattern)) {
      navigator.vibrate(config.pattern);
    } else {
      navigator.vibrate(config.pattern);
    }
  } catch {
    // Silently fail if vibration is not supported or blocked
  }
}
export function isHapticSupported(): boolean {
  return 'vibrate' in navigator && typeof navigator.vibrate === 'function';
}
export function isHapticEnabled(defaultEnabled = true): boolean {
  if (typeof window === 'undefined') return defaultEnabled;
  try {
    const stored = localStorage.getItem('haptic-feedback-enabled');
    if (stored === null) {
      return defaultEnabled;
    }
    return stored !== 'false';
  } catch {
    return defaultEnabled;
  }
}
export function setHapticEnabled(enabled: boolean): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem('haptic-feedback-enabled', enabled.toString());
  } catch {
    // Silently ignore failures writing to storage
  }
}
export function getHapticPatternInfo(pattern: HapticPattern): { 
  name: string; 
  description: string; 
  intensity: 'low' | 'medium' | 'high';
} {
  const patternInfo = {
    light: { name: 'Light', description: 'Subtle feedback for minor interactions', intensity: 'low' as const },
    medium: { name: 'Medium', description: 'Standard feedback for regular interactions', intensity: 'medium' as const },
    heavy: { name: 'Heavy', description: 'Strong feedback for important actions', intensity: 'high' as const },
    success: { name: 'Success', description: 'Positive feedback for successful actions', intensity: 'medium' as const },
    warning: { name: 'Warning', description: 'Cautionary feedback for warnings', intensity: 'medium' as const },
    error: { name: 'Error', description: 'Alert feedback for errors', intensity: 'high' as const },
    notification: { name: 'Notification', description: 'Attention-grabbing feedback for notifications', intensity: 'medium' as const },
    selection: { name: 'Selection', description: 'Gentle feedback for selections', intensity: 'low' as const },
    impact: { name: 'Impact', description: 'Impactful feedback for significant actions', intensity: 'high' as const }
  };
  return patternInfo[pattern];
}
