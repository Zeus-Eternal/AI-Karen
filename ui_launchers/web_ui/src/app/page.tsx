"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { Brain, MessageSquare, SettingsIcon as SettingsIconLucide, Bell, SlidersHorizontal, LayoutGrid, Database, Facebook, BookOpenCheck, Mail, CalendarDays, CloudSun, PlugZap } from 'lucide-react';
import dynamic from 'next/dynamic';
import SettingsDialogComponent from '@/components/settings/SettingsDialog';
import DatabaseConnectorPluginPage from '@/components/plugins/DatabaseConnectorPluginPage';
import FacebookPluginPage from '@/components/plugins/FacebookPluginPage';
import GmailPluginPage from '@/components/plugins/GmailPluginPage';
import DateTimePluginPage from '@/components/plugins/DateTimePluginPage';
import WeatherPluginPage from '@/components/plugins/WeatherPluginPage';
import PluginOverviewPage from '@/components/plugins/PluginOverviewPage'; // Ensure this is imported
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Sidebar,
  SidebarProvider,
  SidebarTrigger as AppSidebarTrigger,
  SidebarInset,
  SidebarHeader as AppSidebarHeader,
  SidebarContent as AppSidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarFooter as AppSidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar";
import { Separator } from '@/components/ui/separator';
import NotificationsSection from '@/components/sidebar/NotificationsSection';
import Dashboard from '@/components/dashboard/Dashboard';
import { webUIConfig } from '@/lib/config';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AuthenticatedHeader } from '@/components/layout/AuthenticatedHeader';

const ExtensionSidebar = dynamic(() => import('@/components/extensions/ExtensionSidebar'));

type ActiveView = 'settings' | 'dashboard' | 'commsCenter' | 'pluginDatabaseConnector' | 'pluginFacebook' | 'pluginGmail' | 'pluginDateTime' | 'pluginWeather' | 'pluginOverview';

export default function HomePage() {
  return (
    <ProtectedRoute>
      <AuthenticatedHomePage />
    </ProtectedRoute>
  );
}

function AuthenticatedHomePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const parseView = (sp: ReturnType<typeof useSearchParams> | null): ActiveView => {
    const v = sp?.get('view') ?? '';
    const allowed: ActiveView[] = [
      'settings',
      'dashboard',
      'commsCenter',
      'pluginDatabaseConnector',
      'pluginFacebook',
      'pluginGmail',
      'pluginDateTime',
      'pluginWeather',
      'pluginOverview',
    ];
    return (allowed as readonly string[]).includes(v) ? (v as ActiveView) : 'dashboard';
  };
  const initialView = parseView(searchParams as any);
  const [activeMainView, setActiveMainView] = useState<ActiveView>(initialView);

  useEffect(() => {
    setActiveMainView(initialView);
  }, [initialView]);

  const navigate = (view: ActiveView) => {
    setActiveMainView(view);
    const params = new URLSearchParams(searchParams ? searchParams.toString() : '');
    params.set('view', view);
    router.push(`/?${params.toString()}`);
  };

  return (
    <SidebarProvider>
      <div className="app-grid">
        <header className="app-header header-enhanced">
          <div className="container-fluid flex-between py-3 md:py-4">
            <div className="flex-start space-x-3">
              <AppSidebarTrigger className="mr-1 md:mr-2 smooth-transition interactive">
                {/* Default PanelLeft icon will be rendered by AppSidebarTrigger itself */}
              </AppSidebarTrigger>
              <Brain className="h-7 w-7 md:h-8 md:w-8 text-primary shrink-0 smooth-transform" />
              <h1 className="text-xl md:text-2xl font-semibold tracking-tight bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent">
                Karen AI
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="icon" aria-label="Settings" className="focus-ring smooth-transition">
                    <SlidersHorizontal className="h-5 w-5 text-muted-foreground hover:text-foreground smooth-transition" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="w-[90vw] max-w-sm sm:w-[480px] p-0 flex flex-col modern-card-glass">
                  <SheetHeader className="p-4 border-b">
                    <SheetTitle>Settings</SheetTitle>
                  </SheetHeader>
                  <div className="flex-1 overflow-y-auto p-4 scroll-smooth">
                    <SettingsDialogComponent />
                  </div>
                </SheetContent>
              </Sheet>
              <AuthenticatedHeader />
            </div>
          </div>
        </header>

        <div className="flex flex-1 min-h-0">
          {webUIConfig.enableExtensions ? (
            <ExtensionSidebar />
          ) : (
            <Sidebar variant="sidebar" collapsible="icon" className="border-r z-20 sidebar-enhanced">
              <AppSidebarHeader className="p-4">
                <h2 className="text-lg font-semibold tracking-tight">Navigation</h2>
              </AppSidebarHeader>
              <Separator className="my-1" />
              <AppSidebarContent className="p-2 scroll-smooth">
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild className="w-full" isActive={pathname === '/chat'}>
                      <Link href="/chat">
                        <MessageSquare />
                        Chat
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => navigate('dashboard')} isActive={activeMainView === 'dashboard'} className="w-full">
                      <LayoutGrid />
                      Dashboard
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => navigate('settings')} isActive={activeMainView === 'settings'} className="w-full">
                      <SettingsIconLucide />
                      Settings
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => navigate('commsCenter')} isActive={activeMainView === 'commsCenter'} className="w-full">
                      <Bell />
                      Comms Center
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>

                <Separator className="my-2" />
                <SidebarGroup>
                  <SidebarGroupLabel className="text-sm">Plugins</SidebarGroupLabel>
                  <SidebarMenu>
                    <SidebarMenuItem>
                      <SidebarMenuButton onClick={() => navigate('pluginOverview')} isActive={activeMainView === 'pluginOverview'} className="w-full">
                        <PlugZap />
                        Plugin Overview
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton onClick={() => navigate('pluginDatabaseConnector')} isActive={activeMainView === 'pluginDatabaseConnector'} className="w-full">
                        <Database />
                        Database Connector
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton onClick={() => navigate('pluginFacebook')} isActive={activeMainView === 'pluginFacebook'} className="w-full">
                        <Facebook />
                        Facebook Plugin
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton onClick={() => navigate('pluginGmail')} isActive={activeMainView === 'pluginGmail'} className="w-full">
                        <Mail />
                        Gmail Plugin
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton onClick={() => navigate('pluginDateTime')} isActive={activeMainView === 'pluginDateTime'} className="w-full">
                        <CalendarDays />
                        Date/Time Plugin
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton onClick={() => navigate('pluginWeather')} isActive={activeMainView === 'pluginWeather'} className="w-full">
                        <CloudSun />
                        Weather Service
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  </SidebarMenu>
                </SidebarGroup>
              </AppSidebarContent>
              <AppSidebarFooter className="p-2 border-t">
                <p className="text-xs text-muted-foreground text-center">Karen AI Menu</p>
              </AppSidebarFooter>
            </Sidebar>
          )}

          <SidebarInset className="app-main">
            <div className="space-y-fluid">
              {activeMainView === 'dashboard' && <Dashboard />}
              {activeMainView === 'settings' && <SettingsDialogComponent />}
              {activeMainView === 'pluginDatabaseConnector' && <DatabaseConnectorPluginPage />}
              {activeMainView === 'pluginFacebook' && <FacebookPluginPage />}
              {activeMainView === 'pluginGmail' && <GmailPluginPage />}
              {activeMainView === 'pluginDateTime' && <DateTimePluginPage />}
              {activeMainView === 'pluginWeather' && <WeatherPluginPage />}
              {activeMainView === 'pluginOverview' && <PluginOverviewPage />}
              {activeMainView === 'commsCenter' && (
                <div className="space-y-fluid">
                  <div className="modern-card">
                    <div className="modern-card-header">
                      <h2 className="text-2xl font-semibold tracking-tight">Communications Center</h2>
                      <p className="text-sm text-muted-foreground mt-2">
                        Updates, alerts, and notes from Karen.
                      </p>
                    </div>
                    <div className="modern-card-content">
                      <NotificationsSection />
                    </div>
                  </div>
                  <div className="modern-card">
                    <div className="modern-card-header">
                      <h3 className="text-lg font-semibold">My Notes (Conceptual)</h3>
                    </div>
                    <div className="modern-card-content min-h-[150px]">
                      <p className="text-sm text-muted-foreground">This space is reserved for future features.</p>
                      <p className="mt-2 text-sm text-muted-foreground">For example, Karen might save summaries of long conversations or important points she's learned here for your easy review.</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </SidebarInset>
        </div>
      </div>
    </SidebarProvider>
  );
}
