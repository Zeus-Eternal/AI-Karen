/**
 * Loading component for chat page
 */

import * as React from 'react';
import { Skeleton } from "@/components/ui/skeleton";
import { Brain } from "lucide-react";

export default function ChatLoading() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header skeleton */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="flex items-center space-x-3">
            <Brain className="h-7 w-7 text-primary" />
            <h1 className="text-xl font-semibold">Karen AI</h1>
          </div>
        </div>
      </header>

      {/* Main content skeleton */}
      <div className="flex h-[calc(100vh-3.5rem)]">
        {/* Sidebar skeleton */}
        <div className="w-64 border-r bg-muted/10 p-4">
          <div className="space-y-4">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-6 w-1/2" />
            <div className="space-y-2 pt-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          </div>
        </div>

        {/* Chat area skeleton */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 p-4 space-y-4">
            <div className="space-y-2">
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-16 w-3/4" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-12 w-2/3" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-20 w-4/5" />
            </div>
          </div>
          
          {/* Input area skeleton */}
          <div className="border-t p-4">
            <Skeleton className="h-12 w-full" />
          </div>
        </div>
      </div>
    </div>
  );
}