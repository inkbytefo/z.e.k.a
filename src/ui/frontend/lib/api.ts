/**
 * Z.E.K.A API istemcisi
 *
 * Backend API ile doğrudan iletişim kurmak için kullanılan fonksiyonlar
 */

export interface Message {
  role: string;
  content: string;
  timestamp?: string;
}

export interface ChatResponse {
  success: boolean;
  message?: string;
  response: string;
  conversation_id?: string;
  model?: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
}

export interface ModelListResponse {
  models: ModelInfo[];
  current_model: string;
}

export interface SetModelResponse {
  success: boolean;
  model: string;
  message?: string;
}

export interface EmbeddingModelInfo {
  id: string;
  name: string;
  provider: string;
  description?: string;
}

export interface EmbeddingModelListResponse {
  models: EmbeddingModelInfo[];
  current_model: string;
  current_function: string;
}

export interface SetEmbeddingModelResponse {
  success: boolean;
  model: string;
  function: string;
  message?: string;
}

export interface UserModelPreferences {
  ai_model: string | null;
  embedding_model: string | null;
  embedding_function: string | null;
  voice_model: string | null;
}

export interface UserModelPreferencesResponse {
  success: boolean;
  preferences: UserModelPreferences;
  message?: string;
}

export interface SetUserModelPreferenceRequest {
  user_id: string;
  model_type: string;  // ai_model, embedding_model, embedding_function, voice_model
  model_value: string;
}

// Kimlik doğrulama modelleri
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface UserResponse {
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
  last_updated: string;
  is_admin: boolean;
}

export interface UserUpdateRequest {
  email?: string;
  full_name?: string;
  password?: string;
  is_active?: boolean;
}

// Hava durumu modelleri
export interface WeatherResponse {
  location: string;
  country: string;
  temperature: number;
  feels_like: number;
  temp_unit: string;
  humidity: number;
  pressure: number;
  wind_speed: number;
  wind_unit: string;
  wind_direction: number;
  clouds: number;
  weather_id: number;
  weather_main: string;
  weather_description: string;
  weather_icon: string;
  sunrise: string;
  sunset: string;
  timestamp: string;
}

export interface ForecastItem {
  datetime: string;
  date: string;
  time: string;
  temperature: number;
  feels_like: number;
  temp_unit: string;
  humidity: number;
  pressure: number;
  wind_speed: number;
  wind_unit: string;
  wind_direction: number;
  clouds: number;
  weather_id: number;
  weather_main: string;
  weather_description: string;
  weather_icon: string;
}

export interface ForecastResponse {
  location: string;
  country: string;
  forecasts: ForecastItem[];
}

// API Anahtarı Yönetimi Türleri
export interface APIKeyRequest {
  service_name: string;
  api_key: string;
  metadata?: Record<string, any>;
}

export interface APIKeyResponse {
  success: boolean;
  message?: string;
}

export interface APIKeyListItem {
  service_name: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface APIKeyListResponse {
  keys: APIKeyListItem[];
}

export interface APIProviderInfo {
  id: string;
  name: string;
  description: string;
  url: string;
  auth_type: string;
  auth_key_name: string;
  logo_url?: string;
  models_endpoint?: string;
  requires_auth: boolean;
}

export interface APIProviderListResponse {
  providers: APIProviderInfo[];
}

// Backend API URL'sini al
const API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

/**
 * Yeni bir sohbet mesajı gönderir
 *
 * @param message Kullanıcı mesajı
 * @param model Kullanılacak model (opsiyonel)
 * @returns API yanıtı
 */
export async function sendChatMessage(message: string, model?: string): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        user_id: 'default_user', // Gerçek uygulamada kullanıcı kimliği kullanılmalı
        language: 'tr',
        style: 'friendly',
        model: model
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Sohbet mesajı gönderme hatası:', error);
    throw error;
  }
}

/**
 * Sohbet geçmişini getirir
 *
 * @param limit Getirilecek maksimum mesaj sayısı
 * @returns Sohbet geçmişi
 */
export async function getConversationHistory(limit: number = 10): Promise<Message[]> {
  try {
    const response = await fetch(`${API_URL}/api/conversation-history?limit=${limit}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'User-ID': 'default_user', // Gerçek uygulamada kullanıcı kimliği kullanılmalı
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    const data = await response.json();
    return data.messages || [];
  } catch (error) {
    console.error('Sohbet geçmişi getirme hatası:', error);
    return [];
  }
}

/**
 * Kullanılabilir modelleri listeler
 *
 * @returns Kullanılabilir modeller ve mevcut model
 */
export async function getAvailableModels(): Promise<ModelListResponse> {
  try {
    const response = await fetch(`${API_URL}/api/models`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Model listesi getirme hatası:', error);
    throw error;
  }
}

/**
 * Kullanılacak modeli değiştirir
 *
 * @param model Kullanılacak model ID'si
 * @returns API yanıtı
 */
export async function setModel(model: string): Promise<SetModelResponse> {
  try {
    const response = await fetch(`${API_URL}/api/models/set`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Model değiştirme hatası:', error);
    throw error;
  }
}

/**
 * Kullanılabilir embedding modellerini listeler
 *
 * @returns Kullanılabilir embedding modelleri ve mevcut model
 */
export async function getAvailableEmbeddingModels(): Promise<EmbeddingModelListResponse> {
  try {
    const response = await fetch(`${API_URL}/api/embedding-models`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Embedding model listesi getirme hatası:', error);
    throw error;
  }
}

/**
 * Kullanılacak embedding modelini değiştirir
 *
 * @param model Kullanılacak embedding model ID'si
 * @returns API yanıtı
 */
export async function setEmbeddingModel(model: string): Promise<SetEmbeddingModelResponse> {
  try {
    const response = await fetch(`${API_URL}/api/embedding-models/set`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Embedding model değiştirme hatası:', error);
    throw error;
  }
}

/**
 * Kullanıcının model tercihlerini getirir
 *
 * @param userId Kullanıcı ID'si
 * @returns Kullanıcı model tercihleri
 */
export async function getUserModelPreferences(userId: string = 'default_user'): Promise<UserModelPreferencesResponse> {
  try {
    const response = await fetch(`${API_URL}/api/user/model-preferences?user_id=${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Kullanıcı model tercihleri getirme hatası:', error);
    throw error;
  }
}

/**
 * Kullanıcının model tercihini ayarlar
 *
 * @param userId Kullanıcı ID'si
 * @param modelType Model türü (ai_model, embedding_model, embedding_function, voice_model)
 * @param modelValue Model değeri
 * @returns API yanıtı
 */
export async function setUserModelPreference(
  userId: string = 'default_user',
  modelType: string,
  modelValue: string
): Promise<UserModelPreferencesResponse> {
  try {
    const response = await fetch(`${API_URL}/api/user/model-preferences/set`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        model_type: modelType,
        model_value: modelValue,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Kullanıcı model tercihi ayarlama hatası:', error);
    throw error;
  }
}

// Kimlik doğrulama fonksiyonları

/**
 * Kullanıcı girişi yapar
 *
 * @param username Kullanıcı adı
 * @param password Şifre
 * @returns Token yanıtı
 */
export async function login(username: string, password: string): Promise<TokenResponse> {
  try {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        password,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Giriş hatası');
    }

    const data = await response.json();

    // Token'ları localStorage'a kaydet
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    return data;
  } catch (error) {
    console.error('Giriş hatası:', error);
    throw error;
  }
}

/**
 * Kullanıcı kaydı yapar
 *
 * @param userData Kullanıcı verileri
 * @returns Kullanıcı yanıtı
 */
export async function register(userData: RegisterRequest): Promise<UserResponse> {
  try {
    const response = await fetch(`${API_URL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Kayıt hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Kayıt hatası:', error);
    throw error;
  }
}

/**
 * Token yeniler
 *
 * @param refreshToken Yenileme token'ı
 * @returns Token yanıtı
 */
export async function refreshToken(refreshToken: string): Promise<TokenResponse> {
  try {
    const response = await fetch(`${API_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Token yenileme hatası');
    }

    const data = await response.json();

    // Token'ları localStorage'a kaydet
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    return data;
  } catch (error) {
    console.error('Token yenileme hatası:', error);
    throw error;
  }
}

/**
 * Kullanıcı çıkışı yapar
 */
export function logout(): void {
  // Token'ları localStorage'dan sil
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

/**
 * API anahtarı ayarlar
 *
 * @param serviceName Servis adı
 * @param apiKey API anahtarı
 * @param metadata Ek meta veriler (opsiyonel)
 * @returns API yanıtı
 */
export async function setAPIKey(
  serviceName: string,
  apiKey: string,
  metadata?: Record<string, any>
): Promise<APIKeyResponse> {
  try {
    const response = await fetch(`${API_URL}/api/api-keys/set`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        service_name: serviceName,
        api_key: apiKey,
        metadata: metadata
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('API anahtarı ayarlama hatası:', error);
    throw error;
  }
}

/**
 * API anahtarını siler
 *
 * @param serviceName Servis adı
 * @returns API yanıtı
 */
export async function deleteAPIKey(serviceName: string): Promise<APIKeyResponse> {
  try {
    const response = await fetch(`${API_URL}/api/api-keys/delete/${serviceName}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('API anahtarı silme hatası:', error);
    throw error;
  }
}

/**
 * Kayıtlı API anahtarlarını listeler
 *
 * @returns API anahtarı listesi
 */
export async function listAPIKeys(): Promise<APIKeyListResponse> {
  try {
    const response = await fetch(`${API_URL}/api/api-keys/list`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('API anahtarları listeleme hatası:', error);
    throw error;
  }
}

/**
 * Desteklenen API sağlayıcılarını listeler
 *
 * @returns API sağlayıcı listesi
 */
export async function listAPIProviders(): Promise<APIProviderListResponse> {
  try {
    const response = await fetch(`${API_URL}/api/api-keys/providers`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('API sağlayıcıları listeleme hatası:', error);
    throw error;
  }
}

/**
 * Mevcut kullanıcı bilgilerini getirir
 *
 * @returns Kullanıcı yanıtı
 */
export async function getCurrentUser(): Promise<UserResponse> {
  try {
    const token = localStorage.getItem('access_token');

    if (!token) {
      throw new Error('Oturum açılmamış');
    }

    const response = await fetch(`${API_URL}/api/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token geçersiz, çıkış yap
        logout();
        throw new Error('Oturum süresi doldu');
      }

      const errorData = await response.json();
      throw new Error(errorData.detail || 'Kullanıcı bilgileri getirme hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Kullanıcı bilgileri getirme hatası:', error);
    throw error;
  }
}

/**
 * Kullanıcı bilgilerini günceller
 *
 * @param userData Güncellenecek kullanıcı verileri
 * @returns Güncellenmiş kullanıcı yanıtı
 */
export async function updateUser(userData: UserUpdateRequest): Promise<UserResponse> {
  try {
    const token = localStorage.getItem('access_token');

    if (!token) {
      throw new Error('Oturum açılmamış');
    }

    const response = await fetch(`${API_URL}/api/auth/me`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token geçersiz, çıkış yap
        logout();
        throw new Error('Oturum süresi doldu');
      }

      const errorData = await response.json();
      throw new Error(errorData.detail || 'Kullanıcı güncelleme hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Kullanıcı güncelleme hatası:', error);
    throw error;
  }
}

// Hava durumu API fonksiyonları

/**
 * Mevcut hava durumunu getirir
 *
 * @param location Konum adı (şehir, ilçe, vb.)
 * @param units Birim sistemi (metric, imperial, standard)
 * @returns Hava durumu verileri
 */
export async function getCurrentWeather(
  location: string,
  units: string = 'metric'
): Promise<WeatherResponse> {
  try {
    const response = await fetch(
      `${API_URL}/api/weather/current?location=${encodeURIComponent(location)}&units=${units}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Hava durumu alma hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Hava durumu alma hatası:', error);
    throw error;
  }
}

/**
 * Hava durumu tahminini getirir
 *
 * @param location Konum adı (şehir, ilçe, vb.)
 * @param units Birim sistemi (metric, imperial, standard)
 * @param days Tahmin günü sayısı (maksimum 5)
 * @returns Hava durumu tahmini verileri
 */
export async function getWeatherForecast(
  location: string,
  units: string = 'metric',
  days: number = 1
): Promise<ForecastResponse> {
  try {
    const response = await fetch(
      `${API_URL}/api/weather/forecast?location=${encodeURIComponent(location)}&units=${units}&days=${days}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Hava durumu tahmini alma hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Hava durumu tahmini alma hatası:', error);
    throw error;
  }
}

/**
 * Saatlik hava durumu tahminini getirir
 *
 * @param location Konum adı (şehir, ilçe, vb.)
 * @param units Birim sistemi (metric, imperial, standard)
 * @param hours Saat sayısı (maksimum 48)
 * @returns Saatlik hava durumu tahmini verileri
 */
export async function getHourlyForecast(
  location: string,
  units: string = 'metric',
  hours: number = 24
): Promise<ForecastItem[]> {
  try {
    const response = await fetch(
      `${API_URL}/api/weather/hourly?location=${encodeURIComponent(location)}&units=${units}&hours=${hours}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Saatlik hava durumu tahmini alma hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Saatlik hava durumu tahmini alma hatası:', error);
    throw error;
  }
}

/**
 * Günlük hava durumu tahminini getirir
 *
 * @param location Konum adı (şehir, ilçe, vb.)
 * @param units Birim sistemi (metric, imperial, standard)
 * @param days Gün sayısı (maksimum 5)
 * @returns Günlük hava durumu tahmini verileri
 */
export async function getDailyForecast(
  location: string,
  units: string = 'metric',
  days: number = 5
): Promise<ForecastItem[]> {
  try {
    const response = await fetch(
      `${API_URL}/api/weather/daily?location=${encodeURIComponent(location)}&units=${units}&days=${days}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Günlük hava durumu tahmini alma hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Günlük hava durumu tahmini alma hatası:', error);
    throw error;
  }
}
