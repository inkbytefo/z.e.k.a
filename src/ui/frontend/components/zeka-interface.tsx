"use client"

import { useState, useEffect } from "react"
import dynamic from "next/dynamic"
import { cn } from "@/lib/utils"
import { sendChatMessage, getConversationHistory, type Message } from "@/lib/api"
import { useWebSocket } from "@/hooks/useWebSocket"

// iOS 18 Components
import TopBar from "@/components/ios18/TopBar"
import SystemStatusPanel from "@/components/ios18/SystemStatusPanel"
import ConversationPanel from "@/components/ios18/ConversationPanel"
import ControlCenterPanel from "@/components/ios18/ControlCenterPanel"

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
        "w-full h-screen relative overflow-hidden transition-all duration-1000",
        initialized ? "opacity-100" : "opacity-0"
      )}
      style={{ background: "var(--ios-background-primary)" }}
    >
      {/* Enhanced 3D Background */}
      <div className="absolute inset-0 z-0 opacity-60">
        <ThreeDBackground />
      </div>

      {/* iOS 18 Layout */}
      <div className="ios-layout relative z-10">
        {/* Top Bar */}
        <TopBar
          userName={userName}
          onVoiceToggle={(isActive) => console.log("Voice toggle:", isActive)}
        />

        {/* System Status Panel (Left) */}
        <SystemStatusPanel
          currentModel={currentModel}
        />

        {/* Conversation Panel (Center) */}
        <ConversationPanel
          messages={messages}
          onSendMessage={addMessage}
          isLoading={isLoading}
        />

        {/* Control Center Panel (Right) */}
        <ControlCenterPanel
          onModelChange={handleModelChange}
        />
      </div>
    </div>
  )
}