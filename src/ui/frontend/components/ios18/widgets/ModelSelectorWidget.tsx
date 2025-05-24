"use client"

import { useState, useEffect } from "react"
import { Brain, ChevronDown, Check, Settings } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  getAvailableModels,
  setModel,
  getUserModelPreferences,
  setUserModelPreference,
  type ModelInfo
} from "@/lib/api"

interface ModelSelectorWidgetProps {
  onModelChange?: (model: string) => void
  className?: string
  size?: "small" | "large"
}

export default function ModelSelectorWidget({
  onModelChange,
  className,
  size = "large"
}: ModelSelectorWidgetProps) {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [currentModel, setCurrentModel] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load models and preferences
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true)
        setError(null)

        const response = await getAvailableModels()
        setModels(response.models)

        // Load user preferences
        try {
          const userPrefs = await getUserModelPreferences()
          if (userPrefs.success && userPrefs.preferences.ai_model) {
            setCurrentModel(userPrefs.preferences.ai_model)
          } else {
            setCurrentModel(response.current_model)
          }
        } catch (prefErr) {
          console.error("User preferences loading error:", prefErr)
          setCurrentModel(response.current_model)
        }
      } catch (err) {
        console.error("Models loading error:", err)
        setError("Modeller yüklenemedi")
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  // Handle model change
  const handleModelChange = async (modelId: string) => {
    if (modelId === currentModel) {
      setIsOpen(false)
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      const response = await setModel(modelId)

      if (response.success) {
        setCurrentModel(response.model)

        // Save user preference
        try {
          await setUserModelPreference("default_user", "ai_model", modelId)
        } catch (prefErr) {
          console.error("User preference save error:", prefErr)
        }

        if (onModelChange) {
          onModelChange(response.model)
        }
      } else {
        setError(response.message || "Model değiştirilemedi")
      }
    } catch (err) {
      console.error("Model change error:", err)
      setError("Model değiştirilemedi")
    } finally {
      setIsLoading(false)
      setIsOpen(false)
    }
  }

  // Format model name for display
  const formatModelName = (modelId: string): string => {
    const model = models.find(m => m.id === modelId)
    if (model) {
      return size === "small" ? model.name : `${model.provider} / ${model.name}`
    }

    const parts = modelId.split('/')
    if (parts.length > 1) {
      return size === "small" ? parts[1] : `${parts[0]} / ${parts[1]}`
    }

    return modelId
  }

  // Get provider color
  const getProviderColor = (provider: string): string => {
    const colors: Record<string, string> = {
      'anthropic': 'bg-purple-500',
      'openai': 'bg-green-500',
      'google': 'bg-blue-500',
      'meta': 'bg-orange-500',
      'mistral': 'bg-red-500',
      'cohere': 'bg-yellow-500'
    }
    return colors[provider] || 'bg-gray-500'
  }

  const currentModelInfo = models.find(m => m.id === currentModel)

  if (size === "small") {
    return (
      <div className={cn("relative", className)}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          disabled={isLoading}
          className="w-full h-full flex flex-col items-center justify-center space-y-2 ios-transition ios-hover-scale"
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Brain size={16} className="text-white" />
          </div>
          <div className="text-center">
            <div className="ios-text-primary text-xs font-medium">AI Model</div>
            <div className="ios-text-secondary text-xs truncate max-w-20">
              {isLoading ? "..." : formatModelName(currentModel)}
            </div>
          </div>
        </button>

        {/* Dropdown for small size */}
        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-2 glass rounded-lg border border-white/20 shadow-lg z-50 max-h-48 overflow-y-auto">
            {models.map((model) => (
              <button
                key={model.id}
                onClick={() => handleModelChange(model.id)}
                className={cn(
                  "w-full px-3 py-2 text-left text-xs ios-transition hover:bg-white/10",
                  model.id === currentModel && "bg-blue-500/20"
                )}
              >
                <div className="flex items-center space-x-2">
                  <div className={cn("w-2 h-2 rounded-full", getProviderColor(model.provider))} />
                  <span className="ios-text-primary truncate">{model.name}</span>
                  {model.id === currentModel && (
                    <Check size={12} className="text-blue-400 ml-auto" />
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={cn("space-y-3", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Brain size={18} className="ios-text-secondary" />
          <span className="ios-text-primary text-sm font-medium">AI Model</span>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-1 rounded-md ios-text-secondary hover:ios-text-primary ios-transition"
        >
          <Settings size={14} />
        </button>
      </div>

      {/* Current Model Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="w-full p-3 rounded-lg bg-white/5 hover:bg-white/10 ios-transition border border-white/10"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {currentModelInfo && (
              <div className={cn("w-3 h-3 rounded-full", getProviderColor(currentModelInfo.provider))} />
            )}
            <div className="text-left">
              <div className="ios-text-primary text-sm font-medium">
                {isLoading ? "Yükleniyor..." : formatModelName(currentModel)}
              </div>
              {currentModelInfo && (
                <div className="ios-text-secondary text-xs">
                  {currentModelInfo.provider}
                </div>
              )}
            </div>
          </div>
          <ChevronDown 
            size={16} 
            className={cn(
              "ios-text-secondary ios-transition",
              isOpen && "rotate-180"
            )} 
          />
        </div>
      </button>

      {/* Error Display */}
      {error && (
        <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/20">
          <p className="text-red-400 text-xs">{error}</p>
        </div>
      )}

      {/* Model List */}
      {isOpen && (
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {models.map((model) => (
            <button
              key={model.id}
              onClick={() => handleModelChange(model.id)}
              className={cn(
                "w-full p-2 rounded-lg text-left ios-transition hover:bg-white/10",
                model.id === currentModel && "bg-blue-500/20 border border-blue-500/30"
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className={cn("w-2 h-2 rounded-full", getProviderColor(model.provider))} />
                  <div>
                    <div className="ios-text-primary text-xs font-medium">{model.name}</div>
                    <div className="ios-text-tertiary text-xs">{model.provider}</div>
                  </div>
                </div>
                {model.id === currentModel && (
                  <Check size={14} className="text-blue-400" />
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
