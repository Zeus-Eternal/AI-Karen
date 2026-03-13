"use client";

import React from "react";
import {
  SidebarHeader,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { PanelLeft } from "lucide-react";

export default function ExtensionHeader() {
  return (
    <SidebarHeader className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-purple-600/20">
            <PanelLeft className="h-5 w-5 text-purple-400" />
          </div>
          <h2 className="text-lg font-semibold text-white">Karen AI</h2>
        </div>
        <SidebarTrigger />
      </div>
    </SidebarHeader>
  );
}
