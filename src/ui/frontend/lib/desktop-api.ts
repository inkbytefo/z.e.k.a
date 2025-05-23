/**
 * Z.E.K.A Masaüstü Denetleyicisi API istemcisi
 *
 * Masaüstü denetleyicisi ile ilgili API fonksiyonları
 */

// Backend API URL'sini al
const API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

// Masaüstü denetleyicisi yanıt tipleri
export interface DesktopResponse {
  success: boolean;
  message?: string;
  data?: any;
}

export interface FileInfo {
  name: string;
  type: 'file' | 'directory';
  path: string;
  size?: number;
  modified?: string;
  created?: string;
}

export interface DirectoryListResponse extends DesktopResponse {
  data: FileInfo[];
}

export interface ScreenshotResponse extends DesktopResponse {
  data: {
    image_data: string; // Base64 encoded image
    timestamp: string;
    path?: string;
  };
}

export interface TextExtractionResponse extends DesktopResponse {
  data: {
    text: string;
    confidence?: number;
    language?: string;
  };
}

export interface WindowInfo {
  title: string;
  process_name: string;
  process_id: number;
  is_active: boolean;
  position?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface WindowListResponse extends DesktopResponse {
  data: WindowInfo[];
}

export interface SystemInfoResponse extends DesktopResponse {
  data: {
    os: string;
    version: string;
    hostname: string;
    cpu_usage: number;
    memory_usage: number;
    total_memory: number;
    disk_usage: number;
    total_disk: number;
    uptime: number;
  };
}

/**
 * Dizin içeriğini listeler
 *
 * @param path Listelenecek dizin yolu
 * @returns Dizin içeriği
 */
export async function listDirectory(path: string): Promise<DirectoryListResponse> {
  try {
    const response = await fetch(`${API_URL}/api/desktop/list-directory?path=${encodeURIComponent(path)}`, {
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
    console.error('Dizin listeleme hatası:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Bilinmeyen hata',
    };
  }
}

/**
 * Ekran görüntüsü alır
 *
 * @param region Ekran bölgesi (x, y, genişlik, yükseklik) - opsiyonel
 * @param save_path Kaydedilecek dosya yolu - opsiyonel
 * @returns Ekran görüntüsü yanıtı
 */
export async function captureScreenshot(
  region?: { x: number, y: number, width: number, height: number },
  save_path?: string
): Promise<ScreenshotResponse> {
  try {
    const params = new URLSearchParams();
    if (region) {
      params.append('region', JSON.stringify(region));
    }
    if (save_path) {
      params.append('save_path', save_path);
    }

    const response = await fetch(`${API_URL}/api/desktop/screenshot?${params.toString()}`, {
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
    console.error('Ekran görüntüsü alma hatası:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Bilinmeyen hata',
    };
  }
}

/**
 * Görüntüden metin çıkarır
 *
 * @param image_data Base64 kodlanmış görüntü verisi veya dosya yolu
 * @param is_path Görüntü verisi bir dosya yolu mu?
 * @param language OCR dili (tur+eng gibi)
 * @returns Metin çıkarma yanıtı
 */
export async function extractTextFromImage(
  image_data: string,
  is_path: boolean = false,
  language: string = 'tur+eng'
): Promise<TextExtractionResponse> {
  try {
    const response = await fetch(`${API_URL}/api/desktop/extract-text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_data,
        is_path,
        language,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Metin çıkarma hatası:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Bilinmeyen hata',
    };
  }
}

/**
 * Sistem komutunu çalıştırır
 *
 * @param command Çalıştırılacak komut
 * @returns Komut çalıştırma yanıtı
 */
export async function executeCommand(command: string): Promise<DesktopResponse> {
  try {
    const response = await fetch(`${API_URL}/api/desktop/execute-command`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        command,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Komut çalıştırma hatası:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Bilinmeyen hata',
    };
  }
}

/**
 * Açık pencereleri listeler
 *
 * @returns Pencere listesi yanıtı
 */
export async function listWindows(): Promise<WindowListResponse> {
  try {
    const response = await fetch(`${API_URL}/api/desktop/list-windows`, {
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
    console.error('Pencere listeleme hatası:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Bilinmeyen hata',
      data: [],
    };
  }
}

/**
 * Yeni dosya oluşturur
 *
 * @param path Dosya yolu
 * @param content Dosya içeriği
 * @returns İşlem sonucu
 */
export async function createFile(path: string, content: string = ""): Promise<DesktopResponse> {
  try {
    const response = await fetch(`${API_URL}/api/desktop/create-file`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        path,
        content,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Dosya oluşturma hatası:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Bilinmeyen hata',
    };
  }
}

/**
 * Yeni dizin oluşturur
 *
 * @param path Dizin yolu
 * @returns İşlem sonucu
 */
export async function createDirectory(path: string): Promise<DesktopResponse> {
  try {
    const response = await fetch(`${API_URL}/api/desktop/create-directory`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        path,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Dizin oluşturma hatası:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Bilinmeyen hata',
    };
  }
}

/**
 * Dosya veya dizin siler
 *
 * @param path Silinecek öğe yolu
 * @param recursive Dizin içeriğiyle birlikte sil (dizinler için)
 * @returns İşlem sonucu
 */
export async function deleteItem(path: string, recursive: boolean = false): Promise<DesktopResponse> {
  try {
    const response = await fetch(`${API_URL}/api/desktop/delete-item`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        path,
        recursive,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Öğe silme hatası:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Bilinmeyen hata',
    };
  }
}

/**
 * Pencereyi etkinleştirir
 *
 * @param processId İşlem ID'si
 * @returns İşlem sonucu
 */
export async function activateWindow(processId: number): Promise<DesktopResponse> {
  try {
    const response = await fetch(`${API_URL}/api/desktop/activate-window`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        process_id: processId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('Pencere etkinleştirme hatası:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Bilinmeyen hata',
    };
  }
}

/**
 * İşlemi sonlandırır
 *
 * @param processId İşlem ID'si
 * @returns İşlem sonucu
 */
export async function terminateProcess(processId: number): Promise<DesktopResponse> {
  try {
    const response = await fetch(`${API_URL}/api/desktop/terminate-process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        process_id: processId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'API hatası');
    }

    return await response.json();
  } catch (error) {
    console.error('İşlem sonlandırma hatası:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Bilinmeyen hata',
    };
  }
}

/**
 * Sistem bilgilerini getirir
 *
 * @returns Sistem bilgileri yanıtı
 */
export async function getSystemInfo(): Promise<SystemInfoResponse> {
  try {
    const response = await fetch(`${API_URL}/api/desktop/system-info`, {
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
    console.error('Sistem bilgisi alma hatası:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Bilinmeyen hata',
      data: {
        os: 'Unknown',
        version: 'Unknown',
        hostname: 'Unknown',
        cpu_usage: 0,
        memory_usage: 0,
        total_memory: 0,
        disk_usage: 0,
        total_disk: 0,
        uptime: 0,
      },
    };
  }
}
