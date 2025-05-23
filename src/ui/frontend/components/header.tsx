"use client"

import type React from "react"

import { Cpu, Shield, Wifi, Menu, X, User, Settings, LogOut } from "lucide-react"
import { useState, useEffect, useRef } from "react"
import VoiceControl from "./voice-control"

interface HeaderProps {
  userName: string
}

export default function Header({ userName }: HeaderProps) {
  const [time, setTime] = useState<Date | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // İlk render'da saati ayarla
    setTime(new Date())

    const timer = setInterval(() => {
      setTime(new Date())
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  return (
    <header className="w-full jarvis-gradient backdrop-blur-md border-b border-sky-500/20 p-4 flex justify-between items-center z-20 shadow-[0_4px_15px_rgba(0,120,215,0.1)]">
      <div className="flex items-center">
        <div className="relative mr-4 group">
          <div className="w-10 h-10 rounded-md bg-sky-900/30 flex items-center justify-center transition-all duration-300 group-hover:scale-110 border border-sky-700/30">
            <div className="w-8 h-8 rounded-md bg-sky-800/50 flex items-center justify-center transition-all duration-300 group-hover:bg-sky-800/70">
              <div className="w-6 h-6 rounded-md bg-sky-700/70 flex items-center justify-center transition-all duration-300 group-hover:bg-sky-700/90">
                <div className="w-4 h-4 rounded-md bg-sky-500 animate-pulse"></div>
              </div>
            </div>
          </div>
          <div className="absolute -bottom-1 -right-1 w-3 h-3 rounded-full bg-emerald-500 border border-slate-900"></div>
        </div>
        <div>
          <h1 className="text-2xl font-medium tracking-wider text-sky-400 flex items-center jarvis-text-glow">
            Z.E.K.A
            <span className="ml-2 text-xs bg-sky-900/50 px-2 py-0.5 rounded-md text-sky-300 border border-sky-700/30">v1.0</span>
          </h1>
          <p className="text-xs text-sky-500/60 font-mono hidden sm:block">Zenginleştirilmiş Etkileşimli Kişisel Asistan</p>
        </div>
      </div>

      {/* Desktop View */}
      <div className="hidden md:flex items-center space-x-6">
        <StatusIndicator icon={<Cpu size={16} />} label="AI Core" status="green" />
        <StatusIndicator icon={<Wifi size={16} />} label="Network" status="green" />
        <StatusIndicator icon={<Shield size={16} />} label="Security" status="orange" />
        <VoiceControl
          compact={true}
          className="bg-slate-800/40 backdrop-blur-sm px-2 py-1 rounded-md border border-sky-700/30"
          onVoiceInput={(text) => console.log("Voice input:", text)}
        />
        <div className="text-white font-mono ml-1 bg-slate-800/40 backdrop-blur-sm px-3 py-1.5 rounded-md border border-sky-700/30 shadow-[inset_0_0_10px_rgba(0,120,215,0.05)]">
          {time ? time.toLocaleTimeString() : "--:--:--"} <span className="text-sky-600">|</span> {userName}
        </div>
      </div>

      {/* Mobile View */}
      <div className="flex md:hidden items-center">
        <div className="text-white font-mono mr-4 bg-slate-800/70 px-3 py-1.5 rounded-md border border-sky-700/30 shadow-[inset_0_0_10px_rgba(0,120,215,0.05)]">
          {time ? time.toLocaleTimeString() : "--:--:--"}
        </div>
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="p-2 rounded-md bg-slate-800/70 border border-sky-700/30 text-sky-400 hover:bg-sky-900/30 transition-colors"
        >
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        {/* Mobile Menu */}
        {menuOpen && (
          <div
            ref={menuRef}
            className="absolute top-16 right-4 jarvis-panel p-4 z-50 w-64 animate-fadeIn"
          >
            <div className="flex items-center mb-4 pb-3 border-b border-sky-900/30">
              <div className="relative">
                <User size={18} className="text-sky-400 mr-2" />
                <div className="absolute -bottom-1 -right-1 w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
              </div>
              <div>
                <span className="text-white">{userName}</span>
                <div className="text-xs text-sky-500/60">Active User</div>
              </div>
            </div>

            <div className="space-y-3 mb-4">
              <StatusIndicator icon={<Cpu size={16} />} label="AI Core" status="green" />
              <StatusIndicator icon={<Wifi size={16} />} label="Network" status="green" />
              <StatusIndicator icon={<Shield size={16} />} label="Security" status="orange" />
              <VoiceControl
                onVoiceInput={(text) => console.log("Voice input:", text)}
              />
            </div>

            <div className="space-y-2 pt-3 border-t border-sky-900/30">
              <button className="w-full flex items-center p-2.5 text-slate-300 hover:bg-sky-900/20 rounded-md transition-colors group border border-sky-900/10">
                <Settings size={16} className="mr-2 group-hover:text-sky-400 transition-colors" />
                <span className="group-hover:text-white transition-colors">Settings</span>
              </button>
              <button className="w-full flex items-center p-2.5 text-slate-300 hover:bg-red-900/20 rounded-md transition-colors group border border-sky-900/10">
                <LogOut size={16} className="mr-2 group-hover:text-red-400 transition-colors" />
                <span className="group-hover:text-white transition-colors">Logout</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}

function StatusIndicator({
  icon,
  label,
  status,
}: {
  icon: React.ReactNode
  label: string
  status: "green" | "orange" | "red"
}) {
  const statusColors = {
    green: "text-emerald-400",
    orange: "text-amber-400",
    red: "text-rose-400",
  }

  const statusBg = {
    green: "bg-emerald-500/10",
    orange: "bg-amber-500/10",
    red: "bg-rose-500/10",
  }

  const statusBorder = {
    green: "border-emerald-500/20",
    orange: "border-amber-500/20",
    red: "border-rose-500/20",
  }

  const statusGlow = {
    green: "shadow-[0_0_5px_rgba(16,185,129,0.3)]",
    orange: "shadow-[0_0_5px_rgba(245,158,11,0.3)]",
    red: "shadow-[0_0_5px_rgba(244,63,94,0.3)]",
  }

  const statusPulse = {
    green: "animate-pulse",
    orange: "animate-pulse",
    red: "animate-ping",
  }

  return (
    <div className={`flex items-center ${statusBg[status]} px-2.5 py-1.5 rounded-md border ${statusBorder[status]} transition-all duration-300 hover:bg-slate-800/40 ${statusGlow[status]}`}>
      <div className="text-slate-300 mr-1.5">{icon}</div>
      <div className="text-xs">
        <span className="text-slate-300">{label}</span>
        <span className={`ml-1.5 ${statusColors[status]} ${statusPulse[status]}`}>●</span>
      </div>
    </div>
  )
}
