// ui_launchers/KAREN-Theme-Default/src/components/dashboard/DashboardFilters.tsx
"use client";

import React, { useEffect, useMemo, useState } from "react";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";

import { Filter, X, Plus, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";

import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  SelectLabel,
  SelectGroup,
  SelectSeparator,
} from "@/components/ui/select";

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

import { cn } from "@/lib/utils";
import type { DashboardFilter } from "@/types/dashboard";

interface DashboardFiltersProps {
  filters: DashboardFilter[];
  onFiltersChange: (filters: DashboardFilter[]) => void;
  availableFilterTypes?: FilterTypeConfig[];
  className?: string;
}

interface FilterTypeConfig {
  type: DashboardFilter["type"];
  label: string;
  description: string;
  valueType: "text" | "select" | "multiselect" | "number" | "date";
  options?: Array<{ value: string; label: string }>;
}

const defaultFilterTypes: FilterTypeConfig[] = [
  {
    type: "category",
    label: "Category",
    description: "Filter by data category",
    valueType: "select",
    options: [
      { value: "system", label: "System" },
      { value: "performance", label: "Performance" },
      { value: "security", label: "Security" },
      { value: "user", label: "User Activity" },
    ],
  },
  {
    type: "status",
    label: "Status",
    description: "Filter by status",
    valueType: "select",
    options: [
      { value: "healthy", label: "Healthy" },
      { value: "warning", label: "Warning" },
      { value: "critical", label: "Critical" },
      { value: "unknown", label: "Unknown" },
    ],
  },
  {
    type: "custom",
    label: "Custom Filter",
    description: "Create a custom key/value filter",
    valueType: "text",
  },
];

export const DashboardFilters: React.FC<DashboardFiltersProps> = ({
  filters,
  onFiltersChange,
  availableFilterTypes = defaultFilterTypes,
  className,
}) => {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newFilter, setNewFilter] = useState<Partial<DashboardFilter>>({
    type: "category" as DashboardFilter["type"],
    enabled: true,
    name: "",
    value: "",
  });

  const activeFilters = useMemo(
    () => filters.filter((f) => f.enabled),
    [filters]
  );
  const inactiveFilters = useMemo(
    () => filters.filter((f) => !f.enabled),
    [filters]
  );

  const getFilterTypeConfig = (type: DashboardFilter["type"]) =>
    availableFilterTypes.find((config) => config.type === type);

  const handleAddFilter = () => {
    if (!newFilter.name || !newFilter.type) return;

    const filter: DashboardFilter = {
      id: `filter-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      name: newFilter.name!,
      type: newFilter.type as DashboardFilter["type"],
      value: newFilter.value ?? "",
      enabled: newFilter.enabled ?? true,
    };

    onFiltersChange([...filters, filter]);
    setNewFilter({ type: "category", enabled: true, name: "", value: "" });
    setIsAddDialogOpen(false);
  };

  const handleUpdateFilter = (
    id: string,
    updates: Partial<DashboardFilter>
  ) => {
    onFiltersChange(
      filters.map((filter) => (filter.id === id ? { ...filter, ...updates } : filter))
    );
  };

  const handleRemoveFilter = (id: string) => {
    onFiltersChange(filters.filter((f) => f.id !== id));
  };

  const handleToggleFilter = (id: string) => {
    const target = filters.find((f) => f.id === id);
    if (!target) return;
    handleUpdateFilter(id, { enabled: !target.enabled });
  };

  const renderFilterValue = (filter: DashboardFilter) => {
    const config = getFilterTypeConfig(filter.type);
    if (!config) return String(filter.value ?? "");

    if (config.valueType === "select" && config.options) {
      const opt = config.options.find((o) => o.value === String(filter.value));
      return opt?.label ?? String(filter.value ?? "");
    }

    if (config.valueType === "multiselect") {
      const values = Array.isArray(filter.value)
        ? filter.value
        : String(filter.value ?? "")
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean);

      if (config.options && config.options.length > 0) {
        const map = new Map(config.options.map((o) => [o.value, o.label]));
        return values.map((v) => map.get(v) ?? v).join(", ");
      }
      return values.join(", ");
    }

    return String(filter.value ?? "");
  };

  const renderFilterInput = (
    value: unknown,
    onChange: (val: unknown) => void,
    config: FilterTypeConfig
  ) => {
    switch (config.valueType) {
      case "select":
        return (
          <Select
            value={String(value ?? "")}
            onValueChange={(v) => onChange(v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select value..." />
            </SelectTrigger>
            <SelectContent>
              {config.options?.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case "multiselect": {
        // Production-safe simple tags input (comma-separated)
        return (
          <Input
            value={
              Array.isArray(value) ? value.join(", ") : String(value ?? "")
            }
            onChange={(e) =>
              onChange(
                e.target.value
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean)
              )
            }
            placeholder="Enter comma-separated values"
          />
        );
      }

      case "number":
        return (
          <Input
            type="number"
            value={
              typeof value === "number"
                ? value
                : value
                ? Number(value)
                : ("" as any)
            }
            onChange={(e) => {
              const v = e.target.value;
              onChange(v === "" ? "" : Number.isNaN(Number(v)) ? "" : Number(v));
            }}
            placeholder="Enter number…"
            inputMode="decimal"
          />
        );

      case "date":
        return (
          <Input
            type="date"
            value={String(value ?? "")}
            onChange={(e) => onChange(e.target.value)}
          />
        );

      default:
        return (
          <Input
            value={String(value ?? "")}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Enter value…"
          />
        );
    }
  };

  // Close the Add dialog with Escape, scoped to open state
  useEffect(() => {
    if (!isAddDialogOpen) return;
    const onKey = (ev: KeyboardEvent) => {
      if (ev.key === "Escape") setIsAddDialogOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [isAddDialogOpen]);

  return (
    <ErrorBoundary fallback={<div>Something went wrong in DashboardFilters</div>}>
      <div className={cn("space-y-3", className)}>
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium md:text-base lg:text-lg">Filters</span>
            {activeFilters.length > 0 && (
              <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                {activeFilters.length} active
              </Badge>
            )}
          </div>

          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" aria-label="Add filter">
                <Plus className="h-3 w-3 mr-1" />
                Add
              </Button>
            </DialogTrigger>

            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Add Filter</DialogTitle>
              </DialogHeader>

              <div className="space-y-4">
                {/* Name */}
                <div className="space-y-2">
                  <Label htmlFor="filter-name">Filter Name</Label>
                  <Input
                    id="filter-name"
                    value={newFilter.name ?? ""}
                    onChange={(e) =>
                      setNewFilter((prev) => ({ ...prev, name: e.target.value }))
                    }
                    placeholder="Enter filter name…"
                  />
                </div>

                {/* Type */}
                <div className="space-y-2">
                  <Label htmlFor="filter-type">Filter Type</Label>
                  <Select
                    value={String(newFilter.type ?? "")}
                    onValueChange={(type) => {
                      const cfg = getFilterTypeConfig(type as DashboardFilter["type"]);
                      // Reset value when the type changes to avoid invalid carry-over
                      const defaultValue =
                        cfg?.valueType === "select"
                          ? cfg?.options?.[0]?.value ?? ""
                          : "";
                      setNewFilter((prev) => ({
                        ...prev,
                        type: type as DashboardFilter["type"],
                        value: defaultValue,
                      }));
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Choose type…" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectLabel>Types</SelectLabel>
                        <SelectSeparator />
                        {availableFilterTypes.map((config) => (
                          <SelectItem key={config.type} value={String(config.type)}>
                            <div className="text-left">
                              <div className="font-medium">{config.label}</div>
                              <div className="text-xs text-muted-foreground">
                                {config.description}
                              </div>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </div>

                {/* Value */}
                {newFilter.type && (
                  <div className="space-y-2">
                    <Label htmlFor="filter-value">Filter Value</Label>
                    {renderFilterInput(
                      newFilter.value,
                      (value) => setNewFilter((prev) => ({ ...prev, value })),
                      getFilterTypeConfig(newFilter.type)!
                    )}
                  </div>
                )}

                {/* Enabled */}
                <div className="flex items-center space-x-2">
                  <Switch
                    id="filter-enabled"
                    checked={!!newFilter.enabled}
                    onCheckedChange={(enabled) =>
                      setNewFilter((prev) => ({ ...prev, enabled }))
                    }
                  />
                  <Label htmlFor="filter-enabled">Enable filter</Label>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    onClick={handleAddFilter}
                    disabled={!newFilter.name || !newFilter.type}
                  >
                    Add Filter
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Active Filters */}
        {activeFilters.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {activeFilters.map((filter) => (
              <Badge
                key={filter.id}
                variant="default"
                className="flex items-center gap-1 px-2 py-1"
              >
                <span className="text-xs sm:text-sm md:text-base">
                  {filter.name}: {renderFilterValue(filter)}
                </span>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0 hover:bg-transparent"
                      aria-label="Filter options"
                    >
                      <Search className="h-3 w-3" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => handleToggleFilter(filter.id)}>
                      Disable
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => handleRemoveFilter(filter.id)}
                      className="text-destructive"
                    >
                      Remove
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </Badge>
            ))}
          </div>
        )}

        {/* Inactive Filters */}
        {inactiveFilters.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
              Inactive Filters
            </div>
            <div className="flex flex-wrap gap-2">
              {inactiveFilters.map((filter) => (
                <Badge
                  key={filter.id}
                  variant="outline"
                  className="flex items-center gap-1 px-2 py-1 opacity-60"
                >
                  <span className="text-xs sm:text-sm md:text-base">
                    {filter.name}: {renderFilterValue(filter)}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 hover:bg-transparent"
                    onClick={() => handleToggleFilter(filter.id)}
                    aria-label="Enable filter"
                  >
                    <Plus className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 hover:bg-transparent"
                    onClick={() => handleRemoveFilter(filter.id)}
                    aria-label="Remove filter"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Empty state */}
        {filters.length === 0 && (
          <div className="text-center py-4 text-sm text-muted-foreground md:text-base lg:text-lg">
            No filters applied. Add filters to refine your dashboard data.
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default DashboardFilters;
