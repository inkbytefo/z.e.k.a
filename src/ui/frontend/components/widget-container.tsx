"use client"

import { useState, useRef, useEffect } from "react"
import { PlusCircle, X, Maximize2, Minimize2, ChevronDown, ChevronUp, Move } from "lucide-react"
import { cn } from "@/lib/utils"

// Constants for widget layout
const DEFAULT_GRID_COLUMNS = 3;
const DEFAULT_WIDGET_HEADER_HEIGHT = 40;
const DEFAULT_WIDGET_Y_SPACING = 20;

// Widget types for the system
export type WidgetType =
  | "weather"
  | "tasks"
  | "calendar"
  | "model-selector"
  | "embedding-selector"
  | "voice-recognition"
  | "mcp-server"
  | "custom"

export interface WidgetPosition {
  x: number      // percentage
  y: number      // pixels
  width: number  // percentage
  height: number // pixels
}

export interface WidgetDefinition {
  id: string
  type: WidgetType
  title: string
  component: React.ReactNode
  position?: WidgetPosition // Initial position (optional)
  defaultWidth?: number     // in grid columns (1-12), e.g., 4 for 4/12 width
  defaultHeight?: number    // in pixels
  isResizable?: boolean     // Not implemented in this version, but good to have for future
  isRemovable?: boolean
  isMaximizable?: boolean
  isMinimizable?: boolean   // Currently, minimize is part of maximize toggle
  isCollapsible?: boolean
}

interface WidgetContainerProps {
  widgets: WidgetDefinition[]
  onAddWidget?: () => void
  onRemoveWidget?: (id: string) => void
}

export default function WidgetContainer({
  widgets: propWidgets,
  onAddWidget,
  onRemoveWidget,
}: WidgetContainerProps) {
  const [activeWidgets, setActiveWidgets] = useState<WidgetDefinition[]>(propWidgets)
  const [draggedWidget, setDraggedWidget] = useState<string | null>(null)
  const [maximizedWidget, setMaximizedWidget] = useState<string | null>(null)
  const [collapsedWidgets, setCollapsedWidgets] = useState<Record<string, boolean>>({})
  const [widgetPositions, setWidgetPositions] = useState<Record<string, WidgetPosition>>({})
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const containerRef = useRef<HTMLDivElement>(null)

  // Sync activeWidgets with propWidgets
  useEffect(() => {
    setActiveWidgets(propWidgets);
  }, [propWidgets]);

  // Initialize and update widget positions when widgets change
  useEffect(() => {
    const newPositions = { ...widgetPositions };
    const widgetIds = new Set(propWidgets.map(w => w.id));

    // Remove positions for widgets that no longer exist
    Object.keys(newPositions).forEach(id => {
      if (!widgetIds.has(id)) {
        delete newPositions[id];
      }
    });

    // Calculate default positions for new widgets
    let nextDefaultY = 0;
    let itemsInCurrentRow = 0;

    propWidgets.forEach((widget) => {
      // Skip widgets that already have positions
      if (newPositions[widget.id]) return;

      if (widget.position) {
        // Use provided position if available
        newPositions[widget.id] = widget.position;
      } else {
        // Calculate default position based on grid layout
        const columnWidth = 100 / DEFAULT_GRID_COLUMNS;
        const defaultWidth = widget.defaultWidth
          ? (widget.defaultWidth / 12) * 100 // Convert from 12-column grid to percentage
          : columnWidth;

        const defaultHeight = widget.defaultHeight || 200;

        // Calculate x position (horizontal)
        const x = itemsInCurrentRow * columnWidth;

        // If this widget would overflow the row, move to next row
        if (x + defaultWidth > 100) {
          nextDefaultY += DEFAULT_WIDGET_HEADER_HEIGHT + DEFAULT_WIDGET_Y_SPACING;
          itemsInCurrentRow = 0;
        }

        newPositions[widget.id] = {
          x: itemsInCurrentRow * columnWidth,
          y: nextDefaultY,
          width: defaultWidth,
          height: defaultHeight
        };

        // Update row tracking
        itemsInCurrentRow++;
        if (itemsInCurrentRow >= DEFAULT_GRID_COLUMNS) {
          itemsInCurrentRow = 0;
          nextDefaultY += defaultHeight + DEFAULT_WIDGET_Y_SPACING;
        }
      }
    });

    setWidgetPositions(newPositions);
  }, [propWidgets]);

  // Handle free-form widget positioning
  const handleWidgetMouseDown = (e: React.MouseEvent, id: string) => {
    // Only allow dragging from the header drag handle
    if (maximizedWidget) return;
    if (!(e.target as HTMLElement).closest('.widget-header-drag-handle')) return;

    e.preventDefault();
    e.stopPropagation();

    const widget = document.getElementById(`widget-${id}`);
    if (!widget) return;

    const rect = widget.getBoundingClientRect();
    const containerRect = containerRef.current?.getBoundingClientRect();

    if (!containerRect) return;

    setIsDragging(true);
    setDraggedWidget(id);
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });

    // Add visual feedback class for dragging
    widget.classList.add('dragging');

    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !containerRect) return;

      const x = ((e.clientX - containerRect.left - dragOffset.x) / containerRect.width) * 100;
      const y = e.clientY - containerRect.top - dragOffset.y;

      setWidgetPositions(prev => ({
        ...prev,
        [id]: {
          ...prev[id],
          x: Math.max(0, Math.min(x, 100 - (prev[id]?.width || 33.33))),
          y: Math.max(0, y)
        }
      }));
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      setDraggedWidget(null);

      // Remove dragging class when done
      widget.classList.remove('dragging');

      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  // Handle widget removal
  const handleRemoveWidget = (id: string) => {
    if (onRemoveWidget) {
      onRemoveWidget(id);
    }
  };

  // Handle widget maximize/minimize
  const handleToggleMaximize = (id: string) => {
    setMaximizedWidget(maximizedWidget === id ? null : id);
  };

  // Handle widget collapse/expand
  const handleToggleCollapse = (id: string) => {
    setCollapsedWidgets(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  return (
    <div className="space-y-4">
      {/* Widget Add Button */}
      {onAddWidget && (
        <button
          onClick={onAddWidget}
          className="w-full p-3 flex items-center justify-center text-white/80 hover:text-white
                    border border-white/10 rounded-xl bg-white/5 backdrop-blur-md transition-all duration-300
                    hover:bg-white/10 hover:shadow-lg"
        >
          <PlusCircle size={18} className="mr-2" />
          <span className="font-medium">Widget Ekle</span>
        </button>
      )}

      {/* Widgets Container */}
      <div
        ref={containerRef}
        className={cn(
          "widget-dashboard-container relative p-4",
          maximizedWidget && "hidden", // Hide container when a widget is maximized
          "min-h-[500px]" // Minimum height for container
        )}
        style={{ position: 'relative' }}
      >
        {activeWidgets.map((widget) => {
          const position = widgetPositions[widget.id] || { x: 0, y: 0, width: 33.33, height: 200 };
          const isCollapsed = collapsedWidgets[widget.id];

          return (
            <div
              id={`widget-${widget.id}`}
              key={widget.id}
              className={cn(
                "widget absolute transition-all duration-300",
                "bg-black/70 backdrop-blur-lg border border-white/10 rounded-lg shadow-md",
                draggedWidget === widget.id && "opacity-80 z-10 shadow-lg",
                isCollapsed && "h-auto"
              )}
              style={{
                left: `${position.x}%`,
                top: `${position.y}px`,
                width: `${position.width}%`,
                height: isCollapsed ? 'auto' : `${position.height}px`,
                zIndex: draggedWidget === widget.id ? 10 : 1
              }}
            >
              <div
                className="widget-header cursor-move"
                onMouseDown={(e) => handleWidgetMouseDown(e, widget.id)}
              >
                <div className="flex items-center widget-header-drag-handle">
                  <Move size={16} className="mr-2 text-white/60" />
                  <h3 className="text-sm font-medium text-white">{widget.title}</h3>
                </div>
                <div className="flex items-center space-x-2">
                  {widget.isCollapsible && (
                    <button
                      onClick={() => handleToggleCollapse(widget.id)}
                      className="p-1.5 rounded-md text-white/70 hover:text-white hover:bg-white/10 transition-colors widget-control-button"
                      title={isCollapsed ? "Genişlet" : "Daralt"}
                    >
                      {isCollapsed ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
                    </button>
                  )}
                  {widget.isMaximizable && (
                    <button
                      onClick={() => handleToggleMaximize(widget.id)}
                      className="p-1.5 rounded-md text-white/70 hover:text-white hover:bg-white/10 transition-colors widget-control-button"
                      title="Tam Ekran"
                    >
                      <Maximize2 size={14} />
                    </button>
                  )}
                  {widget.isRemovable && (
                    <button
                      onClick={() => handleRemoveWidget(widget.id)}
                      className="p-1.5 rounded-md text-white/70 hover:text-white hover:bg-white/10 transition-colors widget-control-button"
                      title="Kaldır"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>
              </div>
              {!isCollapsed && (
                <div className="widget-content overflow-auto p-3" style={{ height: `calc(100% - ${DEFAULT_WIDGET_HEADER_HEIGHT}px)` }}>
                  {widget.component}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Maximized Widget */}
      {maximizedWidget && (
        <div className="fixed inset-4 z-50 bg-black/80 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl flex flex-col">
          {activeWidgets
            .filter(w => w.id === maximizedWidget)
            .map(widget => (
              <div key={widget.id} className="flex flex-col h-full">
                <div className="widget-header">
                  <div className="flex items-center">
                    <h3 className="text-sm font-medium text-white">{widget.title}</h3>
                  </div>
                  <button
                    onClick={() => setMaximizedWidget(null)}
                    className="p-1.5 rounded-md text-white/70 hover:text-white hover:bg-white/10 transition-colors widget-control-button"
                    title="Küçült"
                  >
                    <Minimize2 size={14} />
                  </button>
                </div>
                <div className="widget-content flex-1 overflow-auto p-3">
                  {widget.component}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
