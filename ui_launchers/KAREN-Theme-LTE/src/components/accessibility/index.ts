/**
 * Accessibility System Index
 * Central exports for the comprehensive accessibility system
 */

// Context and Provider
export { AccessibilityProvider, useAccessibility } from '@/contexts/AccessibilityContext';
export type {
  AccessibilityPreferences as IAccessibilityPreferences,
  AccessibilityState,
  AccessibilityContextType,
} from '@/contexts/AccessibilityContext';

// Core Accessibility Libraries
export { useAxeTesting } from '@/lib/accessibility/axe-testing';
export type { AccessibilityTest } from '@/lib/accessibility/axe-testing';
export { wcagComplianceChecker } from '@/lib/accessibility/wcag-compliance';
export type { WCAGComplianceReport } from '@/lib/accessibility/wcag-compliance';
export {
  useKeyboardNavigation,
  useFocusTrap,
  SkipLink,
} from '@/lib/accessibility/keyboard-navigation';
export {
  useARIA,
  useScreenReaderDetection,
  useAccessibleProps,
} from '@/lib/accessibility/screen-reader';
export type {
  ARIAProperties,
  ARIARole,
  ScreenReaderAnnouncement,
  AccessibleComponentProps,
} from '@/lib/accessibility/screen-reader';
export {
  useFocusManagement,
  FocusIndicator,
  FocusSentinel,
  SkipLinks,
  useFocusVisible,
} from '@/lib/accessibility/focus-management';
export {
  useVisualAdaptations,
  ColorContrastChecker,
  TEXT_SCALING_LEVELS,
  WCAG_CONTRAST_RATIOS,
} from '@/lib/accessibility/visual-adaptations';
export type {
  VisualPreferences,
  HighContrastColors,
} from '@/lib/accessibility/visual-adaptations';
export {
  useVoiceControl,
  VoiceControl,
  VoiceCommandCreator,
} from '@/lib/accessibility/voice-control';
export type {
  VoiceCommand,
  VoiceControlState,
} from '@/lib/accessibility/voice-control';
export {
  useAccessibilityTesting,
  AccessibilityTestingDashboard,
} from '@/lib/accessibility/testing-tools';
export type {
  TestResult,
  TestingConfig,
} from '@/lib/accessibility/testing-tools';
export {
  useAccessibilityMonitoring,
  AccessibilityMonitoringDashboard,
} from '@/lib/accessibility/monitoring';
export type {
  MonitoringEvent,
  MonitoringMetrics,
  MonitoringEventType,
} from '@/lib/accessibility/monitoring';

// Accessibility Components
export { default as AccessibilityPreferencesComponent } from './AccessibilityPreferences';
export { default as AccessibilityHelp } from './AccessibilityHelp';

// Accessibility Hooks
export { 
  useAccessibility as default,
  useAccessibleComponent,
  useAccessibleForm,
  useKeyboardNavigation as useKeyboardNav,
  useScreenReader,
} from '@/hooks/use-accessibility';

// Re-export commonly used types
// Note: The types module is missing, so we'll comment out these exports for now
// export type {
//   AccessibilityState as IAccessibilityState,
//   WCAGComplianceReport as IWCAGComplianceReport,
//   TestResult as ITestResult,
//   VoiceCommand as IVoiceCommand,
//   MonitoringEvent as IMonitoringEvent,
//   MonitoringMetrics as IMonitoringMetrics,
// } from '@/lib/accessibility/types';

// CSS for accessibility features
export const ACCESSIBILITY_STYLES = `
  /* Skip links */
  .skip-link {
    position: absolute;
    top: -40px;
    left: 6px;
    background: var(--background);
    color: var(--foreground);
    padding: 8px;
    text-decoration: none;
    border-radius: 4px;
    z-index: 10000;
    transition: top 0.3s;
  }
  
  .skip-link:focus {
    top: 6px;
    outline: 2px solid var(--focus-color, #2563eb);
    outline-offset: 2px;
  }
  
  /* Focus indicators */
  :focus-visible {
    outline: 2px solid var(--focus-color, #2563eb);
    outline-offset: 2px;
  }
  
  .high-contrast :focus-visible {
    outline: 3px solid #ffffff;
    outline-offset: 2px;
    background-color: #000000;
    color: #ffffff;
  }
  
  /* High contrast mode */
  .high-contrast,
  .high-contrast * {
    background-color: #000000 !important;
    color: #ffffff !important;
    border-color: #ffffff !important;
  }
  
  .high-contrast button,
  .high-contrast input,
  .high-contrast select,
  .high-contrast textarea,
  .high-contrast [role="button"] {
    background-color: #000000 !important;
    color: #ffffff !important;
    border: 2px solid #ffffff !important;
  }
  
  .high-contrast a,
  .high-contrast [role="link"] {
    color: #ffff00 !important;
    text-decoration: underline !important;
  }
  
  .high-contrast :focus {
    outline: 3px solid #ffff00 !important;
    outline-offset: 2px !important;
    border-color: #ffff00 !important;
  }
  
  /* Large text mode */
  .large-text {
    font-size: 125% !important;
    line-height: 1.5 !important;
  }
  
  .large-text button,
  .large-text input,
  .large-text select,
  .large-text textarea {
    font-size: 125% !important;
    padding: 0.625rem 1.25rem !important;
    min-height: 2.5rem !important;
  }
  
  /* Reduced motion */
  .reduced-motion *,
  .reduced-motion *::before,
  .reduced-motion *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  
  /* Screen reader only content */
  .sr-only {
    position: absolute;
    left: -10000px;
    width: 1px;
    height: 1px;
    overflow: hidden;
  }
  
  /* Accessibility testing indicators */
  .accessibility-testing-indicator {
    position: fixed;
    top: 10px;
    right: 10px;
    background: var(--background);
    color: var(--foreground);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 14px;
    z-index: 10001;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  }
  
  /* Voice control indicator */
  .voice-control-indicator {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: var(--background);
    color: var(--foreground);
    border: 1px solid var(--border);
    border-radius: 50%;
    width: 60px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10002;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  }
  
  .voice-control-indicator.listening {
    background: var(--accent, #2563eb);
    color: var(--accent-foreground, #ffffff);
  }
  
  .voice-control-indicator .voice-icon {
    font-size: 24px;
  }
  
  /* Accessibility preferences panel */
  .accessibility-preferences {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: var(--background);
    color: var(--foreground);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    max-width: 90vw;
    max-height: 90vh;
    overflow-y: auto;
    z-index: 10003;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  }
  
  .preference-tabs {
    display: flex;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
  }
  
  .tab-button {
    background: none;
    border: none;
    padding: 12px 20px;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
  }
  
  .tab-button:hover {
    background: var(--accent);
    color: var(--accent-foreground);
  }
  
  .tab-button.active {
    border-bottom-color: var(--accent);
    color: var(--accent);
  }
  
  .preference-panel {
    display: none;
  }
  
  .preference-panel.active {
    display: block;
  }
  
  .preference-group {
    margin-bottom: 16px;
  }
  
  .preference-item {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .preference-item input[type="checkbox"] {
    margin-right: 8px;
  }
  
  .preference-item label {
    cursor: pointer;
  }
  
  .preference-description {
    font-size: 12px;
    color: var(--muted-foreground);
    margin-left: 8px;
  }
  
  /* Accessibility help */
  .accessibility-help {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: var(--background);
    color: var(--foreground);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    max-width: 90vw;
    max-height: 90vh;
    overflow-y: auto;
    z-index: 10004;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  }
  
  .help-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .help-search {
    flex: 1;
    margin-right: 20px;
  }
  
  .help-search input {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--background);
    color: var(--foreground);
  }
  
  .topic-list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 20px;
  }
  
  .category-section {
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 16px;
  }
  
  .category-title {
    margin: 0 0 16px 0;
    color: var(--accent);
  }
  
  .topic-button {
    background: var(--background);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 12px;
    text-align: left;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .topic-button:hover {
    background: var(--accent);
    color: var(--accent-foreground);
  }
  
  .topic-content {
    padding: 20px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--background);
  }
  
  .shortcuts-list {
    margin-top: 16px;
  }
  
  .shortcuts-list li {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
  }
  
  .shortcut-key {
    background: var(--muted-background);
    color: var(--muted-foreground);
    padding: 4px 8px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 12px;
  }
  
  .shortcut-description {
    color: var(--muted-foreground);
    font-size: 14px;
  }
`;

// Initialize accessibility system
export const initializeAccessibility = () => {
  // Inject accessibility styles
  if (typeof document !== 'undefined') {
    const styleElement = document.createElement('style');
    styleElement.textContent = ACCESSIBILITY_STYLES;
    styleElement.id = 'accessibility-system-styles';
    document.head.appendChild(styleElement);
  }
  
  // Initialize accessibility context
  console.log('Accessibility system initialized');
};

// Utility function to check if accessibility features should be enabled
export const shouldEnableAccessibility = () => {
  if (typeof window === 'undefined') return false;
  
  // Check for reduced motion preference
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  // Check for high contrast preference
  const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
  
  // Check for screen reader
  const hasScreenReader = 'speechSynthesis' in window;
  
  return {
    reducedMotion: prefersReducedMotion,
    highContrast: prefersHighContrast,
    screenReader: hasScreenReader,
  };
};