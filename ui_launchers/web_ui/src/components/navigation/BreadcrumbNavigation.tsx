/**
 * BreadcrumbNavigation Component
 * 
 * Route-based breadcrumb navigation with context awareness.
 * Based on requirements: 2.1, 2.2, 2.3, 2.4, 11.1, 11.2
 */

"use client";

import React from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { ChevronRight, Home } from 'lucide-react';

// Breadcrumb item type
export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ComponentType<{ className?: string }>;
  current?: boolean;
}

// Route configuration for breadcrumb generation
export interface RouteConfig {
  [key: string]: {
    label: string;
    icon?: React.ComponentType<{ className?: string }>;
    parent?: string;
    dynamic?: boolean;
  };
}

// Default route configuration
export const defaultRouteConfig: RouteConfig = {
  '/': {
    label: 'Home',
    icon: Home,
  },
  '/dashboard': {
    label: 'Dashboard',
    parent: '/',
  },
  '/chat': {
    label: 'Chat Interface',
    parent: '/',
  },
  '/agents': {
    label: 'Agent Management',
    parent: '/',
  },
  '/workflows': {
    label: 'Workflow Builder',
    parent: '/agents',
  },
  '/automation': {
    label: 'Automation',
    parent: '/agents',
  },
  '/memory': {
    label: 'Memory & Analytics',
    parent: '/',
  },
  '/memory/analytics': {
    label: 'Memory Analytics',
    parent: '/memory',
  },
  '/memory/search': {
    label: 'Semantic Search',
    parent: '/memory',
  },
  '/memory/network': {
    label: 'Memory Network',
    parent: '/memory',
  },
  '/plugins': {
    label: 'Plugins & Extensions',
    parent: '/',
  },
  '/plugins/marketplace': {
    label: 'Plugin Marketplace',
    parent: '/plugins',
  },
  '/extensions': {
    label: 'Extensions',
    parent: '/plugins',
  },
  '/providers': {
    label: 'Provider Configuration',
    parent: '/',
  },
  '/models': {
    label: 'Model Management',
    parent: '/providers',
  },
  '/performance': {
    label: 'Performance Metrics',
    parent: '/providers',
  },
  '/users': {
    label: 'User Management',
    parent: '/',
  },
  '/roles': {
    label: 'Roles & Permissions',
    parent: '/users',
  },
  '/audit': {
    label: 'Audit Logs',
    parent: '/users',
  },
  '/settings': {
    label: 'Settings',
    parent: '/',
  },
};

// Breadcrumb variants
export const breadcrumbNavigationVariants = cva(
  [
    'flex items-center space-x-[var(--space-xs)]',
    'text-[var(--text-sm)]',
    'overflow-x-auto scrollbar-none',
  ],
  {
    variants: {
      size: {
        sm: 'text-[var(--text-xs)]',
        md: 'text-[var(--text-sm)]',
        lg: 'text-[var(--text-base)]',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
);

export interface BreadcrumbNavigationProps
  extends React.HTMLAttributes<HTMLElement>,
    VariantProps<typeof breadcrumbNavigationVariants> {
  items?: BreadcrumbItem[];
  routeConfig?: RouteConfig;
  showHome?: boolean;
  maxItems?: number;
  separator?: React.ReactNode;
  ariaLabel?: string;
  enableKeyboardNavigation?: boolean;
}

export const BreadcrumbNavigation = React.forwardRef<HTMLElement, BreadcrumbNavigationProps>(
  ({ 
    className, 
    size,
    items,
    routeConfig = defaultRouteConfig,
    showHome = true,
    maxItems = 5,
    separator,
    ariaLabel = "Breadcrumb navigation",
    enableKeyboardNavigation = true,
    ...props 
  }, ref) => {
    const pathname = usePathname();
    const router = useRouter();

    // Generate breadcrumb items from current route
    const generatedItems = React.useMemo(() => {
      if (items) return items;
      return generateBreadcrumbsFromRoute(pathname, routeConfig, showHome);
    }, [pathname, routeConfig, showHome, items]);

    // Truncate items if needed
    const displayItems = React.useMemo(() => {
      if (generatedItems.length <= maxItems) return generatedItems;
      
      const firstItem = generatedItems[0];
      const lastItems = generatedItems.slice(-maxItems + 2);
      
      return [
        firstItem,
        { label: '...', href: undefined },
        ...lastItems,
      ];
    }, [generatedItems, maxItems]);

    const handleItemClick = (item: BreadcrumbItem) => {
      if (item.href && !item.current) {
        router.push(item.href);
      }
    };

    // Keyboard navigation for breadcrumbs
    React.useEffect(() => {
      if (!enableKeyboardNavigation) return;

      const handleKeyDown = (event: KeyboardEvent) => {
        const target = event.target as HTMLElement;
        if (!target.closest('[role="list"]')) return;

        const buttons = Array.from(target.closest('nav')?.querySelectorAll('button') || []);
        const currentIndex = buttons.indexOf(target as HTMLButtonElement);

        switch (event.key) {
          case 'ArrowLeft':
            event.preventDefault();
            if (currentIndex > 0) {
              (buttons[currentIndex - 1] as HTMLButtonElement).focus();
            }
            break;
          case 'ArrowRight':
            event.preventDefault();
            if (currentIndex < buttons.length - 1) {
              (buttons[currentIndex + 1] as HTMLButtonElement).focus();
            }
            break;
          case 'Home':
            event.preventDefault();
            (buttons[0] as HTMLButtonElement)?.focus();
            break;
          case 'End':
            event.preventDefault();
            (buttons[buttons.length - 1] as HTMLButtonElement)?.focus();
            break;
        }
      };

      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }, [enableKeyboardNavigation]);

    return (
      <nav
        ref={ref}
        className={cn(breadcrumbNavigationVariants({ size, className }))}
        aria-label={ariaLabel}
        {...props}
      >
        <ol className="flex items-center space-x-[var(--space-xs)]" role="list">
          {displayItems.map((item, index) => (
            <li key={`${item.label}-${index}`} className="flex items-center">
              {/* Separator */}
              {index > 0 && (
                <span 
                  className="mx-[var(--space-xs)] text-[var(--color-neutral-400)] dark:text-[var(--color-neutral-600)]"
                  aria-hidden="true"
                >
                  {separator || <ChevronRight className="h-4 w-4 " />}
                </span>
              )}

              {/* Breadcrumb Item */}
              <BreadcrumbItem
                item={item}
                onClick={() => handleItemClick(item)}
              />
            </li>
          ))}
        </ol>
      </nav>
    );
  }
);

BreadcrumbNavigation.displayName = 'BreadcrumbNavigation';

// Individual Breadcrumb Item Component
interface BreadcrumbItemProps {
  item: BreadcrumbItem;
  onClick: () => void;
}

const BreadcrumbItem: React.FC<BreadcrumbItemProps> = ({ item, onClick }) => {
  const Icon = item.icon;
  const isClickable = item.href && !item.current;
  const isEllipsis = item.label === '...';

  if (isEllipsis) {
    return (
      <span className="text-[var(--color-neutral-500)] dark:text-[var(--color-neutral-500)]">
        {item.label}
      </span>
    );
  }

  const content = (
    <>
      {Icon && (
        <Icon className="h-4 w-4 mr-[var(--space-xs)] flex-shrink-0 " />
      )}
      <span className="truncate max-w-[200px]">{item.label}</span>
    </>
  );

  if (isClickable) {
    return (
      <Button
        className={cn(
          'flex items-center',
          'text-[var(--color-neutral-600)] dark:text-[var(--color-neutral-400)]',
          'hover:text-[var(--color-primary-600)] dark:hover:text-[var(--color-primary-400)]',
          'transition-colors [transition-duration:var(--duration-fast)] [transition-timing-function:var(--ease-standard)]',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring-color)] focus-visible:rounded-[var(--radius-sm)]',
          'underline-offset-4 hover:underline'
        )}
        onClick={onClick}
        aria-current={item.current ? 'page' : undefined}
       aria-label="Button">
        {content}
      </Button>
    );
  }

  return (
    <span
      className={cn(
        'flex items-center',
        'text-[var(--color-neutral-900)] dark:text-[var(--color-neutral-100)]',
        'font-medium'
      )}
      aria-current={item.current ? 'page' : undefined}
    >
      {content}
    </span>
  );
};

// Utility function to generate breadcrumbs from route
function generateBreadcrumbsFromRoute(
  pathname: string, 
  routeConfig: RouteConfig,
  showHome: boolean
): BreadcrumbItem[] {
  const breadcrumbs: BreadcrumbItem[] = [];
  
  // Build path hierarchy
  const pathSegments = pathname.split('/').filter(Boolean);
  const paths: string[] = [];
  
  // Add root if showHome is true
  if (showHome && pathname !== '/') {
    paths.push('/');
  }
  
  // Build incremental paths
  let currentPath = '';
  for (const segment of pathSegments) {
    currentPath += `/${segment}`;
    paths.push(currentPath);
  }
  
  // Generate breadcrumb items
  for (let i = 0; i < paths.length; i++) {
    const path = paths[i];
    const config = routeConfig[path];
    const isLast = i === paths.length - 1;
    
    if (config) {
      breadcrumbs.push({
        label: config.label,
        href: isLast ? undefined : path,
        icon: config.icon,
        current: isLast,

    } else {
      // Fallback for unconfigured routes
      const segment = path.split('/').pop() || 'Home';
      const label = segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' ');
      
      breadcrumbs.push({
        label,
        href: isLast ? undefined : path,
        current: isLast,

    }
  }
  
  return breadcrumbs;
}

// Hook for programmatic breadcrumb management
export function useBreadcrumbs(routeConfig?: RouteConfig) {
  const pathname = usePathname();
  
  const breadcrumbs = React.useMemo(() => {
    return generateBreadcrumbsFromRoute(pathname, routeConfig || defaultRouteConfig, true);
  }, [pathname, routeConfig]);
  
  return breadcrumbs;
}
