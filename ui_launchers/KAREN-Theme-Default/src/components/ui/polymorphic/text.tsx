"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

import type {
  PolymorphicComponentPropWithRef,
  PolymorphicComponentWithDisplayName,
  PolymorphicRef,
} from "../compound/types";

export type TextVariant =
  | "default"
  | "muted"
  | "accent"
  | "destructive"
  | "success"
  | "warning";

export type TextSize =
  | "xs"
  | "sm"
  | "base"
  | "lg"
  | "xl"
  | "2xl"
  | "3xl"
  | "4xl";

export type TextWeight = "normal" | "medium" | "semibold" | "bold";

export type TextAlign = "left" | "center" | "right" | "justify";

type TextBaseProps = {
  variant?: TextVariant;
  size?: TextSize;
  weight?: TextWeight;
  align?: TextAlign;
  truncate?: boolean;
  italic?: boolean;
  underline?: boolean;
  children?: React.ReactNode;
  className?: string;
};

export type TextProps<T extends React.ElementType = "span"> =
  PolymorphicComponentPropWithRef<T, TextBaseProps>;

type TextComponent = PolymorphicComponentWithDisplayName<
  "span",
  TextBaseProps
>;

const variantClassMap: Record<TextVariant, string> = {
  default: "text-foreground",
  muted: "text-muted-foreground",
  accent: "text-accent-foreground",
  destructive: "text-destructive",
  success: "text-green-600 dark:text-green-400",
  warning: "text-yellow-600 dark:text-yellow-400",
};

const sizeClassMap: Record<TextSize, string> = {
  xs: "text-xs",
  sm: "text-sm",
  base: "text-base",
  lg: "text-lg",
  xl: "text-xl",
  "2xl": "text-2xl",
  "3xl": "text-3xl",
  "4xl": "text-4xl",
};

const weightClassMap: Record<TextWeight, string> = {
  normal: "font-normal",
  medium: "font-medium",
  semibold: "font-semibold",
  bold: "font-bold",
};

const alignClassMap: Record<TextAlign, string> = {
  left: "text-left",
  center: "text-center",
  right: "text-right",
  justify: "text-justify",
};

function TextInner<T extends React.ElementType = "span">(
  {
    as,
    className,
    variant = "default",
    size = "base",
    weight = "normal",
    align = "left",
    truncate = false,
    italic = false,
    underline = false,
    children,
    ...rest
  }: TextProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const Component = (as ?? "span") as T;
  const ComponentToRender = Component as React.ElementType;

  return (
    <ComponentToRender
      ref={ref as React.Ref<unknown>}
      className={cn(
        "transition-colors duration-200",
        variantClassMap[variant],
        sizeClassMap[size],
        weightClassMap[weight],
        alignClassMap[align],
        truncate ? "truncate" : undefined,
        italic ? "italic" : undefined,
        underline ? "underline" : undefined,
        className
      )}
      {...(rest as TextProps<any>)}
    >
      {children}
    </ComponentToRender>
  );
}

const Text = React.forwardRef(
  TextInner as unknown as React.ForwardRefRenderFunction<
    unknown,
    TextProps<any>
  >
) as TextComponent;

Text.displayName = "Text";

type HeadingLevel = "h1" | "h2" | "h3" | "h4" | "h5" | "h6";

type HeadingComponent = PolymorphicComponentWithDisplayName<
  HeadingLevel,
  TextBaseProps
>;

const headingDefaultSize: Record<HeadingLevel, TextSize> = {
  h1: "4xl",
  h2: "3xl",
  h3: "2xl",
  h4: "xl",
  h5: "lg",
  h6: "base",
};

export type HeadingProps<T extends HeadingLevel = "h1"> = TextProps<T>;

function HeadingInner<T extends HeadingLevel = "h1">(
  { as, size, weight = "bold", ...rest }: HeadingProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const element = as ?? ("h1" as T);
  const resolvedSize = size ?? headingDefaultSize[element as HeadingLevel];
  const BaseText = Text as unknown as React.ComponentType<any>;

  return (
    <BaseText
      ref={ref as React.Ref<unknown>}
      as={element}
      size={resolvedSize}
      weight={weight}
      {...(rest as TextProps<any>)}
    />
  );
}

const Heading = React.forwardRef(
  HeadingInner as unknown as React.ForwardRefRenderFunction<
    unknown,
    HeadingProps<any>
  >
) as HeadingComponent;

Heading.displayName = "Heading";

type ParagraphComponent = PolymorphicComponentWithDisplayName<
  "p",
  TextBaseProps
>;

export type ParagraphProps<T extends React.ElementType = "p"> = TextProps<T>;

function ParagraphInner<T extends React.ElementType = "p">(
  { as, size = "base", ...rest }: ParagraphProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const BaseText = Text as unknown as React.ComponentType<any>;
  return (
    <BaseText
      ref={ref as React.Ref<unknown>}
      as={(as ?? "p") as T}
      size={size}
      {...(rest as TextProps<any>)}
    />
  );
}

const Paragraph = React.forwardRef(
  ParagraphInner as unknown as React.ForwardRefRenderFunction<
    unknown,
    ParagraphProps<any>
  >
) as ParagraphComponent;

Paragraph.displayName = "Paragraph";

type LabelComponent = PolymorphicComponentWithDisplayName<
  "label",
  TextBaseProps
>;

export type LabelProps<T extends React.ElementType = "label"> = TextProps<T>;

function LabelInner<T extends React.ElementType = "label">(
  { as, size = "sm", weight = "medium", ...rest }: LabelProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const BaseText = Text as unknown as React.ComponentType<any>;
  return (
    <BaseText
      ref={ref as React.Ref<unknown>}
      as={(as ?? "label") as T}
      size={size}
      weight={weight}
      {...(rest as TextProps<any>)}
    />
  );
}

const Label = React.forwardRef(
  LabelInner as unknown as React.ForwardRefRenderFunction<
    unknown,
    LabelProps<any>
  >
) as LabelComponent;

Label.displayName = "Label";

type CaptionComponent = PolymorphicComponentWithDisplayName<
  "span",
  TextBaseProps
>;

export type CaptionProps<T extends React.ElementType = "span"> = TextProps<T>;

function CaptionInner<T extends React.ElementType = "span">(
  { as, size = "xs", variant = "muted", ...rest }: CaptionProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const BaseText = Text as unknown as React.ComponentType<any>;
  return (
    <BaseText
      ref={ref as React.Ref<unknown>}
      as={(as ?? "span") as T}
      size={size}
      variant={variant}
      {...(rest as TextProps<any>)}
    />
  );
}

const Caption = React.forwardRef(
  CaptionInner as unknown as React.ForwardRefRenderFunction<
    unknown,
    CaptionProps<any>
  >
) as CaptionComponent;

Caption.displayName = "Caption";

type CodeComponent = PolymorphicComponentWithDisplayName<
  "code",
  TextBaseProps
>;

export type CodeProps<T extends React.ElementType = "code"> = TextProps<T>;

function CodeInner<T extends React.ElementType = "code">(
  { as, className, ...rest }: CodeProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const BaseText = Text as unknown as React.ComponentType<any>;
  return (
    <BaseText
      ref={ref as React.Ref<unknown>}
      as={(as ?? "code") as T}
      className={cn(
        "relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold",
        className
      )}
      {...(rest as TextProps<any>)}
    />
  );
}

const Code = React.forwardRef(
  CodeInner as unknown as React.ForwardRefRenderFunction<
    unknown,
    CodeProps<any>
  >
) as CodeComponent;

Code.displayName = "Code";

export { Text, Heading, Paragraph, Label, Caption, Code };
