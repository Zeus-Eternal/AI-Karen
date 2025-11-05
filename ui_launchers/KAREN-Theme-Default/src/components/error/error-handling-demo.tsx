// ui_launchers/KAREN-Theme-Default/src/components/error/error-handling-demo.tsx
"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

import { useProgressiveEnhancement } from "@/utils/progressive-enhancement";
import { useFeatureDetection } from "@/utils/feature-detection";

/* --- Error boundary sections --- */
import {
  SidebarErrorBoundary,
  RightPanelErrorBoundary,
  FormErrorBoundary,
  ModalErrorBoundary,
  ModernErrorBoundary,
  RetryBoundary,
} from "./section-error-boundaries";

/* --- Retry primitives & helpers --- */
import {
  LoadingRetry,
  RetryCard,
  InlineRetry,
  RetryButton,
  RetryBanner,
} from "../ui/retry-components";

import {
  withRetry,
  useAsyncRetry,
  useRetryFetch,
} from "../ui/with-retry";

/* --- Animation fallbacks --- */
import {
  FadeAnimation,
  SlideAnimation,
  ScaleAnimation,
  CollapseAnimation,
  SpinnerAnimation,
} from "../ui/animation-fallbacks";

/* =========================================================================
 * Test Util Components
 * ========================================================================= */

const ThrowError: React.FC<{ shouldThrow?: boolean; message?: string }> = ({
  shouldThrow = false,
  message = "Test error",
}) => {
  if (shouldThrow) throw new Error(message);
  return (
    <div className="p-4 bg-green-100 rounded sm:p-4 md:p-6">
      ✅ Component working correctly
    </div>
  );
};

const AsyncOperation: React.FC<{ shouldFail?: boolean; delay?: number }> = ({
  shouldFail = false,
  delay = 1000,
}) => {
  const operation = React.useCallback(async () => {
    await new Promise((r) => setTimeout(r, delay));
    if (shouldFail) throw new Error("Async operation failed");
    return "Async operation completed successfully!";
  }, [shouldFail, delay]);

  const { data, error, isLoading, isRetrying, retry } = useAsyncRetry(operation, {
    maxAttempts: 3,
    baseDelay: 800,
    retryOnMount: true,
  });

  return (
    <LoadingRetry
      isLoading={isLoading}
      isRetrying={isRetrying}
      error={error}
      onRetry={retry}
    >
      <div className="p-4 bg-green-100 rounded sm:p-4 md:p-6">✅ {data}</div>
    </LoadingRetry>
  );
};

const FetchDemo: React.FC = () => {
  const [url, setUrl] = React.useState("/api/test");
  const { data, error, isLoading, isRetrying, execute, retry } = useRetryFetch(
    url,
    {},
    { maxAttempts: 3, baseDelay: 700 }
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Button
          onClick={() => {
            setUrl("/api/success");
            execute();
          }}
        >
          Hit /api/success
        </Button>
        <Button
          variant="outline"
          onClick={() => {
            setUrl("/api/error");
            execute();
          }}
        >
          Hit /api/error
        </Button>
        <Button
          variant="secondary"
          onClick={() => {
            setUrl("/api/timeout");
            execute();
          }}
        >
          Hit /api/timeout
        </Button>
      </div>

      <LoadingRetry
        isLoading={isLoading}
        isRetrying={isRetrying}
        error={error}
        onRetry={retry}
      >
        {data && (
          <div className="p-4 bg-green-100 rounded sm:p-4 md:p-6">
            ✅ Fetch successful: <code className="font-mono">{url}</code>
          </div>
        )}
      </LoadingRetry>
    </div>
  );
};

const FeatureDetectionDemo: React.FC = () => {
  const { features, supportsModernCSS, supportsAdvancedFeatures } =
    useFeatureDetection();
  const enhancements = useProgressiveEnhancement();

  if (!features) return <SpinnerAnimation size={24} className="mx-auto" />;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">
              CSS Features
            </CardTitle>
            <CardDescription>Live capability probing</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Row label="Grid" ok={features.cssGrid} />
            <Row label="Custom Properties" ok={features.cssCustomProperties} />
            <Row label="Container Queries" ok={features.cssContainerQueries} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">
              Enhancement Level
            </CardTitle>
            <CardDescription>Composite readiness signals</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Row label="Modern CSS" ok={supportsModernCSS()} />
            <Row label="Advanced Features" ok={supportsAdvancedFeatures()} />
            <Row label="Animations" ok={!!enhancements.animation.useTransitions} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const Row: React.FC<{ label: string; ok: boolean }> = ({ label, ok }) => (
  <div className="flex justify-between">
    <span>{label}:</span>
    <Badge variant={ok ? "default" : "secondary"}>
      {ok ? "Supported" : "Not Supported"}
    </Badge>
  </div>
);

const AnimationFallbackDemo: React.FC = () => {
  const [showFade, setShowFade] = React.useState(true);
  const [showSlide, setShowSlide] = React.useState(true);
  const [showScale, setShowScale] = React.useState(true);
  const [showCollapse, setShowCollapse] = React.useState(true);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Button onClick={() => setShowFade((v) => !v)}>
          Toggle Fade
        </Button>
        <Button variant="outline" onClick={() => setShowSlide((v) => !v)}>
          Toggle Slide
        </Button>
        <Button variant="secondary" onClick={() => setShowScale((v) => !v)}>
          Toggle Scale
        </Button>
        <Button variant="ghost" onClick={() => setShowCollapse((v) => !v)}>
          Toggle Collapse
        </Button>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">
              Fade Animation
            </CardTitle>
            <CardDescription>Fades content in/out</CardDescription>
          </CardHeader>
          <CardContent>
            <FadeAnimation show={showFade}>
              <div className="p-4 bg-blue-100 rounded sm:p-4 md:p-6">
                I fade like a rumor in the wind.
              </div>
            </FadeAnimation>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">
              Slide Animation
            </CardTitle>
            <CardDescription>Slides from the chosen edge</CardDescription>
          </CardHeader>
          <CardContent>
            <SlideAnimation show={showSlide} direction="up">
              <div className="p-4 bg-green-100 rounded sm:p-4 md:p-6">
                I slide in with style.
              </div>
            </SlideAnimation>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">
              Scale Animation
            </CardTitle>
            <CardDescription>Zooms content in/out</CardDescription>
          </CardHeader>
          <CardContent>
            <ScaleAnimation show={showScale}>
              <div className="p-4 bg-purple-100 rounded sm:p-4 md:p-6">
                I scale like ambition.
              </div>
            </ScaleAnimation>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">
              Collapse Animation
            </CardTitle>
            <CardDescription>Height transitions with content</CardDescription>
          </CardHeader>
          <CardContent>
            <CollapseAnimation show={showCollapse}>
              <div className="p-4 bg-yellow-100 rounded sm:p-4 md:p-6">
                <p>This content collapses and expands.</p>
                <p>It can contain multiple lines of content.</p>
                <p>The height animates smoothly.</p>
              </div>
            </CollapseAnimation>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

/* =========================================================================
 * Page Component
 * ========================================================================= */

export function ErrorHandlingDemo() {
  const [errorStates, setErrorStates] = React.useState({
    sidebar: false,
    rightPanel: false,
    form: false,
    modal: false,
    async: false,
  });

  const toggleError = (key: keyof typeof errorStates) =>
    setErrorStates((prev) => ({ ...prev, [key]: !prev[key] }));

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">
          Error Handling & Graceful Degradation Demo
        </h1>
        <p className="text-muted-foreground">
          Boundaries, retries, feature detection, and animation fallbacks—wired for
          resilience.
        </p>
      </div>

      <Tabs defaultValue="error-boundaries" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="error-boundaries">Error Boundaries</TabsTrigger>
          <TabsTrigger value="retry-mechanisms">Retry Mechanisms</TabsTrigger>
          <TabsTrigger value="feature-detection">Feature Detection</TabsTrigger>
          <TabsTrigger value="animation-fallbacks">Animation Fallbacks</TabsTrigger>
          <TabsTrigger value="comprehensive">Comprehensive</TabsTrigger>
        </TabsList>

        {/* ---------- Error Boundaries ---------- */}
        <TabsContent value="error-boundaries" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Sidebar Error Boundary</CardTitle>
                <CardDescription>
                  Localizes failures to the sidebar region.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button onClick={() => toggleError("sidebar")}>
                  {errorStates.sidebar ? "Fix Sidebar" : "Break Sidebar"}
                </Button>
                <SidebarErrorBoundary>
                  <ThrowError
                    shouldThrow={errorStates.sidebar}
                    message="Sidebar component failed"
                  />
                </SidebarErrorBoundary>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Right Panel Error Boundary</CardTitle>
                <CardDescription>
                  Contains and reports panel exceptions.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button onClick={() => toggleError("rightPanel")}>
                  {errorStates.rightPanel ? "Fix Panel" : "Break Panel"}
                </Button>
                <RightPanelErrorBoundary>
                  <ThrowError
                    shouldThrow={errorStates.rightPanel}
                    message="Right panel component failed"
                  />
                </RightPanelErrorBoundary>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Form Error Boundary</CardTitle>
                <CardDescription>Protects forms from fatal errors.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button onClick={() => toggleError("form")}>
                  {errorStates.form ? "Fix Form" : "Break Form"}
                </Button>
                <FormErrorBoundary>
                  <ThrowError
                    shouldThrow={errorStates.form}
                    message="Form component failed"
                  />
                </FormErrorBoundary>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Modal Error Boundary</CardTitle>
                <CardDescription>Isolates modal content failures.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button onClick={() => toggleError("modal")}>
                  {errorStates.modal ? "Fix Modal" : "Break Modal"}
                </Button>
                <ModalErrorBoundary>
                  <ThrowError
                    shouldThrow={errorStates.modal}
                    message="Modal component failed"
                  />
                </ModalErrorBoundary>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ---------- Retry Mechanisms ---------- */}
        <TabsContent value="retry-mechanisms" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Async Operation with Retry</CardTitle>
                <CardDescription>
                  Exponential backoff with attempt caps.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex gap-2">
                    <Button onClick={() => toggleError("async")}>
                      {errorStates.async ? "Make Succeed" : "Make Fail"}
                    </Button>
                  </div>
                  <AsyncOperation shouldFail={errorStates.async} delay={900} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Fetch with Retry</CardTitle>
                <CardDescription>
                  Network request demo with retries and status UI.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FetchDemo />
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Retry Components</CardTitle>
                <CardDescription>
                  Reusable building blocks for resilient flows.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <RetryCard
                    title="Network Error"
                    description="Failed to connect to server"
                    error={new Error("Network connection failed")}
                    onRetry={() => console.log("Retry clicked")}
                    attempt={2}
                    maxAttempts={3}
                    canRetry={true}
                  />

                  <div className="space-y-2">
                    <h4 className="font-medium">Inline Retry</h4>
                    <InlineRetry
                      error={new Error("Failed to load data")}
                      onRetry={() => console.log("Inline retry")}
                      canRetry={true}
                    />
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-medium">Retry Button</h4>
                    <RetryButton
                      onRetry={() => console.log("Button retry")}
                      isRetrying={false}
                    />
                  </div>
                </div>

                <RetryBanner
                  message="Connection lost. Please check your internet connection."
                  onRetry={() => console.log("Banner retry")}
                  onDismiss={() => console.log("Banner dismissed")}
                  variant="warning"
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ---------- Feature Detection ---------- */}
        <TabsContent value="feature-detection" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Feature Detection & Progressive Enhancement</CardTitle>
              <CardDescription>
                Real-time feature detection and enhancement level determination
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FeatureDetectionDemo />
            </CardContent>
          </Card>
        </TabsContent>

        {/* ---------- Animation Fallbacks ---------- */}
        <TabsContent value="animation-fallbacks" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Animation Fallbacks</CardTitle>
              <CardDescription>Graceful transitions on weak UAs</CardDescription>
            </CardHeader>
            <CardContent>
              <AnimationFallbackDemo />
            </CardContent>
          </Card>
        </TabsContent>

        {/* ---------- Comprehensive ---------- */}
        <TabsContent value="comprehensive" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Comprehensive Error Handling</CardTitle>
              <CardDescription>
                Boundary → Retry → Reporting pipeline in one place.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RetryBoundary
                maxRetries={3}
                retryDelay={2000}
                onError={(error, errorInfo) => {
                  // hook into audit/telemetry here
                  console.error("RetryBoundary error:", error, errorInfo);
                }}
              >
                <ModernErrorBoundary
                  section="comprehensive-demo"
                  maxRetries={3}
                  enableAutoRetry={true}
                  enableErrorReporting={true}
                  showTechnicalDetails={true}
                >
                  <div className="space-y-4">
                    <p>
                      This section demonstrates the complete error handling system,
                      including boundaries, retries, and reporting.
                    </p>
                    <Button
                      variant="destructive"
                      onClick={() => {
                        throw new Error("Comprehensive demo error");
                      }}
                    >
                      Trigger Error
                    </Button>
                  </div>
                </ModernErrorBoundary>
              </RetryBoundary>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default ErrorHandlingDemo;
