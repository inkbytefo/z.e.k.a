"use client"

import { useState, useRef, useEffect } from "react"
import { PlusCircle, GripVertical, X, Maximize2, Minimize2 } from "lucide-react"
import { cn } from "@/lib/utils"

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

export interface WidgetDefinition {
  id: string
  type: WidgetType
  title: string
  component: React.ReactNode
  defaultWidth?: number // in grid columns (1-12)
  defaultHeight?: number // in pixels
  isResizable?: boolean
  isRemovable?: boolean
  isMaximizable?: boolean
}

interface WidgetContainerProps {
  widgets: WidgetDefinition[]
  onAddWidget?: () => void
  onRemoveWidget?: (id: string) => void
  onReorderWidgets?: (widgets: WidgetDefinition[]) => void
}

export default function WidgetContainer({ 
  widgets, 
  onAddWidget, 
  onRemoveWidget,
  onReorderWidgets
}: WidgetContainerProps) {
  const [activeWidgets, setActiveWidgets] = useState<WidgetDefinition[]>(widgets)
  const [draggedWidget, setDraggedWidget] = useState<string | null>(null)
  const [maximizedWidget, setMaximizedWidget] = useState<string | null>(null)
  
  // Handle widget drag and drop
  const handleDragStart = (id: string) => {
    setDraggedWidget(id)
  }
  
  const handleDragOver = (e: React.DragEvent, id: string) => {
    e.preventDefault()
    if (draggedWidget && draggedWidget !== id) {
      const dragIndex = activeWidgets.findIndex(w => w.id === draggedWidget)
      const hoverIndex = activeWidgets.findIndex(w => w.id === id)
      
      if (dragIndex !== -1 && hoverIndex !== -1) {
        const newWidgets = [...activeWidgets]
        const draggedItem = newWidgets[dragIndex]
        
        // Remove dragged item
        newWidgets.splice(dragIndex, 1)
        // Insert at new position
        newWidgets.splice(hoverIndex, 0, draggedItem)
        
        setActiveWidgets(newWidgets)
        if (onReorderWidgets) {
          onReorderWidgets(newWidgets)
        }
      }
    }
  }
  
  const handleDragEnd = () => {
    setDraggedWidget(null)
  }
  
  // Handle widget removal
  const handleRemoveWidget = (id: string) => {
    const newWidgets = activeWidgets.filter(w => w.id !== id)
    setActiveWidgets(newWidgets)
    if (onRemoveWidget) {
      onRemoveWidget(id)
    }
  }
  
  // Handle widget maximize/minimize
  const handleToggleMaximize = (id: string) => {
    setMaximizedWidget(maximizedWidget === id ? null : id)
  }
  
  return (
    <div className="space-y-4">
      {/* Widget Add Button */}
      {onAddWidget && (
        <button 
          onClick={onAddWidget}
          className="w-full p-2 flex items-center justify-center text-sky-400 hover:text-sky-300 
                    border border-sky-700/30 rounded-md bg-sky-900/10 transition-colors"
        >
          <PlusCircle size={16} className="mr-2" />
          <span>Add Widget</span>
        </button>
      )}
      
      {/* Widgets Grid */}
      <div className={cn(
        "widget-container",
        maximizedWidget && "hidden" // Hide grid when a widget is maximized
      )}>
        {activeWidgets.map((widget) => (
          <div 
            key={widget.id}
            className={cn(
              "widget transition-all duration-300",
              draggedWidget === widget.id && "opacity-50 border-sky-500/50"
            )}
            draggable={true}
            onDragStart={() => handleDragStart(widget.id)}
            onDragOver={(e) => handleDragOver(e, widget.id)}
            onDragEnd={handleDragEnd}
          >
            <div className="widget-header">
              <div className="flex items-center">
                <GripVertical size={14} className="mr-2 text-sky-500/70 cursor-move" />
                <h3 className="text-sm font-medium text-sky-300">{widget.title}</h3>
              </div>
              <div className="flex items-center space-x-1">
                {widget.isMaximizable && (
                  <button 
                    onClick={() => handleToggleMaximize(widget.id)}
                    className="p-1 text-slate-400 hover:text-sky-400 transition-colors"
                  >
                    <Maximize2 size={14} />
                  </button>
                )}
                {widget.isRemovable && (
                  <button 
                    onClick={() => handleRemoveWidget(widget.id)}
                    className="p-1 text-slate-400 hover:text-rose-400 transition-colors"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>
            </div>
            <div className="widget-content">
              {widget.component}
            </div>
          </div>
        ))}
      </div>
      
      {/* Maximized Widget */}
      {maximizedWidget && (
        <div className="fixed inset-4 z-50 bg-slate-900/95 rounded-lg border border-sky-700/30 shadow-2xl flex flex-col">
          {activeWidgets
            .filter(w => w.id === maximizedWidget)
            .map(widget => (
              <div key={widget.id} className="flex flex-col h-full">
                <div className="widget-header">
                  <div className="flex items-center">
                    <h3 className="text-sm font-medium text-sky-300">{widget.title}</h3>
                  </div>
                  <button 
                    onClick={() => setMaximizedWidget(null)}
                    className="p-1 text-slate-400 hover:text-sky-400 transition-colors"
                  >
                    <Minimize2 size={14} />
                  </button>
                </div>
                <div className="widget-content flex-1 overflow-auto">
                  {widget.component}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  )
}
