/**
 * SidebarNavigation Component
 *
 * Enhanced sidebar navigation with collapsible sections, mobile hamburger menu,
 * improved accessibility, and keyboard navigation support.
 * Based on requirements: 2.1, 2.2, 2.3, 2.4, 11.1, 11.2
 */

"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { useAppShell } from "@/components/layout/AppShell";
import {
  ChevronDown,
  ChevronRight,
  Menu,
  X,
  Home,
  Settings,
  BarChart3,
  Puzzle,
  Brain,
  MessageSquare,
  Shield,
  Workflow,
} from "lucide-react";

// Navigation item types
export interface NavigationItem {
  id: string;
  label: string;
  href?: string;
  icon?: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  children?: NavigationItem[];
  disabled?: boolean;
  external?: boolean;
}

// Default navigation structure
export const defaultNavigationItems: NavigationItem[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    href: "/dashboard",
    icon: Home,
  },
  {
    id: "chat",
    label: "Chat Interface",
    href: "/chat",
    icon: MessageSquare,
  },
  {
    id: "agents",
    label: "Agents & Workflows",
    icon: Workflow,
    children: [
      {
        id: "agents-list",
        label: "Agent Management",
        href: "/agents",
      },
      {
        id: "workflows",
        label: "Workflow Builder",
        href: "/workflows",
      },
      {
        id: "automation",
        label: "Automation",
        href: "/automation",
      },
    ],
  },
  {
    id: "memory",
    label: "Memory & Analytics",
    icon: Brain,
    children: [
      {
        id: "memory-analytics",
        label: "Memory Analytics",
        href: "/memory/analytics",
      },
      {
        id: "memory-search",
        label: "Semantic Search",
        href: "/memory/search",
      },
      {
        id: "memory-network",
        label: "Memory Network",
        href: "/memory/network",
      },
    ],
  },
  {
    id: "plugins",
    label: "Plugins & Extensions",
    icon: Puzzle,
    children: [
      {
        id: "plugins-installed",
        label: "Installed Plugins",
        href: "/plugins",
      },
      {
        id: "plugins-marketplace",
        label: "Plugin Marketplace",
        href: "/plugins/marketplace",
      },
      {
        id: "extensions",
        label: "Extensions",
        href: "/extensions",
      },
    ],
  },
  {
    id: "providers",
    label: "Providers & Models",
    icon: BarChart3,
    children: [
      {
        id: "providers-config",
        label: "Provider Configuration",
        href: "/providers",
      },
      {
        id: "models",
        label: "Model Management",
        href: "/models",
      },
      {
        id: "performance",
        label: "Performance Metrics",
        href: "/performance",
      },
    ],
  },
  {
    id: "security",
    label: "Security & RBAC",
    icon: Shield,
    children: [
      {
        id: "users",
        label: "User Management",
        href: "/users",
      },
      {
        id: "roles",
        label: "Roles & Permissions",
        href: "/roles",
      },
      {
        id: "audit",
        label: "Audit Logs",
        href: "/audit",
      },
    ],
  },
  {
    id: "settings",
    label: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

// Sidebar navigation variants
export const sidebarNavigationVariants = cva([
  "flex flex-col h-full",
  "overflow-hidden",
]);

export interface SidebarNavigationProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof sidebarNavigationVariants> {
  items?: NavigationItem[];
  onItemClick?: (item: NavigationItem) => void;
  enableKeyboardNavigation?: boolean;
  autoFocus?: boolean;
  ariaLabel?: string;
}

export const SidebarNavigation = React.forwardRef<
  HTMLDivElement,
  SidebarNavigationProps
>(
  (
    {
      className,
      items = defaultNavigationItems,
      onItemClick,
      enableKeyboardNavigation = true,
      autoFocus = false,
      ariaLabel = "Main navigation",
      ...props
    },
    ref
  ) => {
    const { sidebarCollapsed, closeSidebar, isMobile } = useAppShell();
    const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
    const pathname = usePathname();
    const router = useRouter();
    const navRef = useRef<HTMLDivElement>(null);
    const itemRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

    // Auto-expand active sections
    useEffect(() => {
      const activeItem = findActiveItem(items, pathname);
      if (activeItem?.parent) {
        setExpandedItems((prev) => new Set([...prev, activeItem.parent!]));
      }
    }, [pathname, items]);

    // Auto-focus navigation when requested
    useEffect(() => {
      if (autoFocus && navRef.current) {
        navRef.current.focus();
      }
    }, [autoFocus]);

    // Flatten items for keyboard navigation
    const flattenedItems = React.useMemo(() => {
      const flattened: {
        item: NavigationItem;
        level: number;
        parent?: string;
      }[] = [];

      const flatten = (items: NavigationItem[], level = 0, parent?: string) => {
        items.forEach((item) => {
          flattened.push({ item, level, parent });
          if (item.children && expandedItems.has(item.id)) {
            flatten(item.children, level + 1, item.id);
          }
        });
      };

      flatten(items);
      return flattened;
    }, [items, expandedItems]);

    // Function declarations
    const toggleExpanded = useCallback((itemId: string) => {
      setExpandedItems((prev) => {
        const newSet = new Set(prev);
        if (newSet.has(itemId)) {
          newSet.delete(itemId);
        } else {
          newSet.add(itemId);
        }
        return newSet;
      });
    }, []);

    const handleItemClick = useCallback(
      (item: NavigationItem) => {
        if (item.href) {
          router.push(item.href);
          if (isMobile) {
            closeSidebar();
          }
        }
        onItemClick?.(item);
      },
      [router, isMobile, closeSidebar, onItemClick]
    );

    // Keyboard navigation
    useEffect(() => {
      if (!enableKeyboardNavigation) return;

      const handleKeyDown = (event: KeyboardEvent) => {
        if (!navRef.current?.contains(event.target as Node)) return;

        const currentButton = event.target as HTMLButtonElement;
        const currentItemId = Array.from(itemRefs.current.entries()).find(
          ([_, button]) => button === currentButton
        )?.[0];

        if (!currentItemId) return;

        const currentIndex = flattenedItems.findIndex(
          (item) => item.item.id === currentItemId
        );

        switch (event.key) {
          case "ArrowDown":
            event.preventDefault();
            const nextIndex = Math.min(
              currentIndex + 1,
              flattenedItems.length - 1
            );
            const nextItem = flattenedItems[nextIndex];
            if (nextItem) {
              const button = itemRefs.current.get(nextItem.item.id);
              button?.focus();
            }
            break;

          case "ArrowUp":
            event.preventDefault();
            const prevIndex = Math.max(currentIndex - 1, 0);
            const prevItem = flattenedItems[prevIndex];
            if (prevItem) {
              const button = itemRefs.current.get(prevItem.item.id);
              button?.focus();
            }
            break;

          case "ArrowRight":
            event.preventDefault();
            const currentItem = flattenedItems[currentIndex];
            if (
              currentItem?.item.children &&
              !expandedItems.has(currentItem.item.id)
            ) {
              toggleExpanded(currentItem.item.id);
            }
            break;

          case "ArrowLeft":
            event.preventDefault();
            const currentItemForLeft = flattenedItems[currentIndex];
            if (
              currentItemForLeft?.item.children &&
              expandedItems.has(currentItemForLeft.item.id)
            ) {
              toggleExpanded(currentItemForLeft.item.id);
            }
            break;

          case "Enter":
          case " ":
            event.preventDefault();
            const currentItemForAction = flattenedItems[currentIndex];
            if (currentItemForAction) {
              handleItemClick(currentItemForAction.item);
            }
            break;

          case "Home":
            event.preventDefault();
            const firstItem = flattenedItems[0];
            if (firstItem) {
              const button = itemRefs.current.get(firstItem.item.id);
              button?.focus();
            }
            break;

          case "End":
            event.preventDefault();
            const lastIndex = flattenedItems.length - 1;
            const lastItem = flattenedItems[lastIndex];
            if (lastItem) {
              const button = itemRefs.current.get(lastItem.item.id);
              button?.focus();
            }
            break;
        }
      };

      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }, [
      enableKeyboardNavigation,
      flattenedItems,
      expandedItems,
      toggleExpanded,
      handleItemClick,
    ]);

    return (
      <nav
        ref={ref || navRef}
        className={cn(sidebarNavigationVariants(), className)}
        aria-label={ariaLabel}
        role="navigation"
        tabIndex={-1}
        {...props}
      >
        {/* Navigation Header */}
        <div className="flex items-center justify-between p-[var(--space-md)] border-b border-[var(--color-neutral-200)] dark:border-[var(--color-neutral-800)]">
          {!sidebarCollapsed && (
            <h2 className="text-[var(--text-lg)] font-semibold text-[var(--color-neutral-900)] dark:text-[var(--color-neutral-100)]">
              Kari AI
            </h2>
          )}
          <SidebarToggle />
        </div>

        {/* Navigation Items */}
        <div className="flex-1 overflow-y-auto py-[var(--space-sm)]">
          <ul className="space-y-[var(--space-xs)]" role="list">
            {items.map((item) => (
              <NavigationItemComponent
                key={item.id}
                item={item}
                isExpanded={expandedItems.has(item.id)}
                isActive={isItemActive(item, pathname)}
                isCollapsed={sidebarCollapsed}
                onToggle={() => toggleExpanded(item.id)}
                onClick={() => handleItemClick(item)}
                itemRef={(el) => {
                  if (el) {
                    itemRefs.current.set(item.id, el);
                  } else {
                    itemRefs.current.delete(item.id);
                  }
                }}
              />
            ))}
          </ul>
        </div>
      </nav>
    );
  }
);

SidebarNavigation.displayName = "SidebarNavigation";

// Navigation Item Component
interface NavigationItemComponentProps {
  item: NavigationItem;
  isExpanded: boolean;
  isActive: boolean;
  isCollapsed: boolean;
  onToggle: () => void;
  onClick: () => void;
  level?: number;
  itemRef?: (el: HTMLButtonElement | null) => void;
}

const NavigationItemComponent: React.FC<NavigationItemComponentProps> = ({
  item,
  isExpanded,
  isActive,
  isCollapsed,
  onToggle,
  onClick,
  level = 0,
  itemRef,
}) => {
  const pathname = usePathname();
  const hasChildren = item.children && item.children.length > 0;
  const Icon = item.icon;

  return (
    <li>
      <button
        ref={itemRef}
        className={cn(
          "w-full flex items-center gap-[var(--space-sm)] px-[var(--space-md)] py-[var(--space-sm)]",
          "text-left text-[var(--text-sm)] font-medium",
          "rounded-[var(--radius-md)] mx-[var(--space-xs)]",
          "transition-all [transition-duration:var(--duration-fast)] [transition-timing-function:var(--ease-standard)]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring-color)]",
          {
            // Active state
            "bg-[var(--color-primary-100)] text-[var(--color-primary-900)] dark:bg-[var(--color-primary-900)] dark:text-[var(--color-primary-100)]":
              isActive,
            // Hover state
            "hover:bg-[var(--color-neutral-200)] hover:text-[var(--color-neutral-900)] dark:hover:bg-[var(--color-neutral-800)] dark:hover:text-[var(--color-neutral-100)]":
              !isActive,
            // Default state
            "text-[var(--color-neutral-700)] dark:text-[var(--color-neutral-300)]":
              !isActive,
            // Disabled state
            "opacity-50 cursor-not-allowed": item.disabled,
            // Collapsed state
            "justify-center": isCollapsed,
            // Nested items
            "ml-[var(--space-lg)]": level > 0 && !isCollapsed,
          }
        )}
        onClick={hasChildren ? onToggle : onClick}
        disabled={item.disabled}
        aria-expanded={hasChildren ? isExpanded : undefined}
        aria-current={isActive ? "page" : undefined}
        aria-level={level + 1}
        title={isCollapsed ? item.label : undefined}
      >
        {/* Icon */}
        {Icon && (
          <Icon
            className={cn("h-5 w-5 flex-shrink-0", {
              "text-[var(--color-primary-600)] dark:text-[var(--color-primary-400)]":
                isActive,
            })}
          />
        )}

        {/* Label */}
        {!isCollapsed && (
          <>
            <span className="flex-1 truncate">{item.label}</span>

            {/* Badge */}
            {item.badge && (
              <span className="inline-flex items-center justify-center px-2 py-1 text-xs font-medium bg-[var(--color-primary-100)] text-[var(--color-primary-800)] rounded-full dark:bg-[var(--color-primary-900)] dark:text-[var(--color-primary-200)]">
                {item.badge}
              </span>
            )}

            {/* Expand/Collapse Icon */}
            {hasChildren && (
              <span className="flex-shrink-0">
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </span>
            )}
          </>
        )}
      </button>

      {/* Children */}
      {hasChildren && isExpanded && !isCollapsed && (
        <ul
          className="mt-[var(--space-xs)] space-y-[var(--space-xs)]"
          role="list"
        >
          {item.children!.map((child) => (
            <NavigationItemComponent
              key={child.id}
              item={child}
              isExpanded={false}
              isActive={isItemActive(child, pathname)}
              isCollapsed={false}
              onToggle={() => {}}
              onClick={onClick}
              level={level + 1}
              itemRef={itemRef}
            />
          ))}
        </ul>
      )}
    </li>
  );
};

// Sidebar Toggle Button
const SidebarToggle: React.FC = () => {
  const { sidebarOpen, toggleSidebar, isMobile } = useAppShell();

  const handleToggle = () => {
    toggleSidebar();
  };

  return (
    <button
      className={cn(
        "flex items-center justify-center",
        "w-8 h-8 rounded-[var(--radius-sm)]",
        "text-[var(--color-neutral-600)] dark:text-[var(--color-neutral-400)]",
        "hover:bg-[var(--color-neutral-200)] hover:text-[var(--color-neutral-900)]",
        "dark:hover:bg-[var(--color-neutral-800)] dark:hover:text-[var(--color-neutral-100)]",
        "transition-colors [transition-duration:var(--duration-fast)] [transition-timing-function:var(--ease-standard)]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring-color)]"
      )}
      onClick={handleToggle}
      aria-label={isMobile ? "Toggle navigation menu" : "Toggle sidebar"}
    >
      {isMobile ? (
        sidebarOpen ? (
          <X className="h-5 w-5" />
        ) : (
          <Menu className="h-5 w-5" />
        )
      ) : (
        <Menu className="h-5 w-5" />
      )}
    </button>
  );
};

// Utility functions
function findActiveItem(
  items: NavigationItem[],
  pathname: string
): { item: NavigationItem; parent?: string } | null {
  for (const item of items) {
    if (item.href === pathname) {
      return { item };
    }
    if (item.children) {
      const found = findActiveItem(item.children, pathname);
      if (found) {
        return { ...found, parent: item.id };
      }
    }
  }
  return null;
}

function isItemActive(item: NavigationItem, pathname: string): boolean {
  if (item.href === pathname) return true;
  if (item.children) {
    return item.children.some((child) => isItemActive(child, pathname));
  }
  return false;
}
