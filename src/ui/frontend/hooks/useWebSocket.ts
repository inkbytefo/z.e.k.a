import { useState, useEffect, useRef, useCallback } from 'react';

// Backend API URL'sini al
const API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface WebSocketHook {
  connected: boolean;
  connecting: boolean;
  messages: WebSocketMessage[];
  sendMessage: (message: any) => void;
  clearMessages: () => void;
  error: string | null;
  connect: () => void;
}

/**
 * WebSocket bağlantısını yöneten React hook
 *
 * @param path WebSocket endpoint yolu (örn. "/api/ws/chat")
 * @param autoReconnect Bağlantı koptuğunda otomatik yeniden bağlanma
 * @param reconnectInterval Yeniden bağlanma aralığı (ms)
 * @param maxReconnectAttempts Maksimum yeniden bağlanma denemesi
 * @returns WebSocketHook
 */
export function useWebSocket(
  path: string,
  autoReconnect: boolean = true,
  reconnectInterval: number = 3000,
  maxReconnectAttempts: number = 5
): WebSocketHook {
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // WebSocket URL'sini oluştur
  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

    // Geliştirme ortamında localhost:8000 kullan, üretimde window.location.host
    const host = process.env.NODE_ENV === 'development' ? 'localhost:8000' : window.location.host;

    // URL oluştur
    const wsUrl = `${protocol}//${host}${path}`;
    console.log("WebSocket URL:", wsUrl);
    return wsUrl;
  }, [path]);

  // WebSocket bağlantısını kur
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      setConnecting(true);
      setError(null);

      const wsUrl = getWebSocketUrl();
      console.log('WebSocket bağlantısı kuruluyor:', wsUrl);

      // Mevcut WebSocket bağlantısını kapat
      if (wsRef.current) {
        wsRef.current.close();
      }

      // Yeni WebSocket bağlantısı oluştur
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setConnected(true);
        setConnecting(false);
        reconnectAttemptsRef.current = 0;
        console.log('WebSocket bağlantısı kuruldu:', wsRef.current?.url);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket mesajı alındı:', data);
          setMessages((prev) => [...prev, data]);
        } catch (e) {
          console.error('WebSocket mesajı işlenirken hata:', e);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket bağlantısı kapandı:', event.code, event.reason);
        setConnected(false);
        setConnecting(false);

        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.log(`WebSocket bağlantısı koptu. Yeniden bağlanılıyor (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);

          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
          }

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setError('Maksimum yeniden bağlanma denemesi aşıldı');
        }
      };

      wsRef.current.onerror = (event) => {
        console.error('WebSocket hatası:', event);
        setError('WebSocket bağlantı hatası');
        setConnecting(false);
      };

    } catch (e) {
      console.error('WebSocket bağlantısı kurulurken hata:', e);
      setError(`WebSocket bağlantısı kurulamadı: ${e instanceof Error ? e.message : String(e)}`);
      setConnecting(false);
    }
  }, [autoReconnect, getWebSocketUrl, maxReconnectAttempts, reconnectInterval]);

  // Mesaj gönder
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof message === 'string' ? message : JSON.stringify(message));
    } else {
      setError('WebSocket bağlantısı açık değil');
    }
  }, []);

  // Mesajları temizle
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Bileşen yüklendiğinde bağlantıyı kur
  useEffect(() => {
    // Otomatik olarak bağlantıyı başlat
    connect();

    // Bileşen kaldırıldığında bağlantıyı kapat
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  // Bağlantı durumunu konsola yazdır
  useEffect(() => {
    console.log("useWebSocket hook durumu:", { connected, connecting, error });
  }, [connected, connecting, error]);

  return {
    connected,
    connecting,
    messages,
    sendMessage,
    clearMessages,
    error,
    connect
  };
}
