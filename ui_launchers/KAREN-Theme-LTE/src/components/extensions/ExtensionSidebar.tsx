"use client";

import {
  Sidebar,
  SidebarProvider,
  SidebarContent,
  SidebarFooter,
  SidebarRail,
} from "@/components/ui/sidebar";
import ExtensionHeader from "./ExtensionHeader";
import SidebarNavigation from "./SidebarNavigation";

export interface ExtensionSidebarProps {
  /**
   * Initial category displayed when sidebar mounts.
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
        <SidebarContent className="p-2 space-y-2 overflow-auto">
          <SidebarNavigation />
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

export default function ExtensionSidebar(props: ExtensionSidebarProps) {
  void props.initialCategory;

  return (
    <SidebarProvider defaultOpen={true}>
      <SidebarInner />
    </SidebarProvider>
  );
}
