"use client"

import { useState, useEffect } from "react"
import { 
  Cpu, 
  Database, 
  Shield, 
  Wifi, 
  Brain, 
  Activity,
  CheckCircle,
  AlertCircle,
  XCircle,
  ChevronRight
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useWebSocket } from "@/hooks/useWebSocket"

interface SystemStatusPanelProps {
  currentModel?: string
  className?: string
}

interface StatusItemData {
  id: string
  label: string
  value: string
  status: "online" | "warning" | "offline"
  icon: React.ReactNode
  description?: string
}

export default function SystemStatusPanel({ 
  currentModel = "gpt-4o-mini",
  className 
}: SystemStatusPanelProps) {
  const [systemMetrics, setSystemMetrics] = useState({
    cpuUsage: 0,
    memoryUsage: 0,
    networkLatency: 0
  })

  // WebSocket connection status
  const { connected, connecting } = useWebSocket("/api/ws/chat")

  // Simulate system metrics
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemMetrics({
        cpuUsage: Math.random() * 100,
        memoryUsage: Math.random() * 100,
        networkLatency: Math.random() * 50 + 10
      })
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  const statusItems: StatusItemData[] = [
    {
      id: "core",
      label: "Çekirdek Sistemler",
      value: "Çevrimiçi",
      status: "online",
      icon: <Cpu size={18} />,
      description: "Tüm temel sistemler aktif"
    },
    {
      id: "neural",
      label: "Sinir Ağı",
      value: "Aktif",
      status: "online",
      icon: <Brain size={18} />,
      description: "AI modeli hazır"
    },
    {
      id: "security",
      label: "Güvenlik Protokolü",
      value: "Devrede",
      status: "warning",
      icon: <Shield size={18} />,
      description: "Güvenlik taraması devam ediyor"
    },
    {
      id: "database",
      label: "Veri İşleme",
      value: "Optimal",
      status: "online",
      icon: <Database size={18} />,
      description: "Vektör veritabanı aktif"
    },
    {
      id: "network",
      label: "Ağ Bağlantısı",
      value: connected ? "Bağlı" : connecting ? "Bağlanıyor" : "Bağlantı Kesildi",
      status: connected ? "online" : connecting ? "warning" : "offline",
      icon: <Wifi size={18} />,
      description: `Gecikme: ${systemMetrics.networkLatency.toFixed(0)}ms`
    },
    {
      id: "model",
      label: "Aktif Model",
      value: currentModel.split('/').pop() || "Varsayılan",
      status: "online",
      icon: <Activity size={18} />,
      description: `Model: ${currentModel}`
    }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "online":
        return <CheckCircle size={14} className="text-green-400" />
      case "warning":
        return <AlertCircle size={14} className="text-yellow-400" />
      case "offline":
        return <XCircle size={14} className="text-red-400" />
      default:
        return <CheckCircle size={14} className="text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "online":
        return "border-green-400/20 bg-green-400/5"
      case "warning":
        return "border-yellow-400/20 bg-yellow-400/5"
      case "offline":
        return "border-red-400/20 bg-red-400/5"
      default:
        return "border-gray-400/20 bg-gray-400/5"
    }
  }

  return (
    <div className={cn("ios-sidebar", className)}>
      {/* Header */}
      <div className="mb-6">
        <h2 className="ios-text-primary text-lg font-semibold mb-2">
          Sistem Durumu
        </h2>
        <p className="ios-text-secondary text-sm">
          Z.E.K.A sistemlerinin gerçek zamanlı durumu
        </p>
      </div>

      {/* Status List */}
      <div className="status-list space-y-3">
        {statusItems.map((item) => (
          <div
            key={item.id}
            className={cn(
              "status-item group cursor-pointer",
              getStatusColor(item.status)
            )}
          >
            <div className="flex items-center space-x-3 flex-1">
              {/* Icon */}
              <div className="ios-text-secondary group-hover:ios-text-primary transition-colors">
                {item.icon}
              </div>
              
              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="ios-text-primary text-sm font-medium">
                    {item.label}
                  </span>
                  <span className={cn(
                    "text-xs font-medium",
                    item.status === "online" && "text-green-400",
                    item.status === "warning" && "text-yellow-400",
                    item.status === "offline" && "text-red-400"
                  )}>
                    {item.value}
                  </span>
                </div>
                {item.description && (
                  <p className="ios-text-tertiary text-xs mt-1 truncate">
                    {item.description}
                  </p>
                )}
              </div>
            </div>

            {/* Status Indicator & Arrow */}
            <div className="flex items-center space-x-2">
              {getStatusIcon(item.status)}
              <ChevronRight size={12} className="ios-text-quaternary group-hover:ios-text-tertiary transition-colors" />
            </div>
          </div>
        ))}
      </div>

      {/* System Metrics */}
      <div className="mt-8">
        <h3 className="ios-text-primary text-sm font-medium mb-4">
          Sistem Metrikleri
        </h3>
        
        <div className="space-y-4">
          {/* CPU Usage */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="ios-text-secondary text-xs">CPU Kullanımı</span>
              <span className="ios-text-primary text-xs font-mono">
                {systemMetrics.cpuUsage.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${systemMetrics.cpuUsage}%` }}
              />
            </div>
          </div>

          {/* Memory Usage */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="ios-text-secondary text-xs">Bellek Kullanımı</span>
              <span className="ios-text-primary text-xs font-mono">
                {systemMetrics.memoryUsage.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${systemMetrics.memoryUsage}%` }}
              />
            </div>
          </div>

          {/* Network Latency */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="ios-text-secondary text-xs">Ağ Gecikmesi</span>
              <span className="ios-text-primary text-xs font-mono">
                {systemMetrics.networkLatency.toFixed(0)}ms
              </span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div 
                className={cn(
                  "h-2 rounded-full transition-all duration-1000",
                  systemMetrics.networkLatency < 30 
                    ? "bg-gradient-to-r from-green-500 to-emerald-500"
                    : systemMetrics.networkLatency < 50
                    ? "bg-gradient-to-r from-yellow-500 to-orange-500"
                    : "bg-gradient-to-r from-red-500 to-rose-500"
                )}
                style={{ width: `${Math.min(systemMetrics.networkLatency * 2, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
