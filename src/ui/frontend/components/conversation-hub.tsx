"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Send, Mic, MicOff, Volume2, VolumeX } from "lucide-react"
import useSpeechRecognition from "@/hooks/useSpeechRecognition"
import useSpeechSynthesis from "@/hooks/useSpeechSynthesis"
import { speechToText, textToSpeech } from "@/lib/voice-api"

interface Message {
  role: string
  content: string
  typing?: boolean
}

interface ConversationHubProps {
  messages: Message[]
  onSendMessage: (message: string) => void
}

export default function ConversationHub({ messages, onSendMessage }: ConversationHubProps) {
  const [input, setInput] = useState("")
  const [displayMessages, setDisplayMessages] = useState<Message[]>([])
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

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

  // Transcript değiştiğinde input alanını güncelle
  useEffect(() => {
    if (transcript) {
      setInput(transcript)
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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [displayMessages])

  // Asistan mesajlarını sesli okuma
  useEffect(() => {
    if (messages.length > 0 && messages[messages.length - 1].role === "assistant") {
      const lastMessage = messages[messages.length - 1];

      // Otomatik sesli okuma özelliği burada etkinleştirilebilir
      // speak(lastMessage.content);
    }
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      onSendMessage(input)
      setInput("")
      resetTranscript()
    }
  }

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

  return (
    <div className="flex flex-col h-full">
      <div className="zeka-panel-header rounded-t-lg p-3">
        <h2 className="text-sky-400 text-lg font-medium flex items-center">
          <span className="w-2 h-2 bg-sky-400 rounded-full mr-2 animate-pulse"></span>
          Conversation Interface
        </h2>
      </div>

      <div className="flex-1 bg-transparent backdrop-blur-sm border-x border-sky-700/20 p-4 overflow-y-auto">
        {/* Hata mesajı */}
        {error && (
          <div className="mb-4 p-3 bg-rose-900/30 border border-rose-700/30 rounded-md text-rose-300 text-sm">
            <p>{error}</p>
          </div>
        )}

        <div className="space-y-4">
          {displayMessages.map((message, index) => (
            <div
              key={index}
              className={cn(
                "max-w-[80%] p-4 rounded-md transition-all duration-300",
                message.role === "user"
                  ? "bg-sky-900/40 backdrop-blur-sm border border-sky-700/30 ml-auto shadow-[0_4px_15px_rgba(0,120,215,0.1)] hover:shadow-[0_4px_20px_rgba(0,120,215,0.15)]"
                  : "bg-slate-800/40 backdrop-blur-sm border border-slate-700/30 shadow-[0_4px_15px_rgba(0,0,0,0.2)] hover:shadow-[0_4px_20px_rgba(0,0,0,0.3)]",
              )}
            >
              <div className="text-xs text-slate-300 mb-2 flex items-center justify-between">
                <div className="flex items-center">
                  {message.role === "user" ? (
                    <>
                      <div className="w-2 h-2 bg-amber-400 rounded-full mr-2"></div>
                      <span>You</span>
                    </>
                  ) : (
                    <>
                      <div className="w-2 h-2 bg-sky-400 rounded-full mr-2"></div>
                      <span>Z.E.K.A</span>
                    </>
                  )}
                </div>

                {/* Asistan mesajları için ses düğmesi */}
                {message.role === "assistant" && (
                  <button
                    onClick={() => toggleSpeakMessage(message.content)}
                    className="text-slate-300 hover:text-sky-400 transition-colors"
                    title={isSpeaking ? "Konuşmayı durdur" : "Sesli oku"}
                  >
                    {isSpeaking ? <VolumeX size={14} /> : <Volume2 size={14} />}
                  </button>
                )}
              </div>
              <div className={cn(
                message.role === "user" ? "text-white" : "text-sky-100",
                "leading-relaxed"
              )}>
                {message.content}
                {message.typing && (
                  <span className="inline-block w-2 h-4 bg-sky-400 ml-1 animate-pulse"></span>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="bg-slate-800/40 backdrop-blur-sm border border-sky-700/20 rounded-b-lg p-4">
        <form onSubmit={handleSubmit} className="flex items-center space-x-3">
          <div className="relative flex-1">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              className="w-full bg-slate-800/40 backdrop-blur-sm border border-sky-700/30 rounded-md px-4 py-3 text-white placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500/50"
            />
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
            type="button"
            onClick={toggleVoiceInput}
            className={`p-3 rounded-md transition-colors ${
              isListening
                ? "bg-sky-600 text-white hover:bg-sky-700"
                : "bg-slate-800/40 backdrop-blur-sm border border-sky-700/30 text-sky-400 hover:bg-sky-900/50"
            }`}
            title={isListening ? "Ses kaydını durdur" : "Sesli komut ver"}
          >
            {isListening ? <MicOff size={20} /> : <Mic size={20} />}
          </button>

          <button
            type="submit"
            className="bg-sky-600 p-3 rounded-md text-white hover:bg-sky-700 transition-colors"
            title="Mesajı gönder"
          >
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  )
}