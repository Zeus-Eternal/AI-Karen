"use client"

import * as React from "react";
import * as LabelPrimitive from "@radix-ui/react-label";
import { Slot } from "@radix-ui/react-slot";
import {
  Controller,
  FormProvider,
  useFormContext,
  type ControllerProps,
  type FieldPath,
  type FieldValues,
} from "react-hook-form";
import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";
// Base types for form compound components
export interface BaseFormProps extends React.HTMLAttributes<HTMLDivElement> {}

export interface FormFieldProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> extends ControllerProps<TFieldValues, TName> {}

export interface FormLabelProps extends React.ComponentPropsWithoutRef<typeof LabelPrimitive.Root> {
  required?: boolean
}

export interface FormErrorProps extends React.HTMLAttributes<HTMLParagraphElement> {
  error?: string | string[]
}

export interface FormGroupProps extends BaseFormProps {
  orientation?: "vertical" | "horizontal"
}

export interface FormActionsProps extends BaseFormProps {
  justify?: "start" | "center" | "end" | "between"
  sticky?: boolean
}

// Form context types
export type FormFieldContextValue<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> = {
  name: TName
}

export type FormItemContextValue = {
  id: string
}

// Form contexts
const FormFieldContext = React.createContext<FormFieldContextValue | undefined>(undefined)

const FormItemContext = React.createContext<FormItemContextValue | undefined>(undefined)

// Form Root Component
const FormRoot = FormProvider
// Note: FormProvider from react-hook-form doesn't support displayName assignment

// Form Field Component
const FormField = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
>({
  ...props
}: FormFieldProps<TFieldValues, TName>) => {
  return (
    <FormFieldContext.Provider value={{ name: props.name }}>
      <Controller {...props} />
    </FormFieldContext.Provider>
  )
}
FormField.displayName = "FormField"

// Custom hook for form field
const useFormField = () => {
  const fieldContext = React.useContext(FormFieldContext)
  if (!fieldContext) {
    throw new Error("useFormField should be used within <FormField>")
  }

  const itemContext = React.useContext(FormItemContext)
  const formContext = useFormContext()
  const { getFieldState, formState } = formContext
  const fieldState = getFieldState(fieldContext.name, formState)

  const id = itemContext?.id ?? fieldContext.name

  return {
    id,
    name: fieldContext.name,
    formItemId: `${id}-form-item`,
    formDescriptionId: `${id}-form-item-description`,
    formMessageId: `${id}-form-item-message`,
    ...fieldState,
  }
}

// Form Group Component
const FormGroup = React.forwardRef<HTMLDivElement, FormGroupProps>(
  ({ className, orientation = "vertical", ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "space-y-4",
        {
          "space-y-4": orientation === "vertical",
          "flex flex-wrap gap-4": orientation === "horizontal",
        },
        className
      )}
      {...props}
    />
  )
)
FormGroup.displayName = "FormGroup"

// Form Item Component
const FormItem = React.forwardRef<HTMLDivElement, BaseFormProps>(
  ({ className, ...props }, ref) => {
    const id = React.useId()

    return (
      <FormItemContext.Provider value={{ id }}>
        <div ref={ref} className={cn("space-y-2", className)} {...props} />
      </FormItemContext.Provider>
    )
  }
)
FormItem.displayName = "FormItem"

// Form Label Component
const FormLabel = React.forwardRef<
  React.ElementRef<typeof LabelPrimitive.Root>,
>(({ className, required = false, children, ...props }, ref) => {
  const { error, formItemId } = useFormField()

  return (
    <Label
      ref={ref}
      className={cn(
        "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
        error && "text-destructive",
        className
      )}
      htmlFor={formItemId}
      {...props}
    >
      {children}
      {required && <span className="text-destructive ml-1">*</span>}
    </Label>
  )
})
FormLabel.displayName = "FormLabel"

// Form Control Component
const FormControl = React.forwardRef<
  React.ElementRef<typeof Slot>,
  React.ComponentPropsWithoutRef<typeof Slot>
>(({ ...props }, ref) => {
  const { error, formItemId, formDescriptionId, formMessageId } = useFormField()

  return (
    <Slot
      ref={ref}
      id={formItemId}
      aria-describedby={
        !error
          ? `${formDescriptionId}`
          : `${formDescriptionId} ${formMessageId}`
      }
      aria-invalid={!!error}
      {...props}
    />
  )
})
FormControl.displayName = "FormControl"

// Form Description Component
const FormDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => {
    const { formDescriptionId } = useFormField()

    return (
      <p
        ref={ref}
        id={formDescriptionId}
        className={cn("text-sm text-muted-foreground", className)}
        {...props}
      />
    )
  }
)
FormDescription.displayName = "FormDescription"

// Form Error Component
const FormError = React.forwardRef<HTMLParagraphElement, FormErrorProps>(
  ({ className, error, children, ...props }, ref) => {
    const { error: fieldError, formMessageId } = useFormField()
    const displayError = error || fieldError?.message
    const body = displayError ? String(displayError) : children

    if (!body) {
      return null
    }

    return (
      <p
        ref={ref}
        id={formMessageId}
        className={cn("text-sm font-medium text-destructive", className)}
        {...props}
      >
        {body}
      </p>
    )
  }
)
FormError.displayName = "FormError"

// Form Actions Component
const FormActions = React.forwardRef<HTMLDivElement, FormActionsProps>(
  ({ className, justify = "end", sticky = false, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flex-col-reverse sm:flex-row sm:space-x-2 pt-4",
        {
          "sm:justify-start": justify === "start",
          "sm:justify-center": justify === "center",
          "sm:justify-end": justify === "end",
          "sm:justify-between": justify === "between",
          "sticky bottom-0 bg-background border-t p-4 -mx-6 -mb-6": sticky,
        },
        className
      )}
      {...props}
    />
  )
)
FormActions.displayName = "FormActions"

// Form Section Component
const FormSection = React.forwardRef<HTMLFieldSetElement, React.FieldsetHTMLAttributes<HTMLFieldSetElement>>(
  ({ className, ...props }, ref) => (
    <fieldset
      ref={ref}
      className={cn("space-y-4 border rounded-lg p-4", className)}
      {...props}
    />
  )
)
FormSection.displayName = "FormSection"

// Form Legend Component
const FormLegend = React.forwardRef<HTMLLegendElement, React.HTMLAttributes<HTMLLegendElement>>(
  ({ className, ...props }, ref) => (
    <legend
      ref={ref}
      className={cn("text-sm font-medium px-2 -ml-2", className)}
      {...props}
    />
  )
)
FormLegend.displayName = "FormLegend"

// Compound Form Component
const Form = {
  Root: FormRoot,
  Field: FormField,
  Group: FormGroup,
  Item: FormItem,
  Label: FormLabel,
  Control: FormControl,
  Description: FormDescription,
  Error: FormError,
  Actions: FormActions,
  Section: FormSection,
  Legend: FormLegend,
}

const FormDefault = Form

export {
  Form,
  FormRoot,
  FormField,
  FormGroup,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormError,
  FormActions,
  FormSection,
  FormLegend,
  useFormField,
}

export default FormDefault;
