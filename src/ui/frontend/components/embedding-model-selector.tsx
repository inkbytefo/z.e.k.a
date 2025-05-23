"use client"

import { useState, useEffect, useRef } from "react"
import { createPortal } from "react-dom"
import {
  getAvailableEmbeddingModels,
  setEmbeddingModel,
  getUserModelPreferences,
  setUserModelPreference,
  listAPIKeys,
  listAPIProviders,
  type EmbeddingModelInfo,
  type APIKeyListItem,
  type APIProviderInfo
} from "@/lib/api"
import { Settings, Check, ChevronDown, Database, Search, X, AlertCircle, Key } from "lucide-react"

interface EmbeddingModelSelectorProps {
  onModelChange?: (model: string) => void
  className?: string
}

export default function EmbeddingModelSelector({ onModelChange, className }: EmbeddingModelSelectorProps) {
  const [models, setModels] = useState<EmbeddingModelInfo[]>([])
  const [currentModel, setCurrentModel] = useState<string>("")
  const [currentFunction, setCurrentFunction] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState<string>("")
  const [apiKeys, setApiKeys] = useState<APIKeyListItem[]>([])
  const [providers, setProviders] = useState<APIProviderInfo[]>([])
  const [missingApiKeys, setMissingApiKeys] = useState<string[]>([])
  const searchInputRef = useRef<HTMLInputElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 })
  const [mounted, setMounted] = useState(false)

  // Modelleri ve API anahtarlarını yükle
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // API sağlayıcılarını yükle
        try {
          const providersResponse = await listAPIProviders()
          setProviders(providersResponse.providers)
        } catch (provErr) {
          console.error("API sağlayıcıları yüklenirken hata:", provErr)
        }

        // API anahtarlarını yükle
        try {
          const keysResponse = await listAPIKeys()
          setApiKeys(keysResponse.keys)
        } catch (keyErr) {
          console.error("API anahtarları yüklenirken hata:", keyErr)
        }

        // Modelleri yükle
        const response = await getAvailableEmbeddingModels()
        setModels(response.models)

        // Kullanıcı tercihlerini yükle
        try {
          const userPrefs = await getUserModelPreferences()
          if (userPrefs.success && userPrefs.preferences.embedding_model) {
            setCurrentModel(userPrefs.preferences.embedding_model)
            setCurrentFunction(userPrefs.preferences.embedding_function || response.current_function)
          } else {
            setCurrentModel(response.current_model)
            setCurrentFunction(response.current_function)
          }
        } catch (prefErr) {
          console.error("Kullanıcı tercihleri yüklenirken hata:", prefErr)
          setCurrentModel(response.current_model)
          setCurrentFunction(response.current_function)
        }

        // Eksik API anahtarlarını kontrol et
        checkMissingAPIKeys(response.models)
      } catch (err) {
        console.error("Embedding modelleri yüklenirken hata:", err)
        setError("Embedding modelleri yüklenemedi")
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  // Eksik API anahtarlarını kontrol et
  const checkMissingAPIKeys = (modelList: EmbeddingModelInfo[]) => {
    // Modellerin sağlayıcılarını topla
    const modelProviders = new Set(modelList.map(model => model.provider))

    // Mevcut API anahtarlarını kontrol et
    const existingKeys = new Set(apiKeys.map(key => key.service_name))

    // Eksik API anahtarlarını bul
    const missing = Array.from(modelProviders).filter(provider => !existingKeys.has(provider))
    setMissingApiKeys(missing)
  }

  // Modeli değiştir
  const handleModelChange = async (modelId: string) => {
    if (modelId === currentModel) {
      setIsOpen(false)
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      // Backend'de modeli değiştir
      const response = await setEmbeddingModel(modelId)

      if (response.success) {
        setCurrentModel(response.model)
        setCurrentFunction(response.function)

        // Kullanıcı tercihlerini kaydet
        try {
          await setUserModelPreference("default_user", "embedding_model", response.model)
          await setUserModelPreference("default_user", "embedding_function", response.function)
          console.log("Kullanıcı embedding model tercihi kaydedildi:", response.model)
        } catch (prefErr) {
          console.error("Kullanıcı tercihi kaydedilirken hata:", prefErr)
        }

        if (onModelChange) {
          onModelChange(response.model)
        }
      } else {
        setError(response.message || "Embedding modeli değiştirilemedi")
      }
    } catch (err) {
      console.error("Embedding modeli değiştirilirken hata:", err)
      setError("Embedding modeli değiştirilemedi")
    } finally {
      setIsLoading(false)
      setIsOpen(false)
    }
  }

  // Arama filtreleme
  const filteredModels = models.filter(model => {
    const searchLower = searchTerm.toLowerCase()
    return (
      model.name.toLowerCase().includes(searchLower) ||
      model.provider.toLowerCase().includes(searchLower) ||
      (model.description && model.description.toLowerCase().includes(searchLower))
    )
  })

  // Dropdown pozisyonunu hesapla
  useEffect(() => {
    setMounted(true)

    const updatePosition = () => {
      if (buttonRef.current) {
        const rect = buttonRef.current.getBoundingClientRect()
        setDropdownPosition({
          top: rect.bottom + window.scrollY + 5,
          left: rect.left + window.scrollX,
          width: rect.width
        })
      }
    }

    if (isOpen) {
      updatePosition()
      window.addEventListener('resize', updatePosition)
      window.addEventListener('scroll', updatePosition)
    }

    return () => {
      window.removeEventListener('resize', updatePosition)
      window.removeEventListener('scroll', updatePosition)
    }
  }, [isOpen])

  // Dropdown dışına tıklandığında kapat
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  // Dropdown açıldığında arama kutusuna odaklan
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }, [isOpen])

  // Modeli görüntülenebilir formata dönüştür
  const formatModelName = (modelId: string): string => {
    const model = models.find(m => m.id === modelId || m.name === modelId)
    if (model) {
      return `${model.provider} / ${model.name}`
    }

    // Model bulunamazsa ID'yi parçalara ayır
    const parts = modelId.split('/')
    if (parts.length > 1) {
      return `${parts[0]} / ${parts[1]}`
    }

    return modelId
  }

  // Sağlayıcıya göre renk belirle
  const getProviderColor = (provider: string): string => {
    const colors: Record<string, string> = {
      'sentence-transformers': 'text-blue-400',
      'huggingface': 'text-yellow-400',
      'openai': 'text-green-400',
      'cohere': 'text-purple-400'
    }

    return colors[provider] || 'text-gray-400'
  }

  return (
    <div className={`${className}`}>
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="flex items-center space-x-1 bg-black/30 border border-cyan-500/30 rounded-lg px-3 py-2 text-sm text-white hover:bg-black/40 transition-colors w-full shadow-md hover:shadow-lg"
      >
        <Database size={14} className="mr-1 text-cyan-400" />
        <span className="truncate flex-1 text-left">
          {isLoading ? (
            <span className="flex items-center">
              <span className="animate-pulse mr-1">⏳</span> Yükleniyor...
            </span>
          ) : (
            <span className="flex items-center">
              <span className={`w-2 h-2 rounded-full mr-2 ${getProviderColor(currentModel.split('/')[0])}`}></span>
              {formatModelName(currentModel)}
            </span>
          )}
        </span>
        <ChevronDown size={14} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && mounted && createPortal(
        <div
          ref={dropdownRef}
          className="fixed z-[9999] w-[calc(100%-2rem)] md:w-80 bg-black/90 backdrop-blur-md border border-cyan-500/30 rounded-xl shadow-lg py-2 max-h-[80vh] overflow-hidden flex flex-col"
          style={{
            top: `${dropdownPosition.top}px`,
            left: `${dropdownPosition.left}px`,
            width: window.innerWidth < 768 ? 'calc(100% - 2rem)' : `${dropdownPosition.width}px`,
          }}>
          <div className="px-3 py-2 text-sm text-cyan-400 border-b border-cyan-500/20 flex justify-between items-center">
            <span className="font-medium">Embedding Modeli Seçin</span>
            <div className="text-xs text-gray-400">
              {currentFunction && `Fonksiyon: ${currentFunction}`}
            </div>
          </div>

          {/* Arama kutusu */}
          <div className="px-3 py-2 border-b border-cyan-500/20">
            <div className="relative">
              <Search size={14} className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Model ara..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-black/50 border border-cyan-500/30 rounded-lg pl-8 pr-8 py-1.5 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 transition-all"
              />
              {searchTerm && (
                <button
                  onClick={() => {
                    setSearchTerm("")
                    searchInputRef.current?.focus()
                  }}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  <X size={14} />
                </button>
              )}
            </div>
          </div>

          {/* Hata mesajı */}
          {error && (
            <div className="px-3 py-2 text-sm text-red-400 border-b border-cyan-500/20">
              {error}
            </div>
          )}

          {/* Eksik API anahtarı uyarısı */}
          {missingApiKeys.length > 0 && (
            <div className="px-3 py-2 bg-amber-900/30 border-b border-amber-800/50">
              <div className="flex items-start text-xs text-amber-300">
                <AlertCircle size={14} className="mr-1.5 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium">Eksik API Anahtarları</p>
                  <p className="mt-1">
                    Bazı sağlayıcılar için API anahtarı eksik. Bu modelleri kullanmak için API anahtarlarını eklemeniz gerekiyor.
                  </p>
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {missingApiKeys.map(provider => (
                      <span key={provider} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs bg-amber-900/50 border border-amber-700/50">
                        <Key size={10} className="mr-1" />
                        {provider}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Model listesi */}
          <div className="overflow-y-auto flex-1">
            {filteredModels.length === 0 ? (
              <div className="px-3 py-4 text-sm text-gray-400 text-center">
                {searchTerm ? "Aranan modeller bulunamadı" : "Henüz model yok"}
              </div>
            ) : (
              <div className="divide-y divide-cyan-500/10">
                {filteredModels.map((model) => {
                  // API anahtarı eksik mi kontrol et
                  const isApiKeyMissing = missingApiKeys.includes(model.provider);

                  return (
                    <button
                      key={model.id}
                      onClick={() => handleModelChange(model.id)}
                      disabled={isApiKeyMissing}
                      className={`w-full px-3 py-3 text-left text-sm hover:bg-cyan-950/30 transition-colors flex items-center justify-between ${(model.id === currentModel || model.name === currentModel) ? 'bg-cyan-950/20' : ''} ${isApiKeyMissing ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <div className="flex-1 pr-2">
                        <div className={`text-xs font-medium ${getProviderColor(model.provider)} flex items-center`}>
                          <span className={`w-2 h-2 rounded-full mr-1 ${getProviderColor(model.provider)}`}></span>
                          {model.provider}
                          {isApiKeyMissing && (
                            <span className="ml-2 text-amber-400 flex items-center">
                              <Key size={10} className="mr-0.5" />
                              API anahtarı gerekli
                            </span>
                          )}
                        </div>
                        <div className="text-white font-medium">{model.name}</div>
                        <div className="text-xs text-gray-400 mt-0.5">{model.id}</div>
                        {model.description && (
                          <div className="text-xs text-gray-400 mt-1 italic">{model.description}</div>
                        )}
                      </div>

                      {(model.id === currentModel || model.name === currentModel) && (
                        <div className="bg-cyan-500/20 p-1 rounded-full">
                          <Check size={16} className="text-cyan-400" />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}
