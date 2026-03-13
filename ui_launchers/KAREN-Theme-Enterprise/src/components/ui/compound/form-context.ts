"use client";

import * as React from "react";
import {
  useFormContext,
  type FieldPath,
  type FieldValues,
} from "react-hook-form";

export type FormFieldContextValue<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> = {
  name: TName;
};

export type FormItemContextValue = {
  id: string;
};

export const FormFieldContext =
  React.createContext<FormFieldContextValue | undefined>(undefined);

export const FormItemContext =
  React.createContext<FormItemContextValue | undefined>(undefined);

export const useFormField = () => {
  const fieldContext = React.useContext(FormFieldContext);
  if (!fieldContext) {
    throw new Error("useFormField should be used within <FormField>");
  }

  const itemContext = React.useContext(FormItemContext);
  const formContext = useFormContext();
  const { getFieldState, formState } = formContext;
  const fieldState = getFieldState(fieldContext.name, formState);

  const id = itemContext?.id ?? fieldContext.name;

  return {
    id,
    name: fieldContext.name,
    formItemId: `${id}-form-item`,
    formDescriptionId: `${id}-form-item-description`,
    formMessageId: `${id}-form-item-message`,
    ...fieldState,
  };
};
