/**
 * BreadcrumbNavigation Component
 *
 * Route-based breadcrumb navigation with context awareness.
 * Based on requirements: 2.1, 2.2, 2.3, 2.4, 11.1, 11.2
 */

"use client";

import React from "react";
import { useRouter, usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  breadcrumbNavigationVariants,
  defaultRouteConfig,
  generateBreadcrumbsFromRoute,
  type BreadcrumbItem,
  type BreadcrumbNavigationProps,
  type RouteConfig,
} from "./breadcrumb-utils";

export const BreadcrumbNavigation = React.forwardRef<
  HTMLElement,
  BreadcrumbNavigationProps
>(
  (
    {
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
    },
    ref
  ) => {
    const pathname = usePathname();
    const router = useRouter();

    // Generate breadcrumb items from current route
    const generatedItems = React.useMemo(() => {
      if (items && items.length) return items;
      return generateBreadcrumbsFromRoute(pathname || '/', routeConfig, showHome);
    }, [pathname, routeConfig, showHome, items]);

    // Truncate items if needed
    const displayItems = React.useMemo(() => {
      if (generatedItems.length <= maxItems) return generatedItems;

      const firstItem = generatedItems[0];
      const lastItems = generatedItems.slice(-maxItems + 2);

      return [firstItem, { label: "...", href: undefined }, ...lastItems];
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
        const navEl = target.closest("nav");
        const listEl = navEl?.querySelector('[role="list"]');
        if (!listEl) return;

        const buttons = Array.from(
          navEl?.querySelectorAll("button") || []
        ) as HTMLButtonElement[];
        const currentIndex = buttons.indexOf(target as HTMLButtonElement);

        switch (event.key) {
          case "ArrowLeft":
            if (currentIndex > 0) {
              event.preventDefault();
              buttons[currentIndex - 1].focus();
            }
            break;
          case "ArrowRight":
            if (currentIndex < buttons.length - 1) {
              event.preventDefault();
              buttons[currentIndex + 1].focus();
            }
            break;
          case "Home":
            if (buttons[0]) {
              event.preventDefault();
              buttons[0].focus();
            }
            break;
          case "End":
            if (buttons[buttons.length - 1]) {
              event.preventDefault();
              buttons[buttons.length - 1].focus();
            }
            break;
        }
      };

      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }, [enableKeyboardNavigation]);

    return (
      <nav
        ref={ref}
        className={cn(breadcrumbNavigationVariants({ size }), className)}
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
                  {separator || <ChevronRight className="h-4 w-4" />}
                </span>
              )}

              {/* Breadcrumb Item */}
              <BreadcrumbNode item={item} onClick={() => handleItemClick(item)} />
            </li>
          ))}
        </ol>
      </nav>
    );
  }
);

BreadcrumbNavigation.displayName = "BreadcrumbNavigation";

// Individual Breadcrumb Item Component
export interface BreadcrumbItemProps {
  item: BreadcrumbItem;
  onClick: () => void;
}

const BreadcrumbNode: React.FC<BreadcrumbItemProps> = ({ item, onClick }) => {
  const Icon = item.icon;
  const isClickable = !!item.href && !item.current;
  const isEllipsis = item.label === "...";

  if (isEllipsis) {
    return (
      <span className="text-[var(--color-neutral-500)] dark:text-[var(--color-neutral-500)]">
        {item.label}
      </span>
    );
  }

  const content = (
    <>
      {Icon && <Icon className="h-4 w-4 mr-[var(--space-xs)] flex-shrink-0" />}
      <span className="truncate max-w-[200px]">{item.label}</span>
    </>
  );

  if (isClickable) {
    return (
      <Button
        className={cn(
          "flex items-center",
          "text-[var(--color-neutral-600)] dark:text-[var(--color-neutral-400)]",
          "hover:text-[var(--color-primary-600)] dark:hover:text-[var(--color-primary-400)]",
          "transition-colors [transition-duration:var(--duration-fast)] [transition-timing-function:var(--ease-standard)]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring-color)] focus-visible:rounded-[var(--radius-sm)]",
          "underline-offset-4 hover:underline"
        )}
        onClick={onClick}
        aria-current={item.current ? "page" : undefined}
        aria-label="Breadcrumb link"
        variant="ghost"
        size="sm"
      >
        {content}
      </Button>
    );
  }

  return (
    <span
      className={cn(
        "flex items-center",
        "text-[var(--color-neutral-900)] dark:text-[var(--color-neutral-100)]",
        "font-medium"
      )}
      aria-current={item.current ? "page" : undefined}
    >
      {content}
    </span>
  );
};

export default BreadcrumbNavigation;
