"use client"

import { useState, useEffect, useRef } from "react"
import { createPortal } from "react-dom"
import {
  listAPIKeys,
  listAPIProviders,
  setAPIKey,
  deleteAPIKey,
  type APIKeyListItem,
  type APIProviderInfo
} from "@/lib/api"
import { 
  Key, 
  Plus, 
  Trash2, 
  AlertCircle, 
  Check, 
  Copy, 
  ExternalLink,
  Eye,
  EyeOff,
  RefreshCw
} from "lucide-react"

interface APIKeyManagerProps {
  className?: string
  onAPIKeyChange?: () => void
}

export default function APIKeyManager({ className, onAPIKeyChange }: APIKeyManagerProps) {
  const [apiKeys, setApiKeys] = useState<APIKeyListItem[]>([])
  const [providers, setProviders] = useState<APIProviderInfo[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState<string>("")
  const [apiKeyValue, setApiKeyValue] = useState<string>("")
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({})
  const [isRefreshing, setIsRefreshing] = useState(false)
  
  // Ref'ler
  const modalRef = useRef<HTMLDivElement>(null)
  
  // API anahtarlarını ve sağlayıcıları yükle
  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      // API anahtarlarını yükle
      const keysResponse = await listAPIKeys()
      setApiKeys(keysResponse.keys)
      
      // API sağlayıcılarını yükle
      const providersResponse = await listAPIProviders()
      setProviders(providersResponse.providers)
      
      // İlk sağlayıcıyı seç
      if (providersResponse.providers.length > 0 && !selectedProvider) {
        setSelectedProvider(providersResponse.providers[0].id)
      }
    } catch (err) {
      console.error("API anahtarları yüklenirken hata:", err)
      setError("API anahtarları yüklenemedi")
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }
  
  // Sayfa yüklendiğinde verileri getir
  useEffect(() => {
    loadData()
  }, [])
  
  // Yenileme işlemi
  const handleRefresh = () => {
    setIsRefreshing(true)
    loadData()
  }
  
  // API anahtarı ekleme
  const handleAddAPIKey = async () => {
    if (!selectedProvider || !apiKeyValue) {
      setError("Lütfen bir sağlayıcı seçin ve API anahtarı girin")
      return
    }
    
    try {
      setIsLoading(true)
      setError(null)
      
      // Seçilen sağlayıcı bilgilerini al
      const provider = providers.find(p => p.id === selectedProvider)
      if (!provider) {
        throw new Error("Geçersiz sağlayıcı")
      }
      
      // API anahtarını kaydet
      const response = await setAPIKey(selectedProvider, apiKeyValue, {
        provider_name: provider.name,
        auth_type: provider.auth_type,
        added_at: new Date().toISOString()
      })
      
      if (response.success) {
        setSuccess(`${provider.name} API anahtarı başarıyla eklendi`)
        setApiKeyValue("")
        setShowAddModal(false)
        
        // Verileri yenile
        await loadData()
        
        // Callback'i çağır
        if (onAPIKeyChange) {
          onAPIKeyChange()
        }
      } else {
        setError(response.message || "API anahtarı eklenemedi")
      }
    } catch (err) {
      console.error("API anahtarı eklenirken hata:", err)
      setError("API anahtarı eklenemedi")
    } finally {
      setIsLoading(false)
    }
  }
  
  // API anahtarı silme
  const handleDeleteAPIKey = async (serviceName: string) => {
    if (!confirm(`${serviceName} API anahtarını silmek istediğinizden emin misiniz?`)) {
      return
    }
    
    try {
      setIsLoading(true)
      setError(null)
      
      // API anahtarını sil
      const response = await deleteAPIKey(serviceName)
      
      if (response.success) {
        setSuccess(`${serviceName} API anahtarı başarıyla silindi`)
        
        // Verileri yenile
        await loadData()
        
        // Callback'i çağır
        if (onAPIKeyChange) {
          onAPIKeyChange()
        }
      } else {
        setError(response.message || "API anahtarı silinemedi")
      }
    } catch (err) {
      console.error("API anahtarı silinirken hata:", err)
      setError("API anahtarı silinemedi")
    } finally {
      setIsLoading(false)
    }
  }
  
  // API anahtarını göster/gizle
  const toggleShowApiKey = (serviceName: string) => {
    setShowApiKey(prev => ({
      ...prev,
      [serviceName]: !prev[serviceName]
    }))
  }
  
  // Sağlayıcı logosu
  const getProviderLogo = (serviceName: string) => {
    const provider = providers.find(p => p.id === serviceName)
    return provider?.logo_url
  }
  
  // Sağlayıcı adı
  const getProviderName = (serviceName: string) => {
    const provider = providers.find(p => p.id === serviceName)
    return provider?.name || serviceName
  }
  
  // Sağlayıcı URL'si
  const getProviderUrl = (serviceName: string) => {
    const provider = providers.find(p => p.id === serviceName)
    return provider?.url
  }
  
  // API anahtarı maskele
  const maskApiKey = (key: string) => {
    if (!key) return "••••••••"
    if (key.length <= 8) return "••••••••"
    return key.substring(0, 4) + "••••••••" + key.substring(key.length - 4)
  }
  
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Başlık ve Yenile butonu */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-white">API Anahtarları</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-1 text-slate-400 hover:text-cyan-400 transition-colors"
            title="Yenile"
          >
            <RefreshCw size={16} className={isRefreshing ? "animate-spin" : ""} />
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center space-x-1 bg-cyan-900/50 hover:bg-cyan-800/50 text-cyan-300 px-2 py-1 rounded-md text-xs transition-colors"
          >
            <Plus size={14} />
            <span>API Anahtarı Ekle</span>
          </button>
        </div>
      </div>
      
      {/* Hata mesajı */}
      {error && (
        <div className="bg-rose-900/20 border border-rose-800 text-rose-300 px-3 py-2 rounded-md text-sm flex items-start">
          <AlertCircle size={16} className="mr-2 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      
      {/* Başarı mesajı */}
      {success && (
        <div className="bg-emerald-900/20 border border-emerald-800 text-emerald-300 px-3 py-2 rounded-md text-sm flex items-start">
          <Check size={16} className="mr-2 mt-0.5 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}
      
      {/* API anahtarları listesi */}
      <div className="space-y-2">
        {isLoading && !isRefreshing ? (
          <div className="text-slate-400 text-sm text-center py-4">
            Yükleniyor...
          </div>
        ) : apiKeys.length === 0 ? (
          <div className="text-slate-400 text-sm text-center py-4 border border-dashed border-slate-700 rounded-md">
            Henüz API anahtarı eklenmemiş
          </div>
        ) : (
          apiKeys.map((key) => (
            <div
              key={key.service_name}
              className="bg-slate-900/50 border border-slate-800 rounded-md p-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getProviderLogo(key.service_name) ? (
                    <img
                      src={getProviderLogo(key.service_name)}
                      alt={getProviderName(key.service_name)}
                      className="w-5 h-5 rounded-full"
                    />
                  ) : (
                    <Key size={16} className="text-cyan-400" />
                  )}
                  <span className="font-medium text-white">{getProviderName(key.service_name)}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <a
                    href={getProviderUrl(key.service_name)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1 text-slate-400 hover:text-cyan-400 transition-colors"
                    title="Sağlayıcı sitesine git"
                  >
                    <ExternalLink size={14} />
                  </a>
                  <button
                    onClick={() => handleDeleteAPIKey(key.service_name)}
                    className="p-1 text-slate-400 hover:text-rose-400 transition-colors"
                    title="API anahtarını sil"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              <div className="mt-2 flex items-center justify-between">
                <div className="text-xs text-slate-400">
                  Eklenme: {new Date(key.created_at).toLocaleDateString()}
                </div>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => toggleShowApiKey(key.service_name)}
                    className="p-1 text-slate-400 hover:text-cyan-400 transition-colors"
                    title={showApiKey[key.service_name] ? "Gizle" : "Göster"}
                  >
                    {showApiKey[key.service_name] ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
      
      {/* API Anahtarı Ekleme Modal */}
      {showAddModal && createPortal(
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div
            ref={modalRef}
            className="bg-slate-900 border border-slate-800 rounded-lg shadow-xl w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-slate-800">
              <h3 className="text-lg font-medium text-white">API Anahtarı Ekle</h3>
            </div>
            <div className="p-4 space-y-4">
              {/* Sağlayıcı seçimi */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-300">
                  API Sağlayıcısı
                </label>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                >
                  <option value="">Sağlayıcı Seçin</option>
                  {providers.map((provider) => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* API anahtarı girişi */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-300">
                  API Anahtarı
                </label>
                <input
                  type="password"
                  value={apiKeyValue}
                  onChange={(e) => setApiKeyValue(e.target.value)}
                  placeholder="API anahtarınızı girin"
                  className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
              
              {/* Seçilen sağlayıcı bilgileri */}
              {selectedProvider && (
                <div className="text-xs text-slate-400 bg-slate-800/50 p-2 rounded-md">
                  {providers.find(p => p.id === selectedProvider)?.description}
                </div>
              )}
            </div>
            <div className="p-4 border-t border-slate-800 flex justify-end space-x-2">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-md transition-colors"
              >
                İptal
              </button>
              <button
                onClick={handleAddAPIKey}
                disabled={isLoading || !selectedProvider || !apiKeyValue}
                className="px-4 py-2 bg-cyan-700 hover:bg-cyan-600 text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? "Ekleniyor..." : "Ekle"}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}
