"use client";

import React from 'react';

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar";
import ExtensionHeader from "./ExtensionHeader";
import SidebarNavigation from "./SidebarNavigation";
import { ExtensionProvider } from "@/extensions/ExtensionContext";
import { ErrorBoundary } from "@/components/ui/error-boundary";

export interface ExtensionSidebarProps {
  /**
   * Initial category displayed when the sidebar mounts.
   * Defaults to `"Plugins"`.
   */
  initialCategory?: "Plugins" | "Extensions";
}

function SidebarInner() {
  return (
    <>
      <SidebarRail />
      <Sidebar variant="sidebar" collapsible="icon" className="border-r z-20">
        <SidebarHeader className="p-2 sm:p-4 md:p-6">
          <ExtensionHeader />
        </SidebarHeader>
        <SidebarContent className="p-2 space-y-2 overflow-auto sm:p-4 md:p-6">
          <SidebarNavigation />
        </SidebarContent>
        <SidebarFooter className="p-2 border-t sm:p-4 md:p-6">
          <p className="text-xs text-muted-foreground text-center sm:text-sm md:text-base">
            Extension Manager
          </p>
        </SidebarFooter>
      </Sidebar>
    </>
  );
}

export default function ExtensionSidebar({
  initialCategory = "Plugins",
}: ExtensionSidebarProps) {
  return (
    <ErrorBoundary>
      <ExtensionProvider initialCategory={initialCategory}>
        <SidebarInner />
      </ExtensionProvider>
    </ErrorBoundary>
  );
}
