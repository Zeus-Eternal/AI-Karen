import * as React from "react";
import { cn } from "@/lib/utils";

interface ResponsiveCardGridProps extends React.HTMLAttributes<HTMLDivElement> {}

const ResponsiveCardGrid = React.forwardRef<HTMLDivElement, ResponsiveCardGridProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("grid gap-4 sm:grid-cols-2 lg:grid-cols-3", className)}
      {...props}
    />
  )
);
ResponsiveCardGrid.displayName = "ResponsiveCardGrid";

export default ResponsiveCardGrid;
