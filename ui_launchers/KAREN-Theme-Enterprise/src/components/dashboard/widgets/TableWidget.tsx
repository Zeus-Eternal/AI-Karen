"use client";

import React from "react";
import { AlertCircle } from "lucide-react";

import type { WidgetProps } from "@/types/dashboard";

const TablePlaceholderIcon = AlertCircle;

const TableWidget: React.FC<WidgetProps> = ({ config }) => {
  return (
    <div
      className="flex h-full items-center justify-center text-muted-foreground"
      role="region"
      aria-label="Table widget placeholder"
    >
      <div className="text-center">
        <TablePlaceholderIcon className="mx-auto mb-2 h-8 w-8" aria-hidden />
        <p className="text-sm md:text-base lg:text-lg">Table Widget</p>
        <p className="text-xs sm:text-sm md:text-base">{config.title}</p>
      </div>
    </div>
  );
};

export default TableWidget;
