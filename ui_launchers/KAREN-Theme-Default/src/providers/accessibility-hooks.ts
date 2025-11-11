import { useContext } from 'react';
import { AccessibilityContext } from './accessibility-context';

export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
}

export function useAnnounce() {
  const { announce } = useAccessibility();
  return announce;
}

export function useScreenReader() {
  const { isScreenReaderActive, settings } = useAccessibility();
  return {
    isActive: isScreenReaderActive,
    verboseDescriptions: settings.verboseDescriptions,
    announcements: settings.announcements,
  };
}

export function useAccessibilitySettings() {
  const { settings, updateSetting } = useAccessibility();
  return { settings, updateSetting };
}
