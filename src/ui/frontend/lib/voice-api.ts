import { API_URL } from './api';

/**
 * Ses tanıma sonucu
 */
export interface SpeechToTextResponse {
  success: boolean;
  text?: string;
  error?: string;
  command?: string;
  result?: any;
}

/**
 * Ses sentezleme sonucu
 */
export interface TextToSpeechResponse {
  success: boolean;
  audio_data?: string; // Base64 encoded audio
  error?: string;
}

/**
 * Ses tanıma ayarları
 */
export interface SpeechToTextOptions {
  language?: string;
  timeout?: number;
}

/**
 * Ses sentezleme ayarları
 */
export interface TextToSpeechOptions {
  voice_id?: string;
  rate?: number;
  pitch?: number;
  volume?: number;
}

/**
 * Ses verisini metne dönüştürür (backend API kullanarak)
 * 
 * @param audioBlob Ses verisi
 * @param options Ses tanıma ayarları
 * @returns Tanıma sonucu
 */
export async function speechToText(
  audioBlob: Blob,
  options: SpeechToTextOptions = {}
): Promise<SpeechToTextResponse> {
  try {
    // FormData oluştur
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');
    
    // Opsiyonel parametreleri ekle
    if (options.language) {
      formData.append('language', options.language);
    }
    
    if (options.timeout) {
      formData.append('timeout', options.timeout.toString());
    }
    
    // API isteği gönder
    const response = await fetch(`${API_URL}/api/voice/speech-to-text`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Ses tanıma hatası');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Ses tanıma hatası:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Bilinmeyen hata'
    };
  }
}

/**
 * Metni ses verisine dönüştürür (backend API kullanarak)
 * 
 * @param text Sese dönüştürülecek metin
 * @param options Ses sentezleme ayarları
 * @returns Sentezleme sonucu
 */
export async function textToSpeech(
  text: string,
  options: TextToSpeechOptions = {}
): Promise<TextToSpeechResponse> {
  try {
    // API isteği gönder
    const response = await fetch(`${API_URL}/api/voice/text-to-speech`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        voice_id: options.voice_id,
        rate: options.rate,
        pitch: options.pitch,
        volume: options.volume,
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Ses sentezleme hatası');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Ses sentezleme hatası:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Bilinmeyen hata'
    };
  }
}

/**
 * Ses kaydı yapar ve blob olarak döndürür
 * 
 * @param timeLimit Kayıt süresi limiti (ms)
 * @returns Ses verisi (Blob)
 */
export function recordAudio(timeLimit: number = 10000): Promise<Blob> {
  return new Promise((resolve, reject) => {
    // Tarayıcı desteğini kontrol et
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      reject(new Error('Tarayıcınız ses kaydını desteklemiyor.'));
      return;
    }
    
    let mediaRecorder: MediaRecorder;
    const chunks: Blob[] = [];
    
    // Mikrofon erişimi iste
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        // MediaRecorder oluştur
        mediaRecorder = new MediaRecorder(stream);
        
        // Veri topla
        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) {
            chunks.push(e.data);
          }
        };
        
        // Kayıt tamamlandığında
        mediaRecorder.onstop = () => {
          // Stream'i kapat
          stream.getTracks().forEach(track => track.stop());
          
          // Blob oluştur
          const audioBlob = new Blob(chunks, { type: 'audio/wav' });
          resolve(audioBlob);
        };
        
        // Hata durumunda
        mediaRecorder.onerror = (e) => {
          stream.getTracks().forEach(track => track.stop());
          reject(e);
        };
        
        // Kaydı başlat
        mediaRecorder.start();
        
        // Süre limiti
        setTimeout(() => {
          if (mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
          }
        }, timeLimit);
      })
      .catch(error => {
        reject(error);
      });
  });
}

export default {
  speechToText,
  textToSpeech,
  recordAudio
};
