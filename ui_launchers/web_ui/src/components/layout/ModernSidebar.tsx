'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Home,
  MessageSquare,
  Brain,
  Cpu,
  Zap,
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
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export interface NavItem {
  icon: LucideIcon;
  label: string;
  href: string;
  badge?: string;
  shortcut?: string;
}

export interface NavSection {
  section: string;
  items: NavItem[];
}

const navigationStructure: NavSection[] = [
  {
    section: 'Core',
    items: [
      { icon: Home, label: 'Dashboard', href: '/', shortcut: 'Ctrl+D' },
      { icon: MessageSquare, label: 'Chat Studio', href: '/chat', shortcut: 'Ctrl+K' },
    ],
  },
  {
    section: 'AI Management',
    items: [
      { icon: Brain, label: 'Memory Lab', href: '/memory', badge: 'New' },
      { icon: Cpu, label: 'Model Manager', href: '/models' },
      { icon: Zap, label: 'Agent Forge', href: '/agents' },
      { icon: Puzzle, label: 'Plugin Hub', href: '/plugins' },
    ],
  },
  {
    section: 'Operations',
    items: [
      { icon: BarChart3, label: 'Analytics Lab', href: '/analytics' },
      { icon: Activity, label: 'Performance', href: '/performance' },
      { icon: Shield, label: 'Security', href: '/security' },
    ],
  },
  {
    section: 'System',
    items: [
      { icon: Settings, label: 'Settings', href: '/settings' },
    ],
  },
];

export interface ModernSidebarProps {
  className?: string;
}

export function ModernSidebar({ className }: ModernSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen border-r border-border bg-card transition-all duration-300 ease-in-out',
        collapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      {/* Sidebar Header */}
      <div className="flex h-16 items-center justify-between border-b border-border px-4">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white font-bold">
              K
            </div>
            <span className="text-lg font-bold gradient-neural bg-clip-text text-transparent">
              Kari AI
            </span>
          </div>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className="h-8 w-8"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Global Search */}
      {!collapsed && (
        <div className="p-4">
          <Button
            variant="outline"
            className="w-full justify-start gap-2 text-muted-foreground"
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
      <ScrollArea className="flex-1 px-3">
        <nav className="space-y-6 py-4">
          {navigationStructure.map((section) => (
            <div key={section.section} className="space-y-1">
              {!collapsed && (
                <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  {section.section}
                </h3>
              )}
              <div className="space-y-1">
                {section.items.map((item) => {
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        'group flex items-center gap-3 rounded-lg px-3 py-2 transition-all duration-200',
                        'hover:bg-accent hover:text-accent-foreground',
                        isActive
                          ? 'bg-primary/10 text-primary font-medium'
                          : 'text-muted-foreground'
                      )}
                      title={collapsed ? item.label : undefined}
                    >
                      <item.icon
                        className={cn(
                          'h-5 w-5 shrink-0 transition-all duration-200',
                          isActive && 'scale-110'
                        )}
                      />
                      {!collapsed && (
                        <>
                          <span className="flex-1 truncate">{item.label}</span>
                          {item.badge && (
                            <Badge
                              variant="secondary"
                              className="ml-auto text-xs"
                            >
                              {item.badge}
                            </Badge>
                          )}
                        </>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </ScrollArea>

      {/* Sidebar Footer */}
      <div className="border-t border-border p-4">
        {!collapsed ? (
          <div className="rounded-lg bg-gradient-to-br from-blue-500/10 to-purple-600/10 p-3 text-xs">
            <p className="font-medium text-foreground mb-1">
              AI Command Center
            </p>
            <p className="text-muted-foreground">
              4 active agents, 12 tasks queued
            </p>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          </div>
        )}
      </div>
    </aside>
  );
}

export default ModernSidebar;
