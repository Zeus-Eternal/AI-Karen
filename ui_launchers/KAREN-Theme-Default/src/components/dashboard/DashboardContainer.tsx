"use client";

import React, { useState, useCallback, useMemo, useEffect } from "react";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// dnd-kit
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  DragStartEvent,
  DragEndEvent,
  useSensor,
  useSensors,
  closestCenter,
} from "@dnd-kit/core";
import { SortableContext, rectSortingStrategy } from "@dnd-kit/sortable";

// UI: dropdown menu
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// Icons
import {
  Plus,
  LayoutGrid,
  Save,
  Edit3,
  Filter as FilterIcon,
} from "lucide-react";

// Local widgets & helpers
import { WidgetBase } from "./WidgetBase";
import { DraggableWidget } from "./DraggableWidget";
import { TimeRangeSelector } from "./TimeRangeSelector";
import { DashboardFilters } from "./DashboardFilters";
import { DashboardTemplateSelector } from "./DashboardTemplateSelector";
import { DashboardExportImport } from "./DashboardExportImport";
import {
  getWidgetComponent,
  getAvailableWidgetTypes,
  getWidgetInfo,
  createWidgetConfig,
} from "./WidgetRegistry";

// Stores
import { useAppStore, selectUser } from "@/store/app-store";
import {
  useDashboardStore,
  selectGlobalTimeRange,
  selectGlobalFilters,
  selectIsEditing,
  selectTemplatesForUser,
} from "@/store/dashboard-store";

// Types
import type {
  DashboardContainerProps,
  WidgetConfig,
  WidgetData,
} from "@/types/dashboard";

/* ----------------------------------------------------------------------------
 * DashboardContainer
 * ---------------------------------------------------------------------------- */

export const DashboardContainer: React.FC<DashboardContainerProps> = ({
  config,
  onConfigChange,
  isEditing: initialIsEditing = false,
  className,
}) => {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [widgetData, setWidgetData] = useState<Record<string, WidgetData>>({});
  const [showFilters, setShowFilters] = useState(false);

  // Dashboard store integration
  const {
    updateDashboard,
    addWidget,
    removeWidget,
    updateWidget,
    reorderWidgets,
    setGlobalTimeRange,
    addDashboardFilter,
    updateDashboardFilter,
    removeDashboardFilter,
    setEditing,
    applyTemplate,
  } = useDashboardStore();

  const user = useAppStore(selectUser);
  const globalTimeRange = useDashboardStore(selectGlobalTimeRange);
  const isEditing = useDashboardStore(selectIsEditing);
  const templates = useDashboardStore(
    selectTemplatesForUser(user?.roles || [])
  );

  // Sync editing state with store
  useEffect(() => {
    setEditing(!!initialIsEditing);
  }, [initialIsEditing, setEditing]);

  // Sensors for DnD
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  );

  // Memoized widget IDs
  const widgetIds = useMemo(
    () => config.widgets.map((w) => w.id),
    [config.widgets]
  );

  const handleDragStart = useCallback((event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  }, []);

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) {
        setActiveId(null);
        return;
      }

      const oldIndex = config.widgets.findIndex((w) => w.id === active.id);
      const newIndex = config.widgets.findIndex((w) => w.id === over.id);

      if (oldIndex !== -1 && newIndex !== -1) {
        const newWidgets = [...config.widgets];
        const [moved] = newWidgets.splice(oldIndex, 1);
        newWidgets.splice(newIndex, 0, moved);

        if (config.id) {
          reorderWidgets(
            config.id,
            newWidgets.map((w) => w.id)
          );
        } else {
          onConfigChange({
            ...config,
            widgets: newWidgets,
            updatedAt: new Date(),
          });
        }
      }

      setActiveId(null);
    },
    [config, onConfigChange, reorderWidgets]
  );

  const handleAddWidget = useCallback(
    (type: string) => {
      // Compute a simple Y position based on current stack
      const nextY = Math.max(
        0,
        ...config.widgets.map((w) => w.position.y + w.position.h)
      );

      const newWidget = createWidgetConfig(type, {
        position: { x: 0, y: nextY, w: 1, h: 1 },
      });

      if (config.id) {
        addWidget(config.id, newWidget);
      } else {
        onConfigChange({
          ...config,
          widgets: [
            ...config.widgets,
            { ...newWidget, id: `widget-${Date.now()}` },
          ],
          updatedAt: new Date(),
        });
      }
    },
    [config, onConfigChange, addWidget]
  );

  const handleRemoveWidget = useCallback(
    (widgetId: string) => {
      if (config.id) {
        removeWidget(config.id, widgetId);
      } else {
        onConfigChange({
          ...config,
          widgets: config.widgets.filter((w) => w.id !== widgetId),
          updatedAt: new Date(),
        });
      }
    },
    [config, onConfigChange, removeWidget]
  );

  const handleWidgetConfigChange = useCallback(
    (widgetId: string, newConfig: WidgetConfig) => {
      if (config.id) {
        updateWidget(config.id, widgetId, newConfig);
      } else {
        onConfigChange({
          ...config,
          widgets: config.widgets.map((w) =>
            w.id === widgetId ? newConfig : w
          ),
          updatedAt: new Date(),
        });
      }
    },
    [config, onConfigChange, updateWidget]
  );

  const handleRefreshWidget = useCallback(async (widgetId: string) => {
    setWidgetData((prev) => ({
      ...prev,
      [widgetId]: { ...prev[widgetId], loading: true, error: undefined },
    }));

    try {
      await new Promise((r) => setTimeout(r, 1000));
      setWidgetData((prev) => ({
        ...prev,
        [widgetId]: {
          id: widgetId,
          data: { value: Math.random() * 100 },
          loading: false,
          lastUpdated: new Date(),
        },
      }));
    } catch (e) {
      setWidgetData((prev) => ({
        ...prev,
        [widgetId]: {
          ...prev[widgetId],
          loading: false,
          error: e instanceof Error ? e.message : "Failed to refresh widget",
        },
      }));
    }
  }, []);

  const toggleEditMode = useCallback(() => {
    setEditing(!isEditing);
  }, [isEditing, setEditing]);

  const handleLayoutChange = useCallback(
    (layout: "grid" | "masonry" | "flex") => {
      if (config.id) updateDashboard(config.id, { layout });
      else onConfigChange({ ...config, layout });
    },
    [config, onConfigChange, updateDashboard]
  );

  const handleApplyTemplate = useCallback(
    (templateId: string) => {
      // If your store expects (templateId, dashboardId)
      applyTemplate(templateId, config.id);
    },
    [applyTemplate, config.id]
  );

  const handleTimeRangeChange = useCallback(
    (timeRange: unknown) => {
      setGlobalTimeRange(timeRange);
    },
    [setGlobalTimeRange]
  );

  const handleFiltersChange = useCallback(
    (filters: unknown[]) => {
      if (config.id) {
        // Remove existing then upsert new
        (config.filters || []).forEach((f) => {
          if (f?.id) removeDashboardFilter(config.id!, f.id);
        });

        filters.forEach((f) => {
          if (f?.id) updateDashboardFilter(config.id!, f.id, f);
          else addDashboardFilter(config.id!, f);
        });
      } else {
        onConfigChange({ ...config, filters });
      }
    },
    [
      config,
      onConfigChange,
      addDashboardFilter,
      updateDashboardFilter,
      removeDashboardFilter,
    ]
  );

  const getLayoutClasses = () => {
    switch (config.layout) {
      case "grid":
        return "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 auto-rows-min";
      case "masonry":
        return "columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-4 space-y-4";
      case "flex":
        return "flex flex-wrap gap-4";
      default:
        return "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 auto-rows-min";
    }
  };

  const renderWidget = (widget: WidgetConfig) => {
    const WidgetComponent = getWidgetComponent(widget.type);

    if (!WidgetComponent) {
      return (
        <WidgetBase
          key={widget.id}
          config={widget}
          error={`Unknown widget type: ${widget.type}`}
          onRemove={() => handleRemoveWidget(widget.id)}
          isEditing={isEditing}
        >
          <div>Unknown widget type</div>
        </WidgetBase>
      );
    }

    const data = widgetData[widget.id];

    return (
      <WidgetBase
        key={widget.id}
        config={widget}
        data={data as unknown}
        loading={data?.loading}
        error={data?.error}
        onConfigChange={(newConfig) =>
          handleWidgetConfigChange(widget.id, newConfig)
        }
        onRefresh={() => handleRefreshWidget(widget.id)}
        onRemove={() => handleRemoveWidget(widget.id)}
        isEditing={isEditing}
      >
        <WidgetComponent
          config={widget}
          data={data as unknown}
          onConfigChange={(newConfig: WidgetConfig) =>
            handleWidgetConfigChange(widget.id, newConfig)
          }
          onRefresh={() => handleRefreshWidget(widget.id)}
          onRemove={() => handleRemoveWidget(widget.id)}
          isEditing={isEditing}
        />
      </WidgetBase>
    );
  };

  const activeWidget = activeId
    ? config.widgets.find((w) => w.id === activeId)
    : null;

  return (
    <ErrorBoundary
      fallback={({ error, resetError }) => (
        <div className="p-4 text-center">
          <p className="text-destructive">Something went wrong in DashboardContainer</p>
          <p className="text-sm text-muted-foreground mt-2">{error.message}</p>
          <Button onClick={resetError} className="mt-4">
            Try Again
          </Button>
        </div>
      )}
    >
      <div className={cn("w-full", className)}>
        {/* Header */}
        <div className="space-y-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">{config.name}</h1>
              {config.description ? (
                <p className="text-muted-foreground mt-1">
                  {config.description}
                </p>
              ) : null}
            </div>

            <div className="flex items-center gap-2">
              {/* Templates */}
              <DashboardTemplateSelector
                templates={templates}
                userRoles={user?.roles || []}
                onApplyTemplate={handleApplyTemplate}
              />

              {/* Export/Import */}
              <DashboardExportImport dashboard={config} />

              {/* Add Widget */}
              {isEditing && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" aria-label="Add widget">
                      <Plus className="h-4 w-4 mr-2" /> Add Widget
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-64">
                    {getAvailableWidgetTypes().map((type) => {
                      const info = getWidgetInfo(type);
                      return (
                        <DropdownMenuItem
                          key={type}
                          onClick={() => handleAddWidget(type)}
                        >
                          <div>
                            <div className="font-medium">
                              {info?.name || type}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {info?.description || "Add this widget"}
                            </div>
                          </div>
                        </DropdownMenuItem>
                      );
                    })}
                  </DropdownMenuContent>
                </DropdownMenu>
              )}

              {/* Layout */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    aria-label="Change layout"
                  >
                    <LayoutGrid className="h-4 w-4 mr-2" /> Layout
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => handleLayoutChange("grid")}>
                    Grid
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => handleLayoutChange("masonry")}
                  >
                    Masonry
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleLayoutChange("flex")}>
                    Flex
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Edit Mode */}
              <Button
                variant={isEditing ? "default" : "outline"}
                size="sm"
                onClick={toggleEditMode}
                aria-label={isEditing ? "Save layout" : "Edit layout"}
              >
                {isEditing ? (
                  <Save className="h-4 w-4 mr-2" />
                ) : (
                  <Edit3 className="h-4 w-4 mr-2" />
                )}
                {isEditing ? "Save" : "Edit"}
              </Button>

              {/* Filters Toggle */}
              <Button
                variant={showFilters ? "default" : "outline"}
                size="sm"
                onClick={() => setShowFilters((p) => !p)}
                aria-label="Toggle filters"
              >
                <FilterIcon className="h-4 w-4 mr-2" /> Filters
              </Button>
            </div>
          </div>

          {/* Time Range + Filters */}
          <div className="flex items-center justify-between">
            <TimeRangeSelector
              value={globalTimeRange}
              onChange={handleTimeRangeChange}
            />
            {showFilters && (
              <div className="flex-1 ml-6">
                <DashboardFilters
                  filters={config.filters}
                  onFiltersChange={handleFiltersChange}
                />
              </div>
            )}
          </div>
        </div>

        {/* Body */}
        {config.widgets.length === 0 ? (
          <Card className="p-8 text-center">
            <div className="text-muted-foreground">
              <LayoutGrid className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">No widgets added</h3>
              <p className="text-sm mb-4">
                Click Edit to add your first widget.
              </p>
              <Button onClick={toggleEditMode} variant="outline">
                <Plus className="h-4 w-4 mr-2" /> Edit
              </Button>
            </div>
          </Card>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <SortableContext items={widgetIds} strategy={rectSortingStrategy}>
              <div className={getLayoutClasses()}>
                {config.widgets.map((widget) =>
                  isEditing ? (
                    <DraggableWidget key={widget.id} id={widget.id}>
                      {renderWidget(widget)}
                    </DraggableWidget>
                  ) : (
                    <div key={widget.id}>{renderWidget(widget)}</div>
                  )
                )}
              </div>
            </SortableContext>

            <DragOverlay>
              {activeWidget ? (
                <div className="opacity-50">{renderWidget(activeWidget)}</div>
              ) : null}
            </DragOverlay>
          </DndContext>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default DashboardContainer;
