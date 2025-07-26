"use client";

import React from "react";
import {
  Sidebar,
  SidebarProvider,
  SidebarTrigger,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarRail,
} from "@/components/ui/sidebar";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import ExtensionBreadcrumbs from "./ExtensionBreadcrumbs";
import ExtensionStats from "./ExtensionStats";
import { useExtensionContext, ExtensionProvider } from "@/extensions";
import { ErrorBoundary } from "@/components/ui/error-boundary";

export interface ExtensionSidebarProps {
  /**
   * Initial category displayed when the sidebar mounts.
   * Defaults to `"Plugins"`.
   */
  initialCategory?: "Plugins" | "Extensions";
}

function SidebarInner() {
  const {
    state: { currentCategory, level },
    dispatch,
  } = useExtensionContext();

  return (
    <>
      <SidebarRail />
      <Sidebar variant="sidebar" collapsible="icon" className="border-r z-20">
        <SidebarHeader className="space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Extension Manager</h2>
            <SidebarTrigger />
          </div>
        <Tabs
          value={currentCategory}
          onValueChange={(val) =>
            dispatch({ type: "SET_CATEGORY", category: val as any })
          }
          className="w-full"
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="Plugins">Plugins</TabsTrigger>
            <TabsTrigger value="Extensions">Extensions</TabsTrigger>
          </TabsList>
        </Tabs>
        {level > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="px-1 gap-1 h-6"
            onClick={() => dispatch({ type: "GO_BACK" })}
          >
            <ArrowLeft className="h-3 w-3" /> Back
          </Button>
        )}
        <ExtensionBreadcrumbs />
        <ExtensionStats />
      </SidebarHeader>
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
