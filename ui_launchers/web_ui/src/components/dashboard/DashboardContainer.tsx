import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import {
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { 
import { cn } from '@/lib/utils';
import type { 
import { WidgetBase } from './WidgetBase';
import { DraggableWidget } from './DraggableWidget';
import { TimeRangeSelector } from './TimeRangeSelector';
import { DashboardFilters } from './DashboardFilters';
import { DashboardTemplateSelector } from './DashboardTemplateSelector';
import { DashboardExportImport } from './DashboardExportImport';
import { useAppStore, selectUser } from '@/store/app-store';
'use client';



  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCenter,
} from '@dnd-kit/core';

  SortableContext,
  rectSortingStrategy,
} from '@dnd-kit/sortable';



  Plus, 
  Settings, 
  LayoutGrid,
  Edit3,
  Save,
  X,
  Filter,
  Clock,
  FileText as Template,
  Share2
} from 'lucide-react';

  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';


  DashboardContainerProps, 
  WidgetConfig, 
  DragItem,
  WidgetData 
} from '@/types/dashboard';



  getWidgetComponent, 
  getAvailableWidgetTypes, 
  getWidgetInfo,
  createWidgetConfig 
} from './WidgetRegistry';





  useDashboardStore, 
  selectActiveDashboard,
  selectTemplatesForUser,
  selectGlobalTimeRange,
  selectGlobalFilters,
  selectIsEditing
} from '@/store/dashboard-store';


export const DashboardContainer: React.FC<DashboardContainerProps> = ({
  config,
  onConfigChange,
  isEditing: initialIsEditing = false,
  className
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
    addGlobalFilter,
    updateGlobalFilter,
    removeGlobalFilter,
    addDashboardFilter,
    updateDashboardFilter,
    removeDashboardFilter,
    setEditing,
    applyTemplate
  } = useDashboardStore();

  const user = useAppStore(selectUser);
  const globalTimeRange = useDashboardStore(selectGlobalTimeRange);
  const globalFilters = useDashboardStore(selectGlobalFilters);
  const isEditing = useDashboardStore(selectIsEditing);
  const templates = useDashboardStore(selectTemplatesForUser(user?.roles || []));

  // Sync editing state with store
  useEffect(() => {
    if (initialIsEditing !== undefined) {
      setEditing(initialIsEditing);
    }
  }, [initialIsEditing, setEditing]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  // Memoized widget IDs for drag and drop
  const widgetIds = useMemo(() => 
    config.widgets.map(widget => widget.id), 
    [config.widgets]
  );

  const handleDragStart = useCallback((event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  }, []);

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event;
    
    if (active.id !== over?.id) {
      const oldIndex = config.widgets.findIndex(widget => widget.id === active.id);
      const newIndex = config.widgets.findIndex(widget => widget.id === over?.id);
      
      if (oldIndex !== -1 && newIndex !== -1) {
        const newWidgets = [...config.widgets];
        const [movedWidget] = newWidgets.splice(oldIndex, 1);
        newWidgets.splice(newIndex, 0, movedWidget);
        
        // Use store action if available, otherwise fallback to prop
        if (config.id) {
          reorderWidgets(config.id, newWidgets.map(w => w.id));
        } else {
          onConfigChange({
            ...config,
            widgets: newWidgets,
            updatedAt: new Date()
          });
        }
      }
    }
    
    setActiveId(null);
  }, [config, onConfigChange, reorderWidgets]);

  const handleAddWidget = useCallback((type: string) => {
    const newWidgetConfig = createWidgetConfig(type, {
      position: {
        x: 0,
        y: Math.max(...config.widgets.map(w => w.position.y + w.position.h), 0),
        w: 1,
        h: 1
      }
    });

    // Use store action if available, otherwise fallback to prop
    if (config.id) {
      addWidget(config.id, newWidgetConfig);
    } else {
      onConfigChange({
        ...config,
        widgets: [...config.widgets, { ...newWidgetConfig, id: `widget-${Date.now()}` }],
        updatedAt: new Date()
      });
    }
  }, [config, onConfigChange, addWidget]);

  const handleRemoveWidget = useCallback((widgetId: string) => {
    // Use store action if available, otherwise fallback to prop
    if (config.id) {
      removeWidget(config.id, widgetId);
    } else {
      onConfigChange({
        ...config,
        widgets: config.widgets.filter(widget => widget.id !== widgetId),
        updatedAt: new Date()
      });
    }
  }, [config, onConfigChange, removeWidget]);

  const handleWidgetConfigChange = useCallback((widgetId: string, newConfig: WidgetConfig) => {
    // Use store action if available, otherwise fallback to prop
    if (config.id) {
      updateWidget(config.id, widgetId, newConfig);
    } else {
      onConfigChange({
        ...config,
        widgets: config.widgets.map(widget => 
          widget.id === widgetId ? newConfig : widget
        ),
        updatedAt: new Date()
      });
    }
  }, [config, onConfigChange, updateWidget]);

  const handleRefreshWidget = useCallback(async (widgetId: string) => {
    // Set loading state
    setWidgetData(prev => ({
      ...prev,
      [widgetId]: {
        ...prev[widgetId],
        loading: true,
        error: undefined
      }
    }));

    try {
      // In a real implementation, this would fetch data from an API
      // For now, we'll simulate a data fetch
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setWidgetData(prev => ({
        ...prev,
        [widgetId]: {
          id: widgetId,
          data: { value: Math.random() * 100 }, // Mock data
          loading: false,
          lastUpdated: new Date()
        }
      }));
    } catch (error) {
      setWidgetData(prev => ({
        ...prev,
        [widgetId]: {
          ...prev[widgetId],
          loading: false,
          error: error instanceof Error ? error.message : 'Failed to refresh widget'
        }
      }));
    }
  }, []);

  const toggleEditMode = useCallback(() => {
    setEditing(!isEditing);
  }, [isEditing, setEditing]);

  const handleLayoutChange = useCallback((layout: 'grid' | 'masonry' | 'flex') => {
    if (config.id) {
      updateDashboard(config.id, { layout });
    } else {
      onConfigChange({ ...config, layout });
    }
  }, [config, onConfigChange, updateDashboard]);

  const handleApplyTemplate = useCallback((templateId: string) => {
    applyTemplate(templateId, config.id);
  }, [applyTemplate, config.id]);

  const handleTimeRangeChange = useCallback((timeRange: any) => {
    setGlobalTimeRange(timeRange);
  }, [setGlobalTimeRange]);

  const handleFiltersChange = useCallback((filters: any[]) => {
    // Update dashboard-specific filters
    if (config.id) {
      // Clear existing filters and add new ones
      config.filters.forEach(filter => {
        removeDashboardFilter(config.id, filter.id);
      });
      
      filters.forEach(filter => {
        if (filter.id) {
          updateDashboardFilter(config.id, filter.id, filter);
        } else {
          addDashboardFilter(config.id, filter);
        }
      });
    } else {
      onConfigChange({ ...config, filters });
    }
  }, [config, onConfigChange, addDashboardFilter, updateDashboardFilter, removeDashboardFilter]);

  const getLayoutClasses = () => {
    switch (config.layout) {
      case 'grid':
        return 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 auto-rows-min';
      case 'masonry':
        return 'columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-4 space-y-4';
      case 'flex':
        return 'flex flex-wrap gap-4';
      default:
        return 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 auto-rows-min';
    }
  };

  const renderWidget = (widget: WidgetConfig) => {
    const WidgetComponent = getWidgetComponent(widget.type);
    
    if (!WidgetComponent) {
      return (
    <ErrorBoundary fallback={<div>Something went wrong in DashboardContainer</div>}>
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
        data={data}
        loading={data?.loading}
        error={data?.error}
        onConfigChange={(newConfig) => handleWidgetConfigChange(widget.id, newConfig)}
        onRefresh={() => handleRefreshWidget(widget.id)}
        onRemove={() => handleRemoveWidget(widget.id)}
        isEditing={isEditing}
      >
        <WidgetComponent
          config={widget}
          data={data}
          onConfigChange={(newConfig) => handleWidgetConfigChange(widget.id, newConfig)}
          onRefresh={() => handleRefreshWidget(widget.id)}
          onRemove={() => handleRemoveWidget(widget.id)}
          isEditing={isEditing}
        />
      </WidgetBase>
    );
  };

  const activeWidget = activeId ? config.widgets.find(w => w.id === activeId) : null;

  return (
    <div className={cn('w-full', className)}>
      {/* Dashboard Header */}
      <div className="space-y-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{config.name}</h1>
            {config.description && (
              <p className="text-muted-foreground mt-1">{config.description}</p>
            )}
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

            {/* Add Widget Dropdown */}
            {isEditing && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button variant="outline" size="sm" aria-label="Button">
                    <Plus className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                    Add Widget
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48 sm:w-auto md:w-full">
                  {getAvailableWidgetTypes().map(type => {
                    const info = getWidgetInfo(type);
                    return (
                      <DropdownMenuItem
                        key={type}
                        onClick={() => handleAddWidget(type)}
                      >
                        <div>
                          <div className="font-medium">{info?.name}</div>
                          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                            {info?.description}
                          </div>
                        </div>
                      </DropdownMenuItem>
                    );
                  })}
                </DropdownMenuContent>
              </DropdownMenu>
            )}

            {/* Layout Options */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button variant="outline" size="sm" aria-label="Button">
                  <LayoutGrid className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Layout
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={() => handleLayoutChange('grid')}
                >
                  Grid Layout
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => handleLayoutChange('masonry')}
                >
                  Masonry Layout
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => handleLayoutChange('flex')}
                >
                  Flex Layout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Edit Mode Toggle */}
            <button
              variant={isEditing ? "default" : "outline"}
              size="sm"
              onClick={toggleEditMode}
             aria-label="Button">
              {isEditing ? (
                <>
                  <Save className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Save
                </>
              ) : (
                <>
                  <Edit3 className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Edit
                </>
              )}
            </Button>

            {/* Filters Toggle */}
            <button
              variant={showFilters ? "default" : "outline"}
              size="sm"
              onClick={() = aria-label="Button"> setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
              Filters
            </Button>
          </div>
        </div>

        {/* Time Range and Filters */}
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

      {/* Dashboard Content */}
      {config.widgets.length === 0 ? (
        <Card className="p-8 text-center sm:p-4 md:p-6">
          <div className="text-muted-foreground">
            <LayoutGrid className="h-12 w-12 mx-auto mb-4 opacity-50 sm:w-auto md:w-full" />
            <h3 className="text-lg font-medium mb-2">No widgets added</h3>
            <p className="text-sm mb-4 md:text-base lg:text-lg">
              Add widgets to start building your dashboard
            </p>
            <button onClick={toggleEditMode} variant="outline" aria-label="Button">
              <Plus className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
              Add Your First Widget
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
              {config.widgets.map(widget => (
                isEditing ? (
                  <DraggableWidget key={widget.id} id={widget.id}>
                    {renderWidget(widget)}
                  </DraggableWidget>
                ) : (
                  renderWidget(widget)
                )
              ))}
            </div>
          </SortableContext>

          <DragOverlay>
            {activeWidget && (
              <div className="opacity-50">
                {renderWidget(activeWidget)}
              </div>
            )}
          </DragOverlay>
        </DndContext>
      )}
    </div>
    </ErrorBoundary>
  );
};

export default DashboardContainer;