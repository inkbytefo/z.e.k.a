"use client"

import { useState, useEffect } from "react"
import { Mic, MicOff, Volume2, VolumeX } from "lucide-react"
import { cn } from "@/lib/utils"

interface VoiceControlProps {
  onVoiceInput?: (text: string) => void
  onSpeakText?: (text: string) => void
  className?: string
  compact?: boolean
}

export default function VoiceControl({
  onVoiceInput,
  onSpeakText,
  className,
  compact = false
}: VoiceControlProps) {
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [browserSupportsSpeechRecognition, setBrowserSupportsSpeechRecognition] = useState(false)
  const [browserSupportsSpeechSynthesis, setBrowserSupportsSpeechSynthesis] = useState(false)
  
  // Check browser support for speech recognition and synthesis
  useEffect(() => {
    // Check for speech recognition
    const hasSpeechRecognition = 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window
    setBrowserSupportsSpeechRecognition(hasSpeechRecognition)
    
    // Check for speech synthesis
    const hasSpeechSynthesis = 'speechSynthesis' in window
    setBrowserSupportsSpeechSynthesis(hasSpeechSynthesis)
  }, [])
  
  // Initialize speech recognition
  useEffect(() => {
    if (!browserSupportsSpeechRecognition) return
    
    // Create speech recognition instance
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    
    // Configure
    recognition.continuous = false
    recognition.interimResults = false
    recognition.lang = 'tr-TR'
    
    // Add event listeners
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      if (onVoiceInput) {
        onVoiceInput(transcript)
      }
      setIsListening(false)
    }
    
    recognition.onerror = (event) => {
      console.error('Speech recognition error', event.error)
      setIsListening(false)
    }
    
    recognition.onend = () => {
      setIsListening(false)
    }
    
    // Start/stop recognition based on isListening state
    if (isListening) {
      recognition.start()
    }
    
    // Cleanup
    return () => {
      recognition.abort()
    }
  }, [isListening, browserSupportsSpeechRecognition, onVoiceInput])
  
  // Toggle voice input
  const toggleVoiceInput = () => {
    if (!browserSupportsSpeechRecognition) return
    setIsListening(!isListening)
  }
  
  // Speak text
  const speakText = (text: string) => {
    if (!browserSupportsSpeechSynthesis) return
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel()
    
    // Create new utterance
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'tr-TR'
    
    // Set voice (try to find a Turkish voice)
    const voices = window.speechSynthesis.getVoices()
    const turkishVoice = voices.find(voice => voice.lang.includes('tr-TR'))
    if (turkishVoice) {
      utterance.voice = turkishVoice
    }
    
    // Events
    utterance.onstart = () => {
      setIsSpeaking(true)
    }
    
    utterance.onend = () => {
      setIsSpeaking(false)
    }
    
    utterance.onerror = () => {
      setIsSpeaking(false)
    }
    
    // Speak
    window.speechSynthesis.speak(utterance)
  }
  
  // Stop speaking
  const stopSpeaking = () => {
    if (!browserSupportsSpeechSynthesis) return
    window.speechSynthesis.cancel()
    setIsSpeaking(false)
  }
  
  // Toggle speech
  const toggleSpeech = (text: string) => {
    if (isSpeaking) {
      stopSpeaking()
    } else if (onSpeakText) {
      onSpeakText(text)
    }
  }
  
  if (compact) {
    return (
      <div className={cn("flex items-center space-x-1", className)}>
        <button
          onClick={toggleVoiceInput}
          disabled={!browserSupportsSpeechRecognition}
          className={cn(
            "p-1 rounded-md transition-colors",
            isListening
              ? "text-rose-400 animate-pulse"
              : "text-slate-400 hover:text-sky-400",
            !browserSupportsSpeechRecognition && "opacity-50 cursor-not-allowed"
          )}
          title={isListening ? "Ses kaydını durdur" : "Sesli komut ver"}
        >
          {isListening ? <MicOff size={16} /> : <Mic size={16} />}
        </button>
        
        <button
          onClick={() => toggleSpeech("Test konuşma")}
          disabled={!browserSupportsSpeechSynthesis}
          className={cn(
            "p-1 rounded-md transition-colors",
            isSpeaking
              ? "text-sky-400 animate-pulse"
              : "text-slate-400 hover:text-sky-400",
            !browserSupportsSpeechSynthesis && "opacity-50 cursor-not-allowed"
          )}
          title={isSpeaking ? "Konuşmayı durdur" : "Test konuşma"}
        >
          {isSpeaking ? <VolumeX size={16} /> : <Volume2 size={16} />}
        </button>
      </div>
    )
  }
  
  return (
    <div className={cn("flex flex-col space-y-2", className)}>
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-300">Ses Kontrolü</span>
        <div className="flex items-center space-x-1">
          <button
            onClick={toggleVoiceInput}
            disabled={!browserSupportsSpeechRecognition}
            className={cn(
              "p-1.5 rounded-md transition-colors",
              isListening
                ? "bg-rose-600 text-white animate-pulse"
                : "bg-slate-800/40 text-slate-300 hover:bg-sky-900/30 hover:text-sky-300 border border-sky-700/30",
              !browserSupportsSpeechRecognition && "opacity-50 cursor-not-allowed"
            )}
            title={isListening ? "Ses kaydını durdur" : "Sesli komut ver"}
          >
            {isListening ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
          
          <button
            onClick={() => toggleSpeech("Test konuşma")}
            disabled={!browserSupportsSpeechSynthesis}
            className={cn(
              "p-1.5 rounded-md transition-colors",
              isSpeaking
                ? "bg-sky-600 text-white animate-pulse"
                : "bg-slate-800/40 text-slate-300 hover:bg-sky-900/30 hover:text-sky-300 border border-sky-700/30",
              !browserSupportsSpeechSynthesis && "opacity-50 cursor-not-allowed"
            )}
            title={isSpeaking ? "Konuşmayı durdur" : "Test konuşma"}
          >
            {isSpeaking ? <VolumeX size={18} /> : <Volume2 size={18} />}
          </button>
        </div>
      </div>
      
      <div className="text-xs text-slate-400">
        {browserSupportsSpeechRecognition ? 
          "Ses tanıma aktif" : 
          "Tarayıcınız ses tanımayı desteklemiyor"}
      </div>
    </div>
  )
}
