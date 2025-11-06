"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

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
  ({ children, className, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("container-fluid", className)} {...props}>
        {children}
      </div>
    );
  }
);
Layout.displayName = "Layout";

// Grid Layout
export const LayoutGrid = forwardRef<HTMLDivElement, LayoutGridProps>(
  (
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
    const autoLayoutMode =
      columns === "auto-fit" ? "auto-fit" : columns === "auto-fill" ? "auto-fill" : null;

    const shouldUsePresetAutoLayoutClass = !!autoLayoutMode && !minItemWidth;
    const columnClass = GRID_COLUMN_CLASS_MAP[columns];
    const gapClass = GAP_CLASS_MAP[gap];

    const responsiveClasses: string[] = [];

    if (responsiveColumns) {
      (Object.entries(responsiveColumns) as [Breakpoint, ResponsiveColumnCount][])
        .forEach(([breakpoint, value]) => {
          const rc = RESPONSIVE_COLUMN_CLASS_MAP[breakpoint]?.[value];
          if (rc) responsiveClasses.push(rc);
        });
    } else if (responsive && autoLayoutMode === "auto-fit") {
      // sensible defaults when auto-fit is used
      responsiveClasses.push("md:grid-cols-2", "lg:grid-cols-3", "xl:grid-cols-4");
    }

    const autoLayoutStyle = autoLayoutMode
      ? {
          gridTemplateColumns: `repeat(${autoLayoutMode}, minmax(${minItemWidth ?? 300}px, 1fr))`,
          ...style,
        }
      : style;

    const gridClasses = cn(
      "grid",
      columnClass && (!autoLayoutMode || shouldUsePresetAutoLayoutClass) && columnClass,
      gapClass,
      responsiveClasses.join(" "),
      className
    );

    return (
      <div ref={ref} className={gridClasses} style={autoLayoutStyle} {...props}>
        {children}
      </div>
    );
  }
);
LayoutGrid.displayName = "LayoutGrid";

// Flex Layout
export const LayoutFlex = forwardRef<HTMLDivElement, LayoutFlexProps>(
  (
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
    const normalizedWrap = typeof wrap === "boolean" ? (wrap ? "wrap" : "nowrap") : wrap;
    const gapClass = GAP_CLASS_MAP[gap];

    const dir = direction as NonNullable<LayoutFlexProps["direction"]>;
    const ali = align as NonNullable<LayoutFlexProps["align"]>;
    const jus = justify as NonNullable<LayoutFlexProps["justify"]>;
    const wrapKey = normalizedWrap as keyof typeof FLEX_WRAP_CLASS_MAP;

    const flexClasses = cn(
      "flex",
      FLEX_DIRECTION_CLASS_MAP[dir],
      FLEX_ALIGN_CLASS_MAP[ali],
      FLEX_JUSTIFY_CLASS_MAP[jus],
      FLEX_WRAP_CLASS_MAP[wrapKey],
      gapClass,
      className
    );

    return (
      <div ref={ref} className={flexClasses} {...otherProps}>
        {children}
      </div>
    );
  }
);
LayoutFlex.displayName = "LayoutFlex";

// Section
export const LayoutSection = forwardRef<HTMLElement, LayoutSectionProps>(
  ({ children, className, variant = "default", padding = "md", ...otherProps }, ref) => {
    const paddingClass = PADDING_CLASS_MAP[padding];
    const variantClass = SECTION_VARIANT_CLASS_MAP[variant];
    const sectionClasses = cn(variantClass, paddingClass, className);

    return (
      <section ref={ref} className={sectionClasses} {...otherProps}>
        {children}
      </section>
    );
  }
);
LayoutSection.displayName = "LayoutSection";

// Page Header
export const LayoutHeader = forwardRef<HTMLElement, LayoutHeaderProps>(
  ({ children, className, title, description, actions, ...otherProps }, ref) => {
    return (
      <header
        ref={ref}
        className={cn("modern-card-header space-y-4", className)}
        {...otherProps}
      >
        <div className={cn("flex items-start justify-between") /* robust replacement for 'flex-between' */}>
          <div className="space-y-1">
            {title && (
              <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            )}
            {description && <p className="text-muted-foreground">{description}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
        {children}
      </header>
    );
  }
);
LayoutHeader.displayName = "LayoutHeader";

// Max-width Container
export const LayoutContainer = forwardRef<HTMLDivElement, LayoutContainerProps>(
  ({ children, className, size = "lg", centered = true, ...otherProps }, ref) => {
    const containerClasses = cn(
      "w-full px-4 sm:px-6 lg:px-8",
      {
        "max-w-2xl": size === "sm",
        "max-w-4xl": size === "md",
        "max-w-6xl": size === "lg",
        "max-w-7xl": size === "xl",
        "max-w-none": size === "full",
      },
      centered && "mx-auto",
      className
    );

    return (
      <div ref={ref} className={containerClasses} {...otherProps}>
        {children}
      </div>
    );
  }
);
LayoutContainer.displayName = "LayoutContainer";
