"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";

import { cn } from "@/lib/utils";

import type {
  PolymorphicComponentPropWithRef,
  PolymorphicComponentWithDisplayName,
  PolymorphicRef,
} from "../compound/types";

export type ButtonVariant =
  | "default"
  | "destructive"
  | "outline"
  | "secondary"
  | "ghost"
  | "link";

export type ButtonSize = "xs" | "sm" | "md" | "lg" | "xl";

type ButtonBaseProps = {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  asChild?: boolean;
  fullWidth?: boolean;
  children?: React.ReactNode;
  className?: string;
};

export type ButtonProps<T extends React.ElementType = "button"> =
  PolymorphicComponentPropWithRef<T, ButtonBaseProps>;

type ButtonComponent = PolymorphicComponentWithDisplayName<
  "button",
  ButtonBaseProps
>;

const variantClasses: Record<ButtonVariant, string> = {
  default: "bg-primary text-primary-foreground hover:bg-primary/90",
  destructive:
    "bg-destructive text-destructive-foreground hover:bg-destructive/90",
  outline:
    "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
  secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
  ghost: "hover:bg-accent hover:text-accent-foreground",
  link: "text-primary underline-offset-4 hover:underline",
};

const sizeClasses: Record<ButtonSize, string> = {
  xs: "h-7 px-2 text-xs",
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 py-2",
  lg: "h-11 px-8",
  xl: "h-12 px-10 text-lg",
};

const iconSizeClasses: Record<ButtonSize, string> = {
  xs: "h-7 w-7",
  sm: "h-8 w-8",
  md: "h-10 w-10",
  lg: "h-11 w-11",
  xl: "h-12 w-12",
};

function ButtonInner<T extends React.ElementType = "button">(
  {
    as,
    asChild = false,
    className,
    variant = "default",
    size = "md",
    loading = false,
    disabled,
    fullWidth = false,
    children,
    ...props
  }: ButtonProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const Component = asChild ? Slot : (as ?? "button");
  const isButtonElement = typeof Component === "string" && Component === "button";
  const isDisabled = (disabled ?? false) || loading;
  const ComponentToRender = Component as React.ElementType;

  return (
    <ComponentToRender
      ref={ref as React.Ref<unknown>}
      className={cn(
        "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium",
        "ring-offset-background transition-colors duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-50",
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && "w-full",
        loading && "cursor-not-allowed",
        className
      )}
      aria-busy={loading || undefined}
      disabled={isButtonElement ? isDisabled : undefined}
      data-variant={variant}
      data-size={size}
      {...(props as ButtonProps<any>)}
    >
      {loading && (
        <svg
          className="-ml-1 mr-2 h-4 w-4 animate-spin"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
          focusable="false"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 0 1 4 12H0c0 3.042 1.135 5.824 3 7.938z"
            fill="currentColor"
          />
        </svg>
      )}
      {children}
    </ComponentToRender>
  );
}

const Button = React.forwardRef(
  ButtonInner as unknown as React.ForwardRefRenderFunction<
    unknown,
    ButtonProps<any>
  >
) as ButtonComponent;

Button.displayName = "Button";

type IconButtonProps = ButtonProps & {
  icon: React.ReactNode;
  "aria-label": string;
};

const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ icon, children, className, size = "md", ...props }, ref) => (
    <Button
      ref={ref}
      size={size}
      className={cn("aspect-square p-0", iconSizeClasses[size], className)}
      {...props}
    >
      {icon}
      {children && <span className="sr-only">{children}</span>}
    </Button>
  )
);

IconButton.displayName = "IconButton";

type LinkButtonProps<T extends React.ElementType = "a"> = ButtonProps<T> & {
  href?: string;
};

type LinkButtonComponent = PolymorphicComponentWithDisplayName<
  "a",
  ButtonBaseProps & { href?: string }
>;

function LinkButtonInner<T extends React.ElementType = "a">(
  {
    as,
    variant = "link",
    children,
    ...props
  }: LinkButtonProps<T>,
  ref: PolymorphicRef<T>
): React.ReactElement | null {
  const BaseButton = Button as unknown as React.ComponentType<any>;
  return (
    <BaseButton
      as={as ?? ("a" as T)}
      ref={ref as React.Ref<unknown>}
      variant={variant}
      {...(props as ButtonProps<any>)}
    >
      {children}
    </BaseButton>
  );
}

const LinkButton = React.forwardRef(
  LinkButtonInner as unknown as React.ForwardRefRenderFunction<
    unknown,
    LinkButtonProps<any>
  >
) as LinkButtonComponent;

LinkButton.displayName = "LinkButton";

const SubmitButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ type = "submit", variant = "default", ...props }, ref) => (
    <Button ref={ref} type={type} variant={variant} {...props} />
  )
);

SubmitButton.displayName = "SubmitButton";

const ResetButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ type = "reset", variant = "outline", ...props }, ref) => (
    <Button ref={ref} type={type} variant={variant} {...props} />
  )
);

ResetButton.displayName = "ResetButton";

const CancelButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "ghost", children = "Cancel", ...props }, ref) => (
    <Button ref={ref} variant={variant} {...props}>
      {children}
    </Button>
  )
);

CancelButton.displayName = "CancelButton";

const DestructiveButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "destructive", ...props }, ref) => (
    <Button ref={ref} variant={variant} {...props} />
  )
);

DestructiveButton.displayName = "DestructiveButton";

export {
  Button,
  IconButton,
  LinkButton,
  SubmitButton,
  ResetButton,
  CancelButton,
  DestructiveButton,
};
