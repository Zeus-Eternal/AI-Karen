"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface VerticalSeparatorProps {
  className?: string;
}

export const VerticalSeparator: React.FC<VerticalSeparatorProps> = ({
  className,
}) => (
  <div aria-hidden="true" className={cn("w-px bg-border", className)} />
);

