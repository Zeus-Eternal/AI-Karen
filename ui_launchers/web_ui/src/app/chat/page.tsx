"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import dynamic from "next/dynamic";
import {
  Brain,
  MessageSquare,
  LayoutGrid,
  SettingsIcon as SettingsIconLucide,
  Bell,
  SlidersHorizontal,
  PlugZap,
} from "lucide-react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AuthenticatedHeader } from "@/components/layout/AuthenticatedHeader";
import { MetaBar } from "@/components/chat";

import { ChatInterface } from "@/components/chat";
import { webUIConfig } from "@/lib/config";
import { Button } from "@/components/ui/button";
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
import { Separator } from "@/components/ui/separator";

const ExtensionSidebar = dynamic(() => import("@/components/extensions/ExtensionSidebar"));

export default function ChatPage() {
  return (
    // Temporarily bypass ProtectedRoute for testing
    // <ProtectedRoute>
      <ChatView />
    // </ProtectedRoute>
  );
}

function ChatView() {
  const pathname = usePathname();

  return (
    <SidebarProvider>
      <div className="chat-grid">
        <header className="chat-header header-enhanced">
          <div className="container-fluid flex-between">
            <div className="flex-start space-x-3">
              <AppSidebarTrigger className="mr-1 md:mr-2 smooth-transition interactive" />
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
                  <div className="flex-1 overflow-y-auto p-4 scroll-smooth" />
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
                    <SidebarMenuButton asChild isActive={pathname === "/chat"} className="w-full">
                      <Link href="/chat">
                        <MessageSquare />
                        Chat
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild className="w-full">
                      <Link href="/?view=dashboard">
                        <LayoutGrid />
                        Dashboard
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild className="w-full">
                      <Link href="/?view=settings">
                        <SettingsIconLucide />
                        Settings
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild className="w-full">
                      <Link href="/?view=commsCenter">
                        <Bell />
                        Comms Center
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
                <Separator className="my-2" />
                <SidebarGroup>
                  <SidebarGroupLabel className="text-sm">Plugins</SidebarGroupLabel>
                  <SidebarMenu>
                    <SidebarMenuItem>
                      <SidebarMenuButton asChild className="w-full">
                        <Link href="/?view=pluginOverview">
                          <PlugZap />
                          Plugin Overview
                        </Link>
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

          <SidebarInset className="flex flex-col min-h-0">
            <MetaBar />
            <div className="chat-messages">
              <div className="container max-w-screen-xl">
                <ChatInterface
                  className="h-full smooth-transition"
                  useCopilotKit={true}
                  enableCodeAssistance={true}
                  enableContextualHelp={true}
                  enableDocGeneration={true}
                  showTabs={true}
                  showSettings={true}
                  enableVoiceInput={false}
                  enableFileUpload={true}
                  enableAnalytics={true}
                  enableExport={true}
                  enableSharing={false}
                />
              </div>
            </div>
          </SidebarInset>
        </div>
      </div>
    </SidebarProvider>
  );
}
