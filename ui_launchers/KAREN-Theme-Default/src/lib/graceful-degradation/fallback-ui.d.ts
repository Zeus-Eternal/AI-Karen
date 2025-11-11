declare module "./fallback-ui" {
  import type { ReactNode } from 'react';

  export interface FallbackUIProps {
    serviceName: string;
    error?: Error | string;
    onRetry?: () => void;
    showRetry?: boolean;
    children?: ReactNode;
  }

  export interface ServiceUnavailableProps extends FallbackUIProps {
    lastSuccessfulConnection?: Date;
    estimatedRecoveryTime?: Date;
  }

  export interface ExtensionUnavailableProps extends FallbackUIProps {
    extensionName: string;
    fallbackData?: unknown;
    showFallbackData?: boolean;
  }

  export function ServiceUnavailable(props: ServiceUnavailableProps): JSX.Element;
  export function ExtensionUnavailable(props: ExtensionUnavailableProps): JSX.Element;
  export function LoadingWithFallback(props: {
    serviceName: string;
    timeout?: number;
    onTimeout?: () => void;
    children?: ReactNode;
  }): JSX.Element;
  export function DegradedModeBanner(props: {
    affectedServices: string[];
    onDismiss?: () => void;
    showDetails?: boolean;
    title?: string;
    subtitle?: string;
  }): JSX.Element;

  export function ProgressiveEnhancement(props: {
    featureName: string;
    fallbackComponent: ReactNode;
    enhancedComponent: ReactNode;
    loadingComponent?: ReactNode;
    errorComponent?: ReactNode;
    detect?: () => Promise<boolean>;
  }): JSX.Element;
}
