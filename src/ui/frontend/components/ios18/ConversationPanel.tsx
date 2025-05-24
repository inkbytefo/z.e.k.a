"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Mic, MicOff, Loader2, Bot, User, Volume2, VolumeX } from "lucide-react"
import { cn } from "@/lib/utils"
import { Message } from "@/lib/api"
import useSpeechRecognition from "@/hooks/useSpeechRecognition"
import useSpeechSynthesis from "@/hooks/useSpeechSynthesis"

interface ConversationPanelProps {
  messages: Message[]
  onSendMessage: (message: string) => void
  isLoading?: boolean
  className?: string
}

export default function ConversationPanel({
  messages,
  onSendMessage,
  isLoading = false,
  className
}: ConversationPanelProps) {
  const [inputValue, setInputValue] = useState("")
  const [displayMessages, setDisplayMessages] = useState<Message[]>([])
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Speech Recognition Hook
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

  // Speech Synthesis Hook
  const {
    speak,
    stop: stopSpeaking,
    isSpeaking: isSynthesisSpeaking,
    browserSupportsSpeechSynthesis,
    error: synthesisError
  } = useSpeechSynthesis()

  // Handle typing animation effect
  useEffect(() => {
    if (messages.length === 0) return

    const lastMessage = messages[messages.length - 1]

    // If it's an assistant message, show typing animation
    if (lastMessage.role === "assistant" && !displayMessages.some(m => m.content === lastMessage.content)) {
      // Add a temporary typing message
      setDisplayMessages(prev => [...prev.filter(m => !m.typing), { ...lastMessage, content: "", typing: true }])

      // Animate the typing effect
      let currentText = ""
      const fullText = lastMessage.content
      let charIndex = 0

      const typingInterval = setInterval(() => {
        if (charIndex < fullText.length) {
          currentText += fullText[charIndex]
          setDisplayMessages(prev => [
            ...prev.filter(m => !m.typing),
            { ...lastMessage, content: currentText, typing: true }
          ])
          charIndex++
        } else {
          // Typing finished
          setDisplayMessages(prev => [
            ...prev.filter(m => !m.typing),
            { ...lastMessage, typing: false }
          ])
          clearInterval(typingInterval)
        }
      }, 30) // Adjust typing speed here

      return () => clearInterval(typingInterval)
    } else if (lastMessage.role === "user") {
      // User messages appear immediately
      setDisplayMessages(prev => [...prev, lastMessage])
    }
  }, [messages])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [displayMessages])

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto"
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`
    }
  }, [inputValue])

  // Transcript değiştiğinde input alanını güncelle
  useEffect(() => {
    if (transcript) {
      setInputValue(transcript)
    }
  }, [transcript])

  // Hata durumlarını izle
  useEffect(() => {
    if (recognitionError) {
      setError(`Ses tanıma hatası: ${recognitionError}`)
    } else if (synthesisError) {
      setError(`Ses sentezleme hatası: ${synthesisError}`)
    } else {
      setError(null)
    }
  }, [recognitionError, synthesisError])

  const handleSend = () => {
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim())
      setInputValue("")
      resetTranscript()
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const toggleVoice = () => {
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

  const formatTime = (timestamp?: string) => {
    if (!timestamp) return ""
    return new Date(timestamp).toLocaleTimeString('tr-TR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className={cn("ios-main", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Bot size={20} className="text-white" />
          </div>
          <div>
            <h2 className="ios-text-primary text-lg font-semibold">
              Z.E.K.A Asistanı
            </h2>
            <p className="ios-text-secondary text-sm">
              Size nasıl yardımcı olabilirim?
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="ios-text-secondary text-xs">Çevrimiçi</span>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-6 pr-2">
        {displayMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full space-y-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-600/20 flex items-center justify-center">
              <Bot size={32} className="ios-text-secondary" />
            </div>
            <div className="text-center">
              <h3 className="ios-text-primary text-lg font-medium mb-2">
                Merhaba! 👋
              </h3>
              <p className="ios-text-secondary text-sm max-w-md">
                Ben Z.E.K.A, kişisel AI asistanınızım. Size nasıl yardımcı olabilirim?
              </p>
            </div>
          </div>
        ) : (
          displayMessages.map((message, index) => (
            <div
              key={index}
              className={cn(
                "flex items-start space-x-3",
                message.role === "user" ? "flex-row-reverse space-x-reverse" : ""
              )}
            >
              {/* Avatar */}
              <div className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                message.role === "user"
                  ? "bg-gradient-to-br from-green-500 to-emerald-600"
                  : "bg-gradient-to-br from-blue-500 to-purple-600"
              )}>
                {message.role === "user" ? (
                  <User size={16} className="text-white" />
                ) : (
                  <Bot size={16} className="text-white" />
                )}
              </div>

              {/* Message Bubble */}
              <div className={cn(
                "max-w-[70%] rounded-2xl px-4 py-3 ios-transition relative group",
                message.role === "user"
                  ? "bg-blue-500 text-white ml-auto"
                  : "glass border border-white/20"
              )}>
                {/* Voice Control for Assistant Messages */}
                {message.role === "assistant" && !message.typing && (
                  <button
                    onClick={() => toggleSpeakMessage(message.content)}
                    className="absolute top-2 right-2 p-1 rounded-md opacity-0 group-hover:opacity-100 ios-transition hover:bg-white/10"
                    title={isSpeaking ? "Konuşmayı durdur" : "Sesli oku"}
                  >
                    {isSpeaking ? (
                      <VolumeX size={12} className="ios-text-secondary" />
                    ) : (
                      <Volume2 size={12} className="ios-text-secondary" />
                    )}
                  </button>
                )}

                <p className={cn(
                  "text-sm leading-relaxed whitespace-pre-wrap",
                  message.role === "user" ? "text-white" : "ios-text-primary"
                )}>
                  {message.content}
                  {message.typing && (
                    <span className="inline-block w-2 h-4 bg-blue-400 ml-1 animate-pulse"></span>
                  )}
                </p>

                {/* Timestamp */}
                <div className={cn(
                  "text-xs mt-2 opacity-70",
                  message.role === "user" ? "text-white" : "ios-text-tertiary"
                )}>
                  {formatTime(message.timestamp)}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Bot size={16} className="text-white" />
            </div>
            <div className="glass border border-white/20 rounded-2xl px-4 py-3">
              <div className="flex items-center space-x-2">
                <Loader2 size={16} className="animate-spin ios-text-secondary" />
                <span className="ios-text-secondary text-sm">Z.E.K.A düşünüyor...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="glass border border-white/20 rounded-2xl p-4">
        <div className="flex items-end space-x-3">
          {/* Voice Button */}
          <button
            onClick={toggleVoice}
            className={cn(
              "p-3 rounded-full ios-transition flex-shrink-0 relative",
              isListening
                ? "bg-red-500 hover:bg-red-600"
                : "bg-white/10 hover:bg-white/20"
            )}
          >
            {isListening ? (
              <MicOff size={18} className="text-white" />
            ) : (
              <Mic size={18} className="ios-text-secondary" />
            )}

            {/* Voice Activity Indicator */}
            {isListening && (
              <div className="absolute -top-1 -right-1 flex items-center space-x-1">
                <div className="w-1 h-2 bg-white rounded-full animate-pulse"></div>
                <div className="w-1 h-3 bg-white rounded-full animate-pulse delay-75"></div>
                <div className="w-1 h-1 bg-white rounded-full animate-pulse delay-150"></div>
              </div>
            )}
          </button>

          {/* Text Input */}
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Mesajınızı yazın..."
              className="w-full bg-transparent ios-text-primary placeholder-white/50 resize-none outline-none text-sm leading-relaxed max-h-32"
              rows={1}
              disabled={isLoading}
            />
          </div>

          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading}
            className={cn(
              "p-3 rounded-full ios-transition flex-shrink-0",
              inputValue.trim() && !isLoading
                ? "bg-blue-500 hover:bg-blue-600"
                : "bg-white/10 cursor-not-allowed"
            )}
          >
            {isLoading ? (
              <Loader2 size={18} className="animate-spin text-white/50" />
            ) : (
              <Send size={18} className={inputValue.trim() ? "text-white" : "text-white/50"} />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
