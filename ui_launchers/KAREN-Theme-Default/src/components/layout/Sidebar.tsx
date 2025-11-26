"use client";

import React, { useState, useMemo, useCallback, memo } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import {
  Home,
  MessageSquare,
  Brain,
  Cpu,
  Puzzle,
  BarChart3,
  Activity,
  Shield,
  Settings,
  ChevronLeft,
  ChevronRight,
  Search,
  Command,
  LucideIcon,
  Bot,
  Database,
  Network,
  Layers,
  Terminal,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";

export interface NavItem {
  icon: LucideIcon;
  label: string;
  href: string;
  badge?: string;
  shortcut?: string;
  description?: string;
  disabled?: boolean;
}

export interface NavSection {
  section: string;
  items: NavItem[];
}

const navigationStructure: NavSection[] = [
  {
    section: "Core",
    items: [
      {
        icon: Home,
        label: "Dashboard",
        href: "/",
        shortcut: "Ctrl+D",
        description: "Overview and system status"
      },
      {
        icon: MessageSquare,
        label: "Chat Studio",
        href: "/chat",
        shortcut: "Ctrl+K",
        description: "Interactive AI conversations"
      },
    ],
  },
  {
    section: "AI Management",
    items: [
      {
        icon: Brain,
        label: "Memory Lab",
        href: "/memory",
        badge: "New",
        description: "Memory management and knowledge base"
      },
      {
        icon: Cpu,
        label: "Model Manager",
        href: "/models",
        description: "AI model configuration and deployment"
      },
      {
        icon: Bot,
        label: "Agent Forge",
        href: "/agents",
        description: "AI agent creation and management"
      },
      {
        icon: Puzzle,
        label: "Plugin Hub",
        href: "/plugins",
        description: "Extensions and integrations"
      },
    ],
  },
  {
    section: "Operations",
    items: [
      {
        icon: BarChart3,
        label: "Analytics Lab",
        href: "/analytics",
        description: "Data analysis and insights"
      },
      {
        icon: Activity,
        label: "Performance",
        href: "/performance",
        description: "System performance monitoring"
      },
      {
        icon: Shield,
        label: "Security",
        href: "/security",
        description: "Security settings and audit logs"
      },
    ],
  },
  {
    section: "Advanced",
    items: [
      {
        icon: Database,
        label: "Data Hub",
        href: "/data",
        description: "Data sources and management"
      },
      {
        icon: Network,
        label: "API Gateway",
        href: "/api-gateway",
        description: "API configuration and monitoring"
      },
      {
        icon: Layers,
        label: "Workflows",
        href: "/workflows",
        description: "Automation and process flows"
      },
    ],
  },
  {
    section: "System",
    items: [
      {
        icon: Settings,
        label: "Settings",
        href: "/settings",
        description: "System configuration"
      },
      {
        icon: Terminal,
        label: "Developer",
        href: "/developer",
        description: "Developer tools and documentation"
      },
    ],
  },
];

export interface ModernSidebarProps {
  className?: string;
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
  navigation?: NavSection[];
  showFooter?: boolean;
  showSearch?: boolean;
}

export const Sidebar = memo(({
  className,
  collapsed: controlledCollapsed,
  onCollapsedChange,
  navigation = navigationStructure,
  showFooter = true,
  showSearch = true
}: ModernSidebarProps) => {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const pathname = usePathname();
  
  const collapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;

  const toggleCollapsed = useCallback(() => {
    const newCollapsed = !collapsed;
    setInternalCollapsed(newCollapsed);
    onCollapsedChange?.(newCollapsed);
  }, [collapsed, onCollapsedChange]);

  const sidebarClasses = useMemo(() => (
    cn(
      "fixed left-0 top-0 z-40 h-screen border-r border-border bg-card/90 backdrop-blur-lg transition-all duration-300 ease-in-out shadow-sm",
      collapsed ? "w-16" : "w-64",
      className
    )
  ), [collapsed, className]);

  return (
    <TooltipProvider>
      <ErrorBoundary>
        <aside
          className={sidebarClasses}
          role="navigation"
          aria-label="Main navigation"
        >
          {/* Skip to main content link for accessibility */}
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:right-4 bg-primary text-primary-foreground px-4 py-2 rounded-md z-50"
            aria-label="Skip to main content"
          >
            Skip to main content
          </a>
          
          {/* Sidebar Header */}
          <div className="flex h-16 items-center justify-between border-b border-border px-4">
            <ErrorBoundary>
              {!collapsed ? (
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white font-bold shadow-md transition-all hover:shadow-lg">
                    K
                  </div>
                  <span className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    Kari AI
                  </span>
                </div>
              ) : (
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white font-bold shadow-md">
                  K
                </div>
              )}
            </ErrorBoundary>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleCollapsed}
                  className="h-8 w-8 transition-all hover:bg-accent hover:text-accent-foreground"
                  aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
                  aria-controls="sidebar-content"
                  aria-expanded={!collapsed}
                >
                  {collapsed ? (
                    <ChevronRight className="h-4 w-4" />
                  ) : (
                    <ChevronLeft className="h-4 w-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">
                {collapsed ? "Expand sidebar" : "Collapse sidebar"}
              </TooltipContent>
            </Tooltip>
          </div>

          {/* Global Search */}
          {showSearch && !collapsed && (
            <div className="p-4">
              <Button
                variant="outline"
                className="w-full justify-start gap-2 text-muted-foreground transition-all hover:bg-accent hover:text-accent-foreground"
              >
                <Search className="h-4 w-4" />
                <span>Search...</span>
                <kbd className="pointer-events-none ml-auto inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
                  <Command className="h-3 w-3" />K
                </kbd>
              </Button>
            </div>
          )}

          {/* Navigation */}
          <ScrollArea className="flex-1 px-3" id="sidebar-content">
            <nav
              className="space-y-6 py-4"
              role="navigation"
              aria-label="Main navigation sections"
            >
              {navigation.map((section, sectionIndex) => (
                <div key={section.section} className="space-y-1">
                  {!collapsed && (
                    <h3
                      className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                      id={`section-${sectionIndex}`}
                    >
                      {section.section}
                    </h3>
                  )}
                  <div
                    className="space-y-1"
                    role="list"
                    aria-labelledby={!collapsed ? `section-${sectionIndex}` : undefined}
                  >
                    {section.items.map((item) => {
                      const isActive = pathname === item.href;
                      
                      if (collapsed) {
                        return (
                          <Tooltip key={item.href}>
                            <TooltipTrigger asChild>
                              <Link
                                href={item.disabled ? '#' : item.href}
                                className={cn(
                                  "group flex items-center justify-center rounded-lg px-3 py-2 transition-all duration-200",
                                  "hover:bg-accent hover:text-accent-foreground",
                                  isActive
                                    ? "bg-primary/10 text-primary font-medium"
                                    : "text-muted-foreground",
                                  item.disabled && "opacity-50 cursor-not-allowed"
                                )}
                                title={item.label}
                                aria-current={isActive ? "page" : undefined}
                                role="listitem"
                              >
                                <item.icon
                                  className={cn(
                                    "h-5 w-5 shrink-0 transition-all duration-200",
                                    isActive && "scale-110 text-primary"
                                  )}
                                  aria-hidden="true"
                                />
                                {item.badge && (
                                  <span className="absolute top-1 right-1 flex h-2 w-2">
                                    <span className="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
                                  </span>
                                )}
                              </Link>
                            </TooltipTrigger>
                            <TooltipContent side="right">
                              <div className="text-center">
                                <p className="font-medium">{item.label}</p>
                                {item.description && (
                                  <p className="text-xs text-muted-foreground mt-1">{item.description}</p>
                                )}
                                {item.shortcut && (
                                  <p className="text-xs mt-1 font-mono">{item.shortcut}</p>
                                )}
                              </div>
                            </TooltipContent>
                          </Tooltip>
                        );
                      }
                      
                      return (
                        <Link
                          key={item.href}
                          href={item.disabled ? '#' : item.href}
                          className={cn(
                            "group flex items-center gap-3 rounded-lg px-3 py-2 transition-all duration-200",
                            "hover:bg-accent hover:text-accent-foreground",
                            isActive
                              ? "bg-primary/10 text-primary font-medium"
                              : "text-muted-foreground",
                            item.disabled && "opacity-50 cursor-not-allowed"
                          )}
                          title={item.label}
                          aria-current={isActive ? "page" : undefined}
                          role="listitem"
                        >
                          <item.icon
                            className={cn(
                              "h-5 w-5 shrink-0 transition-all duration-200",
                              isActive && "scale-110 text-primary"
                            )}
                            aria-hidden="true"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="truncate">{item.label}</span>
                              {item.badge && (
                                <Badge
                                  variant={isActive ? "default" : "secondary"}
                                  className="ml-auto text-xs h-5 px-1.5"
                                  aria-label={`${item.label} ${item.badge}`}
                                >
                                  {item.badge}
                                </Badge>
                              )}
                            </div>
                            {item.shortcut && (
                              <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground ml-auto">
                                {item.shortcut}
                              </kbd>
                            )}
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              ))}
            </nav>
          </ScrollArea>

          {/* Sidebar Footer */}
          {showFooter && (
            <div className="border-t border-border p-4">
              <ErrorBoundary>
                {!collapsed ? (
                  <div className="rounded-lg bg-gradient-to-br from-blue-500/10 to-purple-600/10 p-3 text-xs border border-border/50">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                      <p className="font-medium text-foreground">
                        AI Command Center
                      </p>
                    </div>
                    <p className="text-muted-foreground">
                      4 active agents, 12 tasks queued
                    </p>
                  </div>
                ) : (
                  <div className="flex justify-center">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse cursor-pointer"></div>
                      </TooltipTrigger>
                      <TooltipContent side="right">
                        <p className="text-xs">System active: 4 agents, 12 tasks</p>
                      </TooltipContent>
                    </Tooltip>
                  </div>
                )}
              </ErrorBoundary>
            </div>
          )}
        </aside>
      </ErrorBoundary>
    </TooltipProvider>
  );
});

Sidebar.displayName = 'ModernSidebar';

export default Sidebar;
