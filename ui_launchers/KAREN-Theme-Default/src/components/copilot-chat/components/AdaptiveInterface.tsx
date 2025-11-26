import React, { useState, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { ExpertiseLevel } from '../types/copilot';
import { getDefaultPolicy, UIAdaptationPolicy } from './adaptive-utils';
import { AdaptiveInterfaceContext } from './adaptive-context';

interface AdaptiveInterfaceProps {
  expertiseLevel: ExpertiseLevel;
  className?: string;
  children: React.ReactNode;
}

/**
 * AdaptiveInterface component that dynamically adjusts UI based on user expertise level
 * Implements the Copilot-first adaptive interface system
 */
export const AdaptiveInterface: React.FC<AdaptiveInterfaceProps> = ({
  expertiseLevel,
  className,
  children
}) => {
  const [adaptationPolicy, setAdaptationPolicy] = useState<UIAdaptationPolicy>(getDefaultPolicy(expertiseLevel));
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Update adaptation policy when expertise level changes
  useEffect(() => {
    setIsTransitioning(true);
    const newPolicy = getDefaultPolicy(expertiseLevel);
    
    // Add a small delay for smooth transition
    const timer = setTimeout(() => {
      setAdaptationPolicy(newPolicy);
      setIsTransitioning(false);
    }, 300);
    
    return () => clearTimeout(timer);
  }, [expertiseLevel]);

  // Context value for child components
  const contextValue = {
    expertiseLevel,
    adaptationPolicy,
    isTransitioning,
    updatePolicy: useCallback((updates: Partial<UIAdaptationPolicy>) => {
      setAdaptationPolicy(prev => ({ ...prev, ...updates }));
    }, [])
  };

  return (
    <div
      className={cn(
        'adaptive-interface',
        `expertise-${expertiseLevel}`,
        {
          'simplified-ui': adaptationPolicy.simplifiedUI,
          'guided-mode': adaptationPolicy.guidedMode,
          'show-advanced': adaptationPolicy.showAdvancedFeatures,
          'show-debug': adaptationPolicy.showDebugInfo,
          'show-memory': adaptationPolicy.showMemoryOps,
          'animations-enabled': adaptationPolicy.enableAnimations,
          'auto-scroll': adaptationPolicy.autoScroll,
          'transitioning': isTransitioning
        },
        className
      )}
      data-expertise-level={expertiseLevel}
    >
      {/* CSS-in-JS for dynamic styling based on adaptation policy */}
      <style jsx>{`
        .adaptive-interface {
          transition: all 0.3s ease-in-out;
        }
        
        .adaptive-interface.transitioning {
          opacity: 0.8;
        }
        
        .adaptive-interface.simplified-ui .advanced-feature {
          display: none;
        }
        
        .adaptive-interface.guided-mode .guided-element {
          background-color: rgba(59, 130, 246, 0.1);
          border: 1px dashed rgba(59, 130, 246, 0.3);
          border-radius: 4px;
          padding: 8px;
          margin: 4px 0;
        }
        
        .adaptive-interface.show-debug .debug-info {
          display: block;
        }
        
        .adaptive-interface.show-memory .memory-ops {
          display: block;
        }
        
        .adaptive-interface.expertise-beginner {
          --primary-color: #3b82f6;
          --font-size-multiplier: 1.1;
        }
        
        .adaptive-interface.expertise-intermediate {
          --primary-color: #3b82f6;
          --font-size-multiplier: 1.0;
        }
        
        .adaptive-interface.expertise-advanced {
          --primary-color: #8b5cf6;
          --font-size-multiplier: 0.95;
        }
        
        .adaptive-interface.expertise-expert {
          --primary-color: #ef4444;
          --font-size-multiplier: 0.9;
        }
        
        .adaptive-interface.animations-enabled * {
          transition: all 0.2s ease;
        }
      `}</style>
      
      {/* Context provider for child components */}
      <AdaptiveInterfaceContext.Provider value={contextValue}>
        {children}
      </AdaptiveInterfaceContext.Provider>
    </div>
  );
};
