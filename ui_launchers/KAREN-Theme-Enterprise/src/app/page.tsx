"use client";

import { useState, useCallback, useMemo, useEffect } from 'react';
import { Brain, MessageSquare, Settings, Bell, Database, Facebook, Mail, CalendarDays, CloudSun, PlugZap } from 'lucide-react';
import SettingsDialogComponent from '@/components/settings/SettingsDialog';
import DatabaseConnectorPluginPage from '@/components/plugins/DatabaseConnectorPluginPage';
import FacebookPluginPage from '@/components/plugins/FacebookPluginPage';
import GmailPluginPage from '@/components/plugins/GmailPluginPage';
import DateTimePluginPage from '@/components/plugins/DateTimePluginPage';
import WeatherPluginPage from '@/components/plugins/WeatherPluginPage';
import PluginOverviewPage from '@/components/plugins/PluginOverviewPage';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Sidebar,
  SidebarProvider,
  SidebarTrigger,
  SidebarInset,
  SidebarHeader,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar";
import { Separator } from '@/components/ui/separator';
import NotificationsSection from '@/components/sidebar/NotificationsSection';
import ChatInterface from '@/components/chat/KarenChatInterface';
import { cn } from '@/lib/utils';

// Type definitions with proper TypeScript safety
type ActiveView =
  | 'chat'
  | 'settings'
  | 'commsCenter'
  | 'pluginDatabaseConnector'
  | 'pluginFacebook'
  | 'pluginGmail'
  | 'pluginDateTime'
  | 'pluginWeather'
  | 'pluginOverview';

interface NavigationItem {
  id: ActiveView;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
}

// Modern responsive hook using CSS Grid and Flexbox
const useResponsive = () => {
  const [isMobile, setIsMobile] = useState(false);
  
  useEffect(() => {
    const checkMobile = () => {
      if (typeof window !== 'undefined') {
        setIsMobile(window.innerWidth < 768);
      }
    };
    
    if (typeof window !== 'undefined') {
      checkMobile();
      window.addEventListener('resize', checkMobile);
      return () => window.removeEventListener('resize', checkMobile);
    }
  }, []);
  
  return { isMobile };
};

export default function HomePage() {
  const [activeMainView, setActiveMainView] = useState<ActiveView>('chat');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const { isMobile } = useResponsive();

  // Memoized navigation items for better performance
  const mainNavigationItems = useMemo<NavigationItem[]>(() => [
    {
      id: 'chat',
      label: 'Chat',
      icon: MessageSquare,
      description: 'Start a conversation with Karen AI'
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      description: 'Configure your preferences'
    },
    {
      id: 'commsCenter',
      label: 'Comms Center',
      icon: Bell,
      description: 'View notifications and updates'
    }
  ], []);

  const pluginNavigationItems = useMemo<NavigationItem[]>(() => [
    {
      id: 'pluginOverview',
      label: 'Plugin Overview',
      icon: PlugZap,
      description: 'Manage your plugins'
    },
    {
      id: 'pluginDatabaseConnector',
      label: 'Database Connector',
      icon: Database,
      description: 'Connect to databases'
    },
    {
      id: 'pluginFacebook',
      label: 'Facebook Integration',
      icon: Facebook,
      description: 'Connect to Facebook'
    },
    {
      id: 'pluginGmail',
      label: 'Gmail Integration',
      icon: Mail,
      description: 'Connect to Gmail'
    },
    {
      id: 'pluginDateTime',
      label: 'Date/Time Service',
      icon: CalendarDays,
      description: 'Date and time utilities'
    },
    {
      id: 'pluginWeather',
      label: 'Weather Service',
      icon: CloudSun,
      description: 'Weather information'
    }
  ], []);

  // Optimized navigation handler
  const handleNavigation = useCallback((viewId: ActiveView) => {
    setActiveMainView(viewId);
  }, []);

  // Modern responsive header with CSS Grid
  const Header = () => (
    <header className="karen-chat-header">
      <div className="karen-chat-header-content">
        <div className="flex items-center gap-3">
          <SidebarTrigger className="karen-mobile-desktop-transition">
            <Brain className="h-6 w-6 md:h-8 md:w-8 text-primary" />
          </SidebarTrigger>
          <h1 className="karen-chat-title">Karen AI</h1>
        </div>
        
        <div className="karen-chat-actions">
          <Sheet open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="karen-mobile-desktop-transition"
                aria-label="Settings"
              >
                <Settings className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent className="w-[90vw] max-w-sm sm:w-[480px] p-0 flex flex-col">
              <SheetHeader className="p-4 border-b">
                <SheetTitle>Settings</SheetTitle>
              </SheetHeader>
              <div className="flex-1 overflow-y-auto">
                <SettingsDialogComponent />
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );

  // Modern navigation component with CSS Grid
  const NavigationSection = ({ items, title }: { items: NavigationItem[], title?: string }) => (
    <div className="space-y-2">
      {title && (
        <SidebarGroupLabel className="text-sm font-medium px-2 py-1">
          {title}
        </SidebarGroupLabel>
      )}
      <SidebarMenu>
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <SidebarMenuItem key={item.id}>
              <SidebarMenuButton
                onClick={() => handleNavigation(item.id)}
                isActive={activeMainView === item.id}
                className={cn(
                  "w-full karen-mobile-desktop-transition",
                  "hover:bg-accent/50 focus:bg-accent/50",
                  "data-[active]:bg-accent data-[active]:text-accent-foreground"
                )}
                title={isMobile ? item.description : undefined}
              >
                <Icon className="h-4 w-4" />
                <span className="ml-2">{item.label}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          );
        })}
      </SidebarMenu>
    </div>
  );

  // Modern main content area with CSS Grid
  const MainContent = () => {
    const renderActiveView = () => {
      switch (activeMainView) {
        case 'chat':
          return <ChatInterface />;
        case 'settings':
          return <SettingsDialogComponent />;
        case 'pluginDatabaseConnector':
          return <DatabaseConnectorPluginPage />;
        case 'pluginFacebook':
          return <FacebookPluginPage />;
        case 'pluginGmail':
          return <GmailPluginPage />;
        case 'pluginDateTime':
          return <DateTimePluginPage />;
        case 'pluginWeather':
          return <WeatherPluginPage />;
        case 'pluginOverview':
          return <PluginOverviewPage />;
        case 'commsCenter':
          return (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h2 className="text-2xl font-semibold tracking-tight">Communications Center</h2>
                <p className="text-sm text-muted-foreground">
                  Updates, alerts, and notes from Karen.
                </p>
              </div>
              <Separator />
              <NotificationsSection />

              <div>
                <h3 className="text-lg font-semibold mb-2 pt-4">My Notes (Conceptual)</h3>
                <div className="p-4 border rounded-lg bg-card text-card-foreground shadow-sm min-h-[150px]">
                  <p className="text-sm text-muted-foreground">This space is reserved for future features.</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    For example, Karen might save summaries of long conversations or important points she's learned here for your easy review.
                  </p>
                </div>
              </div>
            </div>
          );
        default:
          return <ChatInterface />;
      }
    };

    return (
      <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          {renderActiveView()}
        </div>
      </main>
    );
  };

  return (
    <SidebarProvider>
      <div className="karen-app">
        <Header />
        
        <div className="karen-grid karen-grid-cols-1 md:karen-grid-cols-12 flex-1 min-h-0">
          <Sidebar
            variant="sidebar"
            collapsible="icon"
            className="karen-mobile-hidden md:karen-mobile-auto border-r z-20"
          >
            <SidebarHeader className="p-4">
              <h2 className="text-lg font-semibold tracking-tight">Navigation</h2>
            </SidebarHeader>
            <Separator className="my-1" />
            <SidebarContent className="p-2">
              <NavigationSection items={mainNavigationItems} />
              <Separator className="my-2" />
              <SidebarGroup>
                <NavigationSection items={pluginNavigationItems} title="Plugins" />
              </SidebarGroup>
            </SidebarContent>
            <SidebarFooter className="p-2 border-t">
              <p className="text-xs text-muted-foreground text-center">Karen AI Menu</p>
            </SidebarFooter>
          </Sidebar>

          <SidebarInset className="md:col-span-11 flex-1 flex flex-col min-h-0">
            <MainContent />
          </SidebarInset>
        </div>
      </div>
    </SidebarProvider>
  );
}
