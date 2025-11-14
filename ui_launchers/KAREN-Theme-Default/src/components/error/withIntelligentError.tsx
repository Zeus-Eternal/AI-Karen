// ui_launchers/KAREN-Theme-Default/src/components/error/withIntelligentError.tsx
/**
 * Higher-Order Component for Intelligent Error Detection
 *
 * Wraps components with automatic error detection and intelligent response display.
 * Provides seamless integration of intelligent error handling into existing components.
 *
 * Requirements: 3.2, 3.3, 3.7, 4.4
 */

"use client";

import React, {
  ComponentType,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  IntelligentErrorPanel,
  type IntelligentErrorPanelProps,
} from "./IntelligentErrorPanel";
import {
  useIntelligentError,
  type UseIntelligentErrorOptions,
} from "@/hooks/use-intelligent-error";

/* ---------------------------- Types & Options ---------------------------- */

export interface WithIntelligentErrorOptions extends UseIntelligentErrorOptions {
  /** Whether to show the error panel automatically when an error is detected */
  autoShow?: boolean;
  /** Position of the error panel relative to the wrapped component */
  position?: "top" | "bottom" | "overlay";
  /** Replace wrapped content with the error panel when an error occurs */
  replaceOnError?: boolean;
  /** Props passed to IntelligentErrorPanel (partial override) */
  errorPanelProps?: Partial<IntelligentErrorPanelProps>;
  /** Custom error detection function */
  detectError?: (props: Record<string, unknown>, prevProps?: unknown) => Error | string | null;
  /** Whether to monitor prop changes for errors */
  monitorProps?: boolean;
  /** Props to monitor for error conditions */
  errorProps?: string[];
  /** Optional name for telemetry */
  boundaryName?: string;
}

export interface WithIntelligentErrorProps {
  /** Error to analyze (can be passed directly) */
  error?: Error | string;
  /** Force show/hide the intelligent error panel */
  showIntelligentError?: boolean;
  /** Called when the error panel is dismissed */
  onErrorDismiss?: () => void;
  /** Additional context for error analysis */
  errorContext?: Record<string, unknown>;
  /** Optional unique id to improve stabilization between re-renders */
  errorContextId?: string | number;
}

/* ------------------------------ Utilities ------------------------------- */

function normalizeError(e: Error | string | null | undefined) {
  if (!e) return null;
  if (typeof e === "string") return e.trim();
  if (e instanceof Error) return e.message?.trim() || String(e);
  try {
    return String(e).trim();
  } catch {
    return "unknown error";
  }
}

/* --------------------------------- HOC ---------------------------------- */

export function withIntelligentError<P extends object>(
  WrappedComponent: ComponentType<P>,
  options: WithIntelligentErrorOptions = {}
) {
  const {
    autoShow = true,
    position = "top",
    replaceOnError = false,
    errorPanelProps = {},
    detectError,
    monitorProps = true,
    errorProps = ["error", "errorMessage", "hasError"],
    boundaryName,
    ...intelligentErrorOptions
  } = options;

  const WithIntelligentErrorComponent: React.FC<P & WithIntelligentErrorProps> = (
    props
  ) => {
    const {
      error: propError,
      showIntelligentError,
      onErrorDismiss,
      errorContext,
      errorContextId,
      ...wrappedProps
    } = props as P & WithIntelligentErrorProps;

    const [showPanel, setShowPanel] = useState<boolean>(false);
    const [detectedError, setDetectedError] = useState<Error | string | null>(
      null
    );

    // Guard against duplicate analyses of the same error payload
    const lastAnalyzedKeyRef = useRef<string>("");

    // Memoize component label for context
    const componentLabel = useMemo(
      () => WrappedComponent.displayName || WrappedComponent.name || "AnonymousComponent",
      []
    );

    // Wire up the analyzer with an onAnalysisComplete tap-in
    const intelligentError = useIntelligentError({
      ...intelligentErrorOptions,
      onAnalysisComplete: (analysis) => {
        if (autoShow) setShowPanel(true);
        intelligentErrorOptions.onAnalysisComplete?.(analysis);
        // Best-effort telemetry
        try {
          const dispatchTarget = window as { dispatchEvent?: (event: Event) => void };
          dispatchTarget?.dispatchEvent?.(
            new CustomEvent("kari:intelligent-error", {
              detail: {
                boundary: boundaryName ?? "withIntelligentError",
                component: componentLabel,
                result: analysis?.summary ?? "analysis_complete",
              },
            })
          );
        } catch {
          /* noop */
        }
      },
    });

    // Keep a previous-props ref for custom detectors that need diffing
    const prevPropsRef = useRef<(P & WithIntelligentErrorProps) | null>(null);
    useEffect(() => {
      prevPropsRef.current = props;
    }, [props]);

    /* -------------------------- Error Detection -------------------------- */
    useEffect(() => {
      const propsRecord = props as Record<string, unknown>;
      let errorToAnalyze: Error | string | null = null;

      // 1) Direct error prop takes precedence
      if (propError) {
        errorToAnalyze = propError;
      }
      // 2) Custom detector (optional, receives prev props)
      else if (typeof detectError === "function") {
        errorToAnalyze = detectError(propsRecord, prevPropsRef.current);
      }
      // 3) Scan known error-ish props
      else if (monitorProps && errorProps.length > 0) {
        for (const key of errorProps) {
          const val = propsRecord[key];
          if (!val) continue;

          if (typeof val === "string" || val instanceof Error) {
            errorToAnalyze = val;
            break;
          }

          if (typeof val === "boolean" && val === true) {
            // Try <propName>Message or derived message key
              const msgKeyCandidates = [
                `${key}Message`,
                key.replace(/^(has|is)/i, "").replace(/^\w/, (c) => c.toLowerCase()) + "Message",
                "message",
              ];
              const msg = msgKeyCandidates
                .map((k) => propsRecord[k])
                .find((m) => typeof m === "string" && m.trim().length > 0);
            errorToAnalyze = (msg as string) || `Error detected in ${key}`;
            break;
          }
        }
      }

      // Stabilize the error key to avoid repeated analyses of the same input
      const normalized = normalizeError(errorToAnalyze);
      const contextKey =
        typeof errorContextId !== "undefined"
          ? String(errorContextId)
          : JSON.stringify(errorContext ?? {});
      const newKey = normalized ? `${normalized}::${contextKey}` : "";

      // Analyze only if error exists and changed
      if (normalized && newKey !== lastAnalyzedKeyRef.current) {
        setDetectedError(errorToAnalyze!);
        lastAnalyzedKeyRef.current = newKey;

        intelligentError.analyzeError(errorToAnalyze!, {
          // Provide consistent context envelope for downstream prompt tools
          user_context: {
            boundary: boundaryName ?? "withIntelligentError",
            component: componentLabel,
            props: errorContext ?? {},
          },
        });

        if (autoShow) setShowPanel(true);
      } else if (!normalized && detectedError) {
        // Clear when error condition disappears
        setDetectedError(null);
        setShowPanel(false);
        lastAnalyzedKeyRef.current = "";
        intelligentError.clearAnalysis();
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [
      propError,
      detectError,
      monitorProps,
      errorProps,
      errorContextId,
      errorContext,
      componentLabel,
      boundaryName,
      intelligentError,
      props, // monitored by design; HOC is about prop-based detection
    ]);

    /* ---------------------------- Panel Controls --------------------------- */
    const handleDismiss = () => {
      setShowPanel(false);
      onErrorDismiss?.();
    };

    const handleRetry = () => {
      // Clear state so detection can re-trigger if the signal remains
      setDetectedError(null);
      setShowPanel(false);
      lastAnalyzedKeyRef.current = "";
      intelligentError.clearAnalysis();
      // Note: If your wrapped component supports a retry prop/callback,
      // pass it in and invoke here.
    };

    const shouldShowPanel =
      (showIntelligentError ?? showPanel) &&
      (Boolean(intelligentError.analysis) || intelligentError.isAnalyzing);

    /* ------------------------------ Rendering ------------------------------ */

    const panel = shouldShowPanel ? (
      <IntelligentErrorPanel
        error={detectedError || "unknown error"}
        onDismiss={handleDismiss}
        onRetry={handleRetry}
        autoFetch={false} // analysis is orchestrated here
        {...errorPanelProps}
      />
    ) : null;

    if (replaceOnError && shouldShowPanel) {
      return (
        <div className="relative" data-testid="intelligent-error-replaced">
          {panel}
        </div>
      );
    }

    return (
      <div className="relative" data-testid="intelligent-error-wrapper">
        {/* Top */}
        {position === "top" && shouldShowPanel && (
          <div className="mb-4">{panel}</div>
        )}

        {/* Overlay */}
        {position === "overlay" && shouldShowPanel && (
          <div className="absolute inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="w-full max-w-2xl">{panel}</div>
          </div>
        )}

        {/* Wrapped content */}
        <WrappedComponent {...(wrappedProps as P)} />

        {/* Bottom */}
        {position === "bottom" && shouldShowPanel && (
          <div className="mt-4">{panel}</div>
        )}
      </div>
    );
  };

  WithIntelligentErrorComponent.displayName = `withIntelligentError(${WrappedComponent.displayName || WrappedComponent.name || "Component"})`;

  return WithIntelligentErrorComponent;
}

/* ----------------------- Decorator for class components ----------------------- */

export function intelligentErrorDecorator(options: WithIntelligentErrorOptions = {}) {
  return function <P extends object>(WrappedComponent: ComponentType<P>) {
    return withIntelligentError(WrappedComponent, options);
  };
}

export default withIntelligentError;
