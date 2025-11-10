import * as React from "react"
import type { FieldPath, FieldValues } from "react-hook-form"

// Base component props
export interface BaseComponentProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode
}

export interface BaseCardProps extends BaseComponentProps {}

// Card compound component types
export interface CardRootProps extends BaseCardProps {
  interactive?: boolean
  variant?: "default" | "elevated" | "outlined" | "glass"
}

export interface CardActionsProps extends BaseCardProps {
  justify?: "start" | "center" | "end" | "between"
}

export type CardProps = CardRootProps

// Modal compound component types
export interface BaseModalProps extends BaseComponentProps {}

export interface ModalRootProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  modal?: boolean
}

export interface ModalTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
}

export interface ModalContentProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "md" | "lg" | "xl" | "full"
  showCloseButton?: boolean
}

export interface ModalActionsProps extends BaseModalProps {
  justify?: "start" | "center" | "end" | "between"
}

export type ModalProps = ModalContentProps & Partial<ModalRootProps>

// Form compound component types
export interface FormFieldProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> {
  name: TName
  control?: any
  render: ({ field }: { field: any }) => React.ReactElement
  defaultValue?: any
  rules?: any
}

export interface FormLabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean
}

export interface FormErrorProps extends React.HTMLAttributes<HTMLParagraphElement> {
  error?: string | string[]
}

export interface FormGroupProps extends BaseComponentProps {
  orientation?: "vertical" | "horizontal"
}

export interface FormActionsProps extends BaseComponentProps {
  justify?: "start" | "center" | "end" | "between"
  sticky?: boolean
}

// Compound component pattern types
export interface CompoundComponentProps {
  children: React.ReactNode
}

// Polymorphic component types
export type PolymorphicRef<T extends React.ElementType> = React.ComponentPropsWithRef<T>["ref"]

export type PolymorphicComponentProp<T extends React.ElementType, Props = {}> = {
  as?: T
} & Props &
  Omit<React.ComponentPropsWithoutRef<T>, keyof Props | "as">

export type PolymorphicComponentPropWithRef<
  T extends React.ElementType,
  Props = {}
> = PolymorphicComponentProp<T, Props> & { ref?: PolymorphicRef<T> }

// Enhanced polymorphic types with better inference
export type PolymorphicPropsWithoutRef<
  T extends React.ElementType,
  Props = {}
> = Props & Omit<React.ComponentPropsWithoutRef<T>, keyof Props>

export type PolymorphicPropsWithRef<
  T extends React.ElementType,
  Props = {}
> = PolymorphicPropsWithoutRef<T, Props> & {
  ref?: PolymorphicRef<T>
}

// Utility type for creating polymorphic components
export type CreatePolymorphicComponent<
  DefaultElement extends React.ElementType,
  Props = {}
> = <T extends React.ElementType = DefaultElement>(
  props: { as?: T } & PolymorphicPropsWithRef<T, Props>
) => React.ReactElement | null

export type PolymorphicComponentWithDisplayName<
  DefaultElement extends React.ElementType,
  Props = {}
> = CreatePolymorphicComponent<DefaultElement, Props> & {
  displayName?: string
}

// Polymorphic component factory type
export interface PolymorphicComponentFactory {
  <T extends React.ElementType = "div">(
    props: PolymorphicComponentPropWithRef<T, any>
  ): React.ReactElement | null
}

// Animation and interaction types
export interface AnimationProps {
  animate?: boolean
  duration?: number
  easing?: string
}

export interface InteractionProps {
  // Note: onFocus, onBlur, and disabled are already included in HTMLAttributes
  // Only include additional interaction props not covered by HTMLAttributes
  onHover?: () => void
}

// Responsive and accessibility types
export interface ResponsiveProps {
  breakpoint?: "sm" | "md" | "lg" | "xl"
  responsive?: boolean
}

export interface AccessibilityProps {
  // Note: aria-expanded, aria-controls, and role are already included in HTMLAttributes
  // Only include additional accessibility props not covered by HTMLAttributes
  "aria-label"?: string
  "aria-describedby"?: string
}

// Combined props for enhanced components
export interface EnhancedComponentProps
  extends BaseComponentProps,
    AccessibilityProps {}

// Utility types for compound components
export type CompoundComponent<T> = T & {
  displayName?: string
}

export type CompoundComponentCollection<T extends Record<string, any>> = {
  [K in keyof T]: CompoundComponent<T[K]>
}

// Context types for compound components
export interface CompoundContextValue {
  id: string
  disabled?: boolean
  size?: "sm" | "md" | "lg"
  variant?: string
}

// Event handler types
export type EventHandler<T = HTMLElement> = (event: React.SyntheticEvent<T>) => void
export type ChangeHandler<T = HTMLInputElement> = (event: React.ChangeEvent<T>) => void
export type ClickHandler<T = HTMLButtonElement> = (event: React.MouseEvent<T>) => void
export type KeyboardHandler<T = HTMLElement> = (event: React.KeyboardEvent<T>) => void

// State management types for compound components
export interface ComponentState {
  isOpen?: boolean
  isLoading?: boolean
  isDisabled?: boolean
  isActive?: boolean
  hasError?: boolean
}

export interface ComponentActions {
  open?: () => void
  close?: () => void
  toggle?: () => void
  reset?: () => void
  submit?: () => void
}

// Theme and styling types
export interface ThemeProps {
  theme?: "light" | "dark" | "system"
  colorScheme?: "primary" | "secondary" | "accent" | "neutral"
}

export interface StylingProps {
  className?: string
  style?: React.CSSProperties
  variant?: string
  size?: "xs" | "sm" | "md" | "lg" | "xl"
}

// Combined enhanced props
export interface FullyEnhancedProps
  extends EnhancedComponentProps,
    ComponentActions {}
