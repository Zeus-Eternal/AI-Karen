"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";
import { ErrorBoundary } from "@/components/ui/error-boundary";

/* ========================
 * Types
 * ====================== */

export type LayoutGap = "none" | "sm" | "md" | "lg" | "xl";
export type LayoutColumns =
  | "auto"
  | "1"
  | "2"
  | "3"
  | "4"
  | "5"
  | "6"
  | "auto-fit"
  | "auto-fill";

export type Breakpoint = "sm" | "md" | "lg" | "xl";
export type ResponsiveColumnCount = "1" | "2" | "3" | "4" | "5" | "6";

export interface BaseLayoutProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export interface LayoutGridProps extends BaseLayoutProps {
  columns?: LayoutColumns;
  gap?: LayoutGap;
  responsive?: boolean;
  responsiveColumns?: Partial<Record<Breakpoint, ResponsiveColumnCount>>;
  /** px; only used when columns is auto-fit/auto-fill */
  minItemWidth?: number;
  /** Pass-through style */
  style?: React.CSSProperties;
}

export interface LayoutFlexProps extends BaseLayoutProps {
  direction?: "row" | "row-reverse" | "col" | "col-reverse";
  align?: "start" | "center" | "end" | "stretch" | "baseline";
  justify?: "start" | "center" | "end" | "between" | "around" | "evenly";
  wrap?: boolean | "nowrap" | "wrap" | "wrap-reverse";
  gap?: LayoutGap;
}

export interface LayoutSectionProps
  extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "card" | "glass";
  padding?: LayoutGap;
}

export interface LayoutHeaderProps extends React.HTMLAttributes<HTMLElement> {
  children?: React.ReactNode;
  className?: string;
  title?: string;
  description?: string;
  actions?: React.ReactNode;
}

export interface LayoutContainerProps extends BaseLayoutProps {
  size?: "sm" | "md" | "lg" | "xl" | "full";
  centered?: boolean;
  className?: string;
  maxWidth?: boolean;
  padding?: boolean;
}

/* ========================
 * Class Maps
 * ====================== */

const GAP_CLASS_MAP: Record<LayoutGap, string> = {
  none: "gap-0",
  sm: "gap-2",
  md: "gap-4",
  lg: "gap-6",
  xl: "gap-8",
};

const PADDING_CLASS_MAP: Record<LayoutGap, string> = {
  none: "p-0",
  sm: "p-2",
  md: "p-4",
  lg: "p-6",
  xl: "p-8",
};

const GRID_COLUMN_CLASS_MAP: Record<LayoutColumns, string> = {
  "1": "grid-cols-1",
  "2": "grid-cols-2",
  "3": "grid-cols-3",
  "4": "grid-cols-4",
  "5": "grid-cols-5",
  "6": "grid-cols-6",
  auto: "grid-cols-[auto_1fr]",
  "auto-fit": "grid-cols-[repeat(auto-fit,minmax(300px,1fr))]",
  "auto-fill": "grid-cols-[repeat(auto-fill,minmax(300px,1fr))]",
};

const RESPONSIVE_COLUMN_CLASS_MAP: Record<
  Breakpoint,
  Record<ResponsiveColumnCount, string>
> = {
  sm: {
    "1": "sm:grid-cols-1",
    "2": "sm:grid-cols-2",
    "3": "sm:grid-cols-3",
    "4": "sm:grid-cols-4",
    "5": "sm:grid-cols-5",
    "6": "sm:grid-cols-6",
  },
  md: {
    "1": "md:grid-cols-1",
    "2": "md:grid-cols-2",
    "3": "md:grid-cols-3",
    "4": "md:grid-cols-4",
    "5": "md:grid-cols-5",
    "6": "md:grid-cols-6",
  },
  lg: {
    "1": "lg:grid-cols-1",
    "2": "lg:grid-cols-2",
    "3": "lg:grid-cols-3",
    "4": "lg:grid-cols-4",
    "5": "lg:grid-cols-5",
    "6": "lg:grid-cols-6",
  },
  xl: {
    "1": "xl:grid-cols-1",
    "2": "xl:grid-cols-2",
    "3": "xl:grid-cols-3",
    "4": "xl:grid-cols-4",
    "5": "xl:grid-cols-5",
    "6": "xl:grid-cols-6",
  },
};

const SECTION_VARIANT_CLASS_MAP: Record<
  NonNullable<LayoutSectionProps["variant"]>,
  string
> = {
  default: "",
  card: "modern-card", // assumes a shadcn card preset or your custom class
  glass: "glass",      // assumes a glassmorphism utility in your CSS
};

const FLEX_DIRECTION_CLASS_MAP: Record<
  NonNullable<LayoutFlexProps["direction"]>,
  string
> = {
  row: "flex-row",
  "row-reverse": "flex-row-reverse",
  col: "flex-col",
  "col-reverse": "flex-col-reverse",
};

const FLEX_ALIGN_CLASS_MAP: Record<
  NonNullable<LayoutFlexProps["align"]>,
  string
> = {
  start: "items-start",
  center: "items-center",
  end: "items-end",
  stretch: "items-stretch",
  baseline: "items-baseline",
};

const FLEX_JUSTIFY_CLASS_MAP: Record<
  NonNullable<LayoutFlexProps["justify"]>,
  string
> = {
  start: "justify-start",
  center: "justify-center",
  end: "justify-end",
  between: "justify-between",
  around: "justify-around",
  evenly: "justify-evenly",
};

const FLEX_WRAP_CLASS_MAP: Record<"nowrap" | "wrap" | "wrap-reverse", string> = {
  nowrap: "flex-nowrap",
  wrap: "flex-wrap",
  "wrap-reverse": "flex-wrap-reverse",
};

/* ========================
 * Components
 * ====================== */

// Main Layout Container (fluid wrapper)
export const Layout = forwardRef<HTMLDivElement, BaseLayoutProps>(
  React.memo(({ children, className, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("container-fluid", className)} {...props}>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </div>
    );
  })
);
Layout.displayName = "Layout";

// Grid Layout
export const LayoutGrid = forwardRef<HTMLDivElement, LayoutGridProps>(
  React.memo((
    {
      children,
      className,
      columns = "auto-fit",
      gap = "md",
      responsive = true,
      responsiveColumns,
      minItemWidth,
      style,
      ...props
    },
    ref
  ) => {
    const autoLayoutMode = React.useMemo(
      () => columns === "auto-fit" ? "auto-fit" : columns === "auto-fill" ? "auto-fill" : null,
      [columns]
    );

    const shouldUsePresetAutoLayoutClass = React.useMemo(
      () => !!autoLayoutMode && !minItemWidth,
      [autoLayoutMode, minItemWidth]
    );
    
    const columnClass = React.useMemo(
      () => GRID_COLUMN_CLASS_MAP[columns],
      [columns]
    );
    
    const gapClass = React.useMemo(
      () => GAP_CLASS_MAP[gap],
      [gap]
    );

    const responsiveClasses = React.useMemo(() => {
      const classes: string[] = [];

      if (responsiveColumns) {
        (Object.entries(responsiveColumns) as [Breakpoint, ResponsiveColumnCount][])
          .forEach(([breakpoint, value]) => {
            const rc = RESPONSIVE_COLUMN_CLASS_MAP[breakpoint]?.[value];
            if (rc) classes.push(rc);
          });
      } else if (responsive && autoLayoutMode === "auto-fit") {
        // sensible defaults when auto-fit is used
        classes.push("md:grid-cols-2", "lg:grid-cols-3", "xl:grid-cols-4");
      }
      
      return classes;
    }, [responsiveColumns, responsive, autoLayoutMode]);

    const autoLayoutStyle = React.useMemo(() => {
      if (!autoLayoutMode) return style;
      
      return {
        gridTemplateColumns: `repeat(${autoLayoutMode}, minmax(${minItemWidth ?? 300}px, 1fr))`,
        ...style,
      };
    }, [autoLayoutMode, minItemWidth, style]);

    const gridClasses = React.useMemo(
      () => cn(
        "grid",
        columnClass && (!autoLayoutMode || shouldUsePresetAutoLayoutClass) && columnClass,
        gapClass,
        responsiveClasses.join(" "),
        className
      ),
      [columnClass, autoLayoutMode, shouldUsePresetAutoLayoutClass, gapClass, responsiveClasses, className]
    );

    return (
      <div ref={ref} className={gridClasses} style={autoLayoutStyle} {...props}>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </div>
    );
  })
);
LayoutGrid.displayName = "LayoutGrid";

// Flex Layout
export const LayoutFlex = forwardRef<HTMLDivElement, LayoutFlexProps>(
  React.memo((
    {
      children,
      className,
      direction = "row",
      align = "start",
      justify = "start",
      wrap = "nowrap",
      gap = "md",
      ...otherProps
    },
    ref
  ) => {
    const normalizedWrap = React.useMemo(
      () => typeof wrap === "boolean" ? (wrap ? "wrap" : "nowrap") : wrap,
      [wrap]
    );
    
    const gapClass = React.useMemo(
      () => GAP_CLASS_MAP[gap],
      [gap]
    );

    const dir = direction as NonNullable<LayoutFlexProps["direction"]>;
    const ali = align as NonNullable<LayoutFlexProps["align"]>;
    const jus = justify as NonNullable<LayoutFlexProps["justify"]>;
    const wrapKey = normalizedWrap as keyof typeof FLEX_WRAP_CLASS_MAP;

    const flexClasses = React.useMemo(
      () => cn(
        "flex",
        FLEX_DIRECTION_CLASS_MAP[dir],
        FLEX_ALIGN_CLASS_MAP[ali],
        FLEX_JUSTIFY_CLASS_MAP[jus],
        FLEX_WRAP_CLASS_MAP[wrapKey],
        gapClass,
        className
      ),
      [dir, ali, jus, wrapKey, gapClass, className]
    );

    return (
      <div ref={ref} className={flexClasses} {...otherProps}>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </div>
    );
  })
);
LayoutFlex.displayName = "LayoutFlex";

// Section
export const LayoutSection = forwardRef<HTMLElement, LayoutSectionProps>(
  React.memo(({ children, className, variant = "default", padding = "md", ...otherProps }, ref) => {
    const paddingClass = React.useMemo(
      () => PADDING_CLASS_MAP[padding],
      [padding]
    );
    
    const variantClass = React.useMemo(
      () => SECTION_VARIANT_CLASS_MAP[variant],
      [variant]
    );
    
    const sectionClasses = React.useMemo(
      () => cn(
        variantClass,
        paddingClass,
        "rounded-lg transition-all duration-300 ease-in-out",
        variant === "card" && "shadow-sm border border-border/50 hover:shadow-md",
        variant === "glass" && "bg-background/60 backdrop-blur-sm",
        className
      ),
      [variantClass, paddingClass, variant, className]
    );

    return (
      <section ref={ref} className={sectionClasses} {...otherProps}>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </section>
    );
  })
);
LayoutSection.displayName = "LayoutSection";

// Page Header
export const LayoutHeader = forwardRef<HTMLElement, LayoutHeaderProps>(
  React.memo(({ children, className, title, description, actions, ...otherProps }, ref) => {
    const headerClasses = React.useMemo(
      () => cn(
        "modern-card-header space-y-4 pb-4 border-b border-border/50 transition-all duration-300 ease-in-out",
        className
      ),
      [className]
    );

    return (
      <header
        ref={ref}
        className={headerClasses}
        {...otherProps}
      >
        <div className={cn("flex items-start justify-between") /* robust replacement for 'flex-between' */}>
          <div className="space-y-1">
            {title && (
              <h1 className="text-2xl font-bold tracking-tight text-foreground">{title}</h1>
            )}
            {description && <p className="text-muted-foreground text-sm max-w-3xl">{description}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </header>
    );
  })
);
LayoutHeader.displayName = "LayoutHeader";

// Max-width Container
export const LayoutContainer = forwardRef<HTMLDivElement, LayoutContainerProps>(
  React.memo(({
    children,
    className,
    size = "lg",
    centered = true,
    maxWidth = true,
    padding = true,
    ...otherProps
  }, ref) => {
    const containerClasses = React.useMemo(
      () => cn(
        "w-full",
        padding ? "px-4 sm:px-6 lg:px-8" : "",
        {
          "max-w-2xl": maxWidth && size === "sm",
          "max-w-4xl": maxWidth && size === "md",
          "max-w-6xl": maxWidth && size === "lg",
          "max-w-7xl": maxWidth && size === "xl",
          "max-w-none": maxWidth && size === "full",
        },
        centered && "mx-auto",
        "transition-all duration-300 ease-in-out",
        className
      ),
      [size, centered, maxWidth, padding, className]
    );

    return (
      <div ref={ref} className={containerClasses} {...otherProps}>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </div>
    );
  })
);
LayoutContainer.displayName = "LayoutContainer";
