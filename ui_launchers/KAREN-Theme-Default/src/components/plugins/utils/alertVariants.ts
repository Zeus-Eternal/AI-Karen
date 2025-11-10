"use client";

import { cn } from "@/lib/utils";

type AlertVariant = "default" | "destructive";

const variantClassMap: Record<AlertVariant, string> = {
  default: "",
  destructive:
    "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive",
};

export function alertClassName(
  variant?: AlertVariant | null,
  className?: string
) {
  if (!variant) {
    return cn(className);
  }

  const variantClasses = variantClassMap[variant] ?? "";
  return cn(variantClasses, className);
}

