/**
 * Skip Links Component
 * Provides accessible skip navigation for keyboard users
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface SkipLink {
  /** Unique identifier for the skip link */
  id: string;
  /** Target element ID to skip to */
  target: string;
  /** Label for the skip link */
  label: string;
  /** Optional description for screen readers */
  description?: string;
}

export interface SkipLinksProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Array of skip links to render */
  links: SkipLink[];
  /** Whether skip links are visible by default */
  alwaysVisible?: boolean;
  /** Custom className for styling */
  className?: string;
}

/**
 * SkipLinks - Provides keyboard navigation shortcuts to main content areas
 */
export const SkipLinks = React.forwardRef<HTMLDivElement, SkipLinksProps>(
  ({ 
    links, 
    alwaysVisible = false, 
    className, 
    ...props 
  }, ref) => {
    const handleSkipClick = (targetId: string) => {
      const targetElement = document.getElementById(targetId);
      if (targetElement) {
        // Focus the target element
        targetElement.focus();
        
        // If the element is not naturally focusable, make it focusable temporarily
        if (targetElement.tabIndex < 0) {
          targetElement.tabIndex = -1;
          targetElement.focus();
          
          // Remove tabindex after a short delay
          setTimeout(() => {
            targetElement.removeAttribute('tabindex');
          }, 100);
        }

        // Scroll to the element
        targetElement.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }
    };

    if (links.length === 0) {
      return null;
    }

    return (
      <div
        ref={ref}
        className={cn(
          'skip-links',
          'fixed top-0 left-0 z-[9999]',
          !alwaysVisible && 'sr-only focus-within:not-sr-only',
          className
        )}
        {...props}
      >
        <nav 
          aria-label="Skip navigation links"
          className="bg-primary text-primary-foreground p-2 shadow-lg rounded-br-md"
        >
          <ul className="flex flex-col gap-1">
            {links.map((link) => (
              <li key={link.id}>
                <a
                  href={`#${link.target}`}
                  className={cn(
                    'inline-block px-3 py-2 text-sm font-medium',
                    'bg-primary-foreground text-primary rounded',
                    'hover:bg-accent hover:text-accent-foreground',
                    'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                    'transition-colors duration-200'
                  )}
                  onClick={(e) => {
                    e.preventDefault();
                    handleSkipClick(link.target);
                  }}
                  aria-describedby={link.description ? `${link.id}-desc` : undefined}
                >
                  {link.label}
                </a>
                {link.description && (
                  <span 
                    id={`${link.id}-desc`}
                    className="sr-only"
                  >
                    {link.description}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </nav>
      </div>
    );
  }
);

SkipLinks.displayName = 'SkipLinks';

/**
 * SkipToContent - Simple skip to main content link
 */
export interface SkipToContentProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  /** Target element ID (defaults to 'main-content') */
  targetId?: string;
  /** Label for the skip link (defaults to 'Skip to main content') */
  label?: string;
  /** Whether the link is always visible */
  alwaysVisible?: boolean;
}

export const SkipToContent = React.forwardRef<HTMLAnchorElement, SkipToContentProps>(
  ({ 
    targetId = 'main-content',
    label = 'Skip to main content',
    alwaysVisible = false,
    className,
    onClick,
    ...props 
  }, ref) => {
    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
      e.preventDefault();
      
      const targetElement = document.getElementById(targetId);
      if (targetElement) {
        // Focus the target element
        if (targetElement.tabIndex < 0) {
          targetElement.tabIndex = -1;
        }
        targetElement.focus();
        
        // Scroll to the element
        targetElement.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }
      
      onClick?.(e);
    };

    return (
      <a
        ref={ref}
        href={`#${targetId}`}
        className={cn(
          'skip-to-content',
          'fixed top-2 left-2 z-[9999]',
          'px-4 py-2 text-sm font-medium',
          'bg-primary text-primary-foreground rounded-md shadow-lg',
          'hover:bg-primary/90 focus:bg-primary/90',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
          'transition-all duration-200',
          !alwaysVisible && 'sr-only focus:not-sr-only',
          className
        )}
        onClick={handleClick}
        {...props}
      >
        {label}
      </a>
    );
  }
);

SkipToContent.displayName = 'SkipToContent';

/**
 * MainContent - Wrapper for main content with proper landmarks
 */
export interface MainContentProps extends React.HTMLAttributes<HTMLElement> {
  /** ID for the main content (defaults to 'main-content') */
  contentId?: string;
  /** Whether to include skip target styling */
  includeSkipTarget?: boolean;
}

export const MainContent = React.forwardRef<HTMLElement, MainContentProps>(
  ({ 
    contentId = 'main-content',
    includeSkipTarget = true,
    className,
    children,
    ...props 
  }, ref) => {
    return (
      <main
        ref={ref}
        id={contentId}
        className={cn(
          'main-content',
          includeSkipTarget && 'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-inset',
          className
        )}
        tabIndex={-1}
        {...props}
      >
        {children}
      </main>
    );
  }
);

MainContent.displayName = 'MainContent';

/**
 * Hook for managing skip links
 */
export const useSkipLinks = () => {
  const [skipLinks, setSkipLinks] = React.useState<SkipLink[]>([]);

  const addSkipLink = React.useCallback((link: SkipLink) => {
    setSkipLinks(prev => {
      // Check if link already exists
      const exists = prev.some(existing => existing.id === link.id);
      if (exists) {
        return prev.map(existing => 
          existing.id === link.id ? link : existing
        );
      }
      return [...prev, link];
    });
  }, []);

  const removeSkipLink = React.useCallback((id: string) => {
    setSkipLinks(prev => prev.filter(link => link.id !== id));
  }, []);

  const clearSkipLinks = React.useCallback(() => {
    setSkipLinks([]);
  }, []);

  return {
    skipLinks,
    addSkipLink,
    removeSkipLink,
    clearSkipLinks,
  };
};

/**
 * Default skip links for common application structure
 */
export const DEFAULT_SKIP_LINKS: SkipLink[] = [
  {
    id: 'skip-to-main',
    target: 'main-content',
    label: 'Skip to main content',
    description: 'Jump to the main content area of the page',
  },
  {
    id: 'skip-to-nav',
    target: 'main-navigation',
    label: 'Skip to navigation',
    description: 'Jump to the main navigation menu',
  },
  {
    id: 'skip-to-search',
    target: 'search',
    label: 'Skip to search',
    description: 'Jump to the search functionality',
  },
  {
    id: 'skip-to-footer',
    target: 'footer',
    label: 'Skip to footer',
    description: 'Jump to the page footer',
  },
];

export default SkipLinks;