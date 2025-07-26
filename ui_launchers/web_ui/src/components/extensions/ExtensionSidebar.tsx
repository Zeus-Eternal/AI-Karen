"use client";

import React from "react";
import {
  Sidebar,
  SidebarProvider,
  SidebarContent,
  SidebarFooter,
  SidebarRail,
} from "@/components/ui/sidebar";
import ExtensionHeader from "./ExtensionHeader";
import { ExtensionProvider } from "@/extensions";
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
        <ExtensionHeader />
      <SidebarContent className="p-2 space-y-2">
        {/* Navigation items will be added in future tasks */}
      </SidebarContent>
      <SidebarFooter className="p-2 border-t">
        <p className="text-xs text-muted-foreground text-center">
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
        <SidebarProvider>
          <SidebarInner />
        </SidebarProvider>
      </ExtensionProvider>
    </ErrorBoundary>
  );
}
