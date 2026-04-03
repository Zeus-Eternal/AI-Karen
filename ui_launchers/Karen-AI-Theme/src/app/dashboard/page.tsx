"use client";

import { useState } from 'react';
import { AuthWrapper } from '@/components/AuthWrapper';
import { Brain, MessageSquare, SettingsIcon as SettingsIconLucide, PanelLeft, Bell, SlidersHorizontal, LayoutGrid, Database, Facebook, BookOpenCheck, Mail, CalendarDays, CloudSun, PlugZap, Binary, Bot as BotIcon, ScrollText, Clock, Workflow, UserCircle } from 'lucide-react';
import SettingsDialogComponent from '@/components/settings/SettingsDialog';
import DataConnectorPluginPage from '@/components/plugins/DataConnectorPluginPage';
import FacebookPluginPage from '@/components/plugins/FacebookPluginPage';
import GmailPluginPage from '@/components/plugins/GmailPluginPage';
import DateTimePluginPage from '@/components/plugins/DateTimePluginPage';
import WeatherPluginPage from '@/components/plugins/WeatherPluginPage';
import PluginOverviewPage from '@/components/plugins/PluginOverviewPage';
import AutomationOverviewPage from '@/components/automation/AutomationOverviewPage';
import AgentsPage from '@/components/automation/AgentsPage';
import TasksPage from '@/components/automation/TasksPage';
import SequencesPage from '@/components/automation/SequencesPage';
import CronJobsPage from '@/components/automation/CronJobsPage';
import AccountPage from '@/components/account/AccountPage';
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
import ChatInterface, { SessionProvider } from '@/components/chat/ChatInterface';
import CommsCenterPage from '@/components/comms/CommsCenterPage';
import AdminSettingsPage from '@/components/admin/AdminSettingsPage';
import { Shield } from 'lucide-react';

type ActiveView = 'chat' | 'settings' | 'commsCenter' | 'pluginDataConnector' | 'pluginFacebook' | 'pluginGmail' | 'pluginDateTime' | 'pluginWeather' | 'pluginOverview' | 'automationOverview' | 'agents' | 'tasks' | 'sequences' | 'cronJobs' | 'account' | 'admin';

export default function DashboardPage() {
  const [activeMainView, setActiveMainView] = useState<ActiveView>('chat');

  return (
    <AuthWrapper>
      <SidebarProvider>
        <div className="flex flex-col h-screen w-full bg-background text-foreground">
        <header className="p-3 md:p-4 border-b border-border flex items-center justify-between sticky top-0 z-30 bg-background/90 backdrop-blur-md shadow-sm">
          <div className="flex items-center space-x-3">
            <AppSidebarTrigger className="mr-1 md:mr-2">
              {/* Default PanelLeft icon will be rendered by AppSidebarTrigger itself */}
            </AppSidebarTrigger>
            <Brain className="h-7 w-7 md:h-8 md:w-8 text-primary shrink-0" />
            <h1 className="text-xl md:text-2xl font-semibold tracking-tight">Karen AI</h1>
          </div>
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
                <SettingsDialogComponent inSheet={true} />
              </div>
            </SheetContent>
          </Sheet>
        </header>

        <div className="flex flex-1">
          <Sidebar
            variant="sidebar"
            collapsible="icon"
            className="border-r z-20"
          >
            <AppSidebarHeader>
              <h2 className="text-lg font-semibold tracking-tight px-2 py-1">Navigation</h2>
            </AppSidebarHeader>
            <Separator className="my-1" />
            <AppSidebarContent className="p-2 space-y-4">
              {/* --- ASSISTANT CATEGORY --- */}
              <SidebarGroup>
                <SidebarGroupLabel className="text-xs uppercase tracking-widest font-bold text-primary/70 mb-2 px-2">Assistant</SidebarGroupLabel>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      onClick={() => setActiveMainView('chat')}
                      isActive={activeMainView === 'chat'}
                      className="w-full"
                    >
                      <MessageSquare className="h-4 w-4" />
                      <span>Chat</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      onClick={() => setActiveMainView('commsCenter')}
                      isActive={activeMainView === 'commsCenter'}
                      className="w-full"
                    >
                      <Bell className="h-4 w-4" />
                      <span>Comms Center</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroup>

              <Separator className="bg-border/50 mx-2" />

              {/* --- PERSONAL CATEGORY --- */}
              <SidebarGroup>
                <SidebarGroupLabel className="text-xs uppercase tracking-widest font-bold text-primary/70 mb-2 px-2">Personal</SidebarGroupLabel>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      onClick={() => setActiveMainView('account')}
                      isActive={activeMainView === 'account'}
                      className="w-full"
                    >
                      <UserCircle className="h-4 w-4" />
                      <span>My Account</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      onClick={() => setActiveMainView('settings')}
                      isActive={activeMainView === 'settings'}
                      className="w-full"
                    >
                      <SettingsIconLucide className="h-4 w-4" />
                      <span>Application Settings</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroup>

              <Separator className="bg-border/50 mx-2" />

              {/* --- MODELS & RUNTIME CATEGORY --- */}
              <SidebarGroup>
                <SidebarGroupLabel className="text-xs uppercase tracking-widest font-bold text-primary/70 mb-2 px-2">Models & Runtime</SidebarGroupLabel>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton
                      onClick={() => setActiveMainView('admin')}
                      isActive={activeMainView === 'admin'}
                      className="w-full text-rose-500/80 hover:text-rose-500 transition-colors"
                    >
                      <Shield className="h-4 w-4" />
                      <span>Admin Settings</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>

                <div className="mt-4 px-2 space-y-4">
                  {/* Automation Hub Sub-group */}
                  <div>
                    <p className="text-[10px] uppercase font-semibold text-muted-foreground/60 mb-2 flex items-center">
                      <Binary className="mr-1.5 h-3 w-3"/> Automation Hub
                    </p>
                    <SidebarMenu>
                      <SidebarMenuItem>
                        <SidebarMenuButton
                          onClick={() => setActiveMainView('automationOverview')}
                          isActive={activeMainView === 'automationOverview'}
                          className="w-full h-8 text-xs"
                        >
                          <LayoutGrid className="h-3.5 w-3.5" />
                          Hub Overview
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                      <SidebarMenuItem>
                        <SidebarMenuButton
                          onClick={() => setActiveMainView('agents')}
                          isActive={activeMainView === 'agents'}
                          className="w-full h-8 text-xs"
                        >
                          <BotIcon className="h-3.5 w-3.5" />
                          Agents
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                      <SidebarMenuItem>
                        <SidebarMenuButton
                          onClick={() => setActiveMainView('tasks')}
                          isActive={activeMainView === 'tasks'}
                          className="w-full h-8 text-xs"
                        >
                          <ScrollText className="h-3.5 w-3.5" />
                          Tasks
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    </SidebarMenu>
                  </div>

                  {/* Plugins Sub-group */}
                  <div>
                    <p className="text-[10px] uppercase font-semibold text-muted-foreground/60 mb-2 flex items-center">
                      <PlugZap className="mr-1.5 h-3 w-3"/> Dynamic Plugins
                    </p>
                    <SidebarMenu>
                      <SidebarMenuItem>
                        <SidebarMenuButton
                          onClick={() => setActiveMainView('pluginOverview')}
                          isActive={activeMainView === 'pluginOverview'}
                          className="w-full h-8 text-xs"
                        >
                          <LayoutGrid className="h-3.5 w-3.5" />
                          Plugin Inventory
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    </SidebarMenu>
                  </div>
                </div>
              </SidebarGroup>
            </AppSidebarContent>
            <AppSidebarFooter className="p-4 border-t bg-muted/20">
              <div className="flex flex-col items-center gap-1">
                <Brain className="h-4 w-4 text-primary/50" />
                <p className="text-[10px] font-medium text-muted-foreground/60 uppercase tracking-tighter">Karen AI Unified Platform</p>
              </div>
            </AppSidebarFooter>
          </Sidebar>

          <SidebarInset className="flex-1 flex flex-col min-h-0">
            <main className="container flex-1 flex flex-col p-4 md:p-6 overflow-y-auto">
              {activeMainView === 'chat' && (
                <SessionProvider>
                  <ChatInterface />
                </SessionProvider>
              )}
              {activeMainView === 'settings' && <SettingsDialogComponent />}
              {activeMainView === 'pluginDataConnector' && <DataConnectorPluginPage />}
              {activeMainView === 'pluginFacebook' && <FacebookPluginPage />}
              {activeMainView === 'pluginGmail' && <GmailPluginPage />}
              {activeMainView === 'pluginDateTime' && <DateTimePluginPage />}
              {activeMainView === 'pluginWeather' && <WeatherPluginPage />}
              {activeMainView === 'pluginOverview' && <PluginOverviewPage />}
              {activeMainView === 'automationOverview' && <AutomationOverviewPage />}
              {activeMainView === 'agents' && <AgentsPage />}
              {activeMainView === 'tasks' && <TasksPage />}
              {activeMainView === 'sequences' && <SequencesPage />}
              {activeMainView === 'cronJobs' && <CronJobsPage />}
              {activeMainView === 'commsCenter' && <CommsCenterPage />}
              {activeMainView === 'account' && <AccountPage />}
              {activeMainView === 'admin' && <AdminSettingsPage />}
            </main>
          </SidebarInset>
        </div>
        </div>
      </SidebarProvider>
    </AuthWrapper>
  );
}
