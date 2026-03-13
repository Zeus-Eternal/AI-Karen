import React, { useState, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { useAdaptiveInterface } from './adaptive-interface-hooks';
import { AdaptiveLayoutContext, LayoutState } from './adaptive-layout-context';

interface AdaptiveLayoutProps {
  className?: string;
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  sidebarPosition?: 'left' | 'right';
  sidebarWidth?: number;
  responsiveBreakpoints?: {
    mobile: number;
    tablet: number;
    desktop: number;
  };
}

/**
 * AdaptiveLayout component that provides responsive layout based on screen size
 * and user expertise level. Implements the Copilot-first adaptive layout system.
 */
export const AdaptiveLayout: React.FC<AdaptiveLayoutProps> = ({
  className,
  children,
  sidebar,
  header,
  footer,
  sidebarPosition = 'left',
  sidebarWidth = 300,
  responsiveBreakpoints = {
    mobile: 768,
    tablet: 1024,
    desktop: 1280
  }
}) => {
  const { adaptationPolicy, expertiseLevel } = useAdaptiveInterface();
  const [layoutState, setLayoutState] = useState<LayoutState>({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    sidebarOpen: !adaptationPolicy.simplifiedUI,
    sidebarWidth
  });
  
  const containerRef = useRef<HTMLDivElement>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  // Update layout state based on screen size
  useEffect(() => {
    const updateLayoutState = () => {
      if (!containerRef.current) return;
      
      const width = containerRef.current.clientWidth;
      const isMobile = width < responsiveBreakpoints.mobile;
      const isTablet = width >= responsiveBreakpoints.mobile && width < responsiveBreakpoints.tablet;
      const isDesktop = width >= responsiveBreakpoints.desktop;
      
      // Auto-close sidebar on mobile for simplified UI
      const sidebarOpen = adaptationPolicy.simplifiedUI 
        ? false 
        : !isMobile;
      
      setLayoutState(prev => ({
        ...prev,
        isMobile,
        isTablet,
        isDesktop,
        sidebarOpen
      }));
    };

    // Initial update
    updateLayoutState();

    // Setup resize observer
    if (containerRef.current && typeof ResizeObserver !== 'undefined') {
      resizeObserverRef.current = new ResizeObserver(updateLayoutState);
      resizeObserverRef.current.observe(containerRef.current);
    }

    // Fallback to window resize event
    const handleResize = () => updateLayoutState();
    window.addEventListener('resize', handleResize);

    return () => {
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
      }
      window.removeEventListener('resize', handleResize);
    };
  }, [responsiveBreakpoints, adaptationPolicy.simplifiedUI]);

  // Update sidebar width when prop changes
  useEffect(() => {
    setLayoutState(prev => ({
      ...prev,
      sidebarWidth
    }));
  }, [sidebarWidth]);

  // Toggle sidebar
  const toggleSidebar = () => {
    setLayoutState(prev => ({
      ...prev,
      sidebarOpen: !prev.sidebarOpen
    }));
  };

  // Close sidebar
  const closeSidebar = () => {
    setLayoutState(prev => ({
      ...prev,
      sidebarOpen: false
    }));
  };

  // Open sidebar
  const openSidebar = () => {
    setLayoutState(prev => ({
      ...prev,
      sidebarOpen: true
    }));
  };

  // Layout context
  const layoutContext = {
    ...layoutState,
    toggleSidebar,
    closeSidebar,
    openSidebar,
    expertiseLevel,
    adaptationPolicy
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        'adaptive-layout',
        {
          'mobile-layout': layoutState.isMobile,
          'tablet-layout': layoutState.isTablet,
          'desktop-layout': layoutState.isDesktop,
          'sidebar-left': sidebarPosition === 'left',
          'sidebar-right': sidebarPosition === 'right',
          'sidebar-open': layoutState.sidebarOpen,
          'sidebar-closed': !layoutState.sidebarOpen,
          'simplified-ui': adaptationPolicy.simplifiedUI,
          'guided-mode': adaptationPolicy.guidedMode
        },
        className
      )}
      style={{
        // Set CSS variables for dynamic styling
        '--sidebar-width': `${layoutState.sidebarWidth}px`,
        '--primary-color': expertiseLevel === 'expert' ? '#ef4444' : 
                          expertiseLevel === 'advanced' ? '#8b5cf6' : '#3b82f6',
        '--font-size-multiplier': expertiseLevel === 'beginner' ? '1.1' :
                                  expertiseLevel === 'expert' ? '0.9' : '1.0'
      } as React.CSSProperties}
    >
      {/* CSS-in-JS for responsive layout */}
      <style jsx>{`
        .adaptive-layout {
          display: flex;
          flex-direction: column;
          height: 100%;
          width: 100%;
          position: relative;
        }
        
        .adaptive-layout.mobile-layout,
        .adaptive-layout.tablet-layout {
          flex-direction: column;
        }
        
        .adaptive-layout.desktop-layout {
          flex-direction: row;
        }
        
        .adaptive-layout.simplified-ui .sidebar {
          display: none;
        }
        
        .adaptive-layout.guided-mode .guided-element {
          background-color: rgba(59, 130, 246, 0.1);
          border: 1px dashed rgba(59, 130, 246, 0.3);
          border-radius: 4px;
          padding: 8px;
          margin: 4px 0;
        }
        
        @media (max-width: ${responsiveBreakpoints.mobile}px) {
          .adaptive-layout:not(.simplified-ui) .sidebar {
            position: fixed;
            top: 0;
            ${sidebarPosition === 'left' ? 'left: 0;' : 'right: 0;'}
            height: 100%;
            width: var(--sidebar-width);
            z-index: 100;
            background: var(--background);
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            transform: ${layoutState.sidebarOpen ? 'translateX(0)' : 
                       sidebarPosition === 'left' ? 'translateX(-100%)' : 'translateX(100%)'};
            transition: transform 0.3s ease;
          }
          
          .adaptive-layout:not(.simplified-ui).sidebar-open .overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 99;
          }
        }
        
        @media (min-width: ${responsiveBreakpoints.tablet}px) and (max-width: ${responsiveBreakpoints.desktop - 1}px) {
          .adaptive-layout:not(.simplified-ui) .sidebar {
            width: calc(var(--sidebar-width) * 0.8);
          }
        }
      `}</style>
      
      {/* Overlay for mobile sidebar */}
      {layoutState.isMobile && layoutState.sidebarOpen && !adaptationPolicy.simplifiedUI && (
        <div className="overlay" onClick={closeSidebar} />
      )}
      
      {/* Header */}
      {header && (
        <header className="adaptive-header">
          {header}
        </header>
      )}
      
      {/* Main content area */}
      <div className="adaptive-main-container flex flex-1 overflow-hidden">
        {/* Sidebar */}
        {sidebar && !adaptationPolicy.simplifiedUI && (
          <aside className="sidebar flex-shrink-0 overflow-y-auto border-r bg-background">
            {sidebar}
          </aside>
        )}
        
        {/* Main content */}
        <main className="adaptive-main flex-1 overflow-hidden">
          {children}
        </main>
      </div>
      
      {/* Footer */}
      {footer && (
        <footer className="adaptive-footer border-t bg-background">
          {footer}
        </footer>
      )}
      
      {/* Layout context provider */}
      <AdaptiveLayoutContext.Provider value={layoutContext}>
        {children}
      </AdaptiveLayoutContext.Provider>
    </div>
  );
};
