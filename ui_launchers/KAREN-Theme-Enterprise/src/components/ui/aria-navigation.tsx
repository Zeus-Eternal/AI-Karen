/**
 * ARIA Enhanced Navigation Components
 * Provides accessible navigation patterns with comprehensive ARIA support
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import {
  createNavigationAria,
  createAriaLabel,
  mergeAriaProps,
  type AriaProps,
} from "@/utils/aria";
import { ARIA_ROLES } from "@/utils/aria";
import { Button } from "@/components/ui/button";

const mergeSafeAriaProps = (
  ...props: Array<Partial<AriaProps> | undefined>
) => {
  const merged = mergeAriaProps(...props);
  const safeProps = { ...merged };
  delete safeProps['aria-relevant'];
  return safeProps;
};

/**
 * Navigation Container - Main navigation wrapper
 */
export interface AriaNavigationProps extends React.HTMLAttributes<HTMLElement> {
  /** Accessible label for the navigation */
  ariaLabel?: string;
  /** ID of element that labels this navigation */
  ariaLabelledBy?: string;
  /** Navigation type for semantic meaning */
  navType?: 'primary' | 'secondary' | 'breadcrumb' | 'pagination' | 'tabs';
  /** Custom ARIA props */
  ariaProps?: Partial<AriaProps>;
}

export const AriaNavigation = React.forwardRef<HTMLElement, AriaNavigationProps>(
  ({ 
    className, 
    ariaLabel, 
    ariaLabelledBy, 
    navType = 'primary',
    ariaProps,
    children,
    ...props 
  }, ref) => {
    const defaultLabel = {
      primary: 'Main navigation',
      secondary: 'Secondary navigation',
      breadcrumb: 'Breadcrumb navigation',
      pagination: 'Pagination navigation',
      tabs: 'Tab navigation'
    }[navType];

    const labelProps = createAriaLabel(
      ariaLabel || defaultLabel, 
      ariaLabelledBy
    );

    return (
      <nav
        ref={ref}
        className={cn("", className)}
        role={ARIA_ROLES.NAVIGATION}
        {...mergeSafeAriaProps(labelProps, ariaProps)}
        {...props}
      >
        {children}
      </nav>
    );
  }
);

AriaNavigation.displayName = "AriaNavigation";

/**
 * Navigation List - List container for navigation items
 */
export interface AriaNavListProps extends React.HTMLAttributes<HTMLUListElement> {
  /** Orientation of the navigation list */
  orientation?: 'horizontal' | 'vertical';
  /** Custom ARIA props */
  ariaProps?: Partial<AriaProps>;
}

export const AriaNavList = React.forwardRef<HTMLUListElement, AriaNavListProps>(
  ({ 
    className, 
    orientation = 'horizontal',
    ariaProps,
    children,
    ...props 
  }, ref) => {
    return (
      <ul
        ref={ref}
        className={cn(
          "flex",
          orientation === 'horizontal' ? "flex-row space-x-1" : "flex-col space-y-1",
          className
        )}
        role={ARIA_ROLES.LIST}
        aria-orientation={orientation}
        {...mergeSafeAriaProps(ariaProps)}
        {...props}
      >
        {children}
      </ul>
    );
  }
);

AriaNavList.displayName = "AriaNavList";

/**
 * Navigation Item - Individual navigation item
 */
export interface AriaNavItemProps extends React.HTMLAttributes<HTMLLIElement> {
  /** Whether this item is currently active/selected */
  current?: boolean | 'page' | 'step' | 'location' | 'date' | 'time';
  /** Whether this item is disabled */
  disabled?: boolean;
  /** Custom ARIA props */
  ariaProps?: Partial<AriaProps>;
}

export const AriaNavItem = React.forwardRef<HTMLLIElement, AriaNavItemProps>(
  ({ 
    className, 
    current,
    disabled,
    ariaProps,
    children,
    ...props 
  }, ref) => {
    const navigationProps = createNavigationAria(current, undefined, undefined);

    return (
      <li
        ref={ref}
        className={cn(
          "relative",
          {
            'opacity-50 pointer-events-none': disabled,
          },
          className
        )}
        role={ARIA_ROLES.LISTITEM}
        {...mergeSafeAriaProps(navigationProps, ariaProps)}
        {...props}
      >
        {children}
      </li>
    );
  }
);

AriaNavItem.displayName = "AriaNavItem";

/**
 * Navigation Link - Accessible navigation link
 */
export interface AriaNavLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  /** Whether this link is currently active */
  current?: boolean | 'page' | 'step' | 'location' | 'date' | 'time';
  /** Whether this link is disabled */
  disabled?: boolean;
  /** Custom ARIA props */
  ariaProps?: Partial<AriaProps>;
}

export const AriaNavLink = React.forwardRef<HTMLAnchorElement, AriaNavLinkProps>(
  ({ 
    className, 
    current,
    disabled,
    ariaProps,
    children,
    href,
    onClick,
    ...props 
  }, ref) => {
    const navigationProps = createNavigationAria(current);

    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
      if (disabled) {
        e.preventDefault();
        return;
      }
      onClick?.(e);
    };

    return (
      <a
        ref={ref}
        href={disabled ? undefined : href}
        className={cn(
          "inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
          "hover:bg-accent hover:text-accent-foreground",
          "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
          {
            'bg-accent text-accent-foreground': current,
            'opacity-50 cursor-not-allowed pointer-events-none': disabled,
          },
          className
        )}
        onClick={handleClick}
        tabIndex={disabled ? -1 : undefined}
        {...mergeSafeAriaProps(navigationProps, ariaProps)}
        {...props}
      >
        {children}
      </a>
    );
  }
);

AriaNavLink.displayName = "AriaNavLink";

/**
 * Breadcrumb Navigation - Specialized breadcrumb component
 */
export interface AriaBreadcrumbProps extends React.HTMLAttributes<HTMLElement> {
  /** Separator between breadcrumb items */
  separator?: React.ReactNode;
  /** Custom ARIA props */
  ariaProps?: Partial<AriaProps>;
}

export const AriaBreadcrumb = React.forwardRef<HTMLElement, AriaBreadcrumbProps>(
  ({ 
    className, 
    separator = "/",
    ariaProps,
    children,
    ...props 
  }, ref) => {
    const childrenArray = React.Children.toArray(children);

    return (
      <nav
        ref={ref}
        className={cn("flex items-center space-x-1 text-sm", className)}
        aria-label="Breadcrumb navigation"
        {...mergeSafeAriaProps(ariaProps)}
        {...props}
      >
        <ol className="flex items-center space-x-1" role={ARIA_ROLES.LIST}>
          {childrenArray.map((child, index) => (
            <React.Fragment key={index}>
              <li role={ARIA_ROLES.LISTITEM}>
                {child}
              </li>
              {index < childrenArray.length - 1 && (
                <li 
                  role="separator" 
                  aria-hidden="true"
                  className="text-muted-foreground"
                >
                  {separator}
                </li>
              )}
            </React.Fragment>
          ))}
        </ol>
      </nav>
    );
  }
);

AriaBreadcrumb.displayName = "AriaBreadcrumb";

/**
 * Breadcrumb Item - Individual breadcrumb item
 */
export interface AriaBreadcrumbItemProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Whether this is the current page */
  current?: boolean;
  /** Link href if this item is a link */
  href?: string;
  /** Custom ARIA props */
  ariaProps?: Partial<AriaProps>;
}

export const AriaBreadcrumbItem = React.forwardRef<HTMLSpanElement, AriaBreadcrumbItemProps>(
  ({ 
    className, 
    current = false,
    href,
    ariaProps,
    children,
    ...props 
  }, ref) => {
    const navigationProps = createNavigationAria(current ? 'page' : undefined);

    if (href && !current) {
      return (
        <a
          href={href}
          className={cn(
            "text-muted-foreground hover:text-foreground transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1 rounded",
            className
          )}
            {...mergeSafeAriaProps(navigationProps, ariaProps)}
        >
          {children}
        </a>
      );
    }

    return (
      <span
        ref={ref}
        className={cn(
          current ? "text-foreground font-medium" : "text-muted-foreground",
          className
        )}
        {...mergeSafeAriaProps(navigationProps, ariaProps)}
        {...props}
      >
        {children}
      </span>
    );
  }
);

AriaBreadcrumbItem.displayName = "AriaBreadcrumbItem";

/**
 * Tab Navigation - Accessible tab interface
 */
export interface AriaTabListProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Orientation of the tab list */
  orientation?: 'horizontal' | 'vertical';
  /** Whether tabs can be activated automatically on focus */
  activationMode?: 'automatic' | 'manual';
  /** Custom ARIA props */
  ariaProps?: Partial<AriaProps>;
}

export const AriaTabList = React.forwardRef<HTMLDivElement, AriaTabListProps>(
  ({ 
    className, 
    orientation = 'horizontal',
    activationMode = 'automatic',
    ariaProps,
    children,
    ...props 
  }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "flex border-b",
          orientation === 'horizontal' ? "flex-row" : "flex-col",
          className
        )}
        role={ARIA_ROLES.TABLIST}
        aria-orientation={orientation}
        data-activation-mode={activationMode}
        {...mergeSafeAriaProps(ariaProps)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

AriaTabList.displayName = "AriaTabList";

/**
 * Tab - Individual tab button
 */
export interface AriaTabProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Whether this tab is selected */
  selected?: boolean;
  /** ID of the associated tab panel */
  controls?: string;
  /** Custom ARIA props */
  ariaProps?: Partial<AriaProps>;
}

export const AriaTab = React.forwardRef<HTMLButtonElement, AriaTabProps>(
  ({ 
    className, 
    selected = false,
    controls,
    ariaProps,
    children,
    ...props 
  }, ref) => {
    const tabProps = {
      'aria-selected': selected,
      'aria-controls': controls,
    };

    return (
      <Button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center px-4 py-2 text-sm font-medium",
          "border-b-2 transition-colors",
          "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
          selected 
            ? "border-primary text-primary" 
            : "border-transparent text-muted-foreground hover:text-foreground hover:border-border",
          className
        )}
        role={ARIA_ROLES.TAB}
        tabIndex={selected ? 0 : -1}
        {...mergeSafeAriaProps(tabProps, ariaProps)}
        {...props}
      >
        {children}
      </Button>
    );
  }
);

AriaTab.displayName = "AriaTab";

/**
 * Tab Panel - Content panel for tabs
 */
export interface AriaTabPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  /** ID of the tab that controls this panel */
  labelledBy?: string;
  /** Whether this panel is currently active */
  active?: boolean;
  /** Custom ARIA props */
  ariaProps?: Partial<AriaProps>;
}

export const AriaTabPanel = React.forwardRef<HTMLDivElement, AriaTabPanelProps>(
  ({ 
    className, 
    labelledBy,
    active = true,
    ariaProps,
    children,
    ...props 
  }, ref) => {
    const panelProps = createAriaLabel(undefined, labelledBy);

    return (
      <div
        ref={ref}
        className={cn(
          "mt-4 focus:outline-none",
          !active && "hidden",
          className
        )}
        role={ARIA_ROLES.TABPANEL}
        tabIndex={0}
        {...mergeSafeAriaProps(panelProps, ariaProps)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

AriaTabPanel.displayName = "AriaTabPanel";