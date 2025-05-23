"use client"

import { useState, useEffect, useRef } from "react"
import { createPortal } from "react-dom"
import {
  getAvailableModels,
  setModel,
  getUserModelPreferences,
  setUserModelPreference,
  listAPIKeys,
  listAPIProviders,
  type ModelInfo,
  type APIKeyListItem,
  type APIProviderInfo
} from "@/lib/api"
import { Settings, Check, ChevronDown, Plus, Search, X, AlertCircle, Key } from "lucide-react"

interface ModelSelectorProps {
  onModelChange?: (model: string) => void
  className?: string
}

export default function ModelSelector({ onModelChange, className }: ModelSelectorProps) {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [currentModel, setCurrentModel] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState<string>("")
  const [isAddingCustomModel, setIsAddingCustomModel] = useState(false)
  const [customModelId, setCustomModelId] = useState<string>("")
  const [customModelProvider, setCustomModelProvider] = useState<string>("")
  const [customModelName, setCustomModelName] = useState<string>("")
  const [apiKeys, setApiKeys] = useState<APIKeyListItem[]>([])
  const [providers, setProviders] = useState<APIProviderInfo[]>([])
  const [missingApiKeys, setMissingApiKeys] = useState<string[]>([])
  const searchInputRef = useRef<HTMLInputElement>(null)
  const customProviderRef = useRef<HTMLInputElement>(null)

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
        const response = await getAvailableModels()
        setModels(response.models)

        // Kullanıcı tercihlerini yükle
        try {
          const userPrefs = await getUserModelPreferences()
          if (userPrefs.success && userPrefs.preferences.ai_model) {
            setCurrentModel(userPrefs.preferences.ai_model)
          } else {
            setCurrentModel(response.current_model)
          }
        } catch (prefErr) {
          console.error("Kullanıcı tercihleri yüklenirken hata:", prefErr)
          setCurrentModel(response.current_model)
        }

        // Eksik API anahtarlarını kontrol et
        checkMissingAPIKeys(response.models)
      } catch (err) {
        console.error("Modeller yüklenirken hata:", err)
        setError("Modeller yüklenemedi")
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  // Eksik API anahtarlarını kontrol et
  const checkMissingAPIKeys = (modelList: ModelInfo[]) => {
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
      const response = await setModel(modelId)

      if (response.success) {
        setCurrentModel(response.model)

        // Kullanıcı tercihlerini kaydet
        try {
          await setUserModelPreference("default_user", "ai_model", modelId)
          console.log("Kullanıcı model tercihi kaydedildi:", modelId)
        } catch (prefErr) {
          console.error("Kullanıcı tercihi kaydedilirken hata:", prefErr)
        }

        if (onModelChange) {
          onModelChange(response.model)
        }
      } else {
        setError(response.message || "Model değiştirilemedi")
      }
    } catch (err) {
      console.error("Model değiştirilirken hata:", err)
      setError("Model değiştirilemedi")
    } finally {
      setIsLoading(false)
      setIsOpen(false)
      setIsAddingCustomModel(false)
      resetCustomModelForm()
    }
  }

  // Özel model ekle
  const handleAddCustomModel = () => {
    // Özel model ekleme formunu göster
    setIsAddingCustomModel(true)

    // Odağı provider input'una ver
    setTimeout(() => {
      if (customProviderRef.current) {
        customProviderRef.current.focus()
      }
    }, 100)
  }

  // Özel model formunu sıfırla
  const resetCustomModelForm = () => {
    setCustomModelProvider("")
    setCustomModelName("")
    setCustomModelId("")
  }

  // Özel model kaydet
  const handleSaveCustomModel = async () => {
    if (!customModelProvider || !customModelName) {
      setError("Sağlayıcı ve model adı gereklidir")
      return
    }

    // Model ID'sini oluştur
    const modelId = customModelId || `${customModelProvider}/${customModelName}`

    // Modeli ekle
    try {
      // Önce modeli models listesine ekle
      const newModel: ModelInfo = {
        id: modelId,
        provider: customModelProvider,
        name: customModelName
      }

      // Eğer model zaten varsa, ekleme
      if (!models.some(m => m.id === modelId)) {
        setModels(prev => [...prev, newModel])
      }

      // Modeli değiştir
      await handleModelChange(modelId)
    } catch (err) {
      console.error("Özel model eklenirken hata:", err)
      setError("Özel model eklenemedi")
    } finally {
      setIsAddingCustomModel(false)
      resetCustomModelForm()
    }
  }

  // Arama terimini değiştir
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value)
  }

  // Arama kutusunu temizle
  const clearSearch = () => {
    setSearchTerm("")
    if (searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }

  // Modelleri filtrele
  const filteredModels = models.filter(model => {
    const searchLower = searchTerm.toLowerCase()
    return (
      model.provider.toLowerCase().includes(searchLower) ||
      model.name.toLowerCase().includes(searchLower) ||
      model.id.toLowerCase().includes(searchLower)
    )
  })

  // Modeli görüntülenebilir formata dönüştür
  const formatModelName = (modelId: string): string => {
    const model = models.find(m => m.id === modelId)
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
      'anthropic': 'text-purple-400',
      'openai': 'text-green-400',
      'google': 'text-blue-400',
      'meta': 'text-orange-400',
      'mistral': 'text-red-400',
      'cohere': 'text-yellow-400'
    }

    return colors[provider] || 'text-gray-400'
  }

  // Dropdown'ın konumunu hesapla
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 })
  const buttonRef = useRef<HTMLButtonElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const [mounted, setMounted] = useState(false)

  // Component mount olduğunda
  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  // Dropdown açıldığında konumunu hesapla
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()

      setDropdownPosition({
        top: rect.bottom + window.scrollY + 4, // 4px margin
        left: rect.left,
        width: rect.width
      })
    }
  }, [isOpen])

  // Dropdown dışına tıklandığında kapat
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isOpen &&
        buttonRef.current &&
        dropdownRef.current &&
        !buttonRef.current.contains(event.target as Node) &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    // Pencere boyutu değiştiğinde dropdown'ı kapat
    const handleResize = () => {
      if (isOpen) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    window.addEventListener('resize', handleResize)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      window.removeEventListener('resize', handleResize)
    }
  }, [isOpen])

  return (
    <div className={`${className}`}>
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="flex items-center space-x-1 bg-black/30 border border-cyan-500/30 rounded-lg px-3 py-2 text-sm text-white hover:bg-black/40 transition-colors w-full shadow-md hover:shadow-lg"
      >
        <Settings size={14} className="mr-1 text-cyan-400" />
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
          className="fixed z-[9999] w-[calc(100%-2rem)] md:w-80 bg-black/90 backdrop-blur-md border border-cyan-500/30 rounded-xl shadow-lg py-2 max-h-96 overflow-hidden flex flex-col"
          style={{
            top: `${dropdownPosition.top}px`,
            left: `${dropdownPosition.left}px`,
            width: window.innerWidth < 768 ? 'calc(100% - 2rem)' : `${dropdownPosition.width}px`,
          }}>
          <div className="px-3 py-2 text-sm text-cyan-400 border-b border-cyan-500/20 flex justify-between items-center">
            <span>AI Modeli Seçin</span>
            <button
              onClick={handleAddCustomModel}
              className="text-cyan-400 hover:text-cyan-300 transition-colors p-1 rounded-full hover:bg-cyan-950/30"
              title="Özel model ekle"
            >
              <Plus size={16} />
            </button>
          </div>

          {error && (
            <div className="px-3 py-2 text-xs text-red-400 border-b border-cyan-500/20">
              {error}
            </div>
          )}

          {/* Arama kutusu */}
          <div className="px-3 py-2 border-b border-cyan-500/20">
            <div className="relative">
              <Search size={14} className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchTerm}
                onChange={handleSearchChange}
                placeholder="Model ara..."
                className="w-full bg-black/50 border border-cyan-500/30 rounded-lg pl-8 pr-8 py-1.5 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
              />
              {searchTerm && (
                <button
                  onClick={clearSearch}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300"
                >
                  <X size={14} />
                </button>
              )}
            </div>
          </div>

          {/* Özel model ekleme formu */}
          {isAddingCustomModel && (
            <div className="px-3 py-2 border-b border-cyan-500/20 bg-cyan-950/20">
              <div className="text-xs text-cyan-400 mb-2">Özel Model Ekle</div>

              <div className="space-y-2">
                <input
                  ref={customProviderRef}
                  type="text"
                  value={customModelProvider}
                  onChange={(e) => setCustomModelProvider(e.target.value)}
                  placeholder="Sağlayıcı (örn: anthropic, openai)"
                  className="w-full bg-black/50 border border-cyan-500/30 rounded-lg px-3 py-1.5 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                />

                <input
                  type="text"
                  value={customModelName}
                  onChange={(e) => setCustomModelName(e.target.value)}
                  placeholder="Model adı (örn: claude-3-opus)"
                  className="w-full bg-black/50 border border-cyan-500/30 rounded-lg px-3 py-1.5 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                />

                <input
                  type="text"
                  value={customModelId}
                  onChange={(e) => setCustomModelId(e.target.value)}
                  placeholder="Model ID (opsiyonel, otomatik oluşturulur)"
                  className="w-full bg-black/50 border border-cyan-500/30 rounded-lg px-3 py-1.5 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                />

                <div className="flex space-x-2">
                  <button
                    onClick={handleSaveCustomModel}
                    className="flex-1 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg py-1.5 text-sm transition-colors"
                  >
                    Ekle
                  </button>

                  <button
                    onClick={() => {
                      setIsAddingCustomModel(false)
                      resetCustomModelForm()
                    }}
                    className="flex-1 bg-gray-700 hover:bg-gray-800 text-white rounded-lg py-1.5 text-sm transition-colors"
                  >
                    İptal
                  </button>
                </div>
              </div>
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
                      className={`w-full px-3 py-3 text-left text-sm hover:bg-cyan-950/30 transition-colors flex items-center justify-between ${model.id === currentModel ? 'bg-cyan-950/20' : ''} ${isApiKeyMissing ? 'opacity-50 cursor-not-allowed' : ''}`}
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
                      </div>

                      {model.id === currentModel && (
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
