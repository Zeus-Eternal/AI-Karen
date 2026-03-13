"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

import {
  forwardRefWithAs,
  type PolymorphicComponentProp,
  type PolymorphicComponentPropWithRef,
  type PolymorphicComponentWithDisplayName,
  type PolymorphicRef,
} from "../compound/types";

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

export type ContainerBorder = "none" | "thin" | "medium" | "thick" | "custom";

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

export type ContainerBlur = "none" | "sm" | "md" | "lg" | "xl" | "2xl" | "custom";

export type ContainerRounded =
  | "none"
  | "sm"
  | "md"
  | "lg"
  | "xl"
  | "2xl"
  | "3xl"
  | "full"
  | "custom";

type HoverConfig = {
  scale?: number;
  shadow?: ContainerShadow;
  background?: ContainerBackground;
  customBackground?: string;
};

type FocusConfig = {
  shadow?: ContainerShadow;
  border?: ContainerBorder;
  outline?: boolean;
};

type ResponsiveOverride = Partial<
  Omit<
    ContainerBaseProps,
    | "children"
    | "hover"
    | "focus"
    | "breakpoints"
    | "customBackground"
    | "customRounded"
    | "customBlur"
    | "customSize"
    | "customMaxSize"
  >
>;

export type ContainerBreakpoints = {
  sm?: ResponsiveOverride;
  md?: ResponsiveOverride;
  lg?: ResponsiveOverride;
  xl?: ResponsiveOverride;
  "2xl"?: ResponsiveOverride;
};

type ContainerAnimation = "none" | "fade" | "slide" | "scale" | "bounce" | "custom";

type ContainerBaseProps = {
  as?: React.ElementType;
  variant?: ContainerVariant;
  size?: ContainerSize;
  customSize?: string | number;
  customMaxSize?: string | number;
  display?: ContainerDisplay;
  responsive?: boolean;
  position?: ContainerPosition;
  overflow?: ContainerOverflow;
  shadow?: ContainerShadow;
  border?: ContainerBorder;
  background?: ContainerBackground;
  customBackground?: string;
  rounded?: ContainerRounded;
  customRounded?: string;
  zIndex?: number | "auto";
  opacity?: number;
  blur?: ContainerBlur;
  customBlur?: string;
  animation?: ContainerAnimation;
  animationDelay?: number;
  animationDuration?: number;
  hover?: HoverConfig;
  focus?: FocusConfig;
  breakpoints?: ContainerBreakpoints;
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
};

type ContainerRenderProps<T extends React.ElementType = "div"> =
  PolymorphicComponentProp<T, ContainerBaseProps>;

export type ContainerProps<T extends React.ElementType = "div"> =
  PolymorphicComponentPropWithRef<T, ContainerBaseProps>;

type ContainerPolymorphicComponent<P = Record<string, unknown>> =
  PolymorphicComponentWithDisplayName<"div", ContainerBaseProps & P>;

type ContainerComponent = ContainerPolymorphicComponent;

const displayClassMap: Record<ContainerDisplay, string> = {
  block: "block",
  flex: "flex",
  grid: "grid",
  inline: "inline",
  "inline-flex": "inline-flex",
  "inline-grid": "inline-grid",
  none: "hidden",
};

const positionClassMap: Record<ContainerPosition, string> = {
  static: "static",
  relative: "relative",
  absolute: "absolute",
  fixed: "fixed",
  sticky: "sticky",
};

const overflowClassMap: Record<ContainerOverflow, string> = {
  auto: "overflow-auto",
  hidden: "overflow-hidden",
  visible: "overflow-visible",
  scroll: "overflow-scroll",
  clip: "overflow-clip",
};

const shadowClassMap: Record<ContainerShadow, string> = {
  none: "shadow-none",
  sm: "shadow-sm",
  md: "shadow",
  lg: "shadow-md",
  xl: "shadow-lg",
  "2xl": "shadow-xl",
  inner: "shadow-inner",
  outline: "shadow-outline",
};

const borderClassMap: Record<Exclude<ContainerBorder, "custom">, string> = {
  none: "border-0",
  thin: "border",
  medium: "border-2",
  thick: "border-4",
};

const backgroundClassMap: Record<Exclude<ContainerBackground, "custom">, string> = {
  transparent: "bg-transparent",
  default: "bg-background",
  muted: "bg-muted",
  primary: "bg-primary",
  secondary: "bg-secondary",
  accent: "bg-accent",
  destructive: "bg-destructive",
  warning: "bg-warning",
  success: "bg-success",
};

const roundedClassMap: Record<Exclude<ContainerRounded, "custom">, string> = {
  none: "rounded-none",
  sm: "rounded-sm",
  md: "rounded",
  lg: "rounded-md",
  xl: "rounded-lg",
  "2xl": "rounded-xl",
  "3xl": "rounded-2xl",
  full: "rounded-full",
};

const blurClassMap: Record<Exclude<ContainerBlur, "custom">, string> = {
  none: "backdrop-blur-none",
  sm: "backdrop-blur-sm",
  md: "backdrop-blur",
  lg: "backdrop-blur-md",
  xl: "backdrop-blur-lg",
  "2xl": "backdrop-blur-xl",
};

const animationClassMap: Record<Exclude<ContainerAnimation, "custom">, string> = {
  none: "",
  fade: "animate-fade-in",
  slide: "animate-slide-in",
  scale: "animate-scale-in",
  bounce: "animate-bounce",
};

const variantClassMap: Record<ContainerVariant, string> = {
  default: "mx-auto w-full px-4 sm:px-6 lg:px-8",
  fluid: "w-full",
  constrained: "mx-auto w-full",
  centered: "flex items-center justify-center",
  padded: "px-4 sm:px-6 lg:px-8",
  hero: "min-h-screen flex items-center justify-center py-20",
  section: "py-12 lg:py-24",
  card: "bg-card text-card-foreground rounded-lg border shadow-sm p-6",
  sidebar: "h-screen w-64 fixed left-0 top-0 border-r bg-background",
  modal: "fixed inset-0 z-50 bg-background/80 backdrop-blur-sm",
};

const responsiveSizeMap: Partial<Record<ContainerSize, string>> = {
  xs: "max-w-xs",
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
  "2xl": "max-w-2xl",
  "3xl": "max-w-3xl",
  "4xl": "max-w-4xl",
  "5xl": "max-w-5xl",
  "6xl": "max-w-6xl",
  "7xl": "max-w-7xl",
  full: "max-w-none",
  screen: "max-w-screen",
};

const staticSizeMap: Partial<Record<ContainerSize, string>> = {
  xs: "w-80",
  sm: "w-96",
  md: "w-[32rem]",
  lg: "w-[40rem]",
  xl: "w-[48rem]",
  "2xl": "w-[56rem]",
  "3xl": "w-[64rem]",
  "4xl": "w-[72rem]",
  "5xl": "w-[80rem]",
  "6xl": "w-[88rem]",
  "7xl": "w-[96rem]",
  full: "w-full",
  screen: "w-screen",
};

const hoverScaleClassMap: Record<number, string> = {
  1.05: "hover:scale-105",
  1.1: "hover:scale-110",
  1.25: "hover:scale-125",
};

const hoverShadowClassMap: Partial<Record<ContainerShadow, string>> = {
  lg: "hover:shadow-lg",
  xl: "hover:shadow-xl",
};

const hoverBackgroundClassMap: Partial<Record<ContainerBackground, string>> = {
  primary: "hover:bg-primary",
  secondary: "hover:bg-secondary",
  accent: "hover:bg-accent",
};

const focusShadowClassMap: Partial<Record<ContainerShadow, string>> = {
  outline: "focus:shadow-outline",
  sm: "focus:shadow-sm",
  md: "focus:shadow",
  lg: "focus:shadow-lg",
};

const gapClassMap: Record<"none" | "xs" | "sm" | "md" | "lg" | "xl" | "2xl", string> = {
  none: "gap-0",
  xs: "gap-1",
  sm: "gap-2",
  md: "gap-4",
  lg: "gap-6",
  xl: "gap-8",
  "2xl": "gap-12",
};

const createResponsiveClasses = (
  breakpoints?: ContainerBreakpoints
): string[] => {
  if (!breakpoints) {
    return [];
  }

  const classes: string[] = [];

  Object.entries(breakpoints).forEach(([breakpoint, config]) => {
    if (!config) {
      return;
    }

    if (config.size && responsiveSizeMap[config.size]) {
      classes.push(`${breakpoint}:${responsiveSizeMap[config.size]}`);
    }

    if (config.display && displayClassMap[config.display]) {
      classes.push(`${breakpoint}:${displayClassMap[config.display]}`);
    }
  });

  return classes;
};

const resolveHoverClasses = (hover?: HoverConfig) => {
  if (!hover) {
    return undefined;
  }

  return cn(
    "transition-all duration-200 ease-in-out",
    hover.scale !== undefined ? hoverScaleClassMap[hover.scale] : undefined,
    hover.shadow ? hoverShadowClassMap[hover.shadow] : undefined,
    hover.background ? hoverBackgroundClassMap[hover.background] : undefined,
    hover.customBackground ? `hover:${hover.customBackground}` : undefined
  );
};

const resolveFocusClasses = (focus?: FocusConfig) => {
  if (!focus) {
    return undefined;
  }

  return cn(
    "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
    focus.outline ? "focus:shadow-outline" : undefined,
    focus.shadow ? focusShadowClassMap[focus.shadow] : undefined,
    focus.border === "medium" ? "focus:border-2" : undefined
  );
};

function ContainerInner<T extends React.ElementType = "div">(
  {
    as,
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
    ...rest
  }: ContainerRenderProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const Component = (as ?? "div") as T;
  const ComponentToRender = Component as React.ElementType;

  const inlineStyles: React.CSSProperties = {
    ...(style as React.CSSProperties | undefined),
    ...(customSize !== undefined && {
      width: customSize,
      height: customSize,
    }),
    ...(customMaxSize !== undefined && {
      maxWidth: customMaxSize,
      maxHeight: customMaxSize,
    }),
    ...(customBackground && { backgroundColor: customBackground }),
    ...(customRounded && { borderRadius: customRounded }),
    ...(customBlur && { filter: `blur(${customBlur})` }),
    ...(zIndex !== "auto" ? { zIndex } : undefined),
    ...(opacity !== undefined && opacity !== 1 ? { opacity } : undefined),
    ...(animationDelay ? { animationDelay: `${animationDelay}ms` } : undefined),
    ...(animationDuration !== undefined && animationDuration !== 300
      ? { animationDuration: `${animationDuration}ms` }
      : undefined),
  };

  const responsiveClasses = createResponsiveClasses(breakpoints);
  const hoverClasses = resolveHoverClasses(hover);
  const focusClasses = resolveFocusClasses(focus);

  return (
    <ComponentToRender
      ref={ref as React.Ref<unknown>}
      className={cn(
        "transition-all duration-200 ease-in-out",
        displayClassMap[display],
        positionClassMap[position],
        overflowClassMap[overflow],
        shadowClassMap[shadow],
        border !== "custom" ? borderClassMap[border] : undefined,
        background !== "custom" ? backgroundClassMap[background] : undefined,
        rounded !== "custom" ? roundedClassMap[rounded] : undefined,
        blur !== "custom" ? blurClassMap[blur] : undefined,
        animation !== "custom" ? animationClassMap[animation] : undefined,
        variantClassMap[variant],
        responsive ? responsiveSizeMap[size] : staticSizeMap[size],
        hoverClasses,
        focusClasses,
        responsiveClasses,
        className
      )}
      style={inlineStyles}
      data-variant={variant}
      {...rest}
    >
      {children}
    </ComponentToRender>
  );
}

const Container: ContainerComponent = forwardRefWithAs<
  "div",
  ContainerBaseProps
>(ContainerInner);

Container.displayName = "Container";

const createVariantContainer = (
  defaultVariant: ContainerVariant,
  displayName: string
): ContainerComponent => {
  const Variant = forwardRefWithAs<
    "div",
    ContainerBaseProps
  >(function VariantComponent<T extends React.ElementType = "div">(
    { variant: providedVariant, ...rest }: ContainerRenderProps<T>,
    ref: PolymorphicRef<T>
  ) {
    const variantProps = {
      ...rest,
      variant: providedVariant ?? defaultVariant,
    };

    return (
      <Container
        {...(variantProps as React.ComponentProps<typeof Container>)}
        ref={ref}
      />
    );
  }) as ContainerComponent;

  Variant.displayName = displayName;
  return Variant;
};

type FlexContainerExtras = {
  direction?: "row" | "column" | "row-reverse" | "column-reverse";
  align?: "start" | "center" | "end" | "stretch" | "baseline";
  justify?: "start" | "center" | "end" | "between" | "around" | "evenly";
  wrap?: boolean | "reverse";
  gap?: "none" | "xs" | "sm" | "md" | "lg" | "xl" | "2xl" | "custom";
  customGap?: string | number;
};

export type FlexContainerProps<T extends React.ElementType = "div"> =
  ContainerProps<T> &
    FlexContainerExtras;

type FlexContainerRenderProps<T extends React.ElementType = "div"> =
  PolymorphicComponentProp<T, ContainerBaseProps & FlexContainerExtras>;

const flexDirectionClassMap: Record<
  NonNullable<FlexContainerExtras["direction"]>,
  string
> = {
  row: "flex-row",
  column: "flex-col",
  "row-reverse": "flex-row-reverse",
  "column-reverse": "flex-col-reverse",
};

const flexAlignClassMap: Record<
  NonNullable<FlexContainerExtras["align"]>,
  string
> = {
  start: "items-start",
  center: "items-center",
  end: "items-end",
  stretch: "items-stretch",
  baseline: "items-baseline",
};

const flexJustifyClassMap: Record<
  NonNullable<FlexContainerExtras["justify"]>,
  string
> = {
  start: "justify-start",
  center: "justify-center",
  end: "justify-end",
  between: "justify-between",
  around: "justify-around",
  evenly: "justify-evenly",
};

function FlexContainerInner<T extends React.ElementType = "div">(
  {
    as,
    display = "flex",
    direction = "row",
    align = "start",
    justify = "start",
    wrap = false,
    gap = "none",
    customGap,
    className,
    style,
    ...rest
  }: FlexContainerRenderProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const wrapClass =
    wrap === "reverse" ? "flex-wrap-reverse" : wrap ? "flex-wrap" : "flex-nowrap";
  const gapClass = gap === "custom" ? undefined : gapClassMap[gap];
  const containerProps = {
    ...rest,
    as,
    display,
    className: cn(
      flexDirectionClassMap[direction],
      flexAlignClassMap[align],
      flexJustifyClassMap[justify],
      wrapClass,
      gapClass,
      className
    ),
    style: {
      ...(style as React.CSSProperties | undefined),
      ...(customGap !== undefined ? { gap: customGap } : undefined),
    },
  };

  return (
    <Container
      {...(containerProps as React.ComponentProps<typeof Container>)}
      ref={ref}
    />
  );
}

const FlexContainer: ContainerPolymorphicComponent<FlexContainerExtras> =
  forwardRefWithAs<"div", ContainerBaseProps & FlexContainerExtras>(
    FlexContainerInner
  );

FlexContainer.displayName = "FlexContainer";

type GridContainerExtras = {
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
};

export type GridContainerProps<T extends React.ElementType = "div"> =
  ContainerProps<T> &
    GridContainerExtras;

type GridContainerRenderProps<T extends React.ElementType = "div"> =
  PolymorphicComponentProp<T, ContainerBaseProps & GridContainerExtras>;

function GridContainerInner<T extends React.ElementType = "div">(
  {
    as,
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
    ...rest
  }: GridContainerRenderProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const computedGap = gap === "custom" ? undefined : gapClassMap[gap];
  const gridTemplateColumns = template?.columns
    ? template.columns
    : columns === "auto-fit"
      ? `repeat(auto-fit, minmax(${minItemWidth}, ${maxItemWidth || "1fr"}))`
      : columns === "auto-fill"
        ? `repeat(auto-fill, minmax(${minItemWidth}, ${maxItemWidth || "1fr"}))`
        : typeof columns === "number"
          ? `repeat(${columns}, 1fr)`
          : columns === "auto"
            ? undefined
            : String(columns);

  const gridTemplateRows = template?.rows ?? (rows === "auto" ? undefined : String(rows));

  const gridTemplateAreas = template?.areas
    ?? (areas && areas.length > 0
      ? areas.map((area) => `'${area}'`).join(" ")
      : undefined);

  const containerProps = {
    ...rest,
    as,
    display,
    className: cn(computedGap, className),
    style: {
      ...(style as React.CSSProperties | undefined),
      ...(customGap !== undefined ? { gap: customGap } : undefined),
      ...(gridTemplateColumns ? { gridTemplateColumns } : undefined),
      ...(gridTemplateRows ? { gridTemplateRows } : undefined),
      ...(gridTemplateAreas ? { gridTemplateAreas } : undefined),
      ...(autoFlow ? { gridAutoFlow: autoFlow } : undefined),
    },
  };

  return (
    <Container
      {...(containerProps as React.ComponentProps<typeof Container>)}
      ref={ref}
    />
  );
}

const GridContainer: ContainerPolymorphicComponent<GridContainerExtras> =
  forwardRefWithAs<"div", ContainerBaseProps & GridContainerExtras>(
    GridContainerInner
  );

GridContainer.displayName = "GridContainer";

const CenteredContainer = createVariantContainer("centered", "CenteredContainer");

const ConstrainedContainer = createVariantContainer(
  "constrained",
  "ConstrainedContainer"
);

const FluidContainer = createVariantContainer("fluid", "FluidContainer");

const HeroContainer = createVariantContainer("hero", "HeroContainer");

const SectionContainer = createVariantContainer("section", "SectionContainer");

const CardContainer = createVariantContainer("card", "CardContainer");

const SidebarContainer = createVariantContainer("sidebar", "SidebarContainer");

const ModalContainer = createVariantContainer("modal", "ModalContainer");

type AspectRatioExtras = {
  ratio?: "1/1" | "4/3" | "16/9" | "21/9" | "9/16" | "custom";
  customRatio?: string;
};

export type AspectRatioContainerProps<T extends React.ElementType = "div"> =
  ContainerProps<T> &
    AspectRatioExtras;

type AspectRatioContainerRenderProps<T extends React.ElementType = "div"> =
  PolymorphicComponentProp<T, ContainerBaseProps & AspectRatioExtras>;

function AspectRatioContainerInner<T extends React.ElementType = "div">(
  {
    ratio = "16/9",
    customRatio,
    className,
    style,
    children,
    ...rest
  }: AspectRatioContainerRenderProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const containerProps = {
    ...rest,
    className: cn("overflow-hidden", className),
    style: {
      ...(style as React.CSSProperties | undefined),
      aspectRatio: customRatio ?? ratio,
    },
  };

  return (
    <Container
      {...(containerProps as React.ComponentProps<typeof Container>)}
      ref={ref}
    >
      {children}
    </Container>
  );
}

const AspectRatioContainer: ContainerPolymorphicComponent<AspectRatioExtras> =
  forwardRefWithAs<"div", ContainerBaseProps & AspectRatioExtras>(
    AspectRatioContainerInner
  );

AspectRatioContainer.displayName = "AspectRatioContainer";

type ScrollContainerExtras = {
  scrollbar?: "none" | "thin" | "auto";
  snap?: "none" | "x" | "y" | "both";
  snapType?: "mandatory" | "proximity";
};

export type ScrollContainerProps<T extends React.ElementType = "div"> =
  ContainerProps<T> &
    ScrollContainerExtras;

type ScrollContainerRenderProps<T extends React.ElementType = "div"> =
  PolymorphicComponentProp<T, ContainerBaseProps & ScrollContainerExtras>;

function ScrollContainerInner<T extends React.ElementType = "div">(
  {
    scrollbar = "auto",
    snap = "none",
    snapType = "proximity",
    className,
    ...rest
  }: ScrollContainerRenderProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const containerProps = {
    ...rest,
    className: cn(
      "overflow-auto",
      scrollbar === "thin"
        ? "scrollbar-thin scrollbar-thumb-rounded scrollbar-track-transparent scrollbar-thumb-muted-foreground/20"
        : undefined,
      scrollbar === "none" ? "scrollbar-hide" : undefined,
      snap === "x" ? "snap-x" : undefined,
      snap === "y" ? "snap-y" : undefined,
      snap === "both" ? "snap-both" : undefined,
      snapType === "mandatory" ? "snap-mandatory" : undefined,
      snapType === "proximity" ? "snap-proximity" : undefined,
      className
    ),
  };

  return (
    <Container
      {...(containerProps as React.ComponentProps<typeof Container>)}
      ref={ref}
    />
  );
}

const ScrollContainer: ContainerPolymorphicComponent<ScrollContainerExtras> =
  forwardRefWithAs<"div", ContainerBaseProps & ScrollContainerExtras>(
    ScrollContainerInner
  );

ScrollContainer.displayName = "ScrollContainer";

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
