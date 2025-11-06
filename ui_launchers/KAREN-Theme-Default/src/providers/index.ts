/**
 * Providers Index - Production Grade
 *
 * Centralized export hub for all context providers and hooks.
 */

export { useAccessibilitySettings, useAnnounce, useAccessibility, AccessibilityProvider, useScreenReader } from './accessibility-provider';
export type { AccessibilityProviderProps, AccessibilityContextValue, AccessibilitySettings } from './accessibility-provider';

export { CombinedProvider } from './combined-provider';
export type { CombinedProviderProps } from './combined-provider';

export { I18nProvider, useFormatting, useTranslation, useLocale, useI18n } from './i18n-provider';
export type { I18nContextValue, I18nProviderProps } from './i18n-provider';

export { useMotion, useAnimationVariants, MotionProvider } from './motion-provider';
export type { MotionProviderProps, MotionContextValue } from './motion-provider';

export { useThemePreference, useAnimationPreference, useAccessibilityPreference, PreferencesProvider, usePreferences } from './preferences-provider';
export type { UserPreferences, PreferencesProviderProps, PreferencesContextValue } from './preferences-provider';

export { useRBAC, RBACProvider } from './rbac-provider';
export type { RBACProviderProps, RBACContextValue } from './rbac-provider';

export { ThemeProvider, useTheme } from './theme-provider';
export type { Theme, ThemeProviderProps, ThemeContextValue, Density } from './theme-provider';

