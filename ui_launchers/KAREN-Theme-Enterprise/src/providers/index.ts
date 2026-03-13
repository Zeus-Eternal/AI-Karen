/**
 * Providers Index - Production Grade
 *
 * Centralized export hub for all context providers and hooks.
 */

export { AccessibilityProvider } from './accessibility-provider';
export type { AccessibilityProviderProps } from './accessibility-provider';
export type { AccessibilityContextValue, AccessibilitySettings } from './accessibility-context';
export { useAccessibilitySettings, useAnnounce, useAccessibility, useScreenReader } from './accessibility-hooks';

export { CombinedProvider } from './combined-provider';
export type { CombinedProviderProps } from './combined-provider';

export { I18nProvider, type I18nProviderProps } from './i18n-provider';
export { type I18nContextValue } from './i18n-context';
export { useFormatting, useTranslation, useLocale, useI18n } from './i18n-hooks';

export { MotionProvider } from './motion-provider';
export type { MotionProviderProps, MotionContextValue } from './motion-types';
export { useMotion, useAnimationVariants } from './motion-context';

export { PreferencesProvider } from './preferences-provider';
export type { PreferencesProviderProps } from './preferences-provider';
export type { UserPreferences, PreferencesContextValue } from './preferences-context';
export { useThemePreference, useAnimationPreference, useAccessibilityPreference, usePreferences } from './preferences-hooks';

export { RBACProvider } from './rbac-provider';
export type { RBACProviderProps } from './rbac-provider';
export type { RBACContextValue } from './rbac-context';
export { useRBAC } from './rbac-hooks';

export { ThemeProvider } from './theme-provider';
export type { ThemeProviderProps } from './theme-provider';
export type { Theme, ThemeContextValue, Density } from './theme-context';
export { useTheme } from './theme-hooks';
