"use client";

import React, { useState } from 'react';
import { Skeleton } from './skeleton';
import { SkeletonText } from './skeleton-text';
import { SkeletonCard } from './skeleton-card';
import { SkeletonAvatar } from './skeleton-avatar';
import { SkeletonButton } from './skeleton-button';
import { SkeletonTable } from './skeleton-table';
import { MicroInteractionProvider } from '../micro-interactions/micro-interaction-provider';
import { InteractiveButton } from '../micro-interactions/interactive-button';

export function SkeletonDemo() {
  const [showSkeletons, setShowSkeletons] = useState(true);

  const toggleSkeletons = () => {
    setShowSkeletons(!showSkeletons);
  };

  return (
    <MicroInteractionProvider>
      <div className="p-8 space-y-8 max-w-6xl mx-auto ">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Skeleton Loading States Demo</h1>
          <InteractiveButton onClick={toggleSkeletons}>
            {showSkeletons ? 'Show Content' : 'Show Skeletons'}
          </InteractiveButton>
        </div>
        
        {showSkeletons ? (
          <>
            {/* Basic Skeletons */}
            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Basic Skeletons</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <h3 className="text-lg font-medium">Default</h3>
                  <Skeleton height="2rem" />
                  <Skeleton height="1rem" width="75%" />
                  <Skeleton height="1rem" width="50%" />
                </div>
                
                <div className="space-y-2">
                  <h3 className="text-lg font-medium">Rounded</h3>
                  <Skeleton height="2rem" variant="rounded" />
                  <Skeleton height="1rem" width="75%" variant="rounded" />
                  <Skeleton height="1rem" width="50%" variant="rounded" />
                </div>
                
                <div className="space-y-2">
                  <h3 className="text-lg font-medium">Circular</h3>
                  <div className="flex space-x-2">
                    <Skeleton width="3rem" height="3rem" variant="circular" />
                    <Skeleton width="2rem" height="2rem" variant="circular" />
                    <Skeleton width="1.5rem" height="1.5rem" variant="circular" />
                  </div>
                </div>
              </div>
            </section>

            {/* Text Skeletons */}
            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Text Skeletons</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h3 className="text-lg font-medium mb-2">Paragraph</h3>
                  <SkeletonText variant="paragraph" lines={4} />
                </div>
                
                <div>
                  <h3 className="text-lg font-medium mb-2">Heading</h3>
                  <SkeletonText variant="heading" lines={2} />
                </div>
                
                <div>
                  <h3 className="text-lg font-medium mb-2">Caption</h3>
                  <SkeletonText variant="caption" lines={3} />
                </div>
              </div>
            </section>

            {/* Avatar Skeletons */}
            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Avatar Skeletons</h2>
              <div className="flex items-center space-x-4">
                <SkeletonAvatar size="xs" />
                <SkeletonAvatar size="sm" />
                <SkeletonAvatar size="md" />
                <SkeletonAvatar size="lg" />
                <SkeletonAvatar size="xl" />
              </div>
            </section>

            {/* Button Skeletons */}
            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Button Skeletons</h2>
              <div className="flex flex-wrap gap-4">
                <SkeletonButton size="sm" />
                <SkeletonButton size="md" />
                <SkeletonButton size="lg" />
                <SkeletonButton variant="outline" />
                <SkeletonButton variant="ghost" />
              </div>
            </section>

            {/* Card Skeletons */}
            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Card Skeletons</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <SkeletonCard />
                <SkeletonCard showAvatar showImage={false} />
                <SkeletonCard showActions={false} imageHeight="8rem" />
              </div>
            </section>

            {/* Table Skeleton */}
            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Table Skeleton</h2>
              <SkeletonTable rows={6} columns={5} />
            </section>
          </>
        ) : (
          <>
            {/* Actual Content */}
            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Actual Content</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="rounded-lg border bg-card p-6 space-y-4 sm:p-4 md:p-6">
                  <img 
                    src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=200&fit=crop" 
                    alt="Sample" 
                    className="w-full h-48 object-cover rounded-lg"
                  />
                  <div className="flex items-start space-x-4">
                    <img 
                      src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop" 
                      alt="Avatar" 
                      className="w-10 h-10 rounded-full "
                    />
                    <div>
                      <h3 className="text-lg font-semibold">Sample Card Title</h3>
                      <p className="text-sm text-muted-foreground md:text-base lg:text-lg">By John Doe</p>
                    </div>
                  </div>
                  <p className="text-muted-foreground">
                    This is a sample card with actual content to show what the skeleton states are representing.
                  </p>
                  <div className="flex justify-between items-center pt-4">
                    <div className="flex space-x-2">
                      <button className="px-3 py-1 bg-primary text-primary-foreground rounded-md text-sm md:text-base lg:text-lg" aria-label="Button">
                      </button>
                      <button className="px-3 py-1 border border-input rounded-md text-sm md:text-base lg:text-lg" aria-label="Button">
                      </button>
                    </div>
                    <span className="text-sm text-muted-foreground md:text-base lg:text-lg">2 min read</span>
                  </div>
                </div>
                
                <div className="rounded-lg border bg-card p-6 space-y-4 sm:p-4 md:p-6">
                  <div className="flex items-start space-x-4">
                    <img 
                      src="https://images.unsplash.com/photo-1494790108755-2616b612b786?w=40&h=40&fit=crop" 
                      alt="Avatar" 
                      className="w-10 h-10 rounded-full "
                    />
                    <div>
                      <h3 className="text-lg font-semibold">Another Card</h3>
                      <p className="text-sm text-muted-foreground md:text-base lg:text-lg">By Jane Smith</p>
                    </div>
                  </div>
                  <p className="text-muted-foreground">
                    Another example of actual content that would replace the skeleton loading state once data is loaded.
                  </p>
                </div>
                
                <div className="rounded-lg border bg-card p-6 space-y-4 sm:p-4 md:p-6">
                  <img 
                    src="https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?w=400&h=128&fit=crop" 
                    alt="Sample" 
                    className="w-full h-32 object-cover rounded-lg"
                  />
                  <h3 className="text-lg font-semibold">Simple Card</h3>
                  <p className="text-muted-foreground">
                    A simpler card without actions to demonstrate different skeleton variations.
                  </p>
                </div>
              </div>
            </section>
          </>
        )}
      </div>
    </MicroInteractionProvider>
  );
}