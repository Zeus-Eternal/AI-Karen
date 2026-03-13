"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { cva, type VariantProps } from "class-variance-authority";
import { Home } from "lucide-react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ComponentType<{ className?: string }>;
  current?: boolean;
}

export interface RouteConfig {
  [key: string]: {
    label: string;
    icon?: React.ComponentType<{ className?: string }>;
    parent?: string;
    dynamic?: boolean;
  };
}

export const defaultRouteConfig: RouteConfig = {
  "/": {
    label: "Home",
    icon: Home,
  },
  "/dashboard": {
    label: "Dashboard",
    parent: "/",
  },
  "/chat": {
    label: "Chat Interface",
    parent: "/",
  },
  "/agents": {
    label: "Agent Management",
    parent: "/",
  },
  "/workflows": {
    label: "Workflow Builder",
    parent: "/agents",
  },
  "/automation": {
    label: "Automation",
    parent: "/agents",
  },
  "/memory": {
    label: "Memory & Analytics",
    parent: "/",
  },
  "/memory/analytics": {
    label: "Memory Analytics",
    parent: "/memory",
  },
  "/memory/search": {
    label: "Semantic Search",
    parent: "/memory",
  },
  "/memory/network": {
    label: "Memory Network",
    parent: "/memory",
  },
  "/plugins": {
    label: "Plugins & Extensions",
    parent: "/",
  },
  "/plugins/marketplace": {
    label: "Plugin Marketplace",
    parent: "/plugins",
  },
  "/extensions": {
    label: "Extensions",
    parent: "/plugins",
  },
  "/providers": {
    label: "Provider Configuration",
    parent: "/",
  },
  "/models": {
    label: "Model Management",
    parent: "/providers",
  },
  "/performance": {
    label: "Performance Metrics",
    parent: "/providers",
  },
  "/users": {
    label: "User Management",
    parent: "/",
  },
  "/roles": {
    label: "Roles & Permissions",
    parent: "/users",
  },
  "/audit": {
    label: "Audit Logs",
    parent: "/users",
  },
  "/settings": {
    label: "Settings",
    parent: "/",
  },
};

export const breadcrumbNavigationVariants = cva(
  [
    "flex items-center space-x-[var(--space-xs)]",
    "text-[var(--text-sm)]",
    "overflow-x-auto scrollbar-none",
  ],
  {
    variants: {
      size: {
        sm: "text-[var(--text-xs)]",
        md: "text-[var(--text-sm)]",
        lg: "text-[var(--text-base)]",
      },
    },
    defaultVariants: {
      size: "md",
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

export function generateBreadcrumbsFromRoute(
  pathname: string,
  routeConfig: RouteConfig,
  includeHome: boolean
): BreadcrumbItem[] {
  const breadcrumbs: BreadcrumbItem[] = [];
  const segments = pathname.split("/").filter(Boolean);

  if (includeHome) {
    breadcrumbs.push({
      label: "Home",
      href: "/",
      icon: Home,
      current: segments.length === 0,
    });
  }

  let currentPath = "";
  const paths: string[] = [];

  segments.forEach((segment) => {
    currentPath += `/${segment}`;
    paths.push(currentPath);
  });

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
      });
    } else {
      const segment = path.split("/").pop() || "Home";
      const label =
        segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, " ");
      breadcrumbs.push({
        label,
        href: isLast ? undefined : path,
        current: isLast,
      });
    }
  }

  return breadcrumbs;
}

export function useBreadcrumbs(routeConfig?: RouteConfig) {
  const pathname = usePathname();

  const breadcrumbs = React.useMemo(() => {
    return generateBreadcrumbsFromRoute(
      pathname || '/',
      routeConfig || defaultRouteConfig,
      true
    );
  }, [pathname, routeConfig]);

  return breadcrumbs;
}

