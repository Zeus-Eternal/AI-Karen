import React from 'react';
import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { 
import {
import { useProgressiveEnhancement } from '@/utils/progressive-enhancement';
import { useFeatureDetection } from '@/utils/feature-detection';
'use client';






  ModernErrorBoundary,
  SidebarErrorBoundary,
  RightPanelErrorBoundary,
  FormErrorBoundary,
  ModalErrorBoundary,
} from './section-error-boundaries';

  RetryButton,
  RetryCard,
  RetryWrapper,
  InlineRetry,
  RetryBanner,
  LoadingRetry,
} from '../ui/retry-components';

  withRetry,
  useAsyncRetry,
  RetryBoundary,
  useRetryFetch,
} from '../ui/with-retry';

  FadeAnimation,
  SlideAnimation,
  ScaleAnimation,
  CollapseAnimation,
  SpinnerAnimation,
} from '../ui/animation-fallbacks';


// Test components that can throw errors
const ThrowError = ({ shouldThrow = false, message = 'Test error' }) => {
  if (shouldThrow) {
    throw new Error(message);
  }
  return <div className="p-4 bg-green-100 rounded sm:p-4 md:p-6">✅ Component working correctly</div>;
};
const AsyncOperation = ({ shouldFail = false, delay = 1000 }) => {
  const operation = React.useCallback(async () => {
    await new Promise(resolve => setTimeout(resolve, delay));
    if (shouldFail) {
      throw new Error('Async operation failed');
    }
    return 'Async operation completed successfully!';
  }, [shouldFail, delay]);
  const { data, error, isLoading, isRetrying, retry, canRetry } = useAsyncRetry(operation, {
    maxAttempts: 3,
    baseDelay: 1000,
    retryOnMount: true,
  });

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <LoadingRetry
      isLoading={isLoading}
      isRetrying={isRetrying}
      error={error}
      onRetry={retry}
    >
      <div className="p-4 bg-green-100 rounded sm:p-4 md:p-6">
        ✅ {data}
      </div>
    </LoadingRetry>
  );
};
const FetchDemo = () => {
  const [url, setUrl] = React.useState('/api/test');
  const { data, error, isLoading, isRetrying, execute, retry, canRetry } = useRetryFetch(url, {}, {
    maxAttempts: 3,
    baseDelay: 1000,
  });
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button onClick={() = aria-label="Button"> { setUrl('/api/success'); execute(); }}>
          Test Success
        </Button>
        <button onClick={() = aria-label="Button"> { setUrl('/api/error'); execute(); }}>
          Test Error
        </Button>
        <button onClick={() = aria-label="Button"> { setUrl('/api/timeout'); execute(); }}>
          Test Timeout
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
            ✅ Fetch successful: {url}
          </div>
        )}
      </LoadingRetry>
    </div>
  );
};
const FeatureDetectionDemo = () => {
  const { features, supportsModernCSS, supportsAdvancedFeatures } = useFeatureDetection();
  const enhancements = useProgressiveEnhancement();
  if (!features) {
    return <SpinnerAnimation size={24} className="mx-auto" />;
  }
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">CSS Features</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span>Grid:</span>
              <Badge variant={features.cssGrid ? 'default' : 'secondary'}>
                {features.cssGrid ? 'Supported' : 'Not Supported'}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span>Custom Properties:</span>
              <Badge variant={features.cssCustomProperties ? 'default' : 'secondary'}>
                {features.cssCustomProperties ? 'Supported' : 'Not Supported'}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span>Container Queries:</span>
              <Badge variant={features.cssContainerQueries ? 'default' : 'secondary'}>
                {features.cssContainerQueries ? 'Supported' : 'Not Supported'}
              </Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">Enhancement Level</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span>Modern CSS:</span>
              <Badge variant={supportsModernCSS() ? 'default' : 'secondary'}>
                {supportsModernCSS() ? 'Yes' : 'No'}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span>Advanced Features:</span>
              <Badge variant={supportsAdvancedFeatures() ? 'default' : 'secondary'}>
                {supportsAdvancedFeatures() ? 'Yes' : 'No'}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span>Animations:</span>
              <Badge variant={enhancements.animation.useTransitions ? 'default' : 'secondary'}>
                {enhancements.animation.useTransitions ? 'Enabled' : 'Disabled'}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
const AnimationFallbackDemo = () => {
  const [showFade, setShowFade] = React.useState(true);
  const [showSlide, setShowSlide] = React.useState(true);
  const [showScale, setShowScale] = React.useState(true);
  const [showCollapse, setShowCollapse] = React.useState(true);
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <button onClick={() = aria-label="Button"> setShowFade(!showFade)}>
          Toggle Fade
        </Button>
        <button onClick={() = aria-label="Button"> setShowSlide(!showSlide)}>
          Toggle Slide
        </Button>
        <button onClick={() = aria-label="Button"> setShowScale(!showScale)}>
          Toggle Scale
        </Button>
        <button onClick={() = aria-label="Button"> setShowCollapse(!showCollapse)}>
          Toggle Collapse
        </Button>
      </div>
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">Fade Animation</CardTitle>
          </CardHeader>
          <CardContent>
            <FadeAnimation show={showFade}>
              <div className="p-4 bg-blue-100 rounded sm:p-4 md:p-6">
                This content fades in and out
              </div>
            </FadeAnimation>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">Slide Animation</CardTitle>
          </CardHeader>
          <CardContent>
            <SlideAnimation show={showSlide} direction="up">
              <div className="p-4 bg-green-100 rounded sm:p-4 md:p-6">
                This content slides up and down
              </div>
            </SlideAnimation>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">Scale Animation</CardTitle>
          </CardHeader>
          <CardContent>
            <ScaleAnimation show={showScale}>
              <div className="p-4 bg-purple-100 rounded sm:p-4 md:p-6">
                This content scales in and out
              </div>
            </ScaleAnimation>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">Collapse Animation</CardTitle>
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
export function ErrorHandlingDemo() {
  const [errorStates, setErrorStates] = React.useState({
    sidebar: false,
    rightPanel: false,
    form: false,
    modal: false,
    async: false,
  });
  const toggleError = (component: keyof typeof errorStates) => {
    setErrorStates(prev => ({ ...prev, [component]: !prev[component] }));
  };
  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6 sm:w-auto md:w-full">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">Error Handling & Graceful Degradation Demo</h1>
        <p className="text-muted-foreground">
          Comprehensive demonstration of modern error handling, retry mechanisms, and progressive enhancement
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
        <TabsContent value="error-boundaries" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Sidebar Error Boundary</CardTitle>
                <CardDescription>
                  Specialized error boundary for sidebar components
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <button onClick={() = aria-label="Button"> toggleError('sidebar')}>
                  {errorStates.sidebar ? 'Fix Sidebar' : 'Break Sidebar'}
                </Button>
                <SidebarErrorBoundary>
                  <ThrowError shouldThrow={errorStates.sidebar} message="Sidebar component failed" />
                </SidebarErrorBoundary>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Right Panel Error Boundary</CardTitle>
                <CardDescription>
                  Specialized error boundary for right panel components
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <button onClick={() = aria-label="Button"> toggleError('rightPanel')}>
                  {errorStates.rightPanel ? 'Fix Panel' : 'Break Panel'}
                </Button>
                <RightPanelErrorBoundary>
                  <ThrowError shouldThrow={errorStates.rightPanel} message="Right panel component failed" />
                </RightPanelErrorBoundary>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Form Error Boundary</CardTitle>
                <CardDescription>
                  Specialized error boundary for form components
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <button onClick={() = aria-label="Button"> toggleError('form')}>
                  {errorStates.form ? 'Fix Form' : 'Break Form'}
                </Button>
                <FormErrorBoundary>
                  <ThrowError shouldThrow={errorStates.form} message="Form component failed" />
                </FormErrorBoundary>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Modal Error Boundary</CardTitle>
                <CardDescription>
                  Specialized error boundary for modal components
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <button onClick={() = aria-label="Button"> toggleError('modal')}>
                  {errorStates.modal ? 'Fix Modal' : 'Break Modal'}
                </Button>
                <ModalErrorBoundary>
                  <ThrowError shouldThrow={errorStates.modal} message="Modal component failed" />
                </ModalErrorBoundary>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        <TabsContent value="retry-mechanisms" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Async Operation with Retry</CardTitle>
                <CardDescription>
                  Demonstrates automatic retry with exponential backoff
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex gap-2">
                    <button onClick={() = aria-label="Button"> toggleError('async')}>
                      {errorStates.async ? 'Make Succeed' : 'Make Fail'}
                    </Button>
                  </div>
                  <AsyncOperation shouldFail={errorStates.async} delay={1000} />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Fetch with Retry</CardTitle>
                <CardDescription>
                  HTTP requests with intelligent retry logic
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
                  Various retry UI components and patterns
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <RetryCard
                    title="Network Error"
                    description="Failed to connect to server"
                    error={new Error('Network connection failed')}
                    onRetry={() => console.log('Retry clicked')}
                    attempt={2}
                    maxAttempts={3}
                    canRetry={true}
                  />
                  <div className="space-y-2">
                    <h4 className="font-medium">Inline Retry</h4>
                    <InlineRetry
                      error={new Error('Failed to load data')}
                      onRetry={() => console.log('Inline retry')}
                      canRetry={true}
                    />
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">Retry Button</h4>
                    <RetryButton
                      onRetry={() => console.log('Button retry')}
                      isRetrying={false}
                    />
                  </div>
                </div>
                <RetryBanner
                  message="Connection lost. Please check your internet connection."
                  onRetry={() => console.log('Banner retry')}
                  onDismiss={() => console.log('Banner dismissed')}
                  variant="warning"
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>
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
        <TabsContent value="animation-fallbacks" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Animation Fallbacks</CardTitle>
              <CardDescription>
                Graceful degradation for animations based on browser support and user preferences
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AnimationFallbackDemo />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="comprehensive" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Comprehensive Error Handling</CardTitle>
              <CardDescription>
                Complete error handling system with all features combined
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RetryBoundary
                maxRetries={3}
                retryDelay={2000}
                onError={(error, errorInfo) => {
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
                    <p>This section demonstrates the complete error handling system.</p>
                    <button onClick={() = aria-label="Button"> {
                      throw new Error('Comprehensive demo error');
                    }}>
                      Trigger Comprehensive Error
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
