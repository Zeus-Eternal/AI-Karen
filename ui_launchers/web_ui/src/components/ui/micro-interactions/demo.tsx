'use client';

import React, { useState } from 'react';
import { InteractiveButton } from './interactive-button';
import { InteractiveInput } from './interactive-input';
import { InteractiveCard } from './interactive-card';
import { LoadingSpinner } from './loading-spinner';
import { ProgressAnimation } from './progress-animation';
import { MicroInteractionProvider } from './micro-interaction-provider';

export function MicroInteractionDemo() {
  const [loading, setLoading] = useState(false);
  const [inputError, setInputError] = useState(false);
  const [inputSuccess, setInputSuccess] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleButtonClick = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 2000);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value.length < 3) {
      setInputError(true);
      setInputSuccess(false);
    } else {
      setInputError(false);
      setInputSuccess(true);
    }
  };

  const incrementProgress = () => {
    setProgress(prev => Math.min(prev + 10, 100));
  };

  const resetProgress = () => {
    setProgress(0);
  };

  return (
    <MicroInteractionProvider>
      <div className="p-8 space-y-8 max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Micro-Interactions Demo</h1>
        
        {/* Interactive Buttons */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold">Interactive Buttons</h2>
          <div className="flex gap-4 flex-wrap">
            <InteractiveButton 
              onClick={handleButtonClick}
              loading={loading}
              loadingText="Processing..."
            >
              Click Me
            </InteractiveButton>
            
            <InteractiveButton 
              variant="outline"
              animationVariant="bounce"
            >
              Bounce Effect
            </InteractiveButton>
            
            <InteractiveButton 
              variant="secondary"
              animationVariant="scale"
            >
              Scale Effect
            </InteractiveButton>
            
            <InteractiveButton 
              variant="ghost"
              animationVariant="slide"
            >
              Slide Effect
            </InteractiveButton>
          </div>
        </section>

        {/* Interactive Inputs */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold">Interactive Inputs</h2>
          <div className="space-y-4 max-w-md">
            <InteractiveInput
              placeholder="Type at least 3 characters..."
              error={inputError}
              success={inputSuccess}
              onChange={handleInputChange}
              animationVariant="default"
            />
            
            <InteractiveInput
              placeholder="Glow effect on focus"
              animationVariant="glow"
            />
            
            <InteractiveInput
              placeholder="Shake on error"
              animationVariant="shake"
              error={true}
            />
          </div>
        </section>

        {/* Interactive Cards */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold">Interactive Cards</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <InteractiveCard 
              interactive 
              hoverEffect="lift"
              className="p-6"
            >
              <h3 className="text-lg font-semibold mb-2">Lift Effect</h3>
              <p className="text-muted-foreground">Hover to see the lift animation</p>
            </InteractiveCard>
            
            <InteractiveCard 
              interactive 
              hoverEffect="glow"
              variant="elevated"
              className="p-6"
            >
              <h3 className="text-lg font-semibold mb-2">Glow Effect</h3>
              <p className="text-muted-foreground">Hover to see the glow animation</p>
            </InteractiveCard>
            
            <InteractiveCard 
              interactive 
              hoverEffect="scale"
              variant="outlined"
              className="p-6"
            >
              <h3 className="text-lg font-semibold mb-2">Scale Effect</h3>
              <p className="text-muted-foreground">Hover to see the scale animation</p>
            </InteractiveCard>
          </div>
        </section>

        {/* Loading Spinners */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold">Loading Spinners</h2>
          <div className="flex gap-8 items-center flex-wrap">
            <div className="text-center">
              <LoadingSpinner size="lg" />
              <p className="mt-2 text-sm">Default</p>
            </div>
            
            <div className="text-center">
              <LoadingSpinner variant="dots" size="lg" />
              <p className="mt-2 text-sm">Dots</p>
            </div>
            
            <div className="text-center">
              <LoadingSpinner variant="pulse" size="lg" />
              <p className="mt-2 text-sm">Pulse</p>
            </div>
            
            <div className="text-center">
              <LoadingSpinner variant="bars" size="lg" />
              <p className="mt-2 text-sm">Bars</p>
            </div>
          </div>
        </section>

        {/* Progress Animations */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold">Progress Animations</h2>
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-2">Linear Progress</h3>
              <ProgressAnimation 
                progress={progress} 
                showPercentage 
                animated 
              />
            </div>
            
            <div>
              <h3 className="text-lg font-medium mb-2">Circular Progress</h3>
              <ProgressAnimation 
                progress={progress} 
                variant="circular"
                showPercentage 
                animated 
              />
            </div>
            
            <div>
              <h3 className="text-lg font-medium mb-2">Dots Progress</h3>
              <ProgressAnimation 
                progress={progress} 
                variant="dots"
                showPercentage 
                animated 
              />
            </div>
            
            <div className="flex gap-4">
              <InteractiveButton onClick={incrementProgress}>
                Increment Progress
              </InteractiveButton>
              <InteractiveButton onClick={resetProgress} variant="outline">
                Reset Progress
              </InteractiveButton>
            </div>
          </div>
        </section>
      </div>
    </MicroInteractionProvider>
  );
}