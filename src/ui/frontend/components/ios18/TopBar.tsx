"use client"

import { useState, useEffect, memo, useCallback } from "react"
import { Mic, MicOff, Wifi, WifiOff, Cpu, Activity } from "lucide-react"
import { cn } from "@/lib/utils"
import { useWebSocket } from "@/hooks/useWebSocket"

interface TopBarProps {
  userName?: string
  onVoiceToggle?: (isActive: boolean) => void
  className?: string
}

const TopBar = memo(function TopBar({
  userName = "Ali",
  onVoiceToggle,
  className
}: TopBarProps) {
  const [currentTime, setCurrentTime] = useState("")
  const [isVoiceActive, setIsVoiceActive] = useState(false)
  const [systemLoad, setSystemLoad] = useState(0)

  // WebSocket connection status
  const { connected, connecting } = useWebSocket("/api/ws/chat")

  // Update time every second
  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setCurrentTime(now.toLocaleTimeString('tr-TR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }))
    }

    updateTime()
    const interval = setInterval(updateTime, 1000)
    return () => clearInterval(interval)
  }, [])

  // Simulate system load
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemLoad(Math.random() * 100)
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  const handleVoiceToggle = useCallback(() => {
    const newState = !isVoiceActive
    setIsVoiceActive(newState)
    onVoiceToggle?.(newState)
  }, [isVoiceActive, onVoiceToggle])

  const getGreeting = useCallback(() => {
    const hour = new Date().getHours()
    if (hour < 12) return "Günaydın"
    if (hour < 18) return "İyi günler"
    return "İyi akşamlar"
  }, [])

  return (
    <div className={cn("ios-topbar", className)}>
      {/* Left Section - Logo & Greeting */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-3">
          {/* ZEKA Logo */}
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">Z</span>
          </div>

          {/* Greeting */}
          <div className="flex flex-col">
            <span className="ios-text-primary text-sm font-medium">
              {getGreeting()}, {userName}
            </span>
            <span className="ios-text-secondary text-xs">
              Z.E.K.A Asistanınız hazır
            </span>
          </div>
        </div>
      </div>

      {/* Center Section - System Status */}
      <div className="flex items-center space-x-6">
        {/* Connection Status */}
        <div className="flex items-center space-x-2">
          {connected ? (
            <Wifi size={16} className="text-green-400" />
          ) : connecting ? (
            <WifiOff size={16} className="text-yellow-400 animate-pulse" />
          ) : (
            <WifiOff size={16} className="text-red-400" />
          )}
          <span className="ios-text-secondary text-xs">
            {connected ? "Bağlı" : connecting ? "Bağlanıyor" : "Bağlantı Yok"}
          </span>
        </div>

        {/* System Load */}
        <div className="flex items-center space-x-2">
          <Activity size={16} className="ios-text-secondary" />
          <span className="ios-text-secondary text-xs">
            CPU: {systemLoad.toFixed(0)}%
          </span>
        </div>

        {/* Current Time */}
        <div className="flex items-center space-x-2">
          <span className="ios-text-primary text-sm font-mono">
            {currentTime}
          </span>
        </div>
      </div>

      {/* Right Section - Voice Control */}
      <div className="flex items-center space-x-4">
        {/* Voice Control - Dynamic Island Style */}
        <div
          className={cn(
            "flex items-center space-x-3 px-4 py-2 rounded-full transition-all duration-300 cursor-pointer",
            "border border-white/20 backdrop-blur-md",
            isVoiceActive
              ? "bg-blue-500/30 border-blue-400/50 shadow-lg shadow-blue-500/20"
              : "bg-white/10 hover:bg-white/15"
          )}
          onClick={handleVoiceToggle}
        >
          {isVoiceActive ? (
            <Mic size={16} className="text-blue-400" />
          ) : (
            <MicOff size={16} className="ios-text-secondary" />
          )}

          <span className={cn(
            "text-xs font-medium transition-colors",
            isVoiceActive ? "text-blue-400" : "ios-text-secondary"
          )}>
            {isVoiceActive ? "Dinliyor" : "Ses Kontrolü"}
          </span>

          {/* Voice Activity Indicator */}
          {isVoiceActive && (
            <div className="flex items-center space-x-1">
              <div className="w-1 h-2 bg-blue-400 rounded-full animate-pulse"></div>
              <div className="w-1 h-3 bg-blue-400 rounded-full animate-pulse delay-75"></div>
              <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse delay-150"></div>
            </div>
          )}
        </div>

        {/* System Menu Button */}
        <button className="p-2 rounded-full bg-white/10 hover:bg-white/15 transition-all duration-200 border border-white/20">
          <Cpu size={16} className="ios-text-secondary" />
        </button>
      </div>
    </div>
  )
})

export default TopBar
