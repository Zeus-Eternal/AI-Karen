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
import InputBox from "@/components/chat/InputBox";
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
      <div className="flex flex-col h-screen bg-background text-foreground">
        <header className="p-3 md:p-4 border-b border-border flex items-center justify-between sticky top-0 z-30 bg-background/90 backdrop-blur-md shadow-sm">
          <div className="flex items-center space-x-3">
            <AppSidebarTrigger className="mr-1 md:mr-2" />
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
                <div className="flex-1 overflow-y-auto" />
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

          <SidebarInset className="flex-1 flex flex-col min-h-0">
            <MetaBar />
            <main className="flex-1 flex flex-col min-h-0 p-4 md:p-6">
              <div className="mx-auto w-full max-w-screen-lg xl:max-w-screen-xl px-4 sm:px-6">
              <ChatInterface
                className="flex-1"
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
            </main>
          </SidebarInset>
        </div>
      </div>
    </SidebarProvider>
  );
}
