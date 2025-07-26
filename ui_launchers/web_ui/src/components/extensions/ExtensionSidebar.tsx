"use client";

import React from "react";
import {
  Sidebar,
  SidebarProvider,
  SidebarTrigger,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
} from "@/components/ui/sidebar";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import ExtensionBreadcrumbs from "./ExtensionBreadcrumbs";
import { useExtensionContext, ExtensionProvider } from "@/extensions";

function SidebarInner() {
  const {
    state: { currentCategory, level },
    dispatch,
  } = useExtensionContext();

  return (
    <Sidebar variant="sidebar" collapsible="icon" className="border-r z-20">
      <SidebarHeader className="space-y-2">
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
  );
}

export default function ExtensionSidebar() {
  return (
    <ExtensionProvider>
      <SidebarProvider>
        <SidebarInner />
      </SidebarProvider>
    </ExtensionProvider>
  );
}
