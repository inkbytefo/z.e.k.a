import { useState, useEffect, useCallback, useRef } from 'react';

interface SpeechSynthesisHook {
  speak: (text: string) => void;
  stop: () => void;
  pause: () => void;
  resume: () => void;
  isSpeaking: boolean;
  isPaused: boolean;
  voices: SpeechSynthesisVoice[];
  setVoice: (voice: SpeechSynthesisVoice) => void;
  setRate: (rate: number) => void;
  setPitch: (pitch: number) => void;
  setVolume: (volume: number) => void;
  browserSupportsSpeechSynthesis: boolean;
  error?: string;
}

/**
 * Web Speech API sentezleme için React hook
 * 
 * @param defaultVoice Varsayılan ses (opsiyonel)
 * @param defaultRate Varsayılan hız (0.1 - 10, varsayılan: 1)
 * @param defaultPitch Varsayılan perde (0 - 2, varsayılan: 1)
 * @param defaultVolume Varsayılan ses seviyesi (0 - 1, varsayılan: 1)
 * @returns SpeechSynthesisHook
 */
export function useSpeechSynthesis({
  defaultVoice,
  defaultRate = 1,
  defaultPitch = 1,
  defaultVolume = 1,
}: {
  defaultVoice?: SpeechSynthesisVoice;
  defaultRate?: number;
  defaultPitch?: number;
  defaultVolume?: number;
} = {}): SpeechSynthesisHook {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [voice, setVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [rate, setRate] = useState(defaultRate);
  const [pitch, setPitch] = useState(defaultPitch);
  const [volume, setVolume] = useState(defaultVolume);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  
  const browserSupportsSpeechSynthesis = typeof window !== 'undefined' && 
    window.speechSynthesis !== undefined;

  // Kullanılabilir sesleri yükle
  useEffect(() => {
    if (!browserSupportsSpeechSynthesis) {
      setError('Tarayıcınız Web Speech API sentezleme özelliğini desteklemiyor.');
      return;
    }

    // Sesleri yükle
    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      setVoices(availableVoices);
      
      // Varsayılan sesi ayarla
      if (defaultVoice) {
        setVoice(defaultVoice);
      } else if (availableVoices.length > 0) {
        // Türkçe ses varsa onu seç, yoksa ilk sesi kullan
        const turkishVoice = availableVoices.find(v => v.lang.includes('tr'));
        setVoice(turkishVoice || availableVoices[0]);
      }
    };

    loadVoices();
    
    // Chrome'da voiceschanged olayını dinle
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    // Sayfa kapatılırken konuşmayı durdur
    return () => {
      if (browserSupportsSpeechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [browserSupportsSpeechSynthesis, defaultVoice]);

  // Konuşma fonksiyonu
  const speak = useCallback((text: string) => {
    if (!browserSupportsSpeechSynthesis) {
      setError('Tarayıcınız Web Speech API sentezleme özelliğini desteklemiyor.');
      return;
    }

    // Önceki konuşmayı durdur
    window.speechSynthesis.cancel();
    setError(undefined);

    try {
      // Yeni konuşma oluştur
      const utterance = new SpeechSynthesisUtterance(text);
      utteranceRef.current = utterance;
      
      // Ayarları uygula
      if (voice) utterance.voice = voice;
      utterance.rate = rate;
      utterance.pitch = pitch;
      utterance.volume = volume;
      
      // Olayları dinle
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => {
        setIsSpeaking(false);
        setIsPaused(false);
      };
      utterance.onerror = (event) => {
        setError(`Konuşma hatası: ${event.error}`);
        setIsSpeaking(false);
        setIsPaused(false);
      };
      
      // Konuşmayı başlat
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      setError(`Konuşma başlatılamadı: ${err}`);
    }
  }, [browserSupportsSpeechSynthesis, voice, rate, pitch, volume]);

  // Konuşmayı durdur
  const stop = useCallback(() => {
    if (browserSupportsSpeechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      setIsPaused(false);
    }
  }, [browserSupportsSpeechSynthesis]);

  // Konuşmayı duraklat
  const pause = useCallback(() => {
    if (browserSupportsSpeechSynthesis && isSpeaking) {
      window.speechSynthesis.pause();
      setIsPaused(true);
    }
  }, [browserSupportsSpeechSynthesis, isSpeaking]);

  // Konuşmayı devam ettir
  const resume = useCallback(() => {
    if (browserSupportsSpeechSynthesis && isPaused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
    }
  }, [browserSupportsSpeechSynthesis, isPaused]);

  return {
    speak,
    stop,
    pause,
    resume,
    isSpeaking,
    isPaused,
    voices,
    setVoice,
    setRate,
    setPitch,
    setVolume,
    browserSupportsSpeechSynthesis,
    error
  };
}

export default useSpeechSynthesis;
