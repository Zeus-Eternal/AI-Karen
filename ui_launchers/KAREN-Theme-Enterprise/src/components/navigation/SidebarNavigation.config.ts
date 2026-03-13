import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import {
  BarChart3,
  Brain,
  ChevronDown,
  ChevronRight,
  GitBranch,
  Home,
  Menu,
  MessageSquare,
  Puzzle,
  Settings,
  Shield,
  X,
} from "lucide-react";

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
    icon: GitBranch,
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

export interface NavigationItemComponentProps {
  item: NavigationItem;
  isExpanded: boolean;
  isActive: boolean;
  isCollapsed: boolean;
  onToggle: () => void;
  onClick: (item: NavigationItem) => void;
  level?: number;
  itemRef?: (el: HTMLButtonElement | null) => void;
  isExpandedById?: (id: string) => boolean;
}

export const sidebarIcons = {
  ChevronDown,
  ChevronRight,
  Menu,
  X,
};
