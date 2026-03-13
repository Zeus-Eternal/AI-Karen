import { cva } from "class-variance-authority";

export const cardEnhancedVariants = cva(
  [
    // Base styles using design tokens
    "rounded-lg border bg-card text-card-foreground",
    "transition-all duration-200 ease-out",
    "relative overflow-hidden",
  ],
  {
    variants: {
      variant: {
        default: [
          "shadow-sm hover:shadow-md",
          "border-border",
        ],
        elevated: [
          "shadow-md hover:shadow-lg",
          "border-border/50",
        ],
        outlined: [
          "border-2 border-dashed border-border",
          "bg-background hover:bg-card",
          "shadow-none hover:shadow-sm",
        ],
        glass: [
          "bg-card/80 backdrop-blur-sm",
          "border-border/50 hover:border-border",
          "shadow-sm hover:shadow-md",
        ],
        gradient: [
          "bg-gradient-to-br from-card to-card/80",
          "border-border/30",
          "shadow-md hover:shadow-lg",
        ],
      },
      interactive: {
        true: [
          "cursor-pointer",
          "hover:scale-[1.01] active:scale-[0.99]",
          "focus-visible:outline-none focus-visible:ring-2",
          "focus-visible:ring-ring focus-visible:ring-offset-2",
          "focus-visible:ring-offset-background",
        ],
        false: "",
      },
      padding: {
        none: "p-0",
        sm: "p-4",
        default: "p-6",
        lg: "p-8",
      },
    },
    defaultVariants: {
      variant: "default",
      interactive: false,
      padding: "default",
    },
  }
);

