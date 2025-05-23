import { useState, useEffect, useCallback, useRef } from 'react';

interface SpeechRecognitionHook {
  isListening: boolean;
  transcript: string;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
  browserSupportsSpeechRecognition: boolean;
  error?: string;
}

/**
 * Web Speech API için React hook
 * 
 * @param language Tanıma dili (varsayılan: 'tr-TR')
 * @param continuous Sürekli tanıma modu (varsayılan: false)
 * @param interimResults Ara sonuçları gösterme (varsayılan: true)
 * @returns SpeechRecognitionHook
 */
export function useSpeechRecognition({
  language = 'tr-TR',
  continuous = false,
  interimResults = true,
}: {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
} = {}): SpeechRecognitionHook {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | undefined>(undefined);
  const recognitionRef = useRef<any>(null);
  const browserSupportsSpeechRecognition = typeof window !== 'undefined' && 
    (window.SpeechRecognition || window.webkitSpeechRecognition);

  // SpeechRecognition nesnesini oluştur
  useEffect(() => {
    if (!browserSupportsSpeechRecognition) {
      setError('Tarayıcınız Web Speech API\'yi desteklemiyor.');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = continuous;
    recognitionRef.current.interimResults = interimResults;
    recognitionRef.current.lang = language;

    recognitionRef.current.onresult = (event: any) => {
      const current = event.resultIndex;
      const result = event.results[current];
      const transcriptText = result[0].transcript;
      
      if (result.isFinal) {
        setTranscript(transcriptText);
      } else {
        // Ara sonuçları göster
        setTranscript(transcriptText);
      }
    };

    recognitionRef.current.onerror = (event: any) => {
      setError(`Ses tanıma hatası: ${event.error}`);
      stopListening();
    };

    recognitionRef.current.onend = () => {
      if (isListening) {
        setIsListening(false);
      }
    };

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [browserSupportsSpeechRecognition, continuous, interimResults, language, isListening]);

  const startListening = useCallback(() => {
    if (!browserSupportsSpeechRecognition) {
      setError('Tarayıcınız Web Speech API\'yi desteklemiyor.');
      return;
    }

    setError(undefined);
    setIsListening(true);
    
    try {
      recognitionRef.current.start();
    } catch (err) {
      // Zaten dinleme yapılıyorsa, önce durdur sonra başlat
      if (err instanceof DOMException && err.name === 'InvalidStateError') {
        recognitionRef.current.stop();
        setTimeout(() => {
          recognitionRef.current.start();
        }, 100);
      } else {
        setError(`Ses tanıma başlatılamadı: ${err}`);
        setIsListening(false);
      }
    }
  }, [browserSupportsSpeechRecognition]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript('');
  }, []);

  return {
    isListening,
    transcript,
    startListening,
    stopListening,
    resetTranscript,
    browserSupportsSpeechRecognition,
    error
  };
}

// Web Speech API için TypeScript tanımlamaları
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}

export default useSpeechRecognition;
