"use client"

import { useState, Suspense, lazy } from "react"
import {
  Settings,
  Brain,
  Key,
  Cloud,
  Thermometer,
  Calendar,
  CheckSquare,
  Mic,
  Monitor,
  Server,
  Plus,
  ChevronRight,
  Loader2
} from "lucide-react"
import { cn } from "@/lib/utils"

// Lazy load widgets for better performance
const ModelSelectorWidget = lazy(() => import("./widgets/ModelSelectorWidget"))
const APIKeysWidget = lazy(() => import("./widgets/APIKeysWidget"))
const WeatherWidget = lazy(() => import("./widgets/WeatherWidget"))

// Widget Loading Fallback
const WidgetSkeleton = ({ size = "large" }: { size?: "small" | "large" }) => (
  <div className={cn(
    "flex items-center justify-center",
    size === "large" ? "h-32" : "h-20"
  )}>
    <Loader2 size={20} className="animate-spin ios-text-secondary" />
  </div>
)

interface ControlCenterPanelProps {
  onModelChange?: (model: string) => void
  className?: string
}

export default function ControlCenterPanel({
  onModelChange,
  className
}: ControlCenterPanelProps) {
  const [activeToggles, setActiveToggles] = useState<Record<string, boolean>>({
    voice: false,
    notifications: true,
    autoMode: true
  })

  const handleToggle = (id: string) => {
    setActiveToggles(prev => ({
      ...prev,
      [id]: !prev[id]
    }))
  }





  return (
    <div className={cn("ios-control", className)}>
      {/* Header */}
      <div className="mb-6">
        <h2 className="ios-text-primary text-lg font-semibold mb-2">
          Denetim Merkezi
        </h2>
        <p className="ios-text-secondary text-sm">
          Z.E.K.A ayarları ve hızlı erişim
        </p>
      </div>

      {/* Control Grid */}
      <div className="space-y-4">
        {/* Primary Widgets - Large Size */}
        <div className="space-y-4">
          {/* AI Model Selector */}
          <div className="control-center-item large">
            <Suspense fallback={<WidgetSkeleton size="large" />}>
              <ModelSelectorWidget
                onModelChange={onModelChange}
                size="large"
              />
            </Suspense>
          </div>

          {/* Weather Widget */}
          <div className="control-center-item large">
            <Suspense fallback={<WidgetSkeleton size="large" />}>
              <WeatherWidget size="large" />
            </Suspense>
          </div>
        </div>

        {/* Secondary Widgets - Small Grid */}
        <div className="control-center-grid">
          {/* API Keys */}
          <div className="control-center-item">
            <Suspense fallback={<WidgetSkeleton size="small" />}>
              <APIKeysWidget size="small" />
            </Suspense>
          </div>

          {/* Voice Control Toggle */}
          <div
            className={cn(
              "control-center-item",
              activeToggles.voice && "bg-blue-500/20 border-blue-400/30"
            )}
            onClick={() => handleToggle("voice")}
          >
            <div className="flex flex-col items-center justify-center h-full space-y-2">
              <div className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center",
                activeToggles.voice
                  ? "bg-blue-500"
                  : "bg-gradient-to-br from-purple-500 to-pink-600"
              )}>
                <Mic size={16} className="text-white" />
              </div>
              <div className="text-center">
                <div className={cn(
                  "text-xs font-medium",
                  activeToggles.voice ? "text-blue-400" : "ios-text-primary"
                )}>
                  Ses Kontrolü
                </div>
                <div className="ios-text-secondary text-xs">
                  {activeToggles.voice ? "Aktif" : "Kapalı"}
                </div>
              </div>
            </div>
          </div>

          {/* System Settings */}
          <div className="control-center-item">
            <div className="flex flex-col items-center justify-center h-full space-y-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-500 to-gray-700 flex items-center justify-center">
                <Settings size={16} className="text-white" />
              </div>
              <div className="text-center">
                <div className="ios-text-primary text-xs font-medium">Ayarlar</div>
                <div className="ios-text-secondary text-xs">Sistem</div>
              </div>
            </div>
          </div>

          {/* Desktop Control */}
          <div className="control-center-item">
            <div className="flex flex-col items-center justify-center h-full space-y-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <Monitor size={16} className="text-white" />
              </div>
              <div className="text-center">
                <div className="ios-text-primary text-xs font-medium">Masaüstü</div>
                <div className="ios-text-secondary text-xs">Kontrol</div>
              </div>
            </div>
          </div>

          {/* MCP Servers */}
          <div className="control-center-item">
            <div className="flex flex-col items-center justify-center h-full space-y-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                <Server size={16} className="text-white" />
              </div>
              <div className="text-center">
                <div className="ios-text-primary text-xs font-medium">MCP</div>
                <div className="ios-text-secondary text-xs">Sunucular</div>
              </div>
            </div>
          </div>

          {/* Add Widget Button */}
          <div className="control-center-item border-dashed border-white/30 bg-transparent hover:bg-white/5">
            <div className="flex flex-col items-center justify-center h-full space-y-2">
              <Plus size={20} className="ios-text-quaternary" />
              <span className="text-xs ios-text-tertiary">Widget Ekle</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <h3 className="ios-text-primary text-sm font-medium mb-4">
          Hızlı İşlemler
        </h3>

        <div className="space-y-2">
          <button className="w-full p-3 rounded-lg bg-white/5 hover:bg-white/10 ios-transition text-left">
            <div className="flex items-center justify-between">
              <span className="ios-text-primary text-sm">Sistem Yeniden Başlat</span>
              <ChevronRight size={14} className="ios-text-quaternary" />
            </div>
          </button>

          <button className="w-full p-3 rounded-lg bg-white/5 hover:bg-white/10 ios-transition text-left">
            <div className="flex items-center justify-between">
              <span className="ios-text-primary text-sm">Önbellek Temizle</span>
              <ChevronRight size={14} className="ios-text-quaternary" />
            </div>
          </button>

          <button className="w-full p-3 rounded-lg bg-white/5 hover:bg-white/10 ios-transition text-left">
            <div className="flex items-center justify-between">
              <span className="ios-text-primary text-sm">Ayarları Dışa Aktar</span>
              <ChevronRight size={14} className="ios-text-quaternary" />
            </div>
          </button>
        </div>
      </div>

      {/* System Info */}
      <div className="mt-8 p-4 rounded-lg bg-white/5 border border-white/10">
        <h4 className="ios-text-primary text-sm font-medium mb-3">
          Sistem Bilgisi
        </h4>

        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="ios-text-secondary">Sürüm</span>
            <span className="ios-text-primary font-mono">v2.1.0</span>
          </div>
          <div className="flex justify-between">
            <span className="ios-text-secondary">Çalışma Süresi</span>
            <span className="ios-text-primary font-mono">2h 34m</span>
          </div>
          <div className="flex justify-between">
            <span className="ios-text-secondary">Son Güncelleme</span>
            <span className="ios-text-primary font-mono">2 gün önce</span>
          </div>
        </div>
      </div>
    </div>
  )
}
