'use client';

import React, { useState } from 'react';
import { PageTransition } from './page-transition';
import { TransitionProvider } from './transition-provider';
import { MicroInteractionProvider } from '../micro-interactions/micro-interaction-provider';
import { InteractiveButton } from '../micro-interactions/interactive-button';
import { TransitionVariant } from './types';

const samplePages = [
  {
    id: 'home',
    title: 'Home Page',
    content: 'Welcome to the home page! This is where your journey begins.',
    color: 'bg-blue-50 border-blue-200'
  },
  {
    id: 'about',
    title: 'About Page',
    content: 'Learn more about us and what we do. We are passionate about creating great experiences.',
    color: 'bg-green-50 border-green-200'
  },
  {
    id: 'services',
    title: 'Services Page',
    content: 'Discover our range of services designed to help you succeed.',
    color: 'bg-purple-50 border-purple-200'
  },
  {
    id: 'contact',
    title: 'Contact Page',
    content: 'Get in touch with us. We would love to hear from you!',
    color: 'bg-orange-50 border-orange-200'
  }
];

const transitionVariants: TransitionVariant[] = [
  'fade',
  'slide-left',
  'slide-right',
  'slide-up',
  'slide-down',
  'scale',
  'rotate',
  'flip'
];

export function TransitionDemo() {
  const [currentPage, setCurrentPage] = useState(0);
  const [currentVariant, setCurrentVariant] = useState<TransitionVariant>('fade');
  const [isTransitioning, setIsTransitioning] = useState(false);

  const handlePageChange = (pageIndex: number) => {
    if (isTransitioning || pageIndex === currentPage) return;
    
    setIsTransitioning(true);
    setTimeout(() => {
      setCurrentPage(pageIndex);
      setIsTransitioning(false);
    }, 150);
  };

  const handleVariantChange = (variant: TransitionVariant) => {
    setCurrentVariant(variant);
  };

  const currentPageData = samplePages[currentPage];

  return (
    <MicroInteractionProvider>
      <TransitionProvider>
        <div className="p-8 space-y-8 max-w-6xl mx-auto sm:w-auto md:w-full">
          <h1 className="text-3xl font-bold">Page Transitions Demo</h1>
          
          {/* Transition Variant Selector */}
          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Transition Variants</h2>
            <div className="flex flex-wrap gap-2">
              {transitionVariants.map((variant) => (
                <InteractiveButton
                  key={variant}
                  variant={currentVariant === variant ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleVariantChange(variant)}
                >
                  {variant}
                </InteractiveButton>
              ))}
            </div>
          </section>

          {/* Page Navigation */}
          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Page Navigation</h2>
            <div className="flex flex-wrap gap-2">
              {samplePages.map((page, index) => (
                <InteractiveButton
                  key={page.id}
                  variant={currentPage === index ? 'default' : 'outline'}
                  onClick={() => handlePageChange(index)}
                  disabled={isTransitioning}
                >
                  {page.title}
                </InteractiveButton>
              ))}
            </div>
          </section>

          {/* Page Content with Transitions */}
          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Page Content</h2>
            <div className="relative min-h-[400px] border-2 border-dashed border-gray-300 rounded-lg overflow-hidden">
              <PageTransition
                key={`${currentPage}-${currentVariant}`}
                variant={currentVariant}
                duration={0.5}
              >
                <div className={`p-8 h-full min-h-[400px] flex flex-col justify-center items-center text-center border-2 rounded-lg ${currentPageData.color}`}>
                  <h3 className="text-3xl font-bold mb-4">{currentPageData.title}</h3>
                  <p className="text-lg text-gray-700 max-w-md">{currentPageData.content}</p>
                  
                  <div className="mt-8 space-y-4">
                    <div className="flex justify-center space-x-4">
                      <div className="w-16 h-16 bg-white rounded-lg shadow-md flex items-center justify-center sm:w-auto md:w-full">
                        <span className="text-2xl">📄</span>
                      </div>
                      <div className="w-16 h-16 bg-white rounded-lg shadow-md flex items-center justify-center sm:w-auto md:w-full">
                        <span className="text-2xl">🎨</span>
                      </div>
                      <div className="w-16 h-16 bg-white rounded-lg shadow-md flex items-center justify-center sm:w-auto md:w-full">
                        <span className="text-2xl">⚡</span>
                      </div>
                    </div>
                    
                    <div className="text-sm text-gray-600 md:text-base lg:text-lg">
                      Current transition: <strong>{currentVariant}</strong>
                    </div>
                  </div>
                </div>
              </PageTransition>
            </div>
          </section>

          {/* Transition Info */}
          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Transition Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg sm:p-4 md:p-6">
                <h3 className="font-semibold mb-2">Current Settings</h3>
                <ul className="space-y-1 text-sm md:text-base lg:text-lg">
                  <li><strong>Variant:</strong> {currentVariant}</li>
                  <li><strong>Duration:</strong> 0.5s</li>
                  <li><strong>Easing:</strong> cubic-bezier(0.4, 0, 0.2, 1)</li>
                  <li><strong>Current Page:</strong> {currentPageData.title}</li>
                </ul>
              </div>
              
              <div className="p-4 border rounded-lg sm:p-4 md:p-6">
                <h3 className="font-semibold mb-2">Features</h3>
                <ul className="space-y-1 text-sm md:text-base lg:text-lg">
                  <li>✅ Smooth animations</li>
                  <li>✅ Reduced motion support</li>
                  <li>✅ Multiple transition variants</li>
                  <li>✅ Customizable duration</li>
                  <li>✅ Browser back/forward support</li>
                </ul>
              </div>
            </div>
          </section>
        </div>
      </TransitionProvider>
    </MicroInteractionProvider>
  );
}