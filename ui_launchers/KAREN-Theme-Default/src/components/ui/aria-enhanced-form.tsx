/**
 * ARIA Enhanced Form Components
 * Extends the base form components with comprehensive accessibility features
 */

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
import {
  createFormAria,
  mergeAriaProps,
  type AriaProps,
} from "@/utils/aria";
import { AriaLiveRegion, AriaStatus } from "./aria-live-region";

// Re-export the base Form provider
const AriaEnhancedForm = FormProvider;

export type FormFieldContextValue<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> = {
  name: TName;
  required?: boolean;
  helpText?: string;
  errorAnnouncement?: boolean;
};

const FormFieldContext = React.createContext<FormFieldContextValue | null>(null);

/**
 * Enhanced FormField with ARIA support
 */
const AriaEnhancedFormField = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
>({
  required = false,
  helpText,
  errorAnnouncement = true,
  ...props
}: ControllerProps<TFieldValues, TName> & {
  required?: boolean;
  helpText?: string;
  errorAnnouncement?: boolean;
}) => {
  return (
    <FormFieldContext.Provider value={{ 
      name: props.name, 
      required, 
      helpText,
      errorAnnouncement 
    }}>
      <Controller {...props} />
    </FormFieldContext.Provider>
  );
};

/**
 * Enhanced useFormField hook with ARIA support
 */
const useAriaFormField = () => {
  const fieldContext = React.useContext(FormFieldContext);
  const itemContext = React.useContext(FormItemContext);
  const { getFieldState, formState } = useFormContext();

  if (!fieldContext) {
    throw new Error("useAriaFormField should be used within <AriaEnhancedFormField>");
  }

  if (!itemContext) {
    throw new Error("useAriaFormField should be used within <AriaEnhancedFormItem>");
  }

  const fieldState = getFieldState(fieldContext.name, formState);

  const { id } = itemContext;

  return {
    id,
    name: fieldContext.name,
    formItemId: `${id}-form-item`,
    formDescriptionId: `${id}-form-item-description`,
    formMessageId: `${id}-form-item-message`,
    formHelpId: `${id}-form-item-help`,
    required: fieldContext.required,
    helpText: fieldContext.helpText,
    errorAnnouncement: fieldContext.errorAnnouncement,
    ...fieldState,
  };
};

export type FormItemContextValue = {
  id: string;
};

const FormItemContext = React.createContext<FormItemContextValue | null>(null);

/**
 * Enhanced FormItem with proper ARIA structure
 */
const AriaEnhancedFormItem = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    /** Custom ARIA props */
    ariaProps?: Partial<AriaProps>;
  }
>(({ className, ariaProps, ...props }, ref) => {
  const id = React.useId();

  return (
    <FormItemContext.Provider value={{ id }}>
      <div 
        ref={ref} 
        className={cn("space-y-2", className)} 
        role="group"
        {...(() => {
          const merged = mergeAriaProps(ariaProps);
          const { 'aria-relevant': _, ...safeProps } = merged;
          return safeProps;
        })()}
        {...props}
      />
    </FormItemContext.Provider>
  );
});

AriaEnhancedFormItem.displayName = "AriaEnhancedFormItem";

/**
 * Enhanced FormLabel with ARIA support
 */
const AriaEnhancedFormLabel = React.forwardRef<
  React.ElementRef<typeof LabelPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof LabelPrimitive.Root> & {
    /** Whether this field is required */
    showRequired?: boolean;
    /** Custom required indicator */
    requiredIndicator?: React.ReactNode;
  }
>(({ className, showRequired, requiredIndicator = " *", children, ...props }, ref) => {
  const { error, formItemId, required } = useAriaFormField();
  const shouldShowRequired = showRequired ?? required;

  return (
    <Label
      ref={ref}
      className={cn(
        error && "text-destructive",
        "font-medium",
        className
      )}
      htmlFor={formItemId}
      {...props}
    >
      {children}
      {shouldShowRequired && (
        <span 
          className="text-destructive ml-1" 
          aria-label="required"
          title="This field is required"
        >
          {requiredIndicator}
        </span>
      )}
    </Label>
  );
});

AriaEnhancedFormLabel.displayName = "AriaEnhancedFormLabel";

/**
 * Enhanced FormControl with comprehensive ARIA support
 */
const AriaEnhancedFormControl = React.forwardRef<
  React.ElementRef<typeof Slot>,
  React.ComponentPropsWithoutRef<typeof Slot> & {
    /** Custom ARIA props */
    ariaProps?: Partial<AriaProps>;
  }
>(({ ariaProps, ...props }, ref) => {
  const { 
    error, 
    formItemId, 
    formDescriptionId, 
    formMessageId, 
    formHelpId,
    required,
    helpText 
  } = useAriaFormField();

  // Build describedBy string
  const describedByParts: string[] = [];
  if (helpText) describedByParts.push(formHelpId);
  if (!error) describedByParts.push(formDescriptionId);
  if (error) describedByParts.push(formDescriptionId, formMessageId);

  const formAriaProps = createFormAria(
    !!error,
    required,
    describedByParts.join(' '),
    error ? formMessageId : undefined
  );

  return (
    <Slot
      ref={ref}
      id={formItemId}
      {...(() => {
        const merged = mergeAriaProps(formAriaProps, ariaProps);
        const { 'aria-relevant': _, ...safeProps } = merged;
        return safeProps;
      })()}
      {...props}
    />
  );
});

AriaEnhancedFormControl.displayName = "AriaEnhancedFormControl";

/**
 * Enhanced FormDescription with ARIA support
 */
const AriaEnhancedFormDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => {
  const { formDescriptionId } = useAriaFormField();

  return (
    <p
      ref={ref}
      id={formDescriptionId}
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  );
});

AriaEnhancedFormDescription.displayName = "AriaEnhancedFormDescription";

/**
 * Enhanced FormMessage with live announcements
 */
const AriaEnhancedFormMessage = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement> & {
    /** Whether to announce errors to screen readers */
    announceError?: boolean;
  }
>(({ className, children, announceError, ...props }, ref) => {
  const { error, formMessageId, errorAnnouncement } = useAriaFormField();
  const body = error ? String(error?.message ?? "") : children;
  const shouldAnnounce = announceError ?? errorAnnouncement;

  if (!body) {
    return null;
  }

  return (
    <>
      <p
        ref={ref}
        id={formMessageId}
        role={error ? "alert" : undefined}
        aria-live={error ? "assertive" : undefined}
        className={cn("text-sm font-medium text-destructive", className)}
        {...props}
      >
        {body}
      </p>
      {error && shouldAnnounce && (
        <AriaStatus 
          message={String(body)} 
          error={true}
        />
      )}
    </>
  );
});

AriaEnhancedFormMessage.displayName = "AriaEnhancedFormMessage";

/**
 * FormHelp - Additional help text component
 */
const AriaFormHelp = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => {
  const { formHelpId } = useAriaFormField();

  return (
    <p
      ref={ref}
      id={formHelpId}
      className={cn("text-xs text-muted-foreground", className)}
      {...props}
    />
  );
});

AriaFormHelp.displayName = "AriaFormHelp";

/**
 * FormFieldset - Grouping related form fields
 */
export interface AriaFormFieldsetProps extends React.FieldsetHTMLAttributes<HTMLFieldSetElement> {
  /** Legend for the fieldset */
  legend?: string;
  /** Whether the legend should be visually hidden */
  hideLegend?: boolean;
  /** Description for the fieldset */
  description?: string;
}

const AriaFormFieldset = React.forwardRef<HTMLFieldSetElement, AriaFormFieldsetProps>(
  ({ className, legend, hideLegend = false, description, children, ...props }, ref) => {
    const descriptionId = React.useId();

    return (
      <fieldset
        ref={ref}
        className={cn("border border-border rounded-lg p-4 space-y-4", className)}
        aria-describedby={description ? descriptionId : undefined}
        {...props}
      >
        {legend && (
          <legend 
            className={cn(
              "text-sm font-medium px-2 -ml-2",
              hideLegend && "sr-only"
            )}
          >
            {legend}
          </legend>
        )}
        {description && (
          <p 
            id={descriptionId}
            className="text-sm text-muted-foreground -mt-2 md:text-base lg:text-lg"
          >
            {description}
          </p>
        )}
        {children}
      </fieldset>
    );
  }
);
AriaFormFieldset.displayName = "AriaFormFieldset";

/**
 * FormSection - Semantic section for forms
 */
export interface AriaFormSectionProps extends React.HTMLAttributes<HTMLElement> {
  /** Heading for the section */
  heading?: string;
  /** Heading level (1-6) */
  headingLevel?: 1 | 2 | 3 | 4 | 5 | 6;
  /** Description for the section */
  description?: string;
}

const AriaFormSection = React.forwardRef<HTMLElement, AriaFormSectionProps>(
  ({ className, heading, headingLevel = 2, description, children, ...props }, ref) => {
    const headingId = React.useId();
    const descriptionId = React.useId();
    const HeadingTag = `h${headingLevel}` as keyof JSX.IntrinsicElements;

    return (
      <section
        ref={ref}
        className={cn("space-y-4", className)}
        aria-labelledby={heading ? headingId : undefined}
        aria-describedby={description ? descriptionId : undefined}
        {...props}
      >
        {heading && (
          <HeadingTag 
            id={headingId}
            className="text-lg font-semibold"
          >
            {heading}
          </HeadingTag>
        )}
        {description && (
          <p 
            id={descriptionId}
            className="text-sm text-muted-foreground md:text-base lg:text-lg"
          >
            {description}
          </p>
        )}
        {children}
      </section>
    );
  }
);
AriaFormSection.displayName = "AriaFormSection";

const AriaFormField = AriaEnhancedFormField;
const AriaFormItem = AriaEnhancedFormItem;
const AriaFormLabel = AriaEnhancedFormLabel;
const AriaFormControl = AriaEnhancedFormControl;
const AriaFormDescription = AriaEnhancedFormDescription;
const AriaFormMessage = AriaEnhancedFormMessage;

export {
  AriaEnhancedForm as Form,
  useAriaFormField,
  AriaEnhancedFormField,
  AriaEnhancedFormItem,
  AriaEnhancedFormLabel,
  AriaEnhancedFormControl,
  AriaEnhancedFormDescription,
  AriaEnhancedFormMessage,
  AriaFormField,
  AriaFormItem,
  AriaFormLabel,
  AriaFormControl,
  AriaFormDescription,
  AriaFormMessage,
  AriaFormHelp,
  AriaFormFieldset,
  AriaFormSection,
};
