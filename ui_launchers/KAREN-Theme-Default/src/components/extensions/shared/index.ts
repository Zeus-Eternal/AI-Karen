// Shared extension components
export { default as ExtensionControls } from '../ExtensionControls';
export { default as ExtensionSettingsPanel } from '../ExtensionSettingsPanel';

// Shared utility components
export { default as ExtensionCard } from './ExtensionCard';
export type { ExtensionCardProps } from './ExtensionCard';

export { default as ExtensionStatusBadge } from './ExtensionStatusBadge';
export type { ExtensionStatusBadgeProps } from './ExtensionStatusBadge';

export { default as ExtensionHealthIndicator } from './ExtensionHealthIndicator';
export type { ExtensionHealthIndicatorProps, HealthState } from './ExtensionHealthIndicator';

// Types and utilities
export * from './types';
export * from './hooks';