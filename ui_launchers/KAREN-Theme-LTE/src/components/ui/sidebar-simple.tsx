"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface SimpleSidebarProps {
  children: React.ReactNode;
  className?: string;
}

export function SimpleSidebar({ children, className }: SimpleSidebarProps) {
  return (
    <div className={cn("w-64 bg-card border-r border-border p-4", className)}>
      <div className="space-y-4">
        <div className="text-lg font-semibold">Navigation</div>
        <div className="space-y-2">
          <div className="p-2 hover:bg-accent rounded cursor-pointer">Chat</div>
          <div className="p-2 hover:bg-accent rounded cursor-pointer">Settings</div>
          <div className="p-2 hover:bg-accent rounded cursor-pointer">Performance</div>
          <div className="p-2 hover:bg-accent rounded cursor-pointer">Memory</div>
          <div className="p-2 hover:bg-accent rounded cursor-pointer">Files</div>
          <div className="p-2 hover:bg-accent rounded cursor-pointer">Analytics</div>
        </div>
      </div>
      <div className="mt-6">
        {children}
      </div>
    </div>
  );
}