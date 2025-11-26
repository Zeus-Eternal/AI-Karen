'use client';

import * as React from 'react';
import { useMemo, memo, useState } from 'react';
import { Bell, Search, User, Settings, Command, Sparkles, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { StatusIndicator } from '@/components/ui/status-indicator';
import { cn } from '@/lib/utils';
import { ErrorBoundary } from '@/components/ui/error-boundary';

export interface HeaderProps {
  className?: string;
  sidebarCollapsed?: boolean;
  title?: string;
  showStatus?: boolean;
  showSearch?: boolean;
  showNotifications?: boolean;
  showUserMenu?: boolean;
  notifications?: NotificationItem[];
  user?: {
    name: string;
    email: string;
    avatar?: string;
  };
}

export interface NotificationItem {
  id: string;
  title: string;
  description: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp?: string;
  read?: boolean;
}

export const Header = memo(({
  className,
  sidebarCollapsed = false,
  title = "Dashboard",
  showStatus = true,
  showSearch = true,
  showNotifications = true,
  showUserMenu = true,
  notifications = [
    {
      id: '1',
      title: 'Model Update Available',
      description: 'GPT-4 Turbo is now available',
      type: 'info',
      timestamp: '2 min ago'
    },
    {
      id: '2',
      title: 'Agent Task Completed',
      description: 'Data analysis workflow finished',
      type: 'success',
      timestamp: '15 min ago'
    },
    {
      id: '3',
      title: 'High Memory Usage',
      description: 'Vector store at 85% capacity',
      type: 'warning',
      timestamp: '1 hour ago'
    }
  ],
  user = {
    name: 'User Name',
    email: 'user@example.com'
  }
}: HeaderProps) => {
  const [notificationCount, setNotificationCount] = useState(notifications.filter(n => !n.read).length);
  
  const headerClasses = useMemo(() => (
    cn(
      'fixed top-0 right-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/90 backdrop-blur-xl px-6 transition-all duration-300 shadow-sm',
      sidebarCollapsed ? 'left-16' : 'left-64',
      className
    )
  ), [sidebarCollapsed, className]);

  const getNotificationIcon = (type: NotificationItem['type']) => {
    switch (type) {
      case 'success': return <Activity className="h-4 w-4 text-green-500" />;
      case 'warning': return <Activity className="h-4 w-4 text-yellow-500" />;
      case 'error': return <Activity className="h-4 w-4 text-red-500" />;
      default: return <Sparkles className="h-4 w-4 text-blue-500" />;
    }
  };

  const getNotificationColor = (type: NotificationItem['type']) => {
    switch (type) {
      case 'success': return 'bg-green-500/10 hover:bg-green-500/20';
      case 'warning': return 'bg-yellow-500/10 hover:bg-yellow-500/20';
      case 'error': return 'bg-red-500/10 hover:bg-red-500/20';
      default: return 'bg-blue-500/10 hover:bg-blue-500/20';
    }
  };

  return (
    <ErrorBoundary>
      <header
        className={headerClasses}
      >
        {/* Left Section - Breadcrumbs or Title */}
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold tracking-tight">{title}</h1>
          {showStatus && (
            <ErrorBoundary>
              <Badge variant="outline" className="gap-1 px-2 py-1 transition-all hover:bg-accent hover:text-accent-foreground">
                <StatusIndicator status="online" size="sm" showDot pulse />
                <span className="hidden sm:inline text-xs">System Active</span>
              </Badge>
            </ErrorBoundary>
          )}
        </div>

        {/* Right Section - Actions */}
        <div className="flex items-center gap-2" role="toolbar" aria-label="Header actions">
          {/* Global Search */}
          {showSearch && (
            <Button
              variant="outline"
              size="sm"
              className="gap-2 text-muted-foreground transition-all hover:bg-accent hover:text-accent-foreground focus:ring-2 focus:ring-primary/20"
              aria-label="Global search"
              title="Global search (Ctrl+K)"
            >
              <Search className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">Search</span>
              <kbd className="pointer-events-none hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium" aria-hidden="true">
                <Command className="h-3 w-3" />K
              </kbd>
            </Button>
          )}

          {/* Notifications */}
          {showNotifications && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="relative transition-all hover:bg-accent hover:text-accent-foreground"
                  aria-label="Notifications"
                  aria-expanded="false"
                  aria-controls="notification-menu"
                >
                  <Bell className="h-5 w-5" aria-hidden="true" />
                  {notificationCount > 0 && (
                    <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-white animate-pulse" aria-label={`${notificationCount} notifications`}>
                      {notificationCount}
                    </span>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-80 max-h-[80vh] overflow-y-auto">
                <div className="flex items-center justify-between p-4">
                  <DropdownMenuLabel className="text-base font-semibold">Notifications</DropdownMenuLabel>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs h-7"
                    onClick={() => setNotificationCount(0)}
                  >
                    Mark all as read
                  </Button>
                </div>
                <DropdownMenuSeparator />
                <ErrorBoundary>
                  <div className="space-y-1 p-1" role="list">
                    {notifications.length > 0 ? (
                      notifications.map((notification) => (
                        <div
                          key={notification.id}
                          className={cn(
                            "rounded-lg p-3 text-sm cursor-pointer transition-all",
                            getNotificationColor(notification.type),
                            !notification.read && "border-l-2 border-primary"
                          )}
                          role="listitem"
                        >
                          <div className="flex items-start gap-3">
                            {getNotificationIcon(notification.type)}
                            <div className="flex-1 space-y-1">
                              <p className="font-medium">{notification.title}</p>
                              <p className="text-xs text-muted-foreground">{notification.description}</p>
                              {notification.timestamp && (
                                <p className="text-xs text-muted-foreground/70">{notification.timestamp}</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No notifications</p>
                      </div>
                    )}
                  </div>
                </ErrorBoundary>
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          {/* User Menu */}
          {showUserMenu && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="relative h-10 w-10 rounded-full transition-all hover:bg-accent hover:text-accent-foreground"
                  aria-label="User menu"
                  aria-expanded="false"
                  aria-controls="user-menu"
                >
                  <Avatar className="h-10 w-10 ring-2 ring-primary/20 transition-all hover:ring-primary/40">
                    <AvatarImage src={user.avatar} alt={user.name} />
                    <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white font-semibold">
                      {user.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <ErrorBoundary>
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium">{user.name}</p>
                      <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                    </div>
                  </ErrorBoundary>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="cursor-pointer transition-colors hover:bg-accent hover:text-accent-foreground">
                  <User className="mr-2 h-4 w-4" aria-hidden="true" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer transition-colors hover:bg-accent hover:text-accent-foreground">
                  <Settings className="mr-2 h-4 w-4" aria-hidden="true" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-red-600 cursor-pointer transition-colors hover:bg-red-50 focus:bg-red-50">
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </header>
    </ErrorBoundary>
  );
});

Header.displayName = 'Header';

export default Header;
