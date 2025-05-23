"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import {
  Send, Mic, MicOff, Volume2, VolumeX, Wifi, WifiOff,
  AlertCircle, Loader2, RefreshCw, Wand2
} from "lucide-react"
import useSpeechRecognition from "@/hooks/useSpeechRecognition"
import useSpeechSynthesis from "@/hooks/useSpeechSynthesis"
import { useWebSocket } from "@/hooks/useWebSocket"

interface Message {
  role: string
  content: string
  typing?: boolean
  model?: string
  timestamp?: string
}

interface RealtimeConversationHubProps {
  initialMessages?: Message[]
  onSendMessage?: (message: string) => void
  currentModel?: string
}

export default function RealtimeConversationHub({
  initialMessages = [],
  onSendMessage,
  currentModel
}: RealtimeConversationHubProps) {
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isTyping, setIsTyping] = useState(false)
  const [currentAssistantMessage, setCurrentAssistantMessage] = useState("")
  const [activeModel, setActiveModel] = useState<string>(currentModel || "")
  const [isRecording, setIsRecording] = useState(false)
  const [recordingProgress, setRecordingProgress] = useState(0)
  const [recordingDuration, setRecordingDuration] = useState(5) // saniye
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)

  // WebSocket bağlantısı
  const {
    connected,
    connecting,
    messages: wsMessages,
    sendMessage,
    error: wsError,
    clearMessages,
    connect
  } = useWebSocket("/api/ws/chat")

  // Bağlantı durumunu konsola yazdır ve hata durumunu güncelle
  useEffect(() => {
    console.log("WebSocket bağlantı durumu:", { connected, connecting, error: wsError })

    if (wsError) {
      setError(`Bağlantı hatası: ${wsError}`)
    } else if (connected) {
      setError(null)
    }
  }, [connected, connecting, wsError])

  // Bileşen yüklendiğinde mesajları temizle ve bağlantıyı kur
  useEffect(() => {
    clearMessages()
    // Bağlantıyı başlat (connect fonksiyonu varsa)
    if (typeof connect === 'function') {
      connect()
    }

    // Karşılama mesajı ekle (eğer başlangıç mesajları boşsa)
    if (initialMessages.length === 0) {
      setMessages([
        {
          role: "assistant",
          content: "Merhaba! Size nasıl yardımcı olabilirim?",
          timestamp: new Date().toISOString()
        }
      ])
    }
  }, [clearMessages, connect, initialMessages])

  // Web Speech API için hook'ları kullan
  const {
    isListening,
    transcript,
    startListening,
    stopListening,
    resetTranscript,
    browserSupportsSpeechRecognition,
    error: recognitionError
  } = useSpeechRecognition({
    language: 'tr-TR',
    continuous: false,
    interimResults: true
  })

  // Ses sentezleme hook'u
  const {
    speak,
    stop: stopSpeaking,
    isSpeaking: isSynthesisSpeaking,
    browserSupportsSpeechSynthesis,
    error: synthesisError
  } = useSpeechSynthesis({
    defaultRate: 1.1 // Biraz daha hızlı konuşma
  })

  // WebSocket mesajlarını işle
  useEffect(() => {
    if (wsMessages.length === 0) return

    const lastMessage = wsMessages[wsMessages.length - 1]
    console.log("İşlenen WebSocket mesajı:", lastMessage)

    switch (lastMessage.type) {
      case "connected":
        console.log("WebSocket bağlantısı başarıyla kuruldu:", lastMessage)
        setError(null)
        // Bağlantı ID'sini göster
        if (lastMessage.connection_id) {
          console.log("Bağlantı ID:", lastMessage.connection_id)
        }
        break

      case "user_message":
        // Kullanıcı mesajını ekle
        setMessages(prev => [
          ...prev,
          {
            role: "user",
            content: lastMessage.message,
            timestamp: lastMessage.timestamp || new Date().toISOString()
          }
        ])
        break

      case "assistant_message_start":
        // Asistan yanıtı başladı
        setIsTyping(true)
        setCurrentAssistantMessage("")
        // Model bilgisini kaydet
        if (lastMessage.model) {
          setActiveModel(lastMessage.model)
        }
        break

      case "assistant_message_chunk":
        // Asistan yanıtı parçası geldi
        setCurrentAssistantMessage(prev => prev + lastMessage.chunk)
        break

      case "assistant_message_end":
        // Asistan yanıtı tamamlandı
        setIsTyping(false)
        setMessages(prev => [
          ...prev,
          {
            role: "assistant",
            content: currentAssistantMessage,
            model: activeModel,
            timestamp: lastMessage.timestamp || new Date().toISOString()
          }
        ])

        // Otomatik sesli okuma özelliği (isteğe bağlı olarak etkinleştirilebilir)
        // if (browserSupportsSpeechSynthesis && currentAssistantMessage) {
        //   speak(currentAssistantMessage)
        //   setIsSpeaking(true)
        // }
        break

      case "speech_recognition_start":
        // Ses tanıma başladı
        console.log("Ses tanıma başladı")
        setError("Ses tanınıyor...")
        break

      case "speech_recognition_result":
        // Ses tanıma sonucu
        setInput(lastMessage.text)
        setError(null)

        // Otomatik gönderme özelliği (isteğe bağlı olarak etkinleştirilebilir)
        // if (lastMessage.text && connected) {
        //   sendMessage({
        //     type: "chat",
        //     message: lastMessage.text,
        //     user_id: "default_user",
        //     language: "tr",
        //     style: "friendly",
        //     model: currentModel
        //   })
        // }
        break

      case "error":
        // Hata mesajı
        setError(lastMessage.message)
        break

      default:
        console.log("Bilinmeyen mesaj tipi:", lastMessage.type)
    }
  }, [wsMessages, currentAssistantMessage, currentModel, browserSupportsSpeechSynthesis, connected, speak])

  // Transcript değiştiğinde input'u güncelle
  useEffect(() => {
    if (transcript) {
      setInput(transcript)
    }
  }, [transcript])

  // Mesajlar değiştiğinde en alta kaydır
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, currentAssistantMessage])

  // Hata durumlarını kontrol et
  useEffect(() => {
    if (recognitionError) {
      setError(`Ses tanıma hatası: ${recognitionError}`)
    } else if (synthesisError) {
      setError(`Ses sentezleme hatası: ${synthesisError}`)
    }
    // wsError durumu ayrı bir useEffect'te ele alınıyor
  }, [recognitionError, synthesisError])

  // Ses kaydı ilerleme çubuğu için zamanlayıcı
  useEffect(() => {
    if (isRecording) {
      const interval = 100 // 100ms aralıklarla güncelle
      const steps = recordingDuration * 1000 / interval
      let currentStep = 0

      // İlerleme çubuğunu sıfırla
      setRecordingProgress(0)

      // Zamanlayıcıyı başlat
      recordingTimerRef.current = setInterval(() => {
        currentStep++
        const progress = (currentStep / steps) * 100
        setRecordingProgress(progress)

        // Kayıt tamamlandığında zamanlayıcıyı durdur
        if (currentStep >= steps) {
          if (recordingTimerRef.current) {
            clearInterval(recordingTimerRef.current)
            recordingTimerRef.current = null
          }
          setIsRecording(false)
          setRecordingProgress(0)
        }
      }, interval)

      return () => {
        if (recordingTimerRef.current) {
          clearInterval(recordingTimerRef.current)
          recordingTimerRef.current = null
        }
      }
    }
  }, [isRecording, recordingDuration])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && connected) {
      console.log("Mesaj gönderiliyor:", input)

      // WebSocket üzerinden mesaj gönder
      sendMessage({
        type: "chat",
        message: input,
        user_id: "default_user",
        language: "tr",
        style: "friendly",
        model: activeModel
      })

      // Kullanıcı arayüzünü güncelle
      setInput("")
      resetTranscript()

      // Opsiyonel callback
      if (onSendMessage) {
        onSendMessage(input)
      }
    } else {
      if (!connected) {
        setError("WebSocket bağlantısı kurulamadı. Lütfen sayfayı yenileyin.")
      } else if (!input.trim()) {
        setError("Lütfen bir mesaj girin veya ses kaydı yapın.")
        setTimeout(() => setError(null), 2000) // 2 saniye sonra hata mesajını kaldır
      }
    }
  }



  // Tarayıcı Web Speech API ile ses tanıma
  const toggleVoiceInput = () => {
    if (!browserSupportsSpeechRecognition) {
      setError("Tarayıcınız Web Speech API'yi desteklemiyor.")
      return
    }

    if (isListening) {
      stopListening()
    } else {
      setError(null)
      resetTranscript()
      startListening()
    }
  }

  // Ses kaydı butonuna tıklandığında (WebSocket üzerinden ses tanıma)
  const handleVoiceButtonClick = () => {
    if (connected) {
      if (isRecording) {
        // Zaten kayıt yapılıyorsa, durdur
        if (recordingTimerRef.current) {
          clearInterval(recordingTimerRef.current)
          recordingTimerRef.current = null
        }
        setIsRecording(false)
        setRecordingProgress(0)
        setError("Ses kaydı iptal edildi")
        setTimeout(() => setError(null), 2000)
      } else {
        // Kayıt başlat
        setIsRecording(true)
        handleVoiceInput()
      }
    } else {
      setError("WebSocket bağlantısı kurulamadı. Lütfen sayfayı yenileyin.")
    }
  }

  // Mesajı sesli okuma/durdurma
  const toggleSpeakMessage = (content: string) => {
    if (!browserSupportsSpeechSynthesis) {
      setError("Tarayıcınız ses sentezleme özelliğini desteklemiyor.")
      return
    }

    if (isSynthesisSpeaking) {
      stopSpeaking()
      setIsSpeaking(false)
    } else {
      speak(content)
      setIsSpeaking(true)
    }
  }

  // Ses kaydını WebSocket üzerinden gönder
  const handleVoiceInput = async () => {
    if (connected) {
      try {
        setError("Ses kaydı başlatılıyor...")
        console.log("Ses kaydı başlatılıyor...")

        // Ses kaydını başlat
        const audioBlob = await navigator.mediaDevices.getUserMedia({ audio: true })
          .then(stream => {
            const mediaRecorder = new MediaRecorder(stream)
            const audioChunks: BlobPart[] = []

            return new Promise<Blob>((resolve) => {
              mediaRecorder.addEventListener("dataavailable", (event) => {
                audioChunks.push(event.data)
              })

              mediaRecorder.addEventListener("stop", () => {
                // WAV yerine webm formatını kullanalım (tarayıcılar için daha uyumlu)
                const audioBlob = new Blob(audioChunks, { type: "audio/webm" })
                console.log("Ses kaydı tamamlandı, format:", audioBlob.type, "boyut:", audioBlob.size)
                resolve(audioBlob)
              })

              // Kayıt başladı bilgisi
              console.log(`Ses kaydı başladı - ${recordingDuration} saniye sürecek`)
              mediaRecorder.start()

              // Belirtilen süre sonra kaydı durdur
              setTimeout(() => {
                console.log("Ses kaydı durduruluyor...")
                mediaRecorder.stop()
                stream.getTracks().forEach(track => track.stop())
              }, recordingDuration * 1000)
            })
          })

        // Ses verisini Base64'e dönüştür
        const reader = new FileReader()
        reader.readAsDataURL(audioBlob)
        reader.onloadend = () => {
          const base64data = reader.result as string
          // Base64 verinin başındaki "data:audio/webm;base64," kısmını kaldır
          const base64Audio = base64data.split(",")[1]

          console.log("Ses kaydı tamamlandı, WebSocket üzerinden gönderiliyor...")
          setError("Ses kaydınız işleniyor...")

          // WebSocket üzerinden ses verisini gönder
          sendMessage({
            type: "voice",
            audio_data: base64Audio,
            language: "tr"
          })
        }
      } catch (error) {
        console.error("Ses kaydı hatası:", error)
        setError(`Ses kaydı hatası: ${error instanceof Error ? error.message : String(error)}`)
        setIsRecording(false)
        setRecordingProgress(0)
      }
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Bağlantı Durumu Göstergesi */}
      <div className={cn(
        "px-3 py-2 flex items-center justify-between border-b transition-colors rounded-t-lg",
        connected
          ? "border-emerald-500/30 bg-emerald-950/10"
          : connecting
            ? "border-amber-500/30 bg-amber-950/10"
            : "border-rose-500/30 bg-rose-950/10"
      )}>
        <div className="flex items-center">
          {connected ? (
            <Wifi size={14} className="text-emerald-400 mr-2" />
          ) : connecting ? (
            <Loader2 size={14} className="text-amber-400 mr-2 animate-spin" />
          ) : (
            <WifiOff size={14} className="text-rose-400 mr-2" />
          )}
          <span className={cn(
            "text-xs font-medium",
            connected
              ? "text-emerald-400"
              : connecting
                ? "text-amber-400"
                : "text-rose-400"
          )}>
            {connected
              ? "Bağlantı Kuruldu"
              : connecting
                ? "Bağlanıyor..."
                : "Bağlantı Kesildi"}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {!connected && !connecting && (
            <button
              onClick={() => connect()}
              className="text-xs bg-sky-600/50 hover:bg-sky-600/80 px-2 py-0.5 rounded-md text-white flex items-center"
            >
              <RefreshCw size={10} className="mr-1" />
              Yeniden Bağlan
            </button>
          )}

          {currentModel && (
            <div className="text-xs text-sky-400 flex items-center border border-sky-700/30 px-2 py-0.5 rounded-md bg-sky-900/20">
              <Wand2 size={10} className="mr-1" />
              {currentModel.split('/').pop()}
            </div>
          )}
        </div>
      </div>

      {/* Mesaj Alanı */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-transparent backdrop-blur-sm border-x border-sky-700/20">
        {messages.map((message, index) => (
          <div
            key={index}
            className={cn(
              "flex flex-col rounded-md p-3 shadow-lg transition-all duration-300",
              message.role === "user"
                ? "ml-auto max-w-[80%] bg-sky-900/40 backdrop-blur-sm border border-sky-700/30 hover:bg-sky-900/50"
                : "mr-auto max-w-[85%] bg-slate-800/40 backdrop-blur-sm border border-slate-700/30 hover:bg-slate-800/50"
            )}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <span className={cn(
                  "text-xs font-medium",
                  message.role === "user" ? "text-amber-300" : "text-sky-300"
                )}>
                  {message.role === "user" ? "Sen" : "ZEKA"}
                </span>
                {message.model && message.role === "assistant" && (
                  <span className="ml-2 text-[10px] text-slate-300 bg-sky-900/30 px-1.5 py-0.5 rounded-sm">
                    {message.model.split('/').pop()}
                  </span>
                )}
              </div>

              <div className="flex items-center">
                {message.timestamp && (
                  <span className="text-[10px] text-slate-300 mr-2">
                    {new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </span>
                )}

                {message.role === "assistant" && (
                  <button
                    onClick={() => toggleSpeakMessage(message.content)}
                    className={cn(
                      "text-slate-300 hover:text-sky-400 transition-colors",
                      isSpeaking && "text-sky-400 animate-pulse"
                    )}
                    title={isSpeaking ? "Sesi durdur" : "Sesli dinle"}
                  >
                    {isSpeaking ? <VolumeX size={14} /> : <Volume2 size={14} />}
                  </button>
                )}
              </div>
            </div>
            <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
          </div>
        ))}

        {/* Yazıyor göstergesi */}
        {isTyping && (
          <div className="flex flex-col max-w-[85%] rounded-md p-3 mr-auto bg-slate-800/40 backdrop-blur-sm border border-sky-700/30 shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <span className="text-xs font-medium text-sky-300">ZEKA</span>
                {currentModel && (
                  <span className="ml-2 text-[10px] text-slate-300 bg-sky-900/30 px-1.5 py-0.5 rounded-sm">
                    {currentModel.split('/').pop()}
                  </span>
                )}
              </div>
              <div className="flex space-x-1">
                <div className="w-1 h-3 bg-sky-400 animate-pulse rounded-full"></div>
                <div className="w-1 h-5 bg-sky-400 animate-pulse rounded-full"></div>
                <div className="w-1 h-2 bg-sky-400 animate-pulse rounded-full"></div>
              </div>
            </div>
            <p className="text-sm whitespace-pre-wrap leading-relaxed">{currentAssistantMessage}</p>
          </div>
        )}

        {/* Hata mesajı */}
        {error && (
          <div className="max-w-full rounded-md p-3 mx-auto bg-rose-900/30 border border-rose-700/30 shadow-lg">
            <div className="flex items-center">
              <AlertCircle size={14} className="text-rose-400 mr-2" />
              <p className="text-sm text-rose-200">{error}</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Giriş Alanı */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-sky-700/20 bg-slate-800/40 backdrop-blur-sm rounded-b-lg">
        <div className="flex items-center gap-3">
          {/* Tarayıcı Web Speech API ses tanıma butonu */}
          <button
            type="button"
            onClick={toggleVoiceInput}
            className={cn(
              "p-2.5 rounded-md transition-colors",
              isListening
                ? "bg-rose-600 hover:bg-rose-700 animate-pulse"
                : "bg-slate-800/40 backdrop-blur-sm border border-sky-700/30 hover:bg-sky-900/30"
            )}
            title={isListening ? "Ses kaydını durdur" : "Tarayıcı ses tanıma"}
            disabled={!browserSupportsSpeechRecognition}
          >
            {isListening ? <MicOff size={20} /> : <Mic size={20} />}
          </button>

          {/* WebSocket üzerinden ses tanıma butonu */}
          <button
            type="button"
            onClick={handleVoiceButtonClick}
            className={cn(
              "p-2.5 rounded-md transition-colors relative",
              isRecording
                ? "bg-violet-600 hover:bg-violet-700 animate-pulse"
                : "bg-slate-800/40 backdrop-blur-sm border border-sky-700/30 hover:bg-sky-900/30"
            )}
            title={isRecording ? "Ses kaydını durdur" : `Ses kaydı (5 saniye)`}
            disabled={!connected}
          >
            <Mic size={20} />

            {/* Kayıt ilerleme göstergesi */}
            {isRecording && (
              <div className="absolute inset-0 rounded-md overflow-hidden">
                <div
                  className="absolute bottom-0 left-0 right-0 bg-violet-400/30"
                  style={{ height: `${recordingProgress}%` }}
                ></div>
              </div>
            )}
          </button>

          <div className="relative flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Mesajınızı yazın..."
              className="w-full bg-slate-800/40 backdrop-blur-sm border border-sky-700/30 rounded-md px-4 py-3 text-white placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500/50 transition-all"
              ref={inputRef}
              disabled={!connected}
            />

            {/* Dinleme göstergesi */}
            {isListening && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="flex space-x-1">
                  <div className="w-1 h-3 bg-sky-400 animate-pulse rounded-full"></div>
                  <div className="w-1 h-5 bg-sky-400 animate-pulse rounded-full"></div>
                  <div className="w-1 h-2 bg-sky-400 animate-pulse rounded-full"></div>
                </div>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={!input.trim() || !connected}
            className={cn(
              "p-3 rounded-md transition-colors",
              input.trim() && connected
                ? "bg-sky-600 hover:bg-sky-700"
                : "bg-slate-700/40 opacity-50 cursor-not-allowed"
            )}
            title="Gönder"
          >
            <Send size={20} />
          </button>
        </div>

        {/* Bağlantı durumu mesajı */}
        {!connected && (
          <div className="mt-2 text-xs text-center text-amber-400">
            {connecting
              ? "Sunucuya bağlanılıyor, lütfen bekleyin..."
              : "Sunucu bağlantısı kesildi. Yeniden bağlanmak için butona tıklayın."}
          </div>
        )}
      </form>
    </div>
  )
}
