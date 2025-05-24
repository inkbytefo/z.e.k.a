"use client"

import { useState, useEffect } from "react"
import { Key, Plus, Eye, EyeOff, Trash2, Check, X } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  listAPIKeys,
  addAPIKey,
  deleteAPIKey,
  type APIKeyListItem
} from "@/lib/api"

interface APIKeysWidgetProps {
  className?: string
  size?: "small" | "large"
}

export default function APIKeysWidget({
  className,
  size = "large"
}: APIKeysWidgetProps) {
  const [apiKeys, setApiKeys] = useState<APIKeyListItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isAddingKey, setIsAddingKey] = useState(false)
  const [newKeyService, setNewKeyService] = useState("")
  const [newKeyValue, setNewKeyValue] = useState("")
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set())

  // Load API keys
  useEffect(() => {
    loadAPIKeys()
  }, [])

  const loadAPIKeys = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await listAPIKeys()
      setApiKeys(response.keys || [])
    } catch (err) {
      console.error("API keys loading error:", err)
      setError("API anahtarları yüklenemedi")
      setApiKeys([]) // Fallback to empty array
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddKey = async () => {
    if (!newKeyService.trim() || !newKeyValue.trim()) {
      setError("Servis adı ve API anahtarı gereklidir")
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      const response = await addAPIKey(newKeyService.trim(), newKeyValue.trim())

      if (response.success) {
        await loadAPIKeys()
        setIsAddingKey(false)
        setNewKeyService("")
        setNewKeyValue("")
      } else {
        setError(response.message || "API anahtarı eklenemedi")
      }
    } catch (err) {
      console.error("API key add error:", err)
      setError("API anahtarı eklenemedi")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteKey = async (serviceName: string) => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await deleteAPIKey(serviceName)

      if (response.success) {
        await loadAPIKeys()
      } else {
        setError(response.message || "API anahtarı silinemedi")
      }
    } catch (err) {
      console.error("API key delete error:", err)
      setError("API anahtarı silinemedi")
    } finally {
      setIsLoading(false)
    }
  }

  const toggleKeyVisibility = (serviceName: string) => {
    const newVisible = new Set(visibleKeys)
    if (newVisible.has(serviceName)) {
      newVisible.delete(serviceName)
    } else {
      newVisible.add(serviceName)
    }
    setVisibleKeys(newVisible)
  }

  const maskApiKey = (key: string): string => {
    if (key.length <= 8) return "*".repeat(key.length)
    return key.substring(0, 4) + "*".repeat(key.length - 8) + key.substring(key.length - 4)
  }

  const getServiceColor = (service: string): string => {
    const colors: Record<string, string> = {
      'openai': 'bg-green-500',
      'anthropic': 'bg-purple-500',
      'google': 'bg-blue-500',
      'mistral': 'bg-red-500',
      'cohere': 'bg-yellow-500'
    }
    return colors[service.toLowerCase()] || 'bg-gray-500'
  }

  if (size === "small") {
    return (
      <div className={cn("relative", className)}>
        <button
          onClick={() => setIsAddingKey(!isAddingKey)}
          className="w-full h-full flex flex-col items-center justify-center space-y-2 ios-transition ios-hover-scale"
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-yellow-500 to-orange-600 flex items-center justify-center">
            <Key size={16} className="text-white" />
          </div>
          <div className="text-center">
            <div className="ios-text-primary text-xs font-medium">API Keys</div>
            <div className="ios-text-secondary text-xs">
              {apiKeys.length} anahtar
            </div>
          </div>
        </button>
      </div>
    )
  }

  return (
    <div className={cn("space-y-3", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Key size={18} className="ios-text-secondary" />
          <span className="ios-text-primary text-sm font-medium">API Anahtarları</span>
        </div>
        <button
          onClick={() => setIsAddingKey(!isAddingKey)}
          className="p-1 rounded-md ios-text-secondary hover:ios-text-primary ios-transition"
        >
          <Plus size={14} />
        </button>
      </div>

      {/* Add Key Form */}
      {isAddingKey && (
        <div className="p-3 rounded-lg bg-white/5 border border-white/10 space-y-2">
          <input
            type="text"
            value={newKeyService}
            onChange={(e) => setNewKeyService(e.target.value)}
            placeholder="Servis adı (örn: openai)"
            className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 ios-text-primary placeholder:ios-text-tertiary text-sm focus:outline-none focus:border-blue-500/50"
          />
          <input
            type="password"
            value={newKeyValue}
            onChange={(e) => setNewKeyValue(e.target.value)}
            placeholder="API anahtarı"
            className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 ios-text-primary placeholder:ios-text-tertiary text-sm focus:outline-none focus:border-blue-500/50"
          />
          <div className="flex space-x-2">
            <button
              onClick={handleAddKey}
              disabled={isLoading}
              className="flex-1 px-3 py-2 rounded-lg bg-blue-500 hover:bg-blue-600 text-white text-sm ios-transition disabled:opacity-50"
            >
              <Check size={14} className="inline mr-1" />
              Ekle
            </button>
            <button
              onClick={() => {
                setIsAddingKey(false)
                setNewKeyService("")
                setNewKeyValue("")
                setError(null)
              }}
              className="flex-1 px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 ios-text-primary text-sm ios-transition"
            >
              <X size={14} className="inline mr-1" />
              İptal
            </button>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/20">
          <p className="text-red-400 text-xs">{error}</p>
        </div>
      )}

      {/* API Keys List */}
      <div className="space-y-2">
        {isLoading && apiKeys.length === 0 ? (
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="ios-text-secondary text-sm text-center">Yükleniyor...</div>
          </div>
        ) : apiKeys.length === 0 ? (
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="ios-text-secondary text-sm text-center">
              Henüz API anahtarı eklenmemiş
            </div>
          </div>
        ) : (
          apiKeys.map((apiKey) => (
            <div
              key={apiKey.service_name}
              className="p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 ios-transition"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <div className={cn("w-3 h-3 rounded-full", getServiceColor(apiKey.service_name))} />
                  <div className="flex-1 min-w-0">
                    <div className="ios-text-primary text-sm font-medium">
                      {apiKey.service_name}
                    </div>
                    <div className="ios-text-tertiary text-xs font-mono">
                      {visibleKeys.has(apiKey.service_name)
                        ? apiKey.masked_key
                        : maskApiKey(apiKey.masked_key)
                      }
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => toggleKeyVisibility(apiKey.service_name)}
                    className="p-1 rounded-md ios-text-secondary hover:ios-text-primary ios-transition"
                  >
                    {visibleKeys.has(apiKey.service_name) ? (
                      <EyeOff size={14} />
                    ) : (
                      <Eye size={14} />
                    )}
                  </button>
                  <button
                    onClick={() => handleDeleteKey(apiKey.service_name)}
                    disabled={isLoading}
                    className="p-1 rounded-md text-red-400 hover:text-red-300 ios-transition disabled:opacity-50"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
