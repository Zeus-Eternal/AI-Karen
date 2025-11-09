"use client";
import React from 'react';
import Link from "next/link";
import { usePathname } from "next/navigation";
import dynamic from "next/dynamic";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AuthenticatedHeader } from "@/components/layout/AuthenticatedHeader";
import { MetaBar } from "@/components/chat";
import { ChatInterface } from "@/components/chat";
import { webUIConfig } from "@/lib/config";
import { GridContainer } from "@/components/ui/layout/grid-container";
import { FlexContainer } from "@/components/ui/layout/flex-container";
import { Separator } from "@/components/ui/separator";
import { Bell, Brain, LayoutGrid, MessageSquare, PlugZap, Settings as SettingsIconLucide, SlidersHorizontal } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";

import {
  SidebarProvider,
  Sidebar,
  SidebarTrigger,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarInset,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarGroup,
  SidebarGroupLabel,
} from "@/components/ui/sidebar";


const ExtensionSidebar = dynamic(() => import("@/components/extensions/ExtensionSidebar"));

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <ChatView />
    </ProtectedRoute>
  );
}

function ChatView() {
  const pathname = usePathname();

  return (
    <SidebarProvider>
      <GridContainer className="chat-grid" rows="auto 1fr auto">
        <header className="chat-header header-enhanced" role="banner">
          <FlexContainer className="container-fluid" justify="between" align="center">
            <FlexContainer className="space-x-3" align="center">
              <SidebarTrigger className="mr-1 md:mr-2 smooth-transition interactive">
                <span className="sr-only">Toggle sidebar</span>
              </SidebarTrigger>
              <Brain className="h-7 w-7 md:h-8 md:w-8 text-primary shrink-0 smooth-transform" />
              <h1 className="text-xl md:text-2xl font-semibold tracking-tight bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent">
              </h1>
            </FlexContainer>
            <FlexContainer className="gap-2" align="center">
                <Sheet>
                  <SheetTrigger asChild>
                    <button
                      type="button"
                      aria-label="Open chat settings"
                      className="focus-ring smooth-transition inline-flex h-10 w-10 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent"
                    >
                      <SlidersHorizontal className="h-5 w-5" />
                      <span className="sr-only">Open settings</span>
                    </button>
                  </SheetTrigger>
                <SheetContent side="right" className="w-[90vw] max-w-sm sm:w-[480px] p-0 flex flex-col modern-card-glass">
                  <SheetHeader className="p-4 border-b">
                    <SheetTitle>Settings</SheetTitle>
                  </SheetHeader>
                  <div className="flex-1 overflow-y-auto p-4 scroll-smooth" />
                </SheetContent>
              </Sheet>
              <AuthenticatedHeader />
            </FlexContainer>
          </FlexContainer>
        </header>

        <div className="flex flex-1 min-h-0">
          {webUIConfig.enableExtensions ? (
            <ExtensionSidebar />
          ) : (
            <Sidebar
              variant="sidebar"
              collapsible="icon"
              className="border-r z-20 sidebar-enhanced"
              aria-label="Main navigation"
            >
              <SidebarHeader className="p-4">
                <h2 id="chat-primary-nav-title" className="text-lg font-semibold tracking-tight">
                </h2>
              </SidebarHeader>
              <Separator className="my-1" />
              <SidebarContent className="p-2 scroll-smooth">
                <nav aria-labelledby="chat-primary-nav-title">
                  <SidebarMenu>
                    <SidebarMenuItem>
                      <SidebarMenuButton asChild isActive={pathname === "/chat"} className="w-full">
                        <Link href="/chat">
                          <MessageSquare />
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton asChild className="w-full">
                        <Link href="/?view=dashboard">
                          <LayoutGrid />
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton asChild className="w-full">
                        <Link href="/?view=settings">
                          <SettingsIconLucide />
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton asChild className="w-full">
                        <Link href="/?view=commsCenter">
                          <Bell />
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  </SidebarMenu>
                </nav>
                <Separator className="my-2" />
                <SidebarGroup>
                  <SidebarGroupLabel asChild className="text-sm font-medium">
                    <h3 id="chat-plugins-nav-title">Plugins</h3>
                  </SidebarGroupLabel>
                  <nav aria-labelledby="chat-plugins-nav-title">
                    <SidebarMenu>
                      <SidebarMenuItem>
                        <SidebarMenuButton asChild className="w-full">
                          <Link href="/?view=pluginOverview">
                            <PlugZap />
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    </SidebarMenu>
                  </nav>
                </SidebarGroup>
              </SidebarContent>
              <SidebarFooter className="p-2 border-t">
                <p className="text-xs text-muted-foreground text-center">Karen AI Menu</p>
              </SidebarFooter>
            </Sidebar>
          )}

          <SidebarInset className="chat-surface min-h-0">
            <MetaBar />
            <div id="chat-messages" className="chat-messages">
              <div className="container max-w-screen-xl">
                <div className="chat-panel">
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
            </div>
          </SidebarInset>
        </div>
      </GridContainer>
    </SidebarProvider>
  );
}
