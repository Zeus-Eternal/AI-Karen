
"use client";

import { useState } from 'react';
import { Brain, MessageSquare, SettingsIcon as SettingsIconLucide, PanelLeft, Bell, SlidersHorizontal, LayoutGrid, Database, Facebook, BookOpenCheck, Mail, CalendarDays, CloudSun, PlugZap } from 'lucide-react';
import dynamic from 'next/dynamic';
import SettingsDialogComponent from '@/components/settings/SettingsDialog';
import DatabaseConnectorPluginPage from '@/components/plugins/DatabaseConnectorPluginPage';
import FacebookPluginPage from '@/components/plugins/FacebookPluginPage';
import GmailPluginPage from '@/components/plugins/GmailPluginPage';
import DateTimePluginPage from '@/components/plugins/DateTimePluginPage';
import WeatherPluginPage from '@/components/plugins/WeatherPluginPage';
import PluginOverviewPage from '@/components/plugins/PluginOverviewPage'; // Ensure this is imported
import AuthHeader from '@/components/auth/AuthHeader'
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
import ModernChatInterface from '@/components/chat/ModernChatInterface';
import Dashboard from '@/components/dashboard/Dashboard';
import { webUIConfig } from '@/lib/config';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AuthenticatedHeader } from '@/components/layout/AuthenticatedHeader';

const ExtensionSidebar = dynamic(() => import('@/components/extensions/ExtensionSidebar'));

type ActiveView = 'chat' | 'settings' | 'dashboard' | 'commsCenter' | 'pluginDatabaseConnector' | 'pluginFacebook' | 'pluginGmail' | 'pluginDateTime' | 'pluginWeather' | 'pluginOverview';

export default function HomePage() {
  return (
    <AuthProvider>
      <ProtectedRoute>
        <AuthenticatedHomePage />
      </ProtectedRoute>
    </AuthProvider>
  );
}

function AuthenticatedHomePage() {
  const [activeMainView, setActiveMainView] = useState<ActiveView>('chat');

  return (
    <SidebarProvider>
      <div className="flex flex-col h-screen bg-background text-foreground">
        <header className="p-3 md:p-4 border-b border-border flex items-center justify-between sticky top-0 z-30 bg-background/90 backdrop-blur-md shadow-sm">
          <div className="flex items-center space-x-3">
            <AppSidebarTrigger className="mr-1 md:mr-2">
              {/* Default PanelLeft icon will be rendered by AppSidebarTrigger itself */}
            </AppSidebarTrigger>
            <Brain className="h-7 w-7 md:h-8 md:w-8 text-primary shrink-0" />
            <h1 className="text-xl md:text-2xl font-semibold tracking-tight">Karen AI</h1>
          </div>
          <div className="flex items-center gap-2">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Settings">
                  <SlidersHorizontal className="h-5 w-5 text-muted-foreground hover:text-foreground transition-colors" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[90vw] max-w-sm sm:w-[480px] p-0 flex flex-col">
                <SheetHeader className="p-4 border-b">
                  <SheetTitle>Settings</SheetTitle>
                </SheetHeader>
                <div className="flex-1 overflow-y-auto">
                  <SettingsDialogComponent />
                </div>
              </SheetContent>
            </Sheet>
            <AuthenticatedHeader />
          </div>
        </header>

        <div className="flex flex-1 min-h-0">
          {webUIConfig.enableExtensions ? (
            <ExtensionSidebar />
          ) : (
            <Sidebar variant="sidebar" collapsible="icon" className="border-r z-20">
              <AppSidebarHeader>
                <h2 className="text-lg font-semibold tracking-tight px-2 py-1">Navigation</h2>
              </AppSidebarHeader>
              <Separator className="my-1" />
              <AppSidebarContent className="p-2">
                <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    onClick={() => setActiveMainView('chat')}
                    isActive={activeMainView === 'chat'}
                    className="w-full"
                  >
                    <MessageSquare />
                    Chat
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    onClick={() => setActiveMainView('dashboard')}
                    isActive={activeMainView === 'dashboard'}
                    className="w-full"
                  >
                    <LayoutGrid />
                    Dashboard
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    onClick={() => setActiveMainView('settings')}
                      isActive={activeMainView === 'settings'}
                      className="w-full"
                    >
                      <SettingsIconLucide />
                      Settings
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      onClick={() => setActiveMainView('commsCenter')}
                      isActive={activeMainView === 'commsCenter'}
                      className="w-full"
                    >
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
                      <SidebarMenuButton
                        onClick={() => setActiveMainView('pluginOverview')}
                        isActive={activeMainView === 'pluginOverview'}
                        className="w-full"
                      >
                        <PlugZap />
                        Plugin Overview
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => setActiveMainView('pluginDatabaseConnector')}
                        isActive={activeMainView === 'pluginDatabaseConnector'}
                        className="w-full"
                      >
                        <Database />
                        Database Connector
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => setActiveMainView('pluginFacebook')}
                        isActive={activeMainView === 'pluginFacebook'}
                        className="w-full"
                      >
                        <Facebook />
                        Facebook Integration
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => setActiveMainView('pluginGmail')}
                        isActive={activeMainView === 'pluginGmail'}
                        className="w-full"
                      >
                        <Mail />
                        Gmail Integration
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => setActiveMainView('pluginDateTime')}
                        isActive={activeMainView === 'pluginDateTime'}
                        className="w-full"
                      >
                        <CalendarDays />
                        Date/Time Service
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => setActiveMainView('pluginWeather')}
                        isActive={activeMainView === 'pluginWeather'}
                        className="w-full"
                      >
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

          <SidebarInset className="flex-1 flex flex-col min-h-0">
            <main className="flex-1 flex flex-col min-h-0 p-4 md:p-6 overflow-y-auto">
              {activeMainView === 'chat' && <ModernChatInterface />}
              {activeMainView === 'dashboard' && <Dashboard />}
              {activeMainView === 'settings' && <SettingsDialogComponent />}
              {activeMainView === 'pluginDatabaseConnector' && <DatabaseConnectorPluginPage />}
              {activeMainView === 'pluginFacebook' && <FacebookPluginPage />}
              {activeMainView === 'pluginGmail' && <GmailPluginPage />}
              {activeMainView === 'pluginDateTime' && <DateTimePluginPage />}
              {activeMainView === 'pluginWeather' && <WeatherPluginPage />}
              {activeMainView === 'pluginOverview' && <PluginOverviewPage />}
              {activeMainView === 'commsCenter' && (
                <div className="space-y-6">
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
                      <p className="mt-1 text-sm text-muted-foreground">For example, Karen might save summaries of long conversations or important points she's learned here for your easy review.</p>
                    </div>
                  </div>
                </div>
              )}
            </main>
          </SidebarInset>
        </div>
      </div>
    </SidebarProvider>
  );
}
