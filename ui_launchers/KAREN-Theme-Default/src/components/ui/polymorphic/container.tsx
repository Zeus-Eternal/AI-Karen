"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

// Enhanced type definitions
export type ContainerVariant = 
  | "default" 
  | "fluid" 
  | "constrained" 
  | "centered" 
  | "padded" 
  | "hero" 
  | "section" 
  | "card" 
  | "sidebar" 
  | "modal";

export type ContainerSize = 
  | "xs" 
  | "sm" 
  | "md" 
  | "lg" 
  | "xl" 
  | "2xl" 
  | "3xl" 
  | "4xl" 
  | "5xl" 
  | "6xl" 
  | "7xl" 
  | "full" 
  | "screen" 
  | "custom";

export type ContainerDisplay = 
  | "block" 
  | "flex" 
  | "grid" 
  | "inline" 
  | "inline-flex" 
  | "inline-grid" 
  | "none";

export type ContainerPosition = 
  | "static" 
  | "relative" 
  | "absolute" 
  | "fixed" 
  | "sticky";

export type ContainerOverflow = 
  | "auto" 
  | "hidden" 
  | "visible" 
  | "scroll" 
  | "clip";

export type ContainerShadow = 
  | "none" 
  | "sm" 
  | "md" 
  | "lg" 
  | "xl" 
  | "2xl" 
  | "inner" 
  | "outline";

export type ContainerBorder = 
  | "none" 
  | "thin" 
  | "medium" 
  | "thick" 
  | "custom";

export type ContainerBackground = 
  | "transparent" 
  | "default" 
  | "muted" 
  | "primary" 
  | "secondary" 
  | "accent" 
  | "destructive" 
  | "warning" 
  | "success" 
  | "custom";

export interface ContainerProps extends React.HTMLAttributes<HTMLElement> {
  as?: React.ElementType;
  variant?: ContainerVariant;
  size?: ContainerSize;
  customSize?: string | number; // For custom width/height
  customMaxSize?: string | number; // For custom max-width/height
  display?: ContainerDisplay;
  responsive?: boolean;
  position?: ContainerPosition;
  overflow?: ContainerOverflow;
  shadow?: ContainerShadow;
  border?: ContainerBorder;
  background?: ContainerBackground;
  customBackground?: string; // For custom background colors
  rounded?: "none" | "sm" | "md" | "lg" | "xl" | "2xl" | "3xl" | "full" | "custom";
  customRounded?: string; // For custom border radius
  zIndex?: number | "auto";
  opacity?: number;
  blur?: "none" | "sm" | "md" | "lg" | "xl" | "2xl" | "custom";
  customBlur?: string; // For custom blur
  animation?: "none" | "fade" | "slide" | "scale" | "bounce" | "custom";
  animationDelay?: number;
  animationDuration?: number;
  hover?: {
    scale?: number;
    shadow?: ContainerShadow;
    background?: ContainerBackground;
    customBackground?: string;
  };
  focus?: {
    shadow?: ContainerShadow;
    border?: ContainerBorder;
    outline?: boolean;
  };
  breakpoints?: {
    sm?: Partial<ContainerProps>;
    md?: Partial<ContainerProps>;
    lg?: Partial<ContainerProps>;
    xl?: Partial<ContainerProps>;
    "2xl"?: Partial<ContainerProps>;
  };
  children: React.ReactNode;
}

// Utility function to generate responsive classes
const generateResponsiveClasses = (breakpoints: ContainerProps['breakpoints']) => {
  if (!breakpoints) return {};

  const responsiveClasses: Record<string, boolean> = {};

  Object.entries(breakpoints).forEach(([breakpoint, config]) => {
    if (config.size) {
      responsiveClasses[`${breakpoint}:max-w-${config.size}`] = true;
    }
    if (config.display) {
      responsiveClasses[`${breakpoint}:${config.display}`] = true;
    }
    // Add more responsive properties as needed
  });

  return responsiveClasses;
};

// Polymorphic Container Component with Enhanced Features
const Container = React.forwardRef<HTMLElement, ContainerProps>(
  (
    {
      as: Component = "div",
      className,
      variant = "default",
      size = "full",
      customSize,
      customMaxSize,
      display = "block",
      responsive = true,
      position = "static",
      overflow = "visible",
      shadow = "none",
      border = "none",
      background = "transparent",
      customBackground,
      rounded = "none",
      customRounded,
      zIndex = "auto",
      opacity = 1,
      blur = "none",
      customBlur,
      animation = "none",
      animationDelay = 0,
      animationDuration = 300,
      hover,
      focus,
      breakpoints,
      children,
      style,
      ...props
    },
    ref
  ) => {
    // Generate inline styles for custom properties
    const customStyles: React.CSSProperties = {
      ...style,
      ...(customSize && { width: customSize, height: customSize }),
      ...(customMaxSize && { maxWidth: customMaxSize, maxHeight: customMaxSize }),
      ...(customBackground && { backgroundColor: customBackground }),
      ...(customRounded && { borderRadius: customRounded }),
      ...(customBlur && { filter: `blur(${customBlur})` }),
      ...(zIndex !== "auto" && { zIndex }),
      ...(opacity !== 1 && { opacity }),
      ...(animationDelay > 0 && { animationDelay: `${animationDelay}ms` }),
      ...(animationDuration !== 300 && { animationDuration: `${animationDuration}ms` }),
    };

    return (
      <Component
        ref={ref}
        className={cn(
          // Base styles
          "transition-all duration-200 ease-in-out",

          // Display styles
          {
            "block": display === "block",
            "flex": display === "flex",
            "grid": display === "grid",
            "inline": display === "inline",
            "inline-flex": display === "inline-flex",
            "inline-grid": display === "inline-grid",
            "hidden": display === "none",
          },

          // Position styles
          {
            "static": position === "static",
            "relative": position === "relative",
            "absolute": position === "absolute",
            "fixed": position === "fixed",
            "sticky": position === "sticky",
          },

          // Overflow styles
          {
            "overflow-auto": overflow === "auto",
            "overflow-hidden": overflow === "hidden",
            "overflow-visible": overflow === "visible",
            "overflow-scroll": overflow === "scroll",
            "overflow-clip": overflow === "clip",
          },

          // Shadow styles
          {
            "shadow-none": shadow === "none",
            "shadow-sm": shadow === "sm",
            "shadow": shadow === "md",
            "shadow-md": shadow === "lg",
            "shadow-lg": shadow === "xl",
            "shadow-xl": shadow === "2xl",
            "shadow-inner": shadow === "inner",
            "shadow-outline": shadow === "outline",
          },

          // Border styles
          {
            "border-0": border === "none",
            "border": border === "thin",
            "border-2": border === "medium",
            "border-4": border === "thick",
          },

          // Background styles
          {
            "bg-transparent": background === "transparent",
            "bg-background": background === "default",
            "bg-muted": background === "muted",
            "bg-primary": background === "primary",
            "bg-secondary": background === "secondary",
            "bg-accent": background === "accent",
            "bg-destructive": background === "destructive",
            "bg-warning": background === "warning",
            "bg-success": background === "success",
          },

          // Border radius styles
          {
            "rounded-none": rounded === "none",
            "rounded-sm": rounded === "sm",
            "rounded": rounded === "md",
            "rounded-md": rounded === "lg",
            "rounded-lg": rounded === "xl",
            "rounded-xl": rounded === "2xl",
            "rounded-2xl": rounded === "3xl",
            "rounded-full": rounded === "full",
          },

          // Blur styles
          {
            "backdrop-blur-none": blur === "none",
            "backdrop-blur-sm": blur === "sm",
            "backdrop-blur": blur === "md",
            "backdrop-blur-md": blur === "lg",
            "backdrop-blur-lg": blur === "xl",
            "backdrop-blur-xl": blur === "2xl",
          },

          // Animation styles
          {
            "animate-fade-in": animation === "fade",
            "animate-slide-in": animation === "slide",
            "animate-scale-in": animation === "scale",
            "animate-bounce": animation === "bounce",
          },

          // Variant styles
          {
            // Default variant
            "mx-auto": variant === "default" || variant === "constrained" || variant === "centered",
            "w-full": variant === "default" || variant === "fluid" || variant === "constrained",
            "px-4 sm:px-6 lg:px-8": variant === "padded" || variant === "default" || variant === "section",
            "flex items-center justify-center": variant === "centered",

            // Hero variant
            "min-h-screen flex items-center justify-center": variant === "hero",
            "py-20": variant === "hero",

            // Section variant
            "py-12 lg:py-24": variant === "section",

            // Card variant
            "bg-card text-card-foreground rounded-lg border shadow-sm p-6": variant === "card",

            // Sidebar variant
            "h-screen w-64 fixed left-0 top-0 border-r bg-background": variant === "sidebar",

            // Modal variant
            "fixed inset-0 z-50 bg-background/80 backdrop-blur-sm": variant === "modal",
          },

          // Size styles (max-width constraints)
          responsive && {
            "max-w-xs": size === "xs",
            "max-w-sm": size === "sm",
            "max-w-md": size === "md",
            "max-w-lg": size === "lg",
            "max-w-xl": size === "xl",
            "max-w-2xl": size === "2xl",
            "max-w-3xl": size === "3xl",
            "max-w-4xl": size === "4xl",
            "max-w-5xl": size === "5xl",
            "max-w-6xl": size === "6xl",
            "max-w-7xl": size === "7xl",
            "max-w-none": size === "full",
            "max-w-screen": size === "screen",
          },

          // Non-responsive size styles
          !responsive && {
            "w-80": size === "xs",
            "w-96": size === "sm",
            "w-[32rem]": size === "md",
            "w-[40rem]": size === "lg",
            "w-[48rem]": size === "xl",
            "w-[56rem]": size === "2xl",
            "w-[64rem]": size === "3xl",
            "w-[72rem]": size === "4xl",
            "w-[80rem]": size === "5xl",
            "w-[88rem]": size === "6xl",
            "w-[96rem]": size === "7xl",
            "w-full": size === "full",
            "w-screen": size === "screen",
          },

          // Hover effects
          hover && cn(
            "transition-all duration-200 ease-in-out",
            {
              "hover:scale-105": hover.scale === 1.05,
              "hover:scale-110": hover.scale === 1.1,
              "hover:scale-125": hover.scale === 1.25,
              "hover:shadow-lg": hover.shadow === "lg",
              "hover:shadow-xl": hover.shadow === "xl",
              "hover:bg-primary": hover.background === "primary",
              "hover:bg-secondary": hover.background === "secondary",
            },
            hover.customBackground && `hover:${hover.customBackground}`
          ),

          // Focus effects
          focus && cn(
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
            {
              "focus:shadow-outline": focus.outline,
              "focus:border-2": focus.border === "medium",
            }
          ),

          // Responsive breakpoints
          ...Object.entries(generateResponsiveClasses(breakpoints || {})),

          className
        )}
        style={customStyles}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

Container.displayName = "Container";

// Enhanced FlexContainer with more customization
const FlexContainer = React.forwardRef<HTMLElement, 
  ContainerProps & {
    direction?: "row" | "column" | "row-reverse" | "column-reverse";
    align?: "start" | "center" | "end" | "stretch" | "baseline";
    justify?: "start" | "center" | "end" | "between" | "around" | "evenly";
    wrap?: boolean | "reverse";
    gap?: "none" | "xs" | "sm" | "md" | "lg" | "xl" | "2xl" | "custom";
    customGap?: string | number;
  }
>(({ 
  display = "flex",
  direction = "row",
  align = "start",
  justify = "start",
  wrap = false,
  gap = "none",
  customGap,
  className,
  style,
  ...props 
}, ref) => (
  <Container
    ref={ref}
    display={display}
    className={cn(
      // Flex direction
      {
        "flex-row": direction === "row",
        "flex-col": direction === "column",
        "flex-row-reverse": direction === "row-reverse",
        "flex-col-reverse": direction === "column-reverse",
      },

      // Align items
      {
        "items-start": align === "start",
        "items-center": align === "center",
        "items-end": align === "end",
        "items-stretch": align === "stretch",
        "items-baseline": align === "baseline",
      },

      // Justify content
      {
        "justify-start": justify === "start",
        "justify-center": justify === "center",
        "justify-end": justify === "end",
        "justify-between": justify === "between",
        "justify-around": justify === "around",
        "justify-evenly": justify === "evenly",
      },

      // Flex wrap
      {
        "flex-wrap": wrap === true,
        "flex-wrap-reverse": wrap === "reverse",
        "flex-nowrap": wrap === false,
      },

      // Gap (using standard classes)
      {
        "gap-0": gap === "none",
        "gap-1": gap === "xs",
        "gap-2": gap === "sm",
        "gap-4": gap === "md",
        "gap-6": gap === "lg",
        "gap-8": gap === "xl",
        "gap-12": gap === "2xl",
      },

      className
    )}
    style={{
      ...(customGap && { gap: customGap }),
      ...style,
    }}
    {...props}
  />
));

FlexContainer.displayName = "FlexContainer";

// Enhanced GridContainer with advanced grid features
const GridContainer = React.forwardRef<HTMLElement,
  ContainerProps & {
    columns?: number | string | "auto" | "auto-fit" | "auto-fill";
    rows?: number | string | "auto";
    gap?: "none" | "xs" | "sm" | "md" | "lg" | "xl" | "2xl" | "custom";
    customGap?: string | number;
    autoFlow?: "row" | "column" | "dense" | "row dense" | "column dense";
    areas?: string[];
    template?: {
      columns?: string;
      rows?: string;
      areas?: string;
    };
    minItemWidth?: string;
    maxItemWidth?: string;
  }
>(({ 
  display = "grid",
  columns = "auto",
  rows = "auto",
  gap = "md",
  customGap,
  autoFlow = "row",
  areas,
  template,
  minItemWidth = "250px",
  maxItemWidth,
  className,
  style,
  ...props 
}, ref) => {
  const gridStyle: React.CSSProperties = {
    gridTemplateColumns: template?.columns 
      ? template.columns 
      : columns === "auto-fit" 
        ? `repeat(auto-fit, minmax(${minItemWidth}, ${maxItemWidth || "1fr"}))`
        : columns === "auto-fill"
          ? `repeat(auto-fill, minmax(${minItemWidth}, 1fr))`
          : typeof columns === "number" 
            ? `repeat(${columns}, 1fr)`
            : columns,
    gridTemplateRows: template?.rows 
      ? template.rows 
      : typeof rows === "number" 
        ? `repeat(${rows}, 1fr)`
        : rows,
    gridTemplateAreas: template?.areas 
      ? template.areas 
      : areas 
        ? `"${areas.join('" "')}"`
        : undefined,
    gridAutoFlow: autoFlow,
    ...(customGap && { gap: customGap }),
    ...style,
  };

  return (
    <Container
      ref={ref}
      display={display}
      className={cn(
        // Gap (using standard classes)
        {
          "gap-0": gap === "none",
          "gap-1": gap === "xs",
          "gap-2": gap === "sm",
          "gap-4": gap === "md",
          "gap-6": gap === "lg",
          "gap-8": gap === "xl",
          "gap-12": gap === "2xl",
        },
        className
      )}
      style={gridStyle}
      {...props}
    />
  );
});

GridContainer.displayName = "GridContainer";

// Specialized container variants
const CenteredContainer = React.forwardRef<HTMLElement, ContainerProps>(
  ({ variant = "centered", ...props }, ref) => (
    <Container ref={ref} variant={variant} {...props} />
  )
);

CenteredContainer.displayName = "CenteredContainer";

const ConstrainedContainer = React.forwardRef<HTMLElement, ContainerProps>(
  ({ variant = "constrained", ...props }, ref) => (
    <Container ref={ref} variant={variant} {...props} />
  )
);

ConstrainedContainer.displayName = "ConstrainedContainer";

const FluidContainer = React.forwardRef<HTMLElement, ContainerProps>(
  ({ variant = "fluid", size = "full", ...props }, ref) => (
    <Container ref={ref} variant={variant} size={size} {...props} />
  )
);

FluidContainer.displayName = "FluidContainer";

const HeroContainer = React.forwardRef<HTMLElement, ContainerProps>(
  ({ variant = "hero", ...props }, ref) => (
    <Container ref={ref} variant={variant} {...props} />
  )
);

HeroContainer.displayName = "HeroContainer";

const SectionContainer = React.forwardRef<HTMLElement, ContainerProps>(
  ({ variant = "section", ...props }, ref) => (
    <Container ref={ref} variant={variant} {...props} />
  )
);

SectionContainer.displayName = "SectionContainer";

const CardContainer = React.forwardRef<HTMLElement, ContainerProps>(
  ({ variant = "card", ...props }, ref) => (
    <Container ref={ref} variant={variant} {...props} />
  )
);

CardContainer.displayName = "CardContainer";

const SidebarContainer = React.forwardRef<HTMLElement, ContainerProps>(
  ({ variant = "sidebar", ...props }, ref) => (
    <Container ref={ref} variant={variant} {...props} />
  )
);

SidebarContainer.displayName = "SidebarContainer";

const ModalContainer = React.forwardRef<HTMLElement, ContainerProps>(
  ({ variant = "modal", ...props }, ref) => (
    <Container ref={ref} variant={variant} {...props} />
  )
);

ModalContainer.displayName = "ModalContainer";

// Utility container for common patterns
const AspectRatioContainer = React.forwardRef<HTMLElement,
  ContainerProps & {
    ratio?: "1/1" | "4/3" | "16/9" | "21/9" | "9/16" | "custom";
    customRatio?: string;
  }
>(({ 
  ratio = "16/9",
  customRatio,
  className,
  style,
  children,
  ...props 
}, ref) => {
  const aspectRatioStyle: React.CSSProperties = {
    aspectRatio: customRatio || ratio,
    ...style,
  };

  return (
    <Container
      ref={ref}
      className={cn("overflow-hidden", className)}
      style={aspectRatioStyle}
      {...props}
    >
      {children}
    </Container>
  );
});

AspectRatioContainer.displayName = "AspectRatioContainer";

// Scrollable container
const ScrollContainer = React.forwardRef<HTMLElement,
  ContainerProps & {
    scrollbar?: "none" | "thin" | "auto";
    snap?: "none" | "x" | "y" | "both";
    snapType?: "mandatory" | "proximity";
  }
>(({ 
  scrollbar = "auto",
  snap = "none",
  snapType = "proximity",
  className,
  ...props 
}, ref) => (
  <Container
    ref={ref}
    className={cn(
      "overflow-auto",
      {
        "scrollbar-thin scrollbar-thumb-rounded scrollbar-track-transparent scrollbar-thumb-muted-foreground/20": 
          scrollbar === "thin",
        "scrollbar-hide": scrollbar === "none",
        "snap-x": snap === "x",
        "snap-y": snap === "y",
        "snap-both": snap === "both",
        "snap-mandatory": snapType === "mandatory",
        "snap-proximity": snapType === "proximity",
      },
      className
    )}
    {...props}
  />
));

ScrollContainer.displayName = "ScrollContainer";

// Exports
export {
  Container,
  FlexContainer,
  GridContainer,
  CenteredContainer,
  ConstrainedContainer,
  FluidContainer,
  HeroContainer,
  SectionContainer,
  CardContainer,
  SidebarContainer,
  ModalContainer,
  AspectRatioContainer,
  ScrollContainer,
};

export type {
  ContainerProps,
  ContainerVariant,
  ContainerSize,
  ContainerDisplay,
};