"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

const Loading = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("animate-pulse", className)}
    {...props}
  >
    <div className="flex items-center justify-center space-x-2">
      <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
      <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
      <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.6s' }} />
    </div>
  </div>
));
Loading.displayName = "Loading";

export { Loading };