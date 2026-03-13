"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import {
  MessageSquare,
  LayoutGrid,
  Settings,
  Bell,
  PlugZap,
  Brain,
  History,
  FileText,
  Bot
} from 'lucide-react';

interface KarenSidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  className?: string;
}

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  badge?: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

/**
 * Production-Ready KAREN Sidebar
 * Implements persistent left sidebar with proper navigation
 */
export const KarenSidebar: React.FC<KarenSidebarProps> = ({
  isOpen = false,
  onClose,
  className = ''
}) => {
  const pathname = usePathname();

  const mainNav: NavSection = {
    title: 'Navigation',
    items: [
      {
        href: '/chat',
        label: 'Chat',
        icon: <MessageSquare className="h-4 w-4" />
      },
      {
        href: '/?view=dashboard',
        label: 'Dashboard',
        icon: <LayoutGrid className="h-4 w-4" />
      },
      {
        href: '/?view=settings',
        label: 'Settings',
        icon: <Settings className="h-4 w-4" />
      },
      {
        href: '/?view=commsCenter',
        label: 'Communications',
        icon: <Bell className="h-4 w-4" />
      }
    ]
  };

  const pluginNav: NavSection = {
    title: 'Plugins',
    items: [
      {
        href: '/?view=pluginOverview',
        label: 'Plugin Overview',
        icon: <PlugZap className="h-4 w-4" />
      }
    ]
  };

  const quickActions: NavSection = {
    title: 'Quick Actions',
    items: [
      {
        href: '/chat',
        label: 'New Chat',
        icon: <MessageSquare className="h-4 w-4" />
      },
      {
        href: '/?view=memory',
        label: 'Memory',
        icon: <History className="h-4 w-4" />
      },
      {
        href: '/?view=artifacts',
        label: 'Artifacts',
        icon: <FileText className="h-4 w-4" />
      }
    ]
  };

  const renderNavItem = (item: NavItem, isActive: boolean) => (
    <Button
      asChild
      variant={isActive ? 'default' : 'ghost'}
      className={cn(
        "w-full justify-start gap-3 h-10 rounded-lg",
        isActive && "bg-primary text-primary-foreground hover:bg-primary/90"
      )}
    >
      <Link href={item.href} className="flex items-center gap-3 w-full">
        {item.icon}
        <span className="font-medium">{item.label}</span>
        {item.badge && (
          <span className="ml-auto bg-accent text-accent-foreground text-xs px-2 py-1 rounded-full">
            {item.badge}
          </span>
        )}
      </Link>
    </Button>
  );

  const renderNavSection = (section: NavSection) => (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-3 px-3">
        {section.title}
      </h3>
      <nav className="space-y-1" aria-label={section.title}>
        {section.items.map((item) => (
          <div key={item.href} className="px-3">
            {renderNavItem(item, pathname === item.href)}
          </div>
        ))}
      </nav>
    </div>
  );

  return (
    <>
      {/* Mobile Overlay */}
      <div 
        className={cn(
          "fixed inset-0 bg-black/50 z-40 transition-opacity duration-200 md:hidden",
          isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        )}
        onClick={onClose}
        aria-label="Close sidebar overlay"
      />

      {/* Sidebar */}
      <aside 
        className={cn(
          "karen-sidebar fixed md:relative h-full bg-white border-r border-neutral-200 transition-transform duration-300 ease-out z-50",
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
        aria-label="Main navigation"
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-6 border-b border-neutral-200">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary/10">
                <Brain className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-neutral-900">
                  Karen AI
                </h2>
                <p className="text-sm text-neutral-500">
                  Assistant Hub
                </p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4" role="navigation">
            {renderNavSection(mainNav)}
            
            <Separator className="my-6" />
            
            {renderNavSection(quickActions)}
            
            <Separator className="my-6" />
            
            {renderNavSection(pluginNav)}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-neutral-200">
            <div className="text-xs text-neutral-500 text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <Bot className="h-3 w-3" />
                <span>Karen AI</span>
              </div>
              <div>Core Operations Suite</div>
              <div className="mt-2 text-neutral-400">
                Version 2.0.0
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default KarenSidebar;