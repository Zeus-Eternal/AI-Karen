// ui_launchers/KAREN-Theme-Default/src/components/navigation/SidebarNavigation.tsx

/**
 * SidebarNavigation Component
 *
 * Enhanced sidebar navigation with collapsible sections, mobile hamburger menu,
 * improved accessibility, and keyboard navigation support.
 * Based on requirements: 2.1, 2.2, 2.3, 2.4, 11.1, 11.2
 */

"use client";

import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useImperativeHandle,
  useMemo,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { useAppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/button";

// Lucide icons (use proven names to avoid TS errors)
import {
  Home,
  MessageSquare,
  GitBranch,
  Brain,
  Puzzle,
  BarChart3,
  Shield,
  Settings,
  ChevronDown,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";

/* ---------------------------------- Types --------------------------------- */

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

// Default navigation structure (icons mapped to known Lucide names)
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
    icon: GitBranch, // previously "Workflow"
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
export const sidebarNavigationVariants = cva(["flex flex-col h-full", "overflow-hidden"]);

export interface SidebarNavigationProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof sidebarNavigationVariants> {
  items?: NavigationItem[];
  onItemClick?: (item: NavigationItem) => void;
  enableKeyboardNavigation?: boolean;
  autoFocus?: boolean;
  ariaLabel?: string;
}

/* --------------------------- Sidebar Navigation --------------------------- */

export const SidebarNavigation = React.forwardRef<HTMLDivElement | null, SidebarNavigationProps>(
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
    const localNavRef = useRef<HTMLDivElement | null>(null);
    const navRef = localNavRef;
    const assignNavRef = useCallback(
      (node: HTMLDivElement | null) => {
        localNavRef.current = node;
        if (typeof ref === "function") {
          ref(node);
        } else if (ref) {
          (ref as React.MutableRefObject<HTMLDivElement | null>).current = node;
        }
      },
      [ref]
    );
    const itemRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

    useImperativeHandle<HTMLDivElement | null, HTMLDivElement | null>(
      ref,
      () => localNavRef.current,
      []
    );

    const activeParentId = React.useMemo(() => {
      const activeItem = findActiveItem(items, pathname || "/");
      return activeItem?.parent ?? null;
    }, [items, pathname]);

    const effectiveExpandedItems = React.useMemo(() => {
      if (!activeParentId) {
        return expandedItems;
      }
      if (expandedItems.has(activeParentId)) {
        return expandedItems;
      }
      return new Set([...expandedItems, activeParentId]);
    }, [expandedItems, activeParentId]);

    // Auto-focus navigation when requested
    useEffect(() => {
      if (autoFocus && localNavRef.current) {
        localNavRef.current.focus();
      }
    }, [autoFocus, navRef]);

    // Flatten items for keyboard navigation
    const flattenedItems = React.useMemo(() => {
      const flattened: { item: NavigationItem; level: number; parent?: string }[] = [];

      const flatten = (nodes: NavigationItem[], level = 0, parent?: string) => {
        nodes.forEach((node) => {
          flattened.push({ item: node, level, parent });
          if (node.children && effectiveExpandedItems.has(node.id)) {
            flatten(node.children, level + 1, node.id);
          }
        });
      };

      flatten(items);
      return flattened;
    }, [items, effectiveExpandedItems]);

    // Toggle expand/collapse
    const toggleExpanded = useCallback((itemId: string) => {
      setExpandedItems((prev) => {
        const next = new Set(prev);
        if (next.has(itemId)) next.delete(itemId);
        else next.add(itemId);
        return next;
      });
    }, []);

    // Handle item click
    const handleItemClick = useCallback(
      (item: NavigationItem) => {
        if (item.href) {
          if (item.external) {
            window.open(item.href, "_blank", "noreferrer,noopener");
          } else {
            router.push(item.href);
          }
          if (isMobile) closeSidebar();
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
          ([, button]) => button === currentButton
        )?.[0];

        if (!currentItemId) return;

        const currentIndex = flattenedItems.findIndex((x) => x.item.id === currentItemId);

        const focusIndex = (index: number) => {
          const meta = flattenedItems[index];
          if (meta) {
            const btn = itemRefs.current.get(meta.item.id);
            btn?.focus();
          }
        };

        switch (event.key) {
          case "ArrowDown": {
            event.preventDefault();
            focusIndex(Math.min(currentIndex + 1, flattenedItems.length - 1));
            break;
          }
          case "ArrowUp": {
            event.preventDefault();
            focusIndex(Math.max(currentIndex - 1, 0));
            break;
          }
          case "ArrowRight": {
            event.preventDefault();
            const curr = flattenedItems[currentIndex];
            if (curr?.item.children && !effectiveExpandedItems.has(curr.item.id)) {
              toggleExpanded(curr.item.id);
            }
            break;
          }
          case "ArrowLeft": {
            event.preventDefault();
            const curr = flattenedItems[currentIndex];
            if (curr?.item.children && effectiveExpandedItems.has(curr.item.id)) {
              toggleExpanded(curr.item.id);
            }
            break;
          }
          case "Enter":
          case " ": {
            event.preventDefault();
            const curr = flattenedItems[currentIndex];
            if (curr) {
              if (curr.item.children && !curr.item.href) {
                toggleExpanded(curr.item.id);
              } else {
                handleItemClick(curr.item);
              }
            }
            break;
          }
          case "Home": {
            event.preventDefault();
            focusIndex(0);
            break;
          }
          case "End": {
            event.preventDefault();
            focusIndex(flattenedItems.length - 1);
            break;
          }
        }
      };

      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }, [
      enableKeyboardNavigation,
      flattenedItems,
      effectiveExpandedItems,
      toggleExpanded,
      handleItemClick,
    ]);

    return (
      <nav
        ref={assignNavRef}
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
              Navigation
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
                isExpanded={effectiveExpandedItems.has(item.id)}
                isActive={isItemActive(item, pathname || '/')}
                isCollapsed={sidebarCollapsed}
                onToggle={() => toggleExpanded(item.id)}
                onClick={handleItemClick}
                itemRef={(el) => {
                  if (el) itemRefs.current.set(item.id, el);
                  else itemRefs.current.delete(item.id);
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

/* ------------------------- Navigation Item Component ---------------------- */

export interface NavigationItemComponentProps {
  item: NavigationItem;
  isExpanded: boolean;
  isActive: boolean;
  isCollapsed: boolean;
  onToggle: () => void;
  onClick: (item: NavigationItem) => void;
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
  const hasChildren = !!(item.children && item.children.length > 0);
  const Icon = item.icon;
  const resolvedItemRef = useCallback(
    (el: HTMLButtonElement | null) => {
      itemRef?.(el);
    },
    [itemRef]
  );

  // Indentation for nested levels when sidebar is expanded
  const nestedIndent =
    level > 0 && !isCollapsed ? "ml-[var(--space-lg)]" : "";

  return (
    <li>
      <Button
        ref={resolvedItemRef}
        className={cn(
          "w-full flex items-center gap-[var(--space-sm)] px-[var(--space-md)] py-[var(--space-sm)]",
          "text-left text-[var(--text-sm)] font-medium",
          "rounded-[var(--radius-md)] mx-[var(--space-xs)]",
          "transition-all [transition-duration:var(--duration-fast)] [transition-timing-function:var(--ease-standard)]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring-color)]",
          nestedIndent,
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
          }
        )}
        onClick={
          hasChildren && !item.href
            ? onToggle
            : () => {
                onClick(item);
              }
        }
        disabled={item.disabled}
        aria-expanded={hasChildren ? isExpanded : undefined}
        aria-current={isActive ? "page" : undefined}
        aria-level={level + 1}
        title={isCollapsed ? item.label : undefined}
        role="button"
      >
        {/* Icon */}
        {Icon && (
          <Icon
            className={cn("h-5 w-5 flex-shrink-0", {
              "text-[var(--color-primary-600)] dark:text-[var(--color-primary-400)]": isActive,
            })}
          />
        )}

        {/* Label */}
        {!isCollapsed && (
          <>
            <span className="flex-1 truncate">{item.label}</span>

            {/* Badge */}
            {item.badge && (
              <span className="inline-flex items-center justify-center px-2 py-1 text-xs font-medium bg-[var(--color-primary-100)] text-[var(--color-primary-800)] rounded-full dark:bg-[var(--color-primary-900)] dark:text-[var(--color-primary-200)] sm:text-sm md:text-base">
                {item.badge}
              </span>
            )}

            {/* Expand/Collapse Icon */}
            {hasChildren && (
              <span className="flex-shrink-0" aria-hidden="true">
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </span>
            )}
          </>
        )}
      </Button>

      {/* Children */}
      {hasChildren && isExpanded && !isCollapsed && (
        <ul className="mt-[var(--space-xs)] space-y-[var(--space-xs)]" role="list">
          {item.children!.map((child) => (
            <NavigationItemComponent
              key={child.id}
              item={child}
              isExpanded={false}
              isActive={isItemActive(child, pathname || '/')}
              isCollapsed={false}
              onToggle={() => {}}
              onClick={() => onClick(child)}
              level={level + 1}
              itemRef={itemRef}
            />
          ))}
        </ul>
      )}
    </li>
  );
};

/* --------------------------- Sidebar Toggle Button ------------------------ */

const SidebarToggle: React.FC = () => {
  const { sidebarOpen, toggleSidebar, isMobile } = useAppShell();

  return (
    <Button
      className={cn(
        "flex items-center justify-center",
        "w-8 h-8 rounded-[var(--radius-sm)]",
        "text-[var(--color-neutral-600)] dark:text-[var(--color-neutral-400)]",
        "hover:bg-[var(--color-neutral-200)] hover:text-[var(--color-neutral-900)]",
        "dark:hover:bg-[var(--color-neutral-800)] dark:hover:text-[var(--color-neutral-100)]",
        "transition-colors [transition-duration:var(--duration-fast)] [transition-timing-function:var(--ease-standard)]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring-color)]"
      )}
      onClick={toggleSidebar}
      aria-label={isMobile ? "Toggle navigation menu" : "Toggle sidebar"}
    >
      {isMobile ? (sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />) : <Menu className="h-5 w-5" />}
    </Button>
  );
};

/* --------------------------------- Utils ---------------------------------- */

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
