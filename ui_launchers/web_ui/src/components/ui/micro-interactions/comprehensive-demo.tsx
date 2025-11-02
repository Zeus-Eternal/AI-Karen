"use client";

import React, { useState } from 'react';
import { MicroInteractionProvider } from './micro-interaction-provider';
import { HapticProvider } from '../haptic-feedback/haptic-provider';
import { TransitionProvider } from '../page-transitions/transition-provider';

// Import all demo components
import { MicroInteractionDemo } from './demo';
import { SkeletonDemo } from '../skeleton/skeleton-demo';
import { TransitionDemo } from '../page-transitions/transition-demo';
import { HapticDemo } from '../haptic-feedback/haptic-demo';

// Import individual components for the showcase
import { InteractiveButton } from './interactive-button';
import { InteractiveInput } from './interactive-input';
import { InteractiveCard } from './interactive-card';
import { LoadingSpinner } from './loading-spinner';
import { ProgressAnimation } from './progress-animation';

type DemoSection = 'overview' | 'micro-interactions' | 'skeletons' | 'transitions' | 'haptics';

export function ComprehensiveMicroInteractionDemo() {
  const [activeSection, setActiveSection] = useState<DemoSection>('overview');
  const [progress, setProgress] = useState(75);

  const sections = [
    { id: 'overview' as const, title: 'Overview', icon: '🎯' },
    { id: 'micro-interactions' as const, title: 'Micro-Interactions', icon: '✨' },
    { id: 'skeletons' as const, title: 'Skeleton States', icon: '💀' },
    { id: 'transitions' as const, title: 'Page Transitions', icon: '🔄' },
    { id: 'haptics' as const, title: 'Haptic Feedback', icon: '📳' }
  ];

  const renderContent = () => {
    switch (activeSection) {
      case 'micro-interactions':
        return <MicroInteractionDemo />;
      case 'skeletons':
        return <SkeletonDemo />;
      case 'transitions':
        return <TransitionDemo />;
      case 'haptics':
        return <HapticDemo />;
      default:
        return (
          <div className="space-y-8">
            <div className="text-center space-y-4">
              <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                Modern UI Micro-Interactions
              </h1>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto ">
                A comprehensive collection of modern micro-interactions, animations, and feedback systems 
                designed to enhance user experience with smooth, accessible, and delightful interactions.
              </p>
            </div>

            {/* Feature Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <InteractiveCard 
                interactive 
                hoverEffect="lift"
                className="p-6 text-center sm:p-4 md:p-6"
              >
                <div className="text-4xl mb-4">✨</div>
                <h3 className="text-lg font-semibold mb-2">Micro-Interactions</h3>
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                </p>
              </InteractiveCard>

              <InteractiveCard 
                interactive 
                hoverEffect="glow"
                variant="elevated"
                className="p-6 text-center sm:p-4 md:p-6"
              >
                <div className="text-4xl mb-4">💀</div>
                <h3 className="text-lg font-semibold mb-2">Skeleton Loading</h3>
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                </p>
              </InteractiveCard>

              <InteractiveCard 
                interactive 
                hoverEffect="scale"
                variant="outlined"
                className="p-6 text-center sm:p-4 md:p-6"
              >
                <div className="text-4xl mb-4">🔄</div>
                <h3 className="text-lg font-semibold mb-2">Page Transitions</h3>
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                  Smooth route-based transitions with multiple variants
                </p>
              </InteractiveCard>

              <InteractiveCard 
                interactive 
                hoverEffect="lift"
                variant="glass"
                className="p-6 text-center sm:p-4 md:p-6"
              >
                <div className="text-4xl mb-4">📳</div>
                <h3 className="text-lg font-semibold mb-2">Haptic Feedback</h3>
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                </p>
              </InteractiveCard>
            </div>

            {/* Interactive Showcase */}
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold">Interactive Showcase</h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Left Column - Buttons and Inputs */}
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium mb-4">Interactive Buttons</h3>
                    <div className="flex flex-wrap gap-3">
                      <InteractiveButton animationVariant="default">
                      </InteractiveButton>
                      <InteractiveButton animationVariant="bounce" variant="outline">
                      </InteractiveButton>
                      <InteractiveButton animationVariant="scale" variant="secondary">
                      </InteractiveButton>
                      <InteractiveButton animationVariant="slide" variant="ghost">
                      </InteractiveButton>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-medium mb-4">Interactive Inputs</h3>
                    <div className="space-y-3">
                      <InteractiveInput 
                        placeholder="Default animation"
                        animationVariant="default"
                      />
                      <InteractiveInput 
                        placeholder="Glow effect on focus"
                        animationVariant="glow"
                      />
                      <InteractiveInput 
                        placeholder="Success state"
                        success={true}
                      />
                    </div>
                  </div>
                </div>

                {/* Right Column - Progress and Spinners */}
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium mb-4">Loading Animations</h3>
                    <div className="flex items-center justify-around p-6 border rounded-lg sm:p-4 md:p-6">
                      <div className="text-center">
                        <LoadingSpinner size="md" />
                        <p className="text-xs mt-2 sm:text-sm md:text-base">Default</p>
                      </div>
                      <div className="text-center">
                        <LoadingSpinner variant="dots" size="md" />
                        <p className="text-xs mt-2 sm:text-sm md:text-base">Dots</p>
                      </div>
                      <div className="text-center">
                        <LoadingSpinner variant="pulse" size="md" />
                        <p className="text-xs mt-2 sm:text-sm md:text-base">Pulse</p>
                      </div>
                      <div className="text-center">
                        <LoadingSpinner variant="bars" size="md" />
                        <p className="text-xs mt-2 sm:text-sm md:text-base">Bars</p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-medium mb-4">Progress Animations</h3>
                    <div className="space-y-4">
                      <ProgressAnimation 
                        progress={progress} 
                        showPercentage 
                        animated 
                      />
                      <ProgressAnimation 
                        progress={progress} 
                        variant="circular"
                        showPercentage 
                        animated 
                      />
                      <div className="flex gap-2">
                        <InteractiveButton 
                          size="sm"
                          onClick={() => setProgress(Math.min(progress + 10, 100))}
                        >
                          +10%
                        </InteractiveButton>
                        <InteractiveButton 
                          size="sm"
                          variant="outline"
                          onClick={() => setProgress(Math.max(progress - 10, 0))}
                        >
                          -10%
                        </InteractiveButton>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Features List */}
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold">Key Features</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Accessibility First</h3>
                  <ul className="space-y-2 text-sm text-muted-foreground md:text-base lg:text-lg">
                    <li>✅ Respects prefers-reduced-motion</li>
                    <li>✅ Keyboard navigation support</li>
                    <li>✅ Screen reader friendly</li>
                    <li>✅ High contrast mode support</li>
                    <li>✅ Focus management</li>
                  </ul>
                </div>
                
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Performance Optimized</h3>
                  <ul className="space-y-2 text-sm text-muted-foreground md:text-base lg:text-lg">
                    <li>✅ Hardware accelerated animations</li>
                    <li>✅ 60fps smooth transitions</li>
                    <li>✅ Minimal layout shifts</li>
                    <li>✅ Efficient re-renders</li>
                    <li>✅ Lazy loading support</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <MicroInteractionProvider>
      <HapticProvider>
        <TransitionProvider>
          <div className="min-h-screen bg-background">
            {/* Navigation */}
            <nav className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
              <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-16">
                  <div className="flex items-center space-x-4">
                    <h1 className="text-xl font-bold">UI Micro-Interactions</h1>
                  </div>
                  <div className="flex items-center space-x-1">
                    {sections.map((section) => (
                      <InteractiveButton
                        key={section.id}
                        variant={activeSection === section.id ? 'default' : 'ghost'}
                        size="sm"
                        onClick={() => setActiveSection(section.id)}
                        className="text-sm md:text-base lg:text-lg"
                      >
                        <span className="mr-2">{section.icon}</span>
                        {section.title}
                      </InteractiveButton>
                    ))}
                  </div>
                </div>
              </div>
            </nav>

            {/* Content */}
            <main className="container mx-auto px-4 py-8">
              {renderContent()}
            </main>
          </div>
        </TransitionProvider>
      </HapticProvider>
    </MicroInteractionProvider>
  );
}