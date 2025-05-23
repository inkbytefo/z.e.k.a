"use client"

import { useState, useEffect } from "react"
import dynamic from "next/dynamic"
import ConversationHub from "@/components/conversation-hub"
import RealtimeConversationHub from "@/components/realtime-conversation-hub"
import Widgets from "@/components/widgets"
import Header from "@/components/header"
import { cn } from "@/lib/utils"
import { sendChatMessage, getConversationHistory, type Message } from "@/lib/api"
import { useWebSocket } from "@/hooks/useWebSocket"

// Dynamically import the 3D components with no SSR to avoid hydration issues
const ThreeDBackground = dynamic(() => import("@/components/three-d-background"), {
  ssr: false,
})

export default function ZekaInterface() {
  const [initialized, setInitialized] = useState(false)
  const [userName, setUserName] = useState("Ali")
  const [timeOfDay, setTimeOfDay] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentModel, setCurrentModel] = useState<string>("")
  const [useRealtime, setUseRealtime] = useState(true)

  // WebSocket bağlantı durumu
  const { connected, connecting } = useWebSocket("/api/ws/chat")

  useEffect(() => {
    // Get time of day for personalized greeting
    const hour = new Date().getHours()
    let greeting = "Good morning"
    if (hour >= 12 && hour < 18) greeting = "Good afternoon"
    else if (hour >= 18) greeting = "Good evening"
    setTimeOfDay(greeting)

    // Başlangıç animasyonu ve sohbet geçmişini yükleme
    const initializeInterface = async () => {
      // Önce animasyonu başlat
      setTimeout(() => {
        setInitialized(true)
      }, 1000)

      try {
        // Sohbet geçmişini yükle
        const history = await getConversationHistory(10)

        // Eğer geçmiş boşsa, karşılama mesajı ekle
        if (history.length === 0) {
          setMessages([
            {
              role: "assistant",
              content: `${greeting}, ${userName}. Size nasıl yardımcı olabilirim?`,
            },
          ])
        } else {
          setMessages(history)
        }
      } catch (error) {
        console.error("Sohbet geçmişi yüklenirken hata:", error)
        // Hata durumunda varsayılan karşılama mesajı
        setMessages([
          {
            role: "assistant",
            content: `${greeting}, ${userName}. Size nasıl yardımcı olabilirim?`,
          },
        ])
      }
    }

    initializeInterface()
  }, [userName])

  const addMessage = async (message: string) => {
    // Kullanıcı mesajını ekle
    setMessages((prev) => [...prev, { role: "user", content: message }])

    // Yükleniyor durumunu ayarla
    setIsLoading(true)

    try {
      // API'ye mesajı gönder (eğer model seçilmişse o modeli kullan)
      const response = await sendChatMessage(message, currentModel || undefined)

      // Asistan yanıtını ekle
      if (response.success) {
        // Yanıt başarılıysa ve model bilgisi varsa, mevcut modeli güncelle
        if (response.model) {
          setCurrentModel(response.model)
        }

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: response.response,
          },
        ])
      } else {
        // Hata durumunda kullanıcıya bilgi ver
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Üzgünüm, mesajınızı işlerken bir sorun oluştu. Lütfen tekrar deneyin.",
          },
        ])
      }
    } catch (error) {
      console.error("Mesaj gönderilirken hata:", error)
      // Hata durumunda kullanıcıya bilgi ver
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Üzgünüm, bir bağlantı hatası oluştu. Lütfen internet bağlantınızı kontrol edip tekrar deneyin.",
        },
      ])
    } finally {
      // Yükleniyor durumunu kapat
      setIsLoading(false)
    }
  }

  // Model değiştiğinde çağrılacak fonksiyon
  const handleModelChange = (model: string) => {
    setCurrentModel(model)
  }

  return (
    <div
      className={cn(
        "w-full h-screen flex flex-col bg-gradient-to-br from-slate-900 to-slate-800 text-white font-light transition-all duration-1000",
        initialized ? "opacity-100 scale-100" : "opacity-0 scale-95",
      )}
    >
      <Header userName={userName} />

      <div className="flex-1 flex flex-col md:flex-row overflow-hidden relative">
        {/* 3D Background */}
        <div className="absolute inset-0 z-0 opacity-30">
          <ThreeDBackground />
        </div>

        {/* Main Interface - Using new flexible layout system */}
        <div className="z-10 zeka-layout">
          {/* Left Panel - Widgets */}
          <div className="w-full lg:w-1/4 space-y-4 order-2 lg:order-1 transition-all duration-500">
            <Widgets onModelChange={handleModelChange} />
          </div>

          {/* Center Panel - Conversation */}
          <div className="w-full lg:w-2/4 flex-1 flex flex-col order-1 lg:order-2 transition-all duration-500">
            <div className="mb-4 flex justify-between items-center">
              <div className="flex items-center">
                <h2 className="text-sky-400 text-lg font-medium jarvis-text-glow">Z.E.K.A</h2>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setUseRealtime(!useRealtime)}
                  className={cn(
                    "px-4 py-1.5 rounded-md text-xs font-medium transition-all duration-300 jarvis-border",
                    useRealtime
                      ? "bg-gradient-to-r from-sky-800/70 to-sky-900/70 hover:from-sky-700/70 hover:to-sky-800/70 shadow-md"
                      : "bg-gradient-to-r from-slate-700/70 to-slate-800/70 hover:from-slate-600/70 hover:to-slate-700/70"
                  )}
                >
                  <span>{useRealtime ? "Gerçek Zamanlı Mod" : "Standart Mod"}</span>
                </button>
              </div>
            </div>

            <div className="flex-1 transition-all duration-500 shadow-xl zeka-panel zeka-panel-resizable">
              {useRealtime ? (
                <RealtimeConversationHub initialMessages={messages} currentModel={currentModel} />
              ) : (
                <ConversationHub messages={messages} onSendMessage={addMessage} />
              )}
            </div>
          </div>

          {/* Right Panel - System Status */}
          <div className="w-full lg:w-1/4 space-y-4 order-3 transition-all duration-500">
            <div className="zeka-panel p-4 h-full">
              <div className="zeka-panel-header">
                <h3 className="text-sky-400 font-medium flex items-center">
                  <div className="w-1.5 h-1.5 rounded-full bg-sky-400 mr-2 animate-pulse"></div>
                  System Status
                </h3>
              </div>
              <div className="zeka-panel-content space-y-3">
                <StatusItem label="Core Systems" value="Online" status="green" />
                <StatusItem label="Neural Network" value="Active" status="green" />
                <StatusItem label="Security Protocol" value="Engaged" status="orange" />
                <StatusItem label="Data Processing" value="Optimal" status="green" />
                <StatusItem label="Voice Recognition" value="Ready" status="green" />
                <StatusItem label="WebSocket" value={connected ? "Connected" : connecting ? "Connecting" : "Disconnected"} status={connected ? "green" : connecting ? "orange" : "red"} />
                <StatusItem label="Current Model" value={currentModel ? currentModel.split('/').pop() || "Default" : "Default"} status="green" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatusItem({ label, value, status }: { label: string; value: string; status: "green" | "orange" | "red" }) {
  const statusColors = {
    green: "bg-emerald-500",
    orange: "bg-amber-500",
    red: "bg-rose-500",
  }

  const statusGlow = {
    green: "shadow-[0_0_5px_rgba(16,185,129,0.5)]",
    orange: "shadow-[0_0_5px_rgba(245,158,11,0.5)]",
    red: "shadow-[0_0_5px_rgba(244,63,94,0.5)]",
  }

  return (
    <div className="flex justify-between items-center p-2.5 rounded-md hover:bg-sky-900/10 transition-colors border border-sky-900/20">
      <span className="text-slate-300">{label}</span>
      <div className="flex items-center">
        <span className="text-white mr-2 font-mono text-sm">{value}</span>
        <div className={`w-2 h-2 rounded-full ${statusColors[status]} ${statusGlow[status]} animate-pulse`}></div>
      </div>
    </div>
  )
}
