"use client";
import * as React from 'react';
import { useMemo } from "react";
import Link from "next/link";
import { useRouter, useSearchParams, usePathname } from "next/navigation";

import SettingsDialogComponent from "@/components/settings/SettingsDialog";
import { GridContainer } from "@/components/ui/layout/grid-container";
import { FlexContainer } from "@/components/ui/layout/flex-container";
import { Separator } from "@/components/ui/separator";
import NotificationsSection from "@/components/sidebar/NotificationsSection";
import Dashboard from "@/components/dashboard/Dashboard";
import { webUIConfig } from "@/lib/config";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AuthenticatedHeader } from "@/components/layout/AuthenticatedHeader";
import dynamic from "next/dynamic";
import { TextSelectionProvider } from "@/components/ui/text-selection-provider";
import { Bell, Brain, LayoutGrid, MessageSquare, Settings as SettingsIconLucide, SlidersHorizontal } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";

import { SidebarProvider } from "@/components/ui/sidebar-context";
import {
  Sidebar,
  SidebarTrigger,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarInset,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar";









const ExtensionSidebar = dynamic(
  () => import("@/components/extensions/ExtensionSidebar")
);

type ActiveView = "settings" | "dashboard" | "commsCenter";

export default function HomePage() {
  return (
    <TextSelectionProvider enableGlobalSelection={true} enableKeyboardShortcuts={true}>
      <ProtectedRoute>
        <AuthenticatedHomePage />
      </ProtectedRoute>
    </TextSelectionProvider>
  );
}

function AuthenticatedHomePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const parseView = (
    sp: ReturnType<typeof useSearchParams> | null
  ): ActiveView => {
    const v = sp?.get("view") ?? "";
    const allowed: ActiveView[] = ["settings", "dashboard", "commsCenter"];
    return (allowed as readonly string[]).includes(v)
      ? (v as ActiveView)
      : "dashboard";
  };

  const activeMainView = useMemo(
    () => parseView(searchParams as unknown),
    [searchParams]
  );

  const navigate = (view: ActiveView) => {
    const params = new URLSearchParams(
      searchParams ? searchParams.toString() : ""
    );
    params.set("view", view);
    router.push(`/?${params.toString()}`);
  };

  return (
    <SidebarProvider>
      <GridContainer className="app-grid" columns="auto 1fr" rows="auto 1fr">
        <header className="app-header header-enhanced" role="banner">
          <FlexContainer
            className="container-fluid py-3 md:py-4"
            justify="between"
            align="center"
          >
            <FlexContainer className="space-x-3" align="center">
              <SidebarTrigger className="mr-1 md:mr-2 smooth-transition interactive">
                <span className="sr-only">Toggle sidebar</span>
              </SidebarTrigger>
              <Brain className="h-7 w-7 md:h-8 md:w-8 text-primary shrink-0 smooth-transform" />
              <h1 className="text-xl md:text-2xl font-semibold tracking-tight bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent">
                Karen Operations Center
              </h1>
            </FlexContainer>
            <FlexContainer className="gap-2" align="center">
                <Sheet>
                  <SheetTrigger asChild>
                    <button
                      type="button"
                      aria-label="Open settings"
                      className="focus-ring smooth-transition inline-flex h-10 w-10 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent"
                    >
                      <SlidersHorizontal className="h-5 w-5" />
                      <span className="sr-only">Open settings</span>
                    </button>
                  </SheetTrigger>
                <SheetContent
                  side="right"
                  className="w-[90vw] max-w-sm sm:w-[480px] p-0 flex flex-col modern-card-glass"
                >
                  <SheetHeader className="p-4 border-b">
                    <SheetTitle>Settings</SheetTitle>
                  </SheetHeader>
                  <div className="flex-1 overflow-y-auto p-4 scroll-smooth">
                    <SettingsDialogComponent />
                  </div>
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
                <h2
                  id="home-primary-nav-title"
                  className="text-lg font-semibold tracking-tight"
                >
                  Mission Control
                </h2>
              </SidebarHeader>
              <Separator className="my-1" />
              <SidebarContent className="p-2 scroll-smooth">
                <nav aria-labelledby="home-primary-nav-title">
                  <SidebarMenu>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        asChild
                        className="w-full"
                        isActive={pathname === "/chat"}
                      >
                        <Link href="/chat" className="flex items-center gap-2">
                          <MessageSquare className="h-5 w-5" />
                          <span className="font-medium">Chat</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => navigate("dashboard")}
                        isActive={activeMainView === "dashboard"}
                        className="w-full"
                      >
                        <div className="flex items-center gap-2">
                          <LayoutGrid className="h-5 w-5" />
                          <span className="font-medium">Dashboard</span>
                        </div>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => navigate("settings")}
                        isActive={activeMainView === "settings"}
                        className="w-full"
                      >
                        <div className="flex items-center gap-2">
                          <SettingsIconLucide className="h-5 w-5" />
                          <span className="font-medium">Settings</span>
                        </div>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    <SidebarMenuItem>
                      <SidebarMenuButton
                        onClick={() => navigate("commsCenter")}
                        isActive={activeMainView === "commsCenter"}
                        className="w-full"
                      >
                        <div className="flex items-center gap-2">
                          <Bell className="h-5 w-5" />
                          <span className="font-medium">Communications</span>
                        </div>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  </SidebarMenu>
                </nav>
              </SidebarContent>
              <SidebarFooter className="p-2 border-t">
                <p className="text-xs text-muted-foreground text-center">
                  Karen AI • Core Operations Suite
                </p>
              </SidebarFooter>
            </Sidebar>
          )}

          <SidebarInset className="app-main">
            <FlexContainer direction="column" className="space-y-fluid">
              {activeMainView === "dashboard" && <Dashboard />}
              {activeMainView === "settings" && <SettingsDialogComponent />}
              {activeMainView === "commsCenter" && (
                <FlexContainer direction="column" className="space-y-fluid">
                  <div className="modern-card">
                    <div className="modern-card-header">
                      <h2 className="text-2xl font-semibold tracking-tight">
                        Operational Updates
                      </h2>
                      <p className="text-sm text-muted-foreground mt-2">
                        Mission-critical alerts and communications from Karen.
                      </p>
                    </div>
                    <div className="modern-card-content">
                      <NotificationsSection />
                    </div>
                  </div>
                  <div className="modern-card">
                    <div className="modern-card-header">
                      <h3 className="text-lg font-semibold">
                        My Notes (Conceptual)
                      </h3>
                    </div>
                    <div className="modern-card-content min-h-[150px]">
                      <p className="text-sm text-muted-foreground">
                        This space is reserved for future features.
                      </p>
                      <p className="mt-2 text-sm text-muted-foreground">
                        conversations or important points she's learned here for
                        your easy review.
                      </p>
                    </div>
                  </div>
                </FlexContainer>
              )}
            </FlexContainer>
          </SidebarInset>
        </div>
      </GridContainer>
    </SidebarProvider>
  );
}
