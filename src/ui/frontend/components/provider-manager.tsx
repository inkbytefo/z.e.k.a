'use client';

import React, { useState, useEffect } from 'react';
import { 
  getProviders, 
  addProvider, 
  removeProvider, 
  discoverProviderModels,
  getProviderDetails,
  type ProviderInfo,
  type AddProviderRequest 
} from '../lib/api';

interface ProviderManagerProps {
  onClose?: () => void;
}

export default function ProviderManager({ onClose }: ProviderManagerProps) {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<ProviderInfo | null>(null);

  // Form state
  const [formData, setFormData] = useState<AddProviderRequest>({
    provider_id: '',
    name: '',
    base_url: '',
    description: '',
    models: [],
    auth_type: 'bearer'
  });

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    try {
      setLoading(true);
      const response = await getProviders();
      setProviders(response.providers);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sağlayıcılar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleAddProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await addProvider(formData);
      setShowAddForm(false);
      setFormData({
        provider_id: '',
        name: '',
        base_url: '',
        description: '',
        models: [],
        auth_type: 'bearer'
      });
      await loadProviders();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sağlayıcı eklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveProvider = async (providerId: string) => {
    if (!confirm('Bu sağlayıcıyı kaldırmak istediğinizden emin misiniz?')) {
      return;
    }

    try {
      setLoading(true);
      await removeProvider(providerId);
      await loadProviders();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sağlayıcı kaldırılamadı');
    } finally {
      setLoading(false);
    }
  };

  const handleDiscoverModels = async (providerId: string) => {
    try {
      setLoading(true);
      const response = await discoverProviderModels(providerId);
      alert(`${response.count} model keşfedildi: ${response.models.join(', ')}`);
      await loadProviders();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Model keşfi başarısız');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (providerId: string) => {
    try {
      const details = await getProviderDetails(providerId);
      setSelectedProvider(details);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sağlayıcı detayları alınamadı');
    }
  };

  if (loading && providers.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Sağlayıcılar yükleniyor...</span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">AI Sağlayıcı Yönetimi</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAddForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Yeni Sağlayıcı Ekle
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
            >
              Kapat
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Sağlayıcı Listesi */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {providers.map((provider) => (
          <div key={provider.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-semibold text-lg">{provider.name}</h3>
              <div className="flex gap-1">
                {provider.custom && (
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                    Özel
                  </span>
                )}
                <span className={`text-xs px-2 py-1 rounded ${
                  provider.enabled 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {provider.enabled ? 'Aktif' : 'Pasif'}
                </span>
              </div>
            </div>
            
            <p className="text-gray-600 text-sm mb-2">{provider.description}</p>
            <p className="text-gray-500 text-xs mb-2">URL: {provider.base_url}</p>
            <p className="text-gray-500 text-xs mb-3">
              Modeller: {provider.models.length} adet
            </p>

            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => handleViewDetails(provider.id)}
                className="bg-gray-100 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-200 transition-colors"
              >
                Detaylar
              </button>
              <button
                onClick={() => handleDiscoverModels(provider.id)}
                className="bg-blue-100 text-blue-700 px-3 py-1 rounded text-sm hover:bg-blue-200 transition-colors"
              >
                Model Keşfi
              </button>
              {provider.custom && (
                <button
                  onClick={() => handleRemoveProvider(provider.id)}
                  className="bg-red-100 text-red-700 px-3 py-1 rounded text-sm hover:bg-red-200 transition-colors"
                >
                  Kaldır
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Yeni Sağlayıcı Ekleme Formu */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-xl font-bold mb-4">Yeni Sağlayıcı Ekle</h3>
            
            <form onSubmit={handleAddProvider} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sağlayıcı ID
                </label>
                <input
                  type="text"
                  value={formData.provider_id}
                  onChange={(e) => setFormData({...formData, provider_id: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="örn: my-openai"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sağlayıcı Adı
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="örn: My OpenAI"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Base URL
                </label>
                <input
                  type="url"
                  value={formData.base_url}
                  onChange={(e) => setFormData({...formData, base_url: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://api.openai.com/v1"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Açıklama
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Sağlayıcı açıklaması"
                  rows={2}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Kimlik Doğrulama Türü
                </label>
                <select
                  value={formData.auth_type}
                  onChange={(e) => setFormData({...formData, auth_type: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="bearer">Bearer Token</option>
                  <option value="none">Kimlik Doğrulama Yok</option>
                </select>
              </div>

              <div className="flex gap-2 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Ekleniyor...' : 'Ekle'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="flex-1 bg-gray-500 text-white py-2 rounded-lg hover:bg-gray-600 transition-colors"
                >
                  İptal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Sağlayıcı Detayları Modal */}
      {selectedProvider && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">{selectedProvider.name} Detayları</h3>
              <button
                onClick={() => setSelectedProvider(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-3">
              <div>
                <strong>ID:</strong> {selectedProvider.id}
              </div>
              <div>
                <strong>Açıklama:</strong> {selectedProvider.description}
              </div>
              <div>
                <strong>Base URL:</strong> {selectedProvider.base_url}
              </div>
              <div>
                <strong>Kimlik Doğrulama:</strong> {selectedProvider.auth_type}
              </div>
              <div>
                <strong>API Anahtarı Gerekli:</strong> {selectedProvider.requires_api_key ? 'Evet' : 'Hayır'}
              </div>
              <div>
                <strong>Streaming Desteği:</strong> {selectedProvider.supports_streaming ? 'Evet' : 'Hayır'}
              </div>
              <div>
                <strong>Durum:</strong> {selectedProvider.enabled ? 'Aktif' : 'Pasif'}
              </div>
              <div>
                <strong>Tür:</strong> {selectedProvider.custom ? 'Özel' : 'Varsayılan'}
              </div>
              {selectedProvider.created_at && (
                <div>
                  <strong>Oluşturulma:</strong> {new Date(selectedProvider.created_at).toLocaleString('tr-TR')}
                </div>
              )}
              {selectedProvider.last_model_discovery && (
                <div>
                  <strong>Son Model Keşfi:</strong> {new Date(selectedProvider.last_model_discovery).toLocaleString('tr-TR')}
                </div>
              )}
              <div>
                <strong>Modeller ({selectedProvider.models.length} adet):</strong>
                <div className="mt-2 max-h-32 overflow-y-auto">
                  {selectedProvider.models.length > 0 ? (
                    <ul className="list-disc list-inside space-y-1">
                      {selectedProvider.models.map((model, index) => (
                        <li key={index} className="text-sm text-gray-600">{model}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-500 text-sm">Henüz model keşfedilmemiş</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
