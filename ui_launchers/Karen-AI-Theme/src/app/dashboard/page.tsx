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
import ChatInterface from '@/components/chat/ChatInterface';
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
                <SidebarMenuItem>
                   <SidebarMenuButton
                    onClick={() => setActiveMainView('admin')}
                    isActive={activeMainView === 'admin'}
                    className="w-full text-rose-500/80 hover:text-rose-500 transition-colors"
                  >
                    <Shield />
                    Admin Settings
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>

              <Separator className="my-2" />

              <SidebarGroup>
                <SidebarGroupLabel className="text-sm flex items-center"><Binary className="mr-2 h-4 w-4"/>Automation Hub</SidebarGroupLabel>
                <SidebarMenu>
                  <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => setActiveMainView('automationOverview')}
                        isActive={activeMainView === 'automationOverview'}
                        className="w-full"
                      >
                        <LayoutGrid />
                        Hub Overview
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => setActiveMainView('agents')}
                        isActive={activeMainView === 'agents'}
                        className="w-full"
                      >
                        <BotIcon />
                        Agents
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => setActiveMainView('tasks')}
                        isActive={activeMainView === 'tasks'}
                        className="w-full"
                      >
                        <ScrollText />
                        Tasks
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => setActiveMainView('sequences')}
                        isActive={activeMainView === 'sequences'}
                        className="w-full"
                      >
                        <Workflow />
                        Jobs
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => setActiveMainView('cronJobs')}
                        isActive={activeMainView === 'cronJobs'}
                        className="w-full"
                      >
                        <Clock />
                        Cron Jobs
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroup>

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
                      onClick={() => setActiveMainView('pluginDataConnector')}
                      isActive={activeMainView === 'pluginDataConnector'}
                      className="w-full"
                    >
                      <Database />
                      Data Connector
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

              <Separator className="my-2" />

              <SidebarMenu>
                <SidebarMenuItem>
                   <SidebarMenuButton
                    onClick={() => setActiveMainView('account')}
                    isActive={activeMainView === 'account'}
                    className="w-full"
                  >
                    <UserCircle />
                    My Account
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </AppSidebarContent>
            <AppSidebarFooter className="p-2 border-t">
              <p className="text-xs text-muted-foreground text-center">Karen AI Menu</p>
            </AppSidebarFooter>
          </Sidebar>

          <SidebarInset className="flex-1 flex flex-col min-h-0">
            <main className="container flex-1 flex flex-col p-4 md:p-6 overflow-y-auto">
              {activeMainView === 'chat' && <ChatInterface />}
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
